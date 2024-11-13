# app.py
from init import app
from routes import *

if __name__ == "__main__":
    app.run(debug=False)