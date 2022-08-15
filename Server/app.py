import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, Response, json
from app2 import parking

plate = parking("wpod-net_update1.json", "svm.xml")

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/predict_video", methods=["POST"])
def predict_video():
    re = []
    if request.method == "POST":
        jpg_as_np = np.frombuffer(request.data, dtype=np.uint8)
        image_buffer = cv2.imdecode(jpg_as_np, flags=1)

        plate_info = plate.read_plate(image_buffer)

        re.append(plate_info)
        #re.append(timenow)

        response = app.response_class(
            response=json.dumps(re),
            mimetype='application/json'
        )
        return response

@app.route("/qrscan", methods=["POST"])
def qrscan():

    if request.method == "POST":
        jpg_as_np = np.frombuffer(request.data, dtype=np.uint8)
        image_buffer = cv2.imdecode(jpg_as_np, flags=1)

        data = plate.scanqr(image_buffer)

        response = app.response_class(
            response=json.dumps(data),
            mimetype='application/json'
        )
        return response


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)