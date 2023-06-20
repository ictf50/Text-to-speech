import speech_recognition as sr
from gtts import gTTS
import pygame
import os
import threading
from playsound import playsound
from pathlib import Path
import tkinter as tk
import uuid
from tkinter import filedialog, ttk
import shutil
import queue


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
            print(f"Loading story file: {file.stem}")  # Debug print
            with open(file, "r") as f:
                story = f.read()
                self.stories[file.stem.lower()] = story  # Make keys case-insensitive

    def play_story(self, story):
        tmp_file = f"tmp_{uuid.uuid4().hex}.mp3"
        tts = gTTS(self.stories[story])
        tts.save(tmp_file)
        print(f"Saved TTS output to {tmp_file}")  # Debug print
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


class VoiceControl:
    def __init__(self, saluting, story_player):
        self.r = sr.Recognizer()
        self.saluting = saluting
        self.story_player = story_player
        self.story_player.stop_flag = False
        self.running = True
        self.command_queue = queue.Queue()

    def start(self):
        greet_thread = threading.Thread(target=self.saluting.greet)
        greet_thread.start()

        commands_thread = threading.Thread(target=self.process_commands)
        commands_thread.start()

        while self.running:
            with sr.Microphone() as source:
                print("Listening...")
                audio = self.r.listen(source, timeout=1, phrase_time_limit=3)

                try:
                    command = self.r.recognize_google(audio)
                    print("Google Speech Recognition thinks you said: " + command)  # Debug print
                    self.command_queue.put(command)
                except sr.UnknownValueError:
                    print("Sorry, I didn't understand that.")
                except sr.RequestError:
                    print("Sorry, I couldn't connect to the service.")
                except sr.WaitTimeoutError:
                    print("Timeout reached, please try again.")

    def process_commands(self):
        while self.running:
            if not self.command_queue.empty():
                command = self.command_queue.get()
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
                        if story.lower() in command.lower():  # Case-insensitive match
                            print(f"Playing {story}...")
                            threading.Thread(target=self.story_player.play_story, args=(story,)).start()
                            break
                    else:
                        print("Sorry, I didn't understand that.")


class VoiceControlUI:
    def __init__(self, voice_control):
        self.voice_control = voice_control
        self.voice_control_thread = None
        self.story_window = None

    def display_story_content(self, story_title):
        for widget in self.story_window.winfo_children():
            widget.destroy()

        # Define an initial font size
        self.font_size = 16

        # Define the font
        self.my_font = ("Arial", self.font_size)

        def increase_font():
            if self.font_size < 24:
                self.font_size += 1
                self.my_font = ("Arial", self.font_size)
                text_area.configure(font=self.my_font)

        def decrease_font():
            if self.font_size > 14:
                self.font_size -= 1
                self.my_font = ("Arial", self.font_size)
                text_area.configure(font=self.my_font)

        control_frame = tk.Frame(self.story_window)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        back_button = tk.Button(control_frame, text="← Back", command=self.display_stories)
        back_button.pack(side=tk.LEFT)

        decrease_button = tk.Button(control_frame, text="-", command=decrease_font)
        decrease_button.pack(side=tk.RIGHT)

        increase_button = tk.Button(control_frame, text="+", command=increase_font)
        increase_button.pack(side=tk.RIGHT)

        story_content = self.voice_control.story_player.stories[story_title]

        scroll = tk.Scrollbar(self.story_window)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        text_area = tk.Text(self.story_window, wrap=tk.WORD, font=self.my_font, yscrollcommand=scroll.set, padx=5,
                            pady=5)
        text_area.insert(tk.INSERT, story_content)
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll.config(command=text_area.yview)

    def display_stories(self):
        try:
            if self.story_window and self.story_window.winfo_viewable():
                for widget in self.story_window.winfo_children():
                    widget.destroy()
            else:
                raise tk.TclError
        except tk.TclError:
            self.story_window = tk.Toplevel()
            window_width = 600
            window_height = 600
            screen_width = self.story_window.winfo_screenwidth()
            screen_height = self.story_window.winfo_screenheight()
            position_top = int(screen_height / 2 - window_height / 2)
            position_right = int(screen_width / 2 - window_width / 2)
            self.story_window.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")
            self.story_window.title("Stories")

        title_label = tk.Label(self.story_window, text="Stories", font=("Arial", 25))
        title_label.pack(pady=20)

        canvas = tk.Canvas(self.story_window)
        scrollbar = ttk.Scrollbar(self.story_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        row = 0
        for story_title in self.voice_control.story_player.stories.keys():
            padding_label = tk.Label(scrollable_frame, text="", width=24)
            padding_label.grid(row=row, column=0)

            story_button = tk.Button(scrollable_frame, text=story_title,
                                     command=lambda title=story_title: self.display_story_content(title),
                                     font=("Arial", 18))
            story_button.grid(row=row, column=1, pady=5)

            row += 1

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def add_story(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            shutil.copy(file_path, self.voice_control.story_player.stories_dir)
            file = Path(file_path)
            with open(file, "r") as f:
                story = f.read()
                self.voice_control.story_player.stories[file.stem] = story

    def run(self):
        def start_voice_control():
            self.voice_control_thread = threading.Thread(target=self.voice_control.start)
            self.voice_control_thread.start()

        def stop_and_exit():
            self.voice_control.story_player.stop_flag = True
            self.voice_control.story_player.pause_event.set()
            self.voice_control.running = False

            if self.voice_control_thread and self.voice_control_thread.is_alive():
                self.voice_control_thread.join()

            root.destroy()

        root = tk.Tk()
        root.geometry("600x600")
        root.title("Voice Control")
        canvas = tk.Canvas(root, width=600, height=600)
        canvas.pack()
        for i in range(0, 600, 100):
            points = [i, 600, i + 50, 550, i + 100, 600]
            canvas.create_polygon(points, fill="#221E38", outline="#221E38")
        start_button = tk.Button(root, text="Start", command=start_voice_control, bg="white", fg="black",
                                 font=("Arial", 25), activebackground="blue")
        start_button.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        exit_button = tk.Button(root, text="Exit", command=stop_and_exit, bg="white", fg="black", font=("Arial", 25),
                                activebackground="blue")
        exit_button.place(relx=0.5, rely=0.7, anchor=tk.CENTER)
        display_stories_button = tk.Button(root, text="Display Stories", command=self.display_stories, bg="white",
                                           fg="black", font=("Arial", 25), activebackground="blue")
        display_stories_button.place(relx=0.5, rely=0.6, anchor=tk.CENTER)
        add_story_button = tk.Button(root, text="Add Story", command=self.add_story, bg="white", fg="black",
                                     font=("Arial", 25), activebackground="blue")
        add_story_button.place(relx=0.5, rely=0.8, anchor=tk.CENTER)
        root.mainloop()


if __name__ == '__main__':
    saluting = Saluting("Welcome!")
    story_player = StoryPlayer("stories")
    voice_control = VoiceControl(saluting, story_player)
    ui = VoiceControlUI(voice_control)
    ui.run()
