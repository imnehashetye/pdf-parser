from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import pikepdf
import PyPDF2
import os

app = Flask(__name__)
CORS(app)

HUGGING_FACE_API_URL = 'https://api-inference.huggingface.co/models/facebook/bart-large-mnli'
HUGGING_FACE_API_TOKEN = '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'

@app.route('/')
def index():
    return render_template('index.html')

def decrypt_pdf(input_pdf_path, output_pdf_path):
    try:
        with pikepdf.open(input_pdf_path, password='') as pdf:
            pdf.save(output_pdf_path)
        return output_pdf_path
    except pikepdf.PasswordError:
        print("Error: This PDF is encrypted and requires a password.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in range(len(reader.pages)):
                page_text = reader.pages[page].extract_text()
                if page_text:
                    text += page_text
        return text
    except Exception as e:
        print(f"An error occurred while extracting text from the PDF: {e}")
        return None

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Save the uploaded PDF to a temporary location
    temp_pdf_path = 'temp.pdf'
    file.save(temp_pdf_path)

    # Try to decrypt the PDF if it is encrypted
    decrypted_pdf_path = 'decrypted_temp.pdf'
    pdf_path = decrypt_pdf(temp_pdf_path, decrypted_pdf_path) or temp_pdf_path

    # Extract text from the appropriate PDF file
    extracted_text = extract_text_from_pdf(pdf_path)
    if extracted_text:
        # Validate the text with Hugging Face API
        response = validate_text_with_huggingface(extracted_text)
        
        return jsonify({
            "extracted_text": extracted_text,
            "validation_result": response
        })
    else:
        return jsonify({"error": "Failed to extract text from PDF"}), 500

def validate_text_with_huggingface(text):
    headers = {
        "Authorization": f"Bearer {HUGGING_FACE_API_TOKEN}"
    }
    payload = {
        "inputs": text,
        "parameters": {
            "candidate_labels": ['safe', 'inappropriate'],
        }
    }
    response = requests.post(HUGGING_FACE_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Validation failed", "details": response.text}

if __name__ == '__main__':
    app.run(debug=True)
