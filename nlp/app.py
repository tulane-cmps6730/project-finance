from flask import Flask, request, jsonify, render_template
from classes import ApiContext, Request, WebScraper, Model, Media, Conversation
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, static_folder='/Users/zacharywiel/Documents/NLP/project-finance/nlp/output')



OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STABILITY_KEY = os.getenv("STABILITY_KEY")
STABILITY_HOST = "grpc.stability.ai:443"
api_context = ApiContext(OPENAI_API_KEY, STABILITY_KEY, STABILITY_HOST)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        media_type = request.form['media_type']
        return redirect(url_for('display_media', media_type=media_type))
    return render_template('index.html')

from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import os

@app.route('/process', methods=['POST'])
def process_request():
    ticker = request.form['ticker']
    media_type = request.form['media_type']
    request_params = (media_type, 'ticker', ticker)


    web_scraper = WebScraper(request_params)
    research = web_scraper.scrape()
    model = Model(research, request_params, api_context)
    content, animation_prompt = model.generate()
    media = Media(content, animation_prompt, request_params, api_context)
    output = media.generate_media()

    
    return redirect(url_for('display_media', media_type=media_type, file_path=output))

@app.route('/display/<media_type>')
def display_media(media_type):
    base_dir = "/Users/zacharywiel/Documents/NLP/project-finance/nlp/output"
    if media_type == 'text':
        file_path = os.path.join(base_dir, 'news.txt')
        with open(file_path, 'r') as file:
            content = file.read()
        return render_template('display_text.html', content=content)
    elif media_type == 'audio':
        file_path = 'speech.mp3'
        return render_template('display_audio.html', file_path=file_path)
    elif media_type == 'video':
        file_path = 'combined_video.mp4'
        return render_template('display_video.html', file_path=file_path)
    else:
        return "Unsupported media type"
    
@app.route('/handle_question', methods=['POST'])
def handle_question():
    print("Form data received:", request.form)
    query = request.form['query']
    print("Query received:", query)
    conversation = Conversation()
    answer = conversation.query(query)
    print("Answer generated:", answer)
    return render_template('display_answer.html', answer=answer)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=True)
