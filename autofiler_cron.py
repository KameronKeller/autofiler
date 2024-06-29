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
from dotenv import load_dotenv
# import requests

load_dotenv()

MAX_FILENAME_WORD_LENGTH = 7
DOWNLOADS_DIR = os.path.expanduser(os.getenv('DOWNLOADS_DIR'))
ICLOUD_DIR = os.path.expanduser(os.getenv('ICLOUD_DIR'))
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


def run():
    for filename in os.listdir(DOWNLOADS_DIR):
        if filename.startswith("Scan"):
            print(f"====== Processing file: {filename}")
            print(f"\t Extracting text from PDF")
            text = extract_text_from_pdf(os.path.join(DOWNLOADS_DIR, filename))
            # text = 'this is a bankstatement from chase bank'
            print(f"\t Suggesting name")

            # Might be advantageous to chain together multiple responses
            # For example, get the business name, then summarize the file, then base the filename off of that.
            # Might be overkill and not necessary, but worth considering
            suggested_name = get_suggested_filename(text)

            print(f"\t\tSuggested name: {suggested_name}")
            print(f"\t Moving file")
            move_file(os.path.join(DOWNLOADS_DIR, filename), suggested_name)
            print(f"****** Done processing file: {filename}\n\n")
    # This might not be necessary, but worth considering if we want ollama running in the background
    kill_ollama()

def extract_text_from_pdf(file_path):
    # Call Swift script to use Apple Vision API
    # print(f"====== Extracting text from: {file_path}")
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
    # print(cleaned_response)
    return cleaned_response.strip()

def move_file(src_path, suggested_name):
    today = datetime.now().strftime("%Y-%m-%d")
    dest_filename = f"{suggested_name}_{today}.pdf"
    dest_path = os.path.join(ICLOUD_DIR, dest_filename)
    shutil.move(src_path, dest_path)
    # print(f"Moved file to: {dest_path}")

if __name__ == '__main__':
    run()
