from gtts import gTTS
from playsound import playsound

main_audio_file = "/home/blabs/Companion-Core/dynamic-system/core/resources/audio/speaker.wav"


def textGen(dialogue=""):
    language = "en"
    speech = gTTS(text=dialogue, lang=language, slow=False,)
    speech.save("/home/blabs/Companion-Core/dynamic-system/core/resources/audio/speaker.wav")
    return


def speak_to_user(mainfile="/home/blabs/Companion-Core/dynamic-system/core/resources/audio/speaker.wav"):
    playsound(mainfile)
    return
