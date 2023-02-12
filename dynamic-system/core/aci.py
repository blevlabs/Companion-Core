from transformers import pipeline
import datetime
import openai
import os
from resources.database_manager import DatabaseManager
import httpx
import time

openai.api_key = os.getenv("OPENAI_PERSONAL")
database_manager = DatabaseManager()
from resources.INFO import info
import asyncio
import json
import uuid
info = info()


class MemoryManager:
    def __init__(self):
        self.memory_file = "/home/blabs/Companion-Core/dynamic-system/core/databases/dialogue_memory_streams.json"
        # format: {user_dialogue: "", bot_dialogue: "", time: time.time(),

    def load_memory(self):
        with open(self.memory_file, "r") as f:
            return json.load(f)

    def save_memory(self, memory):
        with open(self.memory_file, "w") as f:
            json.dump(memory, f)

    def format_memory(self, user_dialogue, bot_dialogue, speakers):
        time_of_log = time.time()
        memory_packet = {"user_dialogue": user_dialogue, "bot_dialogue": bot_dialogue, "time": time_of_log,
                         "speakers": speakers}
        return memory_packet


class ACI:
    def __init__(self, model_name="google/flan-t5-xl", device="cuda:0"):
        self.conversation_duration = None
        self.pipeline = pipeline(model=model_name, device=device, tokenizer=model_name,
                                 framework="pt")
        self.device = device
        self.memory_history = []
        self.start_time = datetime.datetime.now()
        self.memory_manager = MemoryManager()

    def prompt_generation(self, speaker_data, observer_data, context={}):
        # format date like MM DD, YYYY at HH:MM AM/PM
        names = ", ".join(observer_data["names"])
        date = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")
        self.conversation_duration = str(((datetime.datetime.now() - self.start_time).seconds / 60).__round__(2))
        base_prompt = f"Welcome to the Companion Core, a robotic assistant created by Brayden Levangie. The Companion Core " \
                      f"is equipped with the ability to browse the internet and understand its surroundings, and always " \
                      f"strives to provide accurate and truthful information. If you provide context for a conversation, " \
                      f"the Companion Core will use it to better understand and respond to your questions or recall " \
                      f"previously discussed information. If the conversation does not require a response from the " \
                      f"Companion Core, such as when two users are speaking with each other or when the conversation " \
                      f"consists solely of questions and answers, the Companion Core will simply acknowledge this with a " \
                      f"\"NO-RESPONSE\" message. The current date is {date}, and the present observable speakers are " \
                      f"{names}. This conversation has been going on for {self.conversation_duration} minutes."
        appended_prompts = []
        if len(self.memory_history) != 0:
            if len(self.memory_history) != 0:
                for memory_packet in self.memory_history:
                    user_dialogue = memory_packet["user_dialogue"]
                    bot_dialogue = memory_packet["bot_dialogue"]
                    appended_prompts.append(f"\n===\n{user_dialogue}\n===\nCompanion Core: {bot_dialogue}")
        while (len("\n===\n".join(appended_prompts)) // 4) > 2048:
            appended_prompts.pop(0)
        conversation = base_prompt + "".join(appended_prompts) + "\n===\n"
        if context != {}:
            for key, value in context.items():
                conversation += f"{key}: {value}\n"
        if type(speaker_data) == list:
            user_response = "\n".join(speaker_data)
        else:
            user_response = speaker_data
        conversation += f"{user_response}\n===\n" + "Companion Core:"
        conversation_response, cost = self.gpt3_aci_gen(conversation)
        memory_packet = self.memory_manager.format_memory(user_response, conversation_response, names)
        self.memory_history.append(memory_packet)
        self.memory_manager.save_memory(self.memory_history)
        convo_datapacket = {
            "conversation_time": str(((datetime.datetime.now() - self.start_time).seconds / 60).__round__(2)),
            "speakerData": speaker_data, "companionResponse": conversation_response, "observers": observer_data,
            "conversation_length": self.conversation_duration, "context": context}
        database_manager.class_data_uploader("ACI", convo_datapacket)
        return convo_datapacket

    def gpt3_aci_gen(self, prompt):
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0.7,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["==="]
        )["choices"][0]["text"].strip()
        cost = (((len(prompt) + len(response)) // 4) / 1000) * 0.02
        return response, cost

    def generate(self, text):
        return self.pipeline(text)

    def flan_classify(self, classifier_context):
        if classifier_context == "":
            return "NONE"
        if type(classifier_context) == list:
            classifier_context = "\n".join(classifier_context)
        promptSchema = database_manager.promptSchemaRetrieval("aci-classifier")["schema"]
        promptSchema = promptSchema.format(speaker_data=classifier_context)
        print(promptSchema)
        output = self.generate(promptSchema)[0]["generated_text"]
        uuidkey = uuid.uuid4()
        database_manager.class_data_uploader("classifyLog", {"uuid": uuidkey, "userInput": classifier_context,
                                                            "classifyType": output})
        return output

    def gather_info(self, text):
        return info.research(text)

    async def multithread_server_updates(self, servers, server_updates):
        client = httpx.AsyncClient(timeout=20)
        async with client:
            tasks = []
            for url, data in zip(servers, server_updates):
                tasks.append(client.post(url, json=data))
            results = await asyncio.gather(*tasks)
        # close async client
        await client.aclose()
