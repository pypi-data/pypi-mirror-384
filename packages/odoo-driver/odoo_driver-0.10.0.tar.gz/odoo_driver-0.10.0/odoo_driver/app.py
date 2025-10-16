from flask import Flask, request
from flask_babel import Babel
from flask_cors import CORS

# Initialize Flask Application
app = Flask(__name__)

# Include extra route files
from . import flask_app  # noqa: F401,E402

# Handle CORS call
CORS(app, resources={r"/*": {"origins": "*"}})

# Handle translation via babel
app.config["BABEL_DEFAULT_LOCALE"] = "en"
babel = Babel(app)


def get_locale():
    # Use the browser's language preferences to select an available translation
    available_translations = [
        str(translation) for translation in babel.list_translations()
    ]
    for lang in request.accept_languages.values():
        if lang[:2] in available_translations:
            return lang[:2]


babel.init_app(app, locale_selector=get_locale)
