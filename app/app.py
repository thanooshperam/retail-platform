from flask import Flask, jsonify
import os

app = Flask(__name__)

VERSION = os.getenv("APP_VERSION", "4.2.0")
HEALTH_MODE = os.getenv("HEALTH_MODE", "healthy")


@app.route("/")
def home():
    return jsonify({
        "application": "retail-platform",
        "version": VERSION,
        "payment": "OK"
    })


@app.route("/health")
def health():
    if HEALTH_MODE == "fail":
        return jsonify({
            "status": "unhealthy",
            "version": VERSION
        }), 500

    return jsonify({
        "status": "healthy",
        "version": VERSION
    }), 200


@app.route("/payment")
def payment():
    return jsonify({
        "payment_status": "processing"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)