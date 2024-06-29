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
# import requests

DOWNLOADS_DIR = os.path.expanduser('~/Downloads')
ICLOUD_DIR = os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs')
PROMPT = "Based on the content provided, generate a descriptive filename that succinctly captures the essence of the content. The filename should not include any dates. Do not include any other text in your output, only the text of the filename'. Content: "

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
            print('Received created event - %s.' % event.src_path)
            # Check if the file has the prefix "Scan"
            if os.path.basename(event.src_path).startswith("Scan"):
                Handler.processed.add(event.src_path)
                print(f"Processing file: {event.src_path}")
                text = extract_text_from_pdf(event.src_path)
                print(f"Extracted text: {text}")
                # text = 'this is a bankstatement from chase bank'
                print(f"====== Suggesting name")
                suggested_name = get_suggested_filename(text)
                print(f"Suggested name: {suggested_name}")
                # move_file(event.src_path, suggested_name)

    def on_created(self, event):
        self.process(event)

def extract_text_from_pdf(file_path):
    # Call Swift script to use Apple Vision API
    print(f"====== Extracting text from: {file_path}")
    result = subprocess.run(['swift', 'extract_text.swift', file_path], capture_output=True, text=True)
    return result.stdout

def get_suggested_filename(text):
    # Replace with your LLM API call
    response = ollama.chat(model='phi3:mini', messages=[
        {
            'role': 'user',
            'content': PROMPT + text,
        },
    ])
    print(response['message']['content'])
    return response['message']['content'].strip()

# def move_file(src_path, suggested_name):
#     dest_path = os.path.join(ICLOUD_DIR, suggested_name + '.pdf')
#     shutil.move(src_path, dest_path)
#     print(f"Moved file to: {dest_path}")

if __name__ == '__main__':
    w = Watcher()
    w.run()
