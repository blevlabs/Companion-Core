from asa_backend import ASA
from flask import Flask, request, jsonify

asa_instance = ASA()

app = Flask(__name__)


@app.route("/asa", methods=["POST"])
def asa():
    asa_instance.call_asa(request.get_json())
    return jsonify({"asa-response": asa_instance.response})


if __name__ == "__main__":
    app.run(port=5090)
