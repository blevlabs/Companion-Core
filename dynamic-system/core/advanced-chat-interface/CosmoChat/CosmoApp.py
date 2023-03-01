from cosmoagent import CosmoAgent
from flask import Flask, request, jsonify
cosmo_agent = CosmoAgent()

app = Flask(__name__)

@app.route('/help', methods=['GET'])
def run_help():
    return jsonify({'response': "This is a chatbot API. You can send a POST request to /chat with the following parameters: situation_narrative, role_instruction, conversation_history. The response will be a JSON object with the key 'response'."})

@app.route("/chat", methods=["POST"])
def run_app():
    user_input = request.get_json()
    response = cosmo_agent.call_handler(user_input)
    if not response:
        return jsonify({"response": "[END]"})
    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000)