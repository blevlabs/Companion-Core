import time
import requests


class cosmo_chat:
    def __init__(self, cosmo_chat_server="http://127.0.0.1:4000/chat"):
        self.cosmo_chat_server = cosmo_chat_server
        self.situation_narrative = ""
        self.instruction = "You are the Companion Core. You are a robotic assistant created by Brayden Levangie. You are equipped with the ability to browse the internet and understand your surroundings. You strive to provide accurate and truthful information. You are currently talking with {names}."
        self.conversation_history = []

    def send_message(self, message):
        try:
            response = requests.post(self.cosmo_chat_server, json=message, timeout=10)
            if response.status_code != 200:
                return "Error in sending message to Cosmo Chat Server.\n" + response.text
            return response.json()["response"]
        except Exception as e:
            return "Error in sending message to Cosmo Chat Server.\n" + str(e)

    def run_user(self):
        name = input("What is your name? ")
        while True:
            message = input(f"{name}: ")
            if message.lower() == "quit":
                break
            message = message.strip()
            response = self.send_message({"message": message, "name": name})
            print(f"Companion Core: {response}")
            time.sleep(0.25)
        print("Thank you for using the Companion Core Chat Alpha - Powered by CosmoXL")
        return


if __name__ == "__main__":
    input("Please ensure that the Cosmo Chat Server is running. Press enter to continue.")
    chat = cosmo_chat()
    chat.run_user()
