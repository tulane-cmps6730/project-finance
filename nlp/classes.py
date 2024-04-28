from typing import Any, Text
from openai import OpenAI
from pathlib import Path
from stability_sdk import api
from stability_sdk.animation import AnimationArgs, Animator
from stability_sdk.utils import create_video_from_frames
from tqdm import tqdm
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import math
import json

input_prompt = "What would you like to learn about? I can teach you about the state of the market, a specific stock, or a current event. Please specify if you would like the information in text, audio, or video format.\n\n"

conversation_function = {
            "type": "function",
            "function": {
                "name": "media_output",
                "description": "Determine if the user wants to learn about the general state of the market, a specific stock, or a current event, and what format the user wants the information in. If a specific stock is requested, the stock ticker should be provided. If a current event is requested, the event name should be provided. The output should be in the requested format.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "media_format": {"type": "string", "enum": ["text", "audio", "video"]},
                        "subject_type": {"type": "string", "enum": ["market","ticker","news"]},
                        "subject": {"type": "string"}
                        },
                    },
                },
            }

subject_type_prompt = {"market":"Based on the following reasearch articles, summarize if {} is doing well.",
                       "ticker":"Based on the following reasearch articles, summarize if {} is doing well.",
                       "news":"Based on the following reasearch articles, summarize the state of {}."}

media_format_prompt = {"text": "Format this summary in the style of a morning brew newsletter", 
                       "audio": "Format this summary as a script for a podcast. Make it very casual and conversational. Include phrases like umm and uhh to make it sound more natural. Add breaths where natural.", 
                       "video": "Format this summary as a script for an informative video."}

class ApiContext():
    def __init__(self, openai_api_key, stability_api_key, stability_host):
        self.openai_api_key = openai_api_key
        self.client = OpenAI(api_key=openai_api_key)
        self.stability_context = api.Context(stability_host, stability_api_key)


class Request():
    def __init__(self, api_context: ApiContext):
        self.client = api_context.client
        
    def process_request(self):
        while True:
            try:
                message = input(input_prompt)
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
                subject_type = arguments["subject_type"]
                subject = arguments["subject"]
                   
                break
            
            except Exception as e:
                print(e)
                print("Sorry, I didn't understand that. Please try again and clearly specify the subject and the desired media format output.")
            
            print(f"Here is the {media_format} information on the {subject_type} {subject}.")
            
            return [media_format, subject_type, subject]
        

class WebScraper():
    def __init__(self, request_params: list):
        self.subject_type = request_params[1]
    
    def scrape(self):
        if self.subject_type == "market":
            return "market research" #replace with actual scraper
        if self.subject_type == "ticker":
            return "stock research"
        if self.subject_type == "news":
            return "news research"

class Model():
    def __init__(self, research: str, request_params: list, api_context: ApiContext):
        self.research = research
        self.request = request_params
        self.client = api_context.client
    
    def generate(self) -> Text:

        message_subject = subject_type_prompt[self.request[1]].format(self.request[2])
        message_format = media_format_prompt[self.request[0]]
        
        
        message_thread = message_subject+message_format+"\n###\n" + self.research + "\n###"
        messages = [{"role": "system", "content": message_thread}]
        response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo-0125",
                    messages=messages,
                    )
        content = response.choices[0].message.content
        return content

class Media():
    def __init__(self, content: Text, request_params: list, api_context: ApiContext):
        self.request = request_params
        self.base_dir = Path(__file__).parent  # Base directory for the script
        self.output_dir = self.base_dir / "output"  # Define a specific output directory
        self.output_dir.mkdir(exist_ok=True)  # Create the output directory if it doesn't exist
        self.client = api_context.client
        self.stability_context = api_context.stability_context
        self.content = content
    
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
        frames_dir.mkdir(exist_ok=True)  # Ensure the directory exists
        args = AnimationArgs()
        animation_prompts = {
            0: self.content,
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
        # Load the video and audio files
        video_clip = VideoFileClip(str(video_path))
        audio_clip = AudioFileClip(str(audio_path))

        # Calculate how many times the video needs to be looped
        loop_count = math.ceil(audio_clip.duration / video_clip.duration)

        # Loop the video clip
        looped_video_clip = concatenate_videoclips([video_clip] * loop_count)

        # Set the looped video clip's audio to the audio clip
        final_clip = looped_video_clip.set_audio(audio_clip)

        # Write the result to a file
        output_path = self.output_dir / output_filename
        final_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac')

        return output_path
   
    
    def generate_media(self):    
        if self.request[0] == "text":
            text_path = self.output_dir / "news.txt"
            with open(text_path, "w") as f:
                f.write(self.content)
            return text_path
        
        if self.request[0] == "audio":
            audio_path = self.generate_audio()
            return audio_path
        
        if self.request[0] == "video":
            audio_path = self.generate_audio()
            
            video_path = self.output_dir / "video.mp4"
            #frames_dir = self.generate_frames(content, stability_context)
            frames_dir = self.output_dir / "video_frames"
            create_video_from_frames(frames_dir, str(video_path), fps=24)

            output_path = self.output_dir / "combined_video.mp4"

            return self.combine_audio_video(str(audio_path), str(video_path), str(output_path))
        



            
        
    
        
    

        
