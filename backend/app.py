from flask import Flask, Response, flash, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename
from models.yolo_trash_detection import model as yolo_trash_detection_model
import os

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "data")
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def trash_detection_demo():
    return render_template('trash_detection_demo.html')

@app.route("/trash_image", methods=["GET", "POST"])
def trash_image():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            yolo_trash_detection_model.create_folders()
            filename = secure_filename(file.filename)
            provided_image_abs_file_path = os.path.join(app.config['UPLOAD_FOLDER'], "inference_trash_images", "images", filename)
            file.save(provided_image_abs_file_path)
            predicted_file_name = yolo_trash_detection_model.detect_trash_from_image(provided_image_abs_file_path)
            return redirect(url_for('download_file', name=predicted_file_name))
    return Response(status=204)

@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(os.path.join(app.config["UPLOAD_FOLDER"], "inference_trash_images", "inference_results"), name)

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(host="0.0.0.0", port=5000, debug=True)