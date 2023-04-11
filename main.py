import speech_recognition as sr
from gtts import gTTS
import pygame
import os
import requests
from playsound import playsound

# Define the directory where the stories are stored
directory = "stories"

# Get a list of all the files in the directory
files = os.listdir(directory)

# Loop through each file and read in the contents
stories = {}
for file in files:
    # Check that the file is a text file
    if file.endswith(".txt"):
        # Open the file and read in the contents
        with open(os.path.join(directory, file), "r") as f:
            story = f.read()
            stories[file[:-4]] = story

# initialize the speech recognizer
r = sr.Recognizer()

def Saluting(saluting):
    tts = gTTS(saluting)
    tts.save('st.mp3')
    pygame.mixer.init()
    pygame.mixer.music.load('st.mp3')
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pass
    pygame.mixer.quit()

# define a function to play the story
def play_story(story):
    # convert the story to speech
    tts = gTTS(stories[story])
    tts.save('story.mp3')
    # play the speech
    pygame.mixer.init()
    pygame.mixer.music.load('story.mp3')
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pass
    pygame.mixer.quit()

# call the Saluting function to greet the user
Saluting("Welcome!")

# loop forever to listen for voice commands
while True:
    with sr.Microphone() as source:
        print("Listening...")
        # listen for a voice command
        audio = r.listen(source)
        print(audio)  # print the captured audio

        try:
            # recognize the voice command
            command = r.recognize_google(audio)
            print(f"You said: {command}")

            # check if the command contains the word "salute"
            if "salute" in command.lower():
                # play a sound or speech clip that represents a salute
                playsound('salute.mp3')
            else:
                # try to match the command to a story
                for story in stories:
                    if story in command.lower():
                        print(f"Playing {story}...")
                        play_story(story)
                        break
                else:
                    print("Sorry, I didn't understand that.")

        except sr.UnknownValueError:
            print("Sorry, I didn't understand that.")
        except sr.RequestError:
            print("Sorry, I couldn't connect to the service.")
