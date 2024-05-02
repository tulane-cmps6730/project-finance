# Configurable AI Framework for Multimodal News Content Generation (CFMN-CG)

The CFMN-CG is an innovative framework designed to simplify the consumption of financial market news by providing information in various media formats including text, video, and audio. This tool is particularly valuable for individual investors and financial analysts who need quick and accessible financial updates.


### Features

Customizable Content Generation: Generate text, audio, or video content based on user preferences.
Financial Market Focus: Tailored specifically for financial markets, with the capability to expand into other news domains.
Advanced Web Scraping: Automatically scrapes and processes financial news from Yahoo Finance.
AI-Powered Analysis: Uses GPT models for content analysis and summarization.
Multimodal Outputs: Integrates OpenAI's Whisper TTS for audio and Stability AI's tools for video generation.


## Installation
To get started with CFMN-CG, follow these steps to set up the project on your local machine:

### Clone the Repository
git clone https://github.com/tulane-cmps6730/project-finance.git

cd project-finance

### Set up a Virtual Environment (Optional but recommended)
python -m venv venv

source venv/bin/activate

### Install Dependencies
pip install -r requirements.txt

### Install Code
python setup.py develop

### Set Environment Variables
Create a .env file in the root directory and populate it with necessary API keys and configurations:
STABILITY_KEY=your_stability_api_key_here

OPENAI_API_KEY=your_openai_api_key_here

### Start the project
nlp web - flask app

nlp chat - CLI tool 

