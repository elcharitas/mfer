"""
Flask Documentation:     https://flask.palletsprojects.com/
Jinja2 Documentation:    https://jinja.palletsprojects.com/
Werkzeug Documentation:  https://werkzeug.palletsprojects.com/
This file contains the routes for your application.
"""

import cv2
import numpy as np
import imutils
import tensorflow as tf
from app import app
from flask import flash, render_template, request

detection_model = tf.keras.models.load_model("app/models/detection_model.h5")
classification_model = tf.keras.models.load_model("app/models/classification_model.h5")


###
# Routing for your application.
###


@app.route("/")
def home():
    """Render website's home page."""
    return render_template("home.html")


@app.route("/about/")
def about():
    """Render the website's about page."""
    return render_template("about.html", name="Mary Jane")


###
# API routes, should return html
###

LABELS = ["No Tumor", "Glioma Tumor", "Pituitary Tumor", "Meningioma Tumor"]


@app.route("/predict", methods=["POST"])
def predict():
    print("starting prediction")
    if "image" not in request.files:
        print(f"No file part: {request.files}")
        return render_template("predict.html", error="No file part")

    img_file = request.files["image"]
    img_array = np.frombuffer(img_file.read(), np.uint8)  # Read image data
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    prediction_img_array = preprocess_image(img)
    classification_img_array = preprocess_image(img, target_size=(224, 224))

    # Predict
    tumor_value = detection_model.predict(prediction_img_array)[0][0]
    has_tumor = round(tumor_value) == 1
    predicted_tumor = None

    if has_tumor:
        predicted_tumor = classification_model.predict(classification_img_array)
        predicted_class = np.argmax(predicted_tumor, axis=1)[0]
        predicted_probabilities = predicted_tumor[0]

    return render_template("predict.html", prediction=LABELS[predicted_class])


###
# The functions below should be applicable to all Flask apps.
###


def crop_img(img):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # threshold the image, then perform a series of erosions +
    # dilations to remove any small regions of noise
    thresh = cv2.threshold(gray, 45, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.erode(thresh, None, iterations=2)
    thresh = cv2.dilate(thresh, None, iterations=2)

    # find contours in thresholded image, then grab the largest one
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    c = max(cnts, key=cv2.contourArea)

    # find the extreme points
    extLeft = tuple(c[c[:, :, 0].argmin()][0])
    extRight = tuple(c[c[:, :, 0].argmax()][0])
    extTop = tuple(c[c[:, :, 1].argmin()][0])
    extBot = tuple(c[c[:, :, 1].argmax()][0])
    ADD_PIXELS = 0
    new_img = img[
        extTop[1] - ADD_PIXELS : extBot[1] + ADD_PIXELS,
        extLeft[0] - ADD_PIXELS : extRight[0] + ADD_PIXELS,
    ].copy()

    return new_img


def preprocess_image(img, target_size=(256, 256)):
    new_img = crop_img(img)
    new_img = cv2.resize(new_img, target_size, interpolation=cv2.INTER_CUBIC)
    new_img = new_img / 255.0
    img_array = np.expand_dims(new_img, axis=0)
    return img_array


# Display Flask WTF errors as Flash messages
def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(
                "Error in the %s field - %s" % (getattr(form, field).label.text, error),
                "danger",
            )


@app.route("/<file_name>.txt")
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + ".txt"
    return app.send_static_file(file_dot_text)


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also tell the browser not to cache the rendered page. If we wanted
    to we could change max-age to 600 seconds which would be 10 minutes.
    """
    response.headers["X-UA-Compatible"] = "IE=Edge,chrome=1"
    response.headers["Cache-Control"] = "public, max-age=0"
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template("404.html"), 404
