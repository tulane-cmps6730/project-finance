from typing import Any, Text
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from stability_sdk import api
from stability_sdk.animation import AnimationArgs, Animator
from stability_sdk.utils import create_video_from_frames
from tqdm import tqdm
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import math
import os



class Request():
    def __init__(self, media_format, subject_type, subject):
        self.media_format = media_format
        self.subject_type = subject_type
        self.subject = subject

class WebScraper():
    def __init__(self, request: Request):
        self.request = request
    
    def scrape(self):
        if self.request.subject_type == "market":
            return "market research" #replace with actual scraper
        if self.request.subject_type == "ticker":
            return "stock research"
        if self.request.subject_type == "news":
            return "news research"

class Model():
    def __init__(self, request: Request):
        self.request = request
    
    def generate(self, research) -> Text:
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        client = OpenAI(api_key=api_key)

        if self.request.subject_type == "market":
            message_subject = "Based on the following reasearch articles, summarize if" +self.request.subject+" is doing well."
        elif self.request.subject_type == "ticker":
            message_subject = "Based on the following reasearch articles, summarize if" +self.request.subject+" is doing well." 
        elif self.request.subject_type == "news":
            message_subject = "Based on the following reasearch articles, summarize the state of "+self.request.subject+"."


        if self.request.media_format == "text":
            message_format = "Format this summary in the style of a morning brew newsletter"
        elif self.request.media_format == "audio":
            message_format = "Format this summary as a script for a podcast"
        elif self.request.media_format == "video":
            message_format = "Format this summary as a script for an informative video."
        
        
        message_thread = message_subject+message_format+"\n###\n" + research + "\n###"
        messages = [{"role": "system", "content": message_thread}]
        response = client.chat.completions.create(
                    model="gpt-3.5-turbo-0125",
                    messages=messages,
                    )
        content = response.choices[0].message.content
        return content

class Media():
    def __init__(self, request: Request):
        self.request = request
    
    
    def api_context(self):
        load_dotenv()
        STABILITY_HOST = "grpc.stability.ai:443"
        openai_api_key = os.getenv('OPENAI_API_KEY')
        STABILITY_KEY = os.getenv('STABILITY_KEY')
        
        stability_context = api.Context(STABILITY_HOST, STABILITY_KEY)
        openai_client = OpenAI(api_key=openai_api_key)
        return stability_context, openai_client
    
    def generate_audio(self, content: Text, openai_client: OpenAI):
        speech_file_path = Path(__file__).parent / "speech.mp3"
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=content,
        )
        response.stream_to_file(speech_file_path)
        return speech_file_path
    

    def generate_frames(self, content: Text, stability_context: api.Context):
        args = AnimationArgs()
        animation_prompts = {
            0: content,
        }
        negative_prompt = ""
        animator = Animator(
            api_context=stability_context,
            animation_prompts=animation_prompts,
            negative_prompt=negative_prompt,
            args=args,
            out_dir="video_01"
            )
        for _ in tqdm(animator.render(), total=args.max_frames):
            pass
        return animator.out_dir
    
    def generate_media(self, content: Text):
        
        stability_context, openai_client = self.api_context()
        
        if self.request.media_format == "text":
            return content
        
        if self.request.media_format == "audio":
            return self.generate_audio(content, openai_client)
        
        if self.request.media_format == "video":
            out_dir = self.generate_frames(content, stability_context)

            create_video_from_frames(out_dir, "video.mp4", fps=24)
        
    
        
    

        
