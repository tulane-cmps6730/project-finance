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
from .classes import Request, WebScraper, Model, Media


@click.group()
def main(args=None):
    """Console script for nlp."""
    return 0

@main.command('web')
@click.option('-p', '--port', required=False, default=5000, show_default=True, help='port of web server')
def web(port):
    """
    Launch the flask web app.
    """
    from .app import app
    app.run(host='0.0.0.0', debug=True, port=port)
"""    
@main.command('dl-data')
def dl_data():
    
    #Download training/testing data.
    
    data_url = config.get('data', 'url')
    data_file = config.get('data', 'file')
    print('downloading from %s to %s' % (data_url, data_file))
    r = requests.get(data_url)
    with open(data_file, 'wt') as f:
        f.write(r.text)
    

    def data2df():
        return pd.read_csv(config.get('data', 'file'))

    @main.command('stats')
    def stats():
    
    #Read the data files and print interesting statistics.
    
    df = data2df()
    print('%d rows' % len(df))
    print('label counts:')
    print(df.partisan.value_counts())    

@main.command('train')
def train():
    
    #Train a classifier and save it.
    
    # (1) Read the data...
    df = data2df()    
    # (2) Create classifier and vectorizer.
    clf = LogisticRegression(max_iter=1000, C=1, class_weight='balanced')         
    vec = CountVectorizer(min_df=5, ngram_range=(1,3), binary=True, stop_words='english')
    X = vec.fit_transform(df.title)
    y = df.partisan.values
    # (3) do cross-validation and print out validation metrics
    # (classification_report)
    do_cross_validation(clf, X, y)
    # (4) Finally, train on ALL data one final time and
    # train. Save the classifier to disk.
    clf.fit(X, y)
    pickle.dump((clf, vec), open(clf_path, 'wb'))
    top_coef(clf, vec)

def do_cross_validation(clf, X, y):
    all_preds = np.zeros(len(y))
    for train, test in StratifiedKFold(n_splits=5, shuffle=True, random_state=42).split(X,y):
        clf.fit(X[train], y[train])
        all_preds[test] = clf.predict(X[test])
    print(classification_report(y, all_preds))    

def top_coef(clf, vec, labels=['liberal', 'conservative'], n=10):
    feats = np.array(vec.get_feature_names_out())
    print('top coef for %s' % labels[1])
    for i in np.argsort(clf.coef_[0])[::-1][:n]:
        print('%20s\t%.2f' % (feats[i], clf.coef_[0][i]))
    print('\n\ntop coef for %s' % labels[0])
    for i in np.argsort(clf.coef_[0])[:n]:
        print('%20s\t%.2f' % (feats[i], clf.coef_[0][i]))
"""
@main.command('chat')
def chat():
    """
    Chat with the a chatgpt instance.
    """

    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    client = OpenAI(api_key=api_key)

    def run_conversation():
        while True:
            try:
                message = input("What would you like to learn about? I can teach you about the state of the market, a specific stock, or a current event. Please specify if you would like the information in text, audio, or video format.\n\n")
                messages = [{"role": "user", "content": message}]
                tools = [
                    {
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
                                #"required": ["subject", "media_format", "subject_type"],
                            },
                        },
                    }
                ]
                response = client.chat.completions.create(
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
        
        return [media_format, subject_type, subject]
    request_list = run_conversation()
    media_format = request_list[0]
    subject_type = request_list[1]
    subject = request_list[2]
    
    
    print(f"Here is the {media_format} information on the {subject_type} {subject}.")

    request = Request(media_format, subject_type, subject)

    web_scraper = WebScraper(request)
    research = web_scraper.scrape()
    model = Model(request)
    content = model.generate(research)
    media = Media(request)
    output = media.generate_media(content)
    print(output)




if __name__ == "__main__":
    sys.exit(main())
