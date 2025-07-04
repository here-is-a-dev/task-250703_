from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageFilter
import io
import base64
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Image Processing API is running"})

@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        # Get the uploaded file
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No image file selected"}), 400
        
        # Get processing type from form data
        process_type = request.form.get('type', 'grayscale')
        
        # Open and process the image
        image = Image.open(file.stream)
        
        # Apply processing based on type
        if process_type == 'grayscale':
            processed_image = image.convert('L')
        elif process_type == 'blur':
            processed_image = image.filter(ImageFilter.BLUR)
        elif process_type == 'sharpen':
            processed_image = image.filter(ImageFilter.SHARPEN)
        elif process_type == 'edge':
            processed_image = image.filter(ImageFilter.FIND_EDGES)
        else:
            processed_image = image.convert('L')  # Default to grayscale
        
        # Convert processed image to base64
        img_buffer = io.BytesIO()
        processed_image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Encode to base64
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        return jsonify({
            "success": True,
            "processed_image": f"data:image/png;base64,{img_base64}",
            "process_type": process_type
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Production configuration
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
