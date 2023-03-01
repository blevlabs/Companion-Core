import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from flask import Flask, request, jsonify

app = Flask(__name__)


class CosmoAgent:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained("allenai/cosmo-xl")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("allenai/cosmo-xl").to(self.device)
        self.conversation_history = []
        self.situation_narrative = "The Companion Core is chatting with {name}"
        self.role_instruction = "You are the Companion Core, a robotic assistant created by Brayden Levangie. You are equipped with the ability to browse the internet and understand your surroundings. Strive to provide accurate and truthful information. You are currently talking with {name}"

    def observe(self, observation):
        self.conversation_history.append(observation)

    def set_input(self, situation_narrative="", role_instruction=""):
        input_text = " <turn> ".join(self.conversation_history)

        if role_instruction != "":
            input_text = "{} <sep> {}".format(role_instruction, input_text)

        if situation_narrative != "":
            input_text = "{} <sep> {}".format(situation_narrative, input_text)

        return input_text

    def get_inputs(self, situation_narrative, role_instruction, user_response):
        self.observe(user_response)

        input_text = self.set_input(situation_narrative, role_instruction)
        inputs = self.tokenizer([input_text], return_tensors="pt").to(self.device)
        return inputs

    def generate(self, situation_narrative, role_instruction, user_response):
        assert situation_narrative != "", "situation_narrative cannot be empty"
        assert role_instruction != "", "role_instruction cannot be empty"
        assert user_response != "", "user_response cannot be empty"
        inputs = self.get_inputs(situation_narrative, role_instruction, user_response)
        if len(inputs["input_ids"][0]) > 512:
            inputs = self.chat_history_tokenizer_manager(inputs, user_response)
        outputs = self.model.generate(inputs["input_ids"], max_new_tokens=128, temperature=1.0, top_p=.95,
                                      do_sample=True)
        cosmo_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=False)

        self.observe(cosmo_response)

        return cosmo_response

    def reset_history(self):
        self.conversation_history = []

    def chat(self, situation_narrative, role_instruction, message):
        response = self.generate(situation_narrative, role_instruction, message)
        return response

    def chat_history_tokenizer_manager(self, tokenizer_results=None, token_threshold=512, message=""):
        # get length of history
        history_length = len(tokenizer_results["input_ids"])
        print("DEBUG: history_length: ", history_length)
        # Since the conversation is created with a prompt+response as two objects appended to a list, we need to remove the prompt responses in the beginning to create a moving-window of the last 512 tokens
        # We do this by removing the first two objects in the list until the list is less than 512 tokens
        inputs = tokenizer_results
        while history_length > token_threshold:
            # remove the first two objects in the list
            self.conversation_history = self.conversation_history[2:]
            # re-tokenize the conversation history
            inputs = self.get_inputs(self.situation_narrative, self.role_instruction, message)
            # get the length of the new tokenized history
            history_length = len(inputs["input_ids"])
        print("DEBUG: history_length: ", history_length)
        return inputs

    def call_handler(self, user_input):
        name = user_input["name"]
        message = user_input["message"]
        if len(message) > 500:
            return "Message too long. Please keep your message under 500 characters."
        try:
            assert name != "", "name cannot be empty"
            assert message != "", "message cannot be empty"
        except AssertionError as e:
            return str(e)
        self.situation_narrative = self.situation_narrative.format(name=name)
        self.role_instruction = self.role_instruction.format(name=name)
        if message == "[RESET]":
            self.reset_history()
            return "[Conversation history cleared]"
        if message == "[END]":
            return False
        return self.chat(self.situation_narrative, self.role_instruction, message)


