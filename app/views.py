"""
Flask Documentation:     https://flask.palletsprojects.com/
Jinja2 Documentation:    https://jinja.palletsprojects.com/
Werkzeug Documentation:  https://werkzeug.palletsprojects.com/
This file contains the routes for your application.
"""

import io
import tensorflow as tf
from app import app
from flask import flash, render_template, request
from PIL import Image

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


@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return render_template("predict.html", error="No file part")

    img_file = request.files["image"].read()
    img = Image.open(io.BytesIO(img_file))

    img_array = preprocess_image(img)

    # Predict age
    predicted_age = detection_model.predict(img_array)[0][0]
    predicted_age = round(predicted_age)
    return render_template("predict.html", age=predicted_age)


###
# The functions below should be applicable to all Flask apps.
###


def preprocess_image(img: Image):
    img = img.resize((224, 224))
    img_array = keras.preprocessing.image.img_to_array(img)
    img_array = img_array / 255.0
    img_array = img_array.reshape(1, 224, 224, 3)
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
