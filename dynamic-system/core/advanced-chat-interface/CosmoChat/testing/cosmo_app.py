# setup flask server for the chatbot
from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

device = torch.device("cuda")
tokenizer = AutoTokenizer.from_pretrained("allenai/cosmo-xl")
model = AutoModelForSeq2SeqLM.from_pretrained("allenai/cosmo-xl").to(device)

app = Flask(__name__)
CORS(app)


def set_input(situation_narrative, role_instruction, conversation_history):
    input_text = " <turn> ".join(conversation_history)

    if role_instruction != "":
        input_text = "{} <sep> {}".format(role_instruction, input_text)

    if situation_narrative != "":
        input_text = "{} <sep> {}".format(situation_narrative, input_text)

    return input_text


def generate(situation_narrative="", role_instruction="", conversation_history="", chat_name=""):
    """
    situation_narrative: the description of situation/context with the characters included (e.g., "David goes to an amusement park")
    role_instruction: the perspective/speaker instruction (e.g., "Imagine you are David and speak to his friend Sarah").
    conversation_history: the previous utterances in the conversation in a list
    """
    with torch.no_grad():
        input_text = set_input(situation_narrative, role_instruction, conversation_history) + " <sep> Companion Core:"
        inputs = tokenizer([input_text], return_tensors="pt").to(device)
        outputs = model.generate(inputs["input_ids"], max_new_tokens=128, temperature=1.0, top_p=.95, do_sample=True)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=False)
        return response


@app.route('/cosmo', methods=['POST'])
def chat():
    data = request.get_json()
    assert data is not None, "No data provided"
    try:
        assert 'situation_narrative' in data, "situation_narrative not provided"
        assert 'role_instruction' in data, "role_instruction not provided"
        assert 'conversation_history' in data, "conversation_history not provided"
    except AssertionError as e:
        return jsonify({'error': str(e)}), 400
    situation_narrative = data['situation_narrative']
    role_instruction = data['role_instruction']
    conversation_history = data['conversation_history']
    print("role_instruction: ", role_instruction)
    print("conversation_history: ", conversation_history)
    response = generate(situation_narrative, role_instruction, conversation_history)
    return jsonify({'response': response}), 200


@app.route('/help', methods=['GET'])
def help():
    return jsonify({'response': "This is a chatbot API. You can send a POST request to /chat with the following parameters: situation_narrative, role_instruction, conversation_history. The response will be a JSON object with the key 'response'."})