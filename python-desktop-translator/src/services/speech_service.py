from gtts import gTTS
import os
import playsound

class SpeechService:
    def __init__(self, language='en'):
        self.language = language

    def text_to_speech(self, text):
        tts = gTTS(text=text, lang=self.language)
        filename = 'temp_audio.mp3'
        tts.save(filename)
        playsound.playsound(filename)
        os.remove(filename)

    def set_language(self, language):
        self.language = language

    def get_language(self):
        return self.language