from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import fitz  # PyMuPDF
import requests
import tempfile

app = Flask(__name__)
CORS(app)

HUGGING_FACE_API_URL = 'https://api-inference.huggingface.co/models/facebook/bart-large-mnli'
HUGGING_FACE_API_TOKEN = '1'

@app.route('/')
def index():
    return render_template('index.html')

def read_pdf_in_binary(file_path):
    try:
        # Open the PDF file in binary mode
        with open(file_path, 'rb') as file:
            # Read the entire file content
            binary_data = file.read()
            return binary_data
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def save_binary_to_file(binary_data, output_path):
    try:
        # Write the binary data to a new file
        with open(output_path, 'wb') as output_file:
            output_file.write(binary_data)
        print(f"Binary data successfully written to '{output_path}'.")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")

@app.route('/upload', methods=['POST'])
def upload_file():
    print('qqqqqq', request)
    print('qqqqqq', request.files)
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Save the uploaded file to a temporary location
    temp_pdf_path = 'temp.pdf'
    file.save(temp_pdf_path)

    # Read the PDF in binary
    binary_content = read_pdf_in_binary(temp_pdf_path)
    print('11111', binary_content)
    if binary_content:
        # Save binary data to a new file
        output_path = 'output_binary_file.bin'
        save_binary_to_file(binary_content, output_path)
        print('binary_contentuuuuu', binary_content)
        
        response = validate_text_with_huggingface(output_path)
        print('kkkkkkkkk', jsonify(response))
        return jsonify(response)

    
    # # Use a temporary file to store the uploaded PDF
    # with tempfile.NamedTemporaryFile(delete=True) as temp_file:
    #     file.save(temp_file.name)  # Save the uploaded file to the temp file

    #     try:
    #         # Open the saved PDF file
    #         pdf_document = fitz.open(temp_file.name)

    #         text = ''
    #         for page in pdf_document:
    #             text += page.get_text()
    #         pdf_document.close()

    #     except fitz.fitz.FileNotFoundError as e:
    #         return jsonify({"error": "File not found: " + str(e)}), 500
    #     # except fitz.fitz.PdfError as e:
    #     #     return jsonify({"error": "PDF error: " + str(e)}), 500
    #     except Exception as e:
    #         print('iiieeeeiiiii', e)
    #         return jsonify({"error": str(e)}), 500
    # print('iiiiiiii', text)

    # Validate the text with Hugging Face
    # response = validate_text_with_huggingface(text)
    # return jsonify(response)

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
    print('response.status_codeooooo', response.status_code)
    print('response.status_codeoooootext', response.text)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Validation failed", "details": response.text}

if __name__ == '__main__':
    app.run(debug=True)
