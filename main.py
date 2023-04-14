import speech_recognition as sr
from gtts import gTTS
import pygame
import os
import threading
from playsound import playsound
from pathlib import Path
import uuid

class Saluting:
    def __init__(self, greeting):
        self.greeting = greeting

    def greet(self):
        tmp_file = f"tmp_{uuid.uuid4().hex}.mp3"
        tts = gTTS(self.greeting)
        tts.save(tmp_file)
        pygame.mixer.init()
        pygame.mixer.music.load(tmp_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pass
        pygame.mixer.quit()
        os.remove(tmp_file)

class StoryPlayer:
    def __init__(self, stories_dir):
        self.stories_dir = stories_dir
        self.stories = {}
        self.stop_flag = False
        self.finished = False
        self.mixer_initialized = False
        self.pause_event = threading.Event()

        for file in Path(self.stories_dir).glob("*.txt"):
            with open(file, "r") as f:
                story = f.read()
                self.stories[file.stem] = story

    def play_story(self, story):
        tmp_file = f"tmp_{uuid.uuid4().hex}.mp3"
        tts = gTTS(self.stories[story])
        tts.save(tmp_file)
        pygame.mixer.init()
        self.mixer_initialized = True
        pygame.mixer.music.load(tmp_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() and not self.stop_flag:
            pygame.time.Clock().tick(10)
            self.pause_event.wait()
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        self.mixer_initialized = False
        os.remove(tmp_file)

    def pause(self):
        if self.mixer_initialized:
            pygame.mixer.music.pause()
            self.pause_event.clear()

    def resume(self):
        if self.mixer_initialized:
            pygame.mixer.music.unpause()
            self.pause_event.set()

class VoiceControl:
    def __init__(self, saluting, story_player):
        self.r = sr.Recognizer()
        self.saluting = saluting
        self.story_player = story_player
        self.story_player.stop_flag = False

    def start(self):
        threading.Thread(target=self.saluting.greet).start()

        while True:
            with sr.Microphone() as source:
                print("Listening...")
                audio = self.r.listen(source, timeout=1, phrase_time_limit=3)
                print(audio)

                try:
                    command = self.r.recognize_google(audio)
                    print(f"You said: {command}")

                    if "stop" in command.lower():
                        if self.story_player.finished:
                            self.saluting.greeting = "nothing to stop, please try again."
                            self.saluting.greet()
                        else:
                            self.story_player.pause()
                    elif "complete" in command.lower():
                        if self.story_player.finished:
                            self.saluting.greeting = "nothing to complete, please try again."
                            self.saluting.greet()
                        else:
                            self.story_player.resume()
                    elif "finish" in command.lower():
                        self.story_player.stop_flag = True
                        self.story_player.finished = True
                        self.story_player.pause_event.set()
                        self.story_player.pause()
                    elif "salute" in command.lower():
                        playsound('salute.mp3')
                    else:
                        self.story_player.stop_flag = False
                        self.story_player.finished = False
                        for story in self.story_player.stories:
                            if story in command.lower():
                                print(f"Playing {story}...")
                                threading.Thread(target=self.story_player.play_story, args=(story,)).start()
                                break
                        else:
                            print("Sorry, I didn't understand that.")

                except sr.UnknownValueError:
                    print("Sorry, I didn't understand that.")
                except sr.RequestError:
                    print("Sorry, I couldn't connect to the service.")
                except sr.WaitTimeoutError:
                    print("Timeout reached, please try again.")

if __name__ == '__main__':
    saluting = Saluting("Welcome!")
    story_player = StoryPlayer("stories")
    voice_control = VoiceControl(saluting, story_player)
    voice_control.start()
