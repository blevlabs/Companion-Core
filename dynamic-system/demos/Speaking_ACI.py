import sys
import random
import time

sys.path.insert(0, '/home/blabs/Companion-Core/dynamic-system/core')
from dynamic_library import dynamic

dynamic_instance = dynamic()
input("Please ensure that the audio server is running. Press enter to continue.")
prevSpeech = ""
while 1:
    audio_data = dynamic_instance.audio_request()
    speech = audio_data["text"]
    if speech != prevSpeech:
        print("SPEECH: ", speech)
        time.sleep(0.5)
    else:
        continue
    prevSpeech = speech
    # print("Interpreting..")
    # response = aci_instance.prompt_generation(speech, {"names": ["Brayden"]})
    # aci_instance.generate_speech(response["companionResponse"])
    # print("Companion Core: ", response["companionResponse"])
    # aci_instance.run_speech()
