import cv2
import pytesseract
import pyautogui
import json
import os
from plyer import notification
import shutil
import sys
import keyboard
import time

from interface import mainInterface

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
config_path = os.path.join(root_dir, "config.json")

if not os.path.exists(config_path):
    raise FileNotFoundError(f"{config_path} does not exist!")

with open(config_path, "r", encoding="utf-8") as f:
    content = f.read().strip()
    if not content:
        raise ValueError(f"{config_path} is empty!")
    data = json.loads(content)

mainInterface.log(f"Config loaded: {data}")

stop_key = data["Keybinds"]["WriteText"]

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False


def detect_tesseract():
    tesseract_path = shutil.which("tesseract")
    if tesseract_path:
        return tesseract_path

    default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(default_path):
        return default_path

    appdata_path = os.path.expandvars(
        r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"
    )
    if os.path.exists(appdata_path):
        return appdata_path

    return None


tesseract_cmd = detect_tesseract()

if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    mainInterface.log(f"Tesseract found: {tesseract_cmd}")
else:
    sys.exit(
        "Tesseract not found! Install from https://github.com/tesseract-ocr/tesseract"
    )

img_path = os.path.join(os.path.dirname(__file__), "snap.png")

if not os.path.exists(img_path):
    raise FileNotFoundError(f"{img_path} does not exist! Run Snapshot.py first.")

img = cv2.imread(img_path)

if img is None:
    raise ValueError(f"Failed to load image at {img_path}")

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

text = pytesseract.image_to_string(gray)
text = text.replace("\n", " ")

wpm = data["WPM"]
interval = 12 / wpm

mainInterface.log(f"Typing interval: f{interval}")
mainInterface.log(f"Press '{stop_key}' to stop typing.")

for char in text:

    if keyboard.is_pressed(stop_key):
        mainInterface.log("Typing stopped by user.")
        notification.notify(
            title="Vireon",
            message="Typing stopped.",
            timeout=1
        )
        sys.exit()

    pyautogui.write(char)
    time.sleep(interval)


mainInterface.log("Typing complete!")

notification.notify(
    title="Vireon",
    message="Text typing complete!",
    timeout=1
)