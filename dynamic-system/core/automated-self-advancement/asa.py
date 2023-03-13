from asa_backend import ASA
from flask import Flask, request, jsonify

asa_instance = ASA()

app = Flask(__name__)


@app.route("/health", methods=["POST"])
def health():
    return jsonify({"status": "OK"}), 200


@app.route("/asa", methods=["POST"])
def asa():
    user_request = request.get_json()
    asa_instance.call_asa(user_request)
    if asa_instance.response is None:
        return None
    return jsonify({"asa-response": asa_instance.response})



if __name__ == "__main__":
    app.run(port=5090)
