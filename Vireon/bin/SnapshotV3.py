# This cannot yet be implemented.
import cv2
import pytesseract
import pyautogui
import time
import os
import json
import tkinter as tk
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)  # main folder
config_path = os.path.join(root_dir, "config.json")

if not os.path.exists(config_path):
    raise FileNotFoundError(f"{config_path} does not exist!")

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

wpm = config.get("WPM", 120)
interval = 12 / wpm  

pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Danny\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

class BoxSelector:
    def __init__(self):
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.coords = None

        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.root.attributes("-topmost", True)
        self.root.config(cursor="cross")
        self.canvas = tk.Canvas(self.root, cursor="cross", bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.mainloop()

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2
        )

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        self.coords = (
            min(self.start_x, event.x),
            min(self.start_y, event.y),
            abs(event.x - self.start_x),
            abs(event.y - self.start_y)
        )
        self.root.destroy()

selector = BoxSelector()
x, y, width, height = selector.coords
if not width or not height:
    print("No region selected. Exiting.")
    exit(1)

typed_text = ""
print("Starting real-time typing in 2 seconds...")
time.sleep(2)  

try:
    while True:
        img = pyautogui.screenshot(region=(x, y, width, height))
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

        text = pytesseract.image_to_string(thresh).replace("\n", " ")

        if len(text) > len(typed_text):
            new_text = text[len(typed_text):]
            chunk_size = 15
            for i in range(0, len(new_text), chunk_size):
                chunk = new_text[i:i+chunk_size]
                pyautogui.typewrite(chunk, interval=interval)
                typed_text += chunk
                time.sleep(0.05)

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nReal-time typing stopped by user.")