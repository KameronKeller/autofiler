import ollama
# response = ollama.chat(model='phi3:mini', messages=[
#   {
#     'role': 'user',
#     'content': """
# Based on the content provided, generate a descriptive filename that succinctly captures the essence of the content. The filename should not include any dates. For example, for content related to the installation and authorization of a TDS system, a suitable filename might be 'tds_installation_authorization'.
# Content: 'This document outlines the quarterly financial results and provides an analysis of the revenue streams. It also includes projections for the next quarter.'
# """,
#   },
# ])
# print(response['message']['content'])



import os
import time
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
from datetime import datetime
# import requests

MAX_FILENAME_WORD_LENGTH = 7
DOWNLOADS_DIR = os.path.expanduser('~/Downloads')
ICLOUD_DIR = os.path.expanduser('/Users/kameron/Library/Mobile Documents/com~apple~CloudDocs/scanned_docs')
# PROMPT = "Based on the content provided, generate a descriptive filename that succinctly captures the essence of the content. The filename should not include any dates. Do not include any other text in your output, only the text of the filename'. Content: "
PROMPT = """
        You will be provided with the contents of a scanned pdf and you will generate a descriptive filename for the content.
        When possible, make the first word the name of the company, organization, or subject.
        After the company or organization name, describe the document type in 3 or 4 words.
        The filename should be 3 or 4 words.
        The filename should not include any dates.
        Do not inlude any other text in your output, only the text of the filename.
        Here is an example output to model your outputs off of: 'company name document_type'
        When possible, make the first word the name of the company or organization.
        Only generate one filename.
        Do not include any quotations or other special characters in your output.
        Content: '
"""
DOCUMENT_DESCRIBE_PROMPT = "Confidently describe what the following document is in 15 words or less: "
FILENAME_PROMPT = """
    Write a filename for the document description.
    If the document includes order numbers, invoice numbers, or a date, include those in the filename.
    Only generate the filename, do not reply with any other text.
    Do not include a file extension.
    """

class Watcher:
    DIRECTORY_TO_WATCH = DOWNLOADS_DIR

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=False)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()

class Handler(FileSystemEventHandler):
    processed = set()

    @staticmethod
    def process(event):
        if event.is_directory or event.src_path in Handler.processed:
            return None

        elif event.event_type == 'created':
            print('Received created event:  %s.' % event.src_path)
            
            # Sleep for 5 seconds to ensure the file is fully downloaded
            time.sleep(5)
            # Check if the file has the prefix "Scan"
            if os.path.basename(event.src_path).startswith("Scan"):
                Handler.processed.add(event.src_path)
                print(f"Processing file: {event.src_path}")
                text = extract_text_from_pdf(event.src_path)
                print(f"Extracted text: {text}")
                # text = 'this is a bankstatement from chase bank'
                print(f"====== Suggesting name")

                # Might be advantageous to chain together multiple responses
                # For example, get the business name, then summarize the file, then base the filename off of that.
                # Might be overkill and not necessary, but worth considering
                suggested_name = get_suggested_filename(text)
                # This might not be necessary, but worth considering if we want ollama running in the background
                kill_ollama()

                print(f"Suggested name: {suggested_name}")
                move_file(event.src_path, suggested_name)

    def on_created(self, event):
        self.process(event)

def extract_text_from_pdf(file_path):
    # Call Swift script to use Apple Vision API
    print(f"====== Extracting text from: {file_path}")
    result = subprocess.run(['swift', 'extract_text.swift', file_path], capture_output=True, text=True)
    return result.stdout

def start_ollama():
    subprocess.run(['ollama', 'run', 'llama3:8b'])

def kill_ollama():
    subprocess.run(['pkill', 'ollama'])

def check_length(text):
    words = text.split('_')
    if len(words) > MAX_FILENAME_WORD_LENGTH:
        return '_'.join(words[:MAX_FILENAME_WORD_LENGTH])

def clean_text(text):
    return text.replace('"', '').replace("'", "").replace(",", "").strip().replace(" ", "_")

def get_suggested_filename(text):
    # Replace with your LLM API call
    response = ollama.chat(model='llama3:8b', messages=[
        {
            'role': 'user',
            'content': DOCUMENT_DESCRIBE_PROMPT + text,
        },
        {
            'role': 'user',
            'content': FILENAME_PROMPT,
        }
    ])
    cleaned_response = clean_text(response['message']['content'])
    # cleaned_response = check_length(cleaned_response)
    print(cleaned_response)
    return cleaned_response.strip()

def move_file(src_path, suggested_name):
    today = datetime.now().strftime("%Y-%m-%d")
    dest_filename = f"{suggested_name}_{today}.pdf"
    dest_path = os.path.join(ICLOUD_DIR, dest_filename)
    shutil.move(src_path, dest_path)
    print(f"Moved file to: {dest_path}")

if __name__ == '__main__':
    w = Watcher()
    w.run()
