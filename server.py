"""Flask web service for the offline emotion detector."""

from __future__ import annotations

import os

from flask import Flask, jsonify, render_template, request

from EmotionDetection.emotion_detection import EMOTIONS, emotion_detector

MAX_TEXT_LENGTH = 5000


def _json_payload(text, result):
    return {
        "ok": True,
        "text": text,
        "scores": {emotion: result[emotion] for emotion in EMOTIONS},
        "dominant_emotion": result["dominant_emotion"],
        "confidence": result.get("confidence", 0.0),
        "emoji": result.get("emoji", "😐"),
        "word_count": result.get("word_count", 0),
    }


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        MAX_CONTENT_LENGTH=64 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    @app.get("/")
    def index():
        return render_template("index.html", result=None, text="")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "service": "emotion-detector"})

    @app.get("/emotionDetector")
    def legacy_detector():
        text = request.args.get("textToAnalyze", "").strip()
        if not text:
            if request.accept_mimetypes.best == "application/json":
                return jsonify({"ok": False, "error": "Invalid text! Please try again!"}), 400
            return render_template(
                "index.html",
                result=None,
                text="",
                error="Invalid text! Please try again!",
            ), 400

        if len(text) > MAX_TEXT_LENGTH:
            return jsonify({"ok": False, "error": "Text is too long."}), 413

        result = emotion_detector(text)
        if result["dominant_emotion"] is None:
            return jsonify({"ok": False, "error": "Invalid text! Please try again!"}), 400

        wants_json = (
            request.args.get("format") == "json"
            or request.accept_mimetypes.best == "application/json"
            or request.is_json
        )
        if wants_json:
            return jsonify(_json_payload(text, result))

        return f"""For the given statement, the system response is 'anger': {result['anger']}, \
'disgust': {result['disgust']}, 'fear': {result['fear']}, 'joy': {result['joy']} and \
'sadness': {result['sadness']}.
The dominant emotion is {result['dominant_emotion']}."""

    @app.post("/api/analyze")
    def analyze():
        payload = request.get_json(silent=True) or {}
        text = str(payload.get("text", "")).strip()
        if not text:
            return jsonify({"ok": False, "error": "Enter some text to analyze."}), 400
        if len(text) > MAX_TEXT_LENGTH:
            return jsonify({
                "ok": False,
                "error": f"Text must be {MAX_TEXT_LENGTH} characters or fewer.",
            }), 413
        return jsonify(_json_payload(text, emotion_detector(text)))

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify({"ok": False, "error": "Request body is too large."}), 413

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") in {"1", "true", "yes"}
    app.run(host="0.0.0.0", port=port, debug=debug)
