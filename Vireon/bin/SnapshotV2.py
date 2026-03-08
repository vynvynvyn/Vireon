import pyautogui
import os
from plyer import notification
import tkinter as tk
from interface import mainInterface

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
            outline="white", width=2
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
selected_box = selector.coords  
if not selected_box or selected_box[2] == 0 or selected_box[3] == 0:
    mainInterface.log("No region selected. Exiting...")
    exit(1)

x, y, width, height = selected_box
img = pyautogui.screenshot(region=(x, y, width, height))

img_path = os.path.join(os.path.dirname(__file__), "snap.png")
img.save(img_path)

notification.notify(
    title="Vireon",
    message=f"Snapshot has been taken ({width}x{height})!",
    timeout=1
)

mainInterface.log(f"Snapshot saved at {img_path}")

