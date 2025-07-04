from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageFilter
import io
import base64
import os
import cv2
import numpy as np
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Simple in-memory storage for face data (in production, use a proper database)
face_database = {
    'faces': [],  # List of known face encodings
    'names': [],  # Corresponding names
    'attendance': []  # Attendance records
}

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Face Recognition API is running"})

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

@app.route('/detect-faces', methods=['POST'])
def detect_faces():
    try:
        # Get the uploaded file
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No image file selected"}), 400

        # Read image data
        image_data = file.read()

        # Convert to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return jsonify({"error": "Invalid image format"}), 400

        # Load OpenCV face detection model
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # Convert to grayscale for face detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        # Prepare response data
        faces_data = []
        for i, (x, y, w, h) in enumerate(faces):
            # For simplicity, all faces are "Unknown" since we don't have face recognition
            # In a real implementation, you would extract features and compare with database

            faces_data.append({
                'id': i + 1,
                'location': {
                    'top': int(y),
                    'right': int(x + w),
                    'bottom': int(y + h),
                    'left': int(x)
                },
                'name': "Unknown",
                'confidence': 0.8,  # Dummy confidence for detection
                'is_known': False
            })

        return jsonify({
            "success": True,
            "faces_detected": len(faces_data),
            "faces": faces_data,
            "image_size": {
                "width": image.shape[1],
                "height": image.shape[0]
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/register-face', methods=['POST'])
def register_face():
    try:
        # Get the uploaded file and name
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        file = request.files['image']
        name = request.form.get('name', '').strip()

        if file.filename == '':
            return jsonify({"error": "No image file selected"}), 400

        if not name:
            return jsonify({"error": "Name is required"}), 400

        # Read image data
        image_data = file.read()

        # Convert to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return jsonify({"error": "Invalid image format"}), 400

        # Load OpenCV face detection model
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # Convert to grayscale for face detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) == 0:
            return jsonify({"error": "No face found in the image"}), 400

        if len(faces) > 1:
            return jsonify({"error": "Multiple faces found. Please use an image with only one face"}), 400

        # For simplicity, just store the name (in real app, you'd store face features)
        # Extract face region for future comparison (simplified approach)
        x, y, w, h = faces[0]
        face_region = image[y:y+h, x:x+w]

        # Store face data (simplified - in production use proper face encoding)
        face_database['faces'].append({
            'region': face_region.tolist(),  # Convert to list for JSON serialization
            'location': {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)}
        })
        face_database['names'].append(name)

        return jsonify({
            "success": True,
            "message": f"Face registered successfully for {name}",
            "total_registered": len(face_database['faces'])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/attendance', methods=['GET'])
def get_attendance():
    return jsonify({
        "success": True,
        "attendance": face_database['attendance'],
        "total_records": len(face_database['attendance'])
    })

@app.route('/registered-faces', methods=['GET'])
def get_registered_faces():
    return jsonify({
        "success": True,
        "registered_faces": face_database['names'],
        "total_registered": len(face_database['faces'])
    })

if __name__ == '__main__':
    # Production configuration
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
