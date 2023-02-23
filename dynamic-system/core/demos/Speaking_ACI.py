import sys
import random
import time

sys.path.insert(0, '/home/blabs/Companion-Core/dynamic-system/core')
from dynamic_library import dynamic, aci

dynamic_instance = dynamic()
aci_instance = aci
input("Please ensure that the audio server is running. Press enter to continue.")
prevSpeech = ""
while 1:
    audio_data = dynamic_instance.audio_request()
    speech = audio_data["text"]
    if type(speech) == list:
        speechdata = [x.split(":")[-1].strip() for x in speech]
        print(speechdata)
        continue
    else:
        speech = speech.split(":")[-1].strip()
    if speech != prevSpeech:
        print("SPEECH: ", speech)
        time.sleep(0.5)
    else:
        continue
    prevSpeech = speech
    print("Interpreting..")
    response = aci_instance.prompt_generation(speech, {"names": ["Brayden"]})
    aci_instance.generate_speech(response["companionResponse"])
    print("Companion Core: ", response["companionResponse"])
    aci_instance.run_speech()
