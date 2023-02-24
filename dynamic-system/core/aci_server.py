from aci_backend import ACI, MemoryManager
from flask import Flask, request, jsonify

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
    return jsonify(aci.flan_chat(classifier_context=data["text"]))


@app.route("/get_memory", methods=["POST"])
def get_memory():
    return jsonify(memory.get_memory())


@app.route("/help", methods=["POST"])
def help():
    help_text = """/health - check if the server is up
    /classify - classify a text
    /chat - chat with the bot
    /get_memory - get the memory of the bot"""
    return jsonify({"message": help_text})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)
