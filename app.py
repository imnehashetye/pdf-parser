import os
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import requests
import pikepdf
import io

app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    return render_template('index.html')


def remove_pdf_encryption(input_pdf, output_pdf_stream):
    try:
        with pikepdf.open(input_pdf, password='') as pdf:
            pdf.save(output_pdf_stream)
            output_pdf_stream.seek(0)  # Rewind to the beginning of the stream
        print("Decrypted PDF in memory.")
        return True
    except pikepdf.PasswordError:
        print("Error: This PDF is encrypted and requires a password.")
        return False
    except Exception as e:
        print(f"An error occurred while decrypting: {e}")
        return False


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Decrypt the uploaded file in memory
    input_pdf = file.stream  # File as a stream (in-memory)
    file_content = file.read() 
    input_pdf = io.BytesIO(file_content)
    decrypted_pdf_stream = io.BytesIO()  # In-memory stream to hold decrypted file

    # Decrypt the PDF
    if not remove_pdf_encryption(input_pdf, decrypted_pdf_stream):
        return jsonify({"error": "Failed to decrypt the PDF"}), 400

    # Return the decrypted PDF directly in the response
    decrypted_pdf_stream.seek(0)  # Ensure we start from the beginning of the stream
    # return send_file(decrypted_pdf_stream, as_attachment=True, download_name='decrypted.pdf', mimetype='application/pdf')
    # Return the decrypted PDF directly in the response
    # Return the decrypted PDF directly in the response
    response = send_file(
        decrypted_pdf_stream,
        as_attachment=True,
        download_name='decrypted.pdf',
        mimetype='application/pdf'
    )

    # Set the content-length header explicitly
    # decrypted_pdf_stream.seek(0)  # Reset to the beginning before determining length
    # response.headers['Content-Length'] = str(decrypted_pdf_stream.tell())

    # # Optional: Set the content-disposition header for proper download behavior
    # response.headers['Content-Disposition'] = 'attachment; filename=decrypted.pdf'

    return response


if __name__ == '__main__':
    app.run(debug=True)
