import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import colorful as cf

cf.use_true_colors()
cf.use_style('monokai')


class CosmoAgent:
    def __init__(self):
        print(cf.bold | cf.purple("Loading COSMO-xl..."))
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained("allenai/cosmo-xl")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("allenai/cosmo-xl").to(self.device)
        self.conversation_history = []

    def observe(self, observation):
        self.conversation_history.append(observation)

    def set_input(self, situation_narrative="", role_instruction=""):
        input_text = " <turn> ".join(self.conversation_history)

        if role_instruction != "":
            input_text = "{} <sep> {}".format(role_instruction, input_text)

        if situation_narrative != "":
            input_text = "{} <sep> {}".format(situation_narrative, input_text)

        return input_text

    def generate(self, situation_narrative, role_instruction, user_response):

        self.observe(user_response)

        input_text = self.set_input(situation_narrative, role_instruction)

        inputs = self.tokenizer([input_text], return_tensors="pt").to(self.device)
        outputs = self.model.generate(inputs["input_ids"], max_new_tokens=128, temperature=1.0, top_p=.95,
                                      do_sample=True)
        cosmo_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=False)

        self.observe(cosmo_response)

        return cosmo_response

    def reset_history(self):
        self.conversation_history = []

    def run(self):
        def get_valid_input(prompt, default):
            while True:
                user_input = input(prompt)
                if user_input in ["Y", "N", "y", "n"]:
                    return user_input
                if user_input == "":
                    return default

        while True:
            name = input(cf.purple("What is your name? "))
            continue_chat = ""
            situation_narrative = "The Companion Core is chatting with {name}"
            role_instruction = "You are the Companion Core. You are a robotic assistant created by Brayden Levangie. You are equipped with the ability to browse the internet and understand your surroundings. You strive to provide accurate and truthful information. You are currently talking with {name}"
            situation_narrative = situation_narrative.format(name=name)
            role_instruction = role_instruction.format(name=name)
            self.chat(situation_narrative, role_instruction)
            continue_chat = get_valid_input(cf.purple("Start a new conversation with new setup? [Y/N]:"), "Y")
            if continue_chat in ["N", "n"]:
                break

        print(cf.blue("Cosmo: See you!"))

    def chat(self, situation_narrative, role_instruction):
        print(cf.green(
            "Chat with the Companion Core (Powered by Cosmo-XL)! Input [RESET] to reset the conversation history and [END] to end the conversation."))
        while True:
            user_input = input("You: ")
            if user_input == "[RESET]":
                self.reset_history()
                print(cf.green("[Conversation history cleared. Chat with Cosmo!]"))
                continue
            if user_input == "[END]":
                break
            response = self.generate(situation_narrative, role_instruction, user_input)
            print(cf.blue("Companion Core: " + response))


def main():
    cosmo = CosmoAgent()
    cosmo.run()


if __name__ == '__main__':
    main()
