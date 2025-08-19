from flask import Flask, request
import os

app = Flask(__name__)

@app.route("/healthz", methods=["GET"])
def healthz():
    return "OK", 200

@app.route("/", methods=["POST"])
def webhook():
    return "Webhook received", 200

if __name__ == "__main__":
    app.run()
