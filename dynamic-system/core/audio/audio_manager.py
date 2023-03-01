from gtts import gTTS
from playsound import playsound

main_audio_file = "/home/blabs/Companion-Core/dynamic-system/core/audio/speaker.wav"


def textGen(dialogue=""):
    language = "en"
    speech = gTTS(text=dialogue, lang=language, slow=False,)
    speech.save(main_audio_file)
    return


def speak_to_user(mainfile=main_audio_file):
    playsound(mainfile)
    return
