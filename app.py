from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import pikepdf
import PyPDF2
from io import BytesIO
import os

app = Flask(__name__)
CORS(app)

HUGGING_FACE_API_URL = 'https://api-inference.huggingface.co/models/facebook/bart-large-mnli'
HUGGING_FACE_API_TOKEN = ''

@app.route('/')
def index():
    return render_template('index.html')

def decrypt_pdf(input_pdf_stream, password=''):
    try:
        with pikepdf.open(input_pdf_stream, password=password) as pdf:
            output_stream = BytesIO()
            pdf.save(output_stream)
            output_stream.seek(0)
            return output_stream
    except pikepdf.PasswordError:
        print("Error: This PDF is encrypted and requires a password.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def extract_text_from_pdf(pdf_stream):
    text = ""
    try:
        reader = PyPDF2.PdfReader(pdf_stream)
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

    # Read the uploaded PDF into memory
    pdf_stream = BytesIO(file.read())

    # Try to decrypt the PDF if it is encrypted
    decrypted_pdf_stream = decrypt_pdf(pdf_stream)

    if decrypted_pdf_stream is None:
        return jsonify({"error": "Failed to decrypt PDF or PDF is encrypted with a password."}), 500

    # Extract text from the appropriate PDF stream
    extracted_text = extract_text_from_pdf(decrypted_pdf_stream)
    if extracted_text:
        # Validate the text with Hugging Face API
        response = validate_text_with_huggingface(extracted_text)
        
        # Clean up temporary resources if any were created
        pdf_stream.close()  # Close the original PDF stream
        decrypted_pdf_stream.close()  # Close the decrypted PDF stream
        
        return jsonify({
            "extracted_text": extracted_text,
            "validation_result": response
        })
    else:
        # Clean up streams if extraction failed
        pdf_stream.close()
        decrypted_pdf_stream.close()
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
