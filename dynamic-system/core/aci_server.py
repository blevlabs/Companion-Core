from flask import Flask, request, jsonify

from aci_backend import ACI, MemoryManager

aci = ACI()
memory = MemoryManager()
app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    # blank call to check if the server is up
    return jsonify({"status": "ok"})


@app.route("/classify", methods=["POST"])
def classify():
    # requires a "text" key in the json
    data = request.get_json()
    return jsonify(aci.flan_classify(classifier_context=data["text"]))


@app.route("/chat", methods=["POST"])
def chat():
    # requires a "text" key in the json
    data = request.get_json()
    try:
        assert "speaker_data" in data and type(data["speaker_data"]) == dict
        assert "observer_data" in data and type(data["observer_data"]) == dict
        assert "context" in data and type(data["context"]) == dict
    except AssertionError:
        return jsonify({
                           "error": "missing keys in json. Please provide speaker_data, observer_data, and context. If you have provided them, make sure they are dictionaries"})
    try:
        assert data["speaker_data"] != {}
        assert data["observer_data"] != {}
    except AssertionError:
        return jsonify({"error": f"speaker_data and/or observer_data cannot be empty. Here are the values:\n" + str(
            data["speaker_data"]) + "\n" + str(data["observer_data"])})
    speaker_data = data["speaker_data"]
    observer_data = data["observer_data"]
    context = data["context"]
    chat_packet = aci.prompt_generation(speaker_data=speaker_data, observer_data=observer_data, context=context)
    return jsonify(chat_packet)


@app.route("/get_memory", methods=["POST"])
def get_memory():
    return jsonify(memory.load_memory())


@app.route("/speak", methods=["POST"])
def speak():
    aci.run_speech()
    return jsonify({"status": "ok"})


@app.route("/help", methods=["POST"])
def help():
    help_text = """/health - check if the server is up
    /classify - classify a text
    /chat - chat with the bot
    /get_memory - get the memory of the bot"""
    return jsonify({"message": help_text})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)
