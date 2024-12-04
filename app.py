from flask import Flask, request, redirect, url_for, render_template, send_from_directory
import os
from pydub import AudioSegment
import assemblyai as aai
from openai import OpenAI, OpenAIError

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed_lectures'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)


openai_client = OpenAI(api_key='YOUR_OPENAI_API_KEY')
aai.settings.api_key = 'YOUR_ASSEMBLYAI_API_KEY'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'lecture' not in request.files:
            return 'No file part'
        file = request.files['lecture']
        if file.filename == '':
            return 'No selected file'
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            print(f"File saved to {filepath}")
            try:
                process_file(filepath)
            except Exception as e:
                print(f"Error processing file: {e}")
                return f"Error processing file: {e}"
            return redirect(url_for('uploaded_file', filename=file.filename))
    return render_template('upload.html')

def process_file(filepath):
    print(f"Processing file {filepath}")
    try:
        
        audio = AudioSegment.from_file(filepath)
        wav_path = filepath.replace(filepath.split('.')[-1], 'wav')
        audio.export(wav_path, format='wav')
        
        
        transcriber = aai.Transcriber(region='us')  
        transcript = transcriber.transcribe(wav_path)
        
        text = transcript.text 
        print("Transcription complete")

        
        processed_text = process_text(text)
        save_processed_text(wav_path, processed_text)
    except OpenAIError as e:
        print(f"OpenAI Error: {e}")
        raise
    except Exception as e:
        print(f"Error in process_file: {e}")
        raise

def process_text(text):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract key points and summarize the text."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message['content']
    except OpenAIError as e:
        print(f"OpenAI Error: {e}")
        raise

def save_processed_text(filepath, processed_text):
    filename = os.path.basename(filepath).replace('.wav', '.txt')
    processed_filepath = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    with open(processed_filepath, 'w') as f:
        f.write(processed_text)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
