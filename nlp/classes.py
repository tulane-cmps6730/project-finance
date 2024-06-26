from typing import Any, Text
import os
from openai import OpenAI
from pathlib import Path
from stability_sdk import api
from stability_sdk.animation import AnimationArgs, Animator
from stability_sdk.utils import create_video_from_frames
from tqdm import tqdm
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import math
import json
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)

input_prompt = "What stock would you like to learn about? Please specify if you would like the information in text, audio, or video format.\n\n"

conversation_function = {
    "type": "function",
    "function": {
        "name": "media_output",
        "description": "If a specific stock is requested, the stock ticker should be provided. The output should be in the requested format as either text, video, or audio.",
        "parameters": {
            "type": "object",
            "properties": {
                "media_format": {"type": "string", "enum": ["text", "audio", "video"]},
                "subject": {"type": "string"},
            },
        },
    },
}

media_format_prompt = {
    "text": "Format this summary in the style of a morning brew newsletter",
    "audio": "Format this summary as a script for a podcast. Make it very casual and conversational. Include phrases like umm and uhh to make it sound more natural. Add breaths where natural. The summary should be ready to be read aloud with no cues for the speaker.",
    "video": "Format this summary as the captions for an informative video. The summary should be ready to be attatched to a video with no additional text beyond what would be heard.",
}

animation_prompt_generating_prompt = "Based on the following script, generate a single prompt for an animation LLM that visually represents the content. IMPORTANT: The prompt should be a single sentence that describes the general theme or concept of the script. The prompt should be clear and concise, and should not include any specific details or instructions. The animation LLM will use this prompt to generate a visual representation of the script. Make sure no words or numbers should be displayed in the animation. The animation should be engaging and visually appealing."


class ApiContext:
    def __init__(self, openai_api_key, stability_api_key, stability_host):
        self.openai_api_key = openai_api_key
        self.client = OpenAI(api_key=openai_api_key)
        self.stability_context = api.Context(stability_host, stability_api_key)


class Request:
    def __init__(self, api_context: ApiContext):
        self.client = api_context.client
    
    def process_request(self, message):
        while True:
            try:
                messages = [{"role": "user", "content": message}]
                tools = [conversation_function]
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo-0125",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )

                response_message = response.choices[0].message
                tool_call = response_message.tool_calls[0]
                arguments = json.loads(tool_call.function.arguments)

                media_format = arguments["media_format"]
                subject = arguments["subject"]

                print(f"Here is the {media_format} information on {subject}.")
                return [media_format, subject]

            except Exception as e:
                print(e)
                print(
                    "Sorry, I didn't understand that. Please try again and clearly specify the ticker and the desired media format output."
                )
            

            
    
    def route_request(self):
        return self.process_request(input(input_prompt))


class WebScraper:
    def __init__(self, request_params: list):
        self.subject = request_params[1]
        self.base_dir = Path(__file__).parent
        self.research_dir = self.base_dir / "research"
        self.research_dir.mkdir(exist_ok=True)

    def get_news_articles(self, ticker):
        articles_list = []
        stock = yf.Ticker(ticker)
        news_items = stock.news

        for item in news_items:
            url = item["link"]
            try:
                response = requests.get(
                    url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True
                )
                final_url = response.url
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    article_content = soup.find(
                        "div", {"class": "caas-body"}
                    ) or soup.find("article")
                    if article_content:
                        articles_list.append(
                            {
                                "title": item["title"],
                                "url": final_url,
                                "content": article_content.text,
                            }
                        )
                    else:
                        articles_list.append(
                            {
                                "title": item["title"],
                                "url": final_url,
                                "content": "Content not found - page may use dynamic loading or have a different layout",
                            }
                        )
                else:
                    articles_list.append(
                        {
                            "title": item["title"],
                            "url": final_url,
                            "content": f"Failed to fetch article: HTTP {response.status_code}",
                        }
                    )
            except requests.exceptions.RequestException as e:
                articles_list.append(
                    {
                        "title": item["title"],
                        "url": url,
                        "content": f"Error fetching the article: {str(e)}",
                    }
                )

        return articles_list

    @staticmethod
    def save_to_json(data, path):
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def scrape(self):
        ticker = self.subject
        news_articles = self.get_news_articles(ticker)
        research_path = self.research_dir / f"{ticker}.json"
        self.save_to_json(news_articles, research_path)
        print("News articles saved to JSON.")
        return research_path


class Model:
    def __init__(self, research: str, request_params: list, api_context: ApiContext):
        with open(research, "r", encoding="utf-8") as file:
            self.research = file.read()
            self.subject = request_params[1]
            self.media_format = request_params[0]

        self.request = request_params
        self.client = api_context.client

    def generate_script(self) -> str:

        message_subject = "Based on the following reasearch articles, summarize if {} is doing well.".format(self.subject)
        message_format = media_format_prompt[self.media_format]

        message_thread = (
            message_subject + message_format + "\n###\n" + self.research + "\n###"
        )
        messages = [{"role": "system", "content": message_thread}]
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages,
        )
        content = response.choices[0].message.content
        return content

    def generate_animation_prompt(self) -> str:
        animation_script = self.generate_script()

        message_thread = (
            animation_prompt_generating_prompt + "\n###\n" + animation_script + "\n###"
        )
        messages = [{"role": "system", "content": message_thread}]
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages,
        )
        animation_prompt = response.choices[0].message.content
        return [animation_script, animation_prompt]

    def generate(self) -> list:
        if self.media_format == "text":
            return [self.generate_script(), None]

        if self.media_format == "audio":
            return [self.generate_script(), None]

        if self.media_format == "video":
            return self.generate_animation_prompt()


class Media:
    def __init__(
        self, content, animation_prompt, request_params: list, api_context: ApiContext
    ):
        self.media_format = request_params[0]
        self.base_dir = Path(__file__).parent
        self.output_dir = self.base_dir / "output"
        self.output_dir.mkdir(
            exist_ok=True
        ) 
        self.client = api_context.client
        self.stability_context = api_context.stability_context
        self.content = content
        self.animation_prompt = animation_prompt

    def generate_audio(self):
        speech_file_path = self.output_dir / "speech.mp3"
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=self.content,
        )
        response.stream_to_file(str(speech_file_path))
        return speech_file_path

    def generate_frames(self):
        frames_dir = self.output_dir / "video_frames"
        frames_dir.mkdir(exist_ok=True)
        args = AnimationArgs()
        animation_prompts = {
            0: self.animation_prompt,
        }
        negative_prompt = ""
        animator = Animator(
            api_context=self.stability_context,
            animation_prompts=animation_prompts,
            negative_prompt=negative_prompt,
            args=args,
            out_dir=str(frames_dir),
        )
        for _ in tqdm(animator.render(), total=args.max_frames):
            pass
        return frames_dir

    def combine_audio_video(self, audio_path, video_path, output_filename):

        video_clip = VideoFileClip(str(video_path))
        audio_clip = AudioFileClip(str(audio_path))


        loop_count = math.ceil(audio_clip.duration / video_clip.duration)

        looped_video_clip = concatenate_videoclips([video_clip] * loop_count)

        final_clip = looped_video_clip.set_audio(audio_clip)

        output_path = self.output_dir / output_filename
        final_clip.write_videofile(output_filename, codec="libx264", audio_codec="aac")

        return output_path

    def generate_media(self):
        if self.media_format == "text":
            text_path = self.output_dir / "news.txt"
            with open(text_path, "w") as f:
                f.write(self.content)
            return text_path

        if self.media_format == "audio":
            audio_path = self.generate_audio()
            return audio_path

        if self.media_format == "video":
            audio_path = self.generate_audio()

            video_path = self.output_dir / "video.mp4"
            # frames_dir = self.generate_frames()
            frames_dir = self.output_dir / "video_frames"
            create_video_from_frames(frames_dir, str(video_path), fps=24)

            output_path = self.output_dir / "combined_video.mp4"

            return self.combine_audio_video(
                str(audio_path), str(video_path), str(output_path)
            )


class Conversation:
    def __init__(self) -> None:      
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.PERSIST_DIR = os.path.join(self.BASE_DIR, "storage")
        self.RESEARCH_DIR = os.path.join(self.BASE_DIR, "research")

        if not os.path.exists(self.PERSIST_DIR):
            self.documents = SimpleDirectoryReader(self.RESEARCH_DIR).load_data()
            self.index = VectorStoreIndex.from_documents(self.documents)

            self.index.storage_context.persist(persist_dir=self.PERSIST_DIR)
        else:

            self.storage_context = StorageContext.from_defaults(persist_dir=self.PERSIST_DIR)
            self.index = load_index_from_storage(self.storage_context)


    def query(self, query):
        query_engine = self.index.as_query_engine()
        response = query_engine.query(query)
        return response

