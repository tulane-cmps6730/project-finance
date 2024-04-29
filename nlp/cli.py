# -*- coding: utf-8 -*-

"""Demonstrating a very simple NLP project. Yours should be more exciting than this."""
import click
import glob
import pickle
import sys
import json
import numpy as np
import pandas as pd
import re
import requests
from openai import OpenAI
from dotenv import load_dotenv
import os
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report

from . import clf_path, config
from .classes import ApiContext, Request, WebScraper, Model, Media


@click.group()
def main(args=None):
    """Console script for nlp."""
    return 0


@main.command("web")
@click.option(
    "-p",
    "--port",
    required=False,
    default=5000,
    show_default=True,
    help="port of web server",
)
def web(port):
    """
    Launch the flask web app.
    """
    from .app import app

    app.run(host="0.0.0.0", debug=True, port=port)


@main.command("chat")
def chat():
    """
    Chat with the a chatgpt instance.
    """

    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    STABILITY_KEY = os.getenv("STABILITY_KEY")
    STABILITY_HOST = "grpc.stability.ai:443"

    api = ApiContext(
        openai_api_key=OPENAI_API_KEY,
        stability_api_key=STABILITY_KEY,
        stability_host=STABILITY_HOST,
    )

    request = Request(api)
    request_params = request.process_request()

    web_scraper = WebScraper(request_params)
    research = web_scraper.scrape()

    model = Model(research, request_params, api)
    [content, animation_prompt] = model.generate()

    media = Media(content, animation_prompt, request_params, api)
    output = media.generate_media()

    print(output)


@main.command("debug")
def debug():
    """
    Debug the chat function.
    """
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    STABILITY_KEY = os.getenv("STABILITY_KEY")
    STABILITY_HOST = "grpc.stability.ai:443"

    api = ApiContext(
        openai_api_key=OPENAI_API_KEY,
        stability_api_key=STABILITY_KEY,
        stability_host=STABILITY_HOST,
    )

    request_params = ("video", "ticker", "AAPL")

    # web_scraper = WebScraper(request_params)
    research = "/Users/zacharywiel/Documents/NLP/project-finance/nlp/research/AAPL.json"

    model = Model(research, request_params, api)
    [content, animation_prompt] = model.generate()
    print(content)
    print(animation_prompt)

    media = Media(content, animation_prompt, request_params, api)
    output = media.generate_media()

    # print(output)


if __name__ == "__main__":
    sys.exit(main())
