from typing import Any, Text
from openai import OpenAI
from dotenv import load_dotenv
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
    
    def generate_media(self, content: Text):
        if self.request.media_format == "text":
            return content
        elif self.request.media_format == "audio":
            return "audio file" #replace with actual audio file
        elif self.request.media_format == "video":
            return "video file" #replace with actual video file