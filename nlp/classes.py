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
            message_format = "Format this summary as a script for a podcast. Make it very casual and conversational. Include phrases like umm and uhh to make it sound more natural. Add breaths where natural."
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
        self.base_dir = Path(__file__).parent  # Base directory for the script
        self.output_dir = self.base_dir / "output"  # Define a specific output directory
        self.output_dir.mkdir(exist_ok=True)  # Create the output directory if it doesn't exist
    
    
    
    def api_context(self):
        load_dotenv()
        STABILITY_HOST = "grpc.stability.ai:443"
        openai_api_key = os.getenv('OPENAI_API_KEY')
        STABILITY_KEY = os.getenv('STABILITY_KEY')
        
        stability_context = api.Context(STABILITY_HOST, STABILITY_KEY)
        openai_client = OpenAI(api_key=openai_api_key)
        return stability_context, openai_client
    
    def generate_audio(self, content: Text, openai_client: OpenAI):
        speech_file_path = self.output_dir / "speech.mp3"
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=content,
        )
        response.stream_to_file(str(speech_file_path))
        return speech_file_path
    

    def generate_frames(self, content: Text, stability_context: api.Context):
        frames_dir = self.output_dir / "video_frames"
        frames_dir.mkdir(exist_ok=True)  # Ensure the directory exists
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
   
    
    def generate_media(self, content: Text):
        
        stability_context, openai_client = self.api_context()
        
        if self.request.media_format == "text":
            text_path = self.output_dir / "news.txt"
            with open(text_path, "w") as f:
                f.write(content)
            return text_path
        
        if self.request.media_format == "audio":
            audio_path = self.generate_audio(content, openai_client)
            return audio_path
        
        if self.request.media_format == "video":
            video_path = self.output_dir / "video.mp4"
            #frames_dir = self.generate_frames(content, stability_context)
            frames_dir = self.output_dir / "video_frames"
            create_video_from_frames(frames_dir, str(video_path), fps=24)

            audio_path = self.generate_audio(content, openai_client)

            output_path = self.output_dir / "combined_video.mp4"

            
        
            return self.combine_audio_video(str(audio_path), str(video_path), str(output_path))
        



            
        
    
        
    

        
