# hot_ocr_hub.py
import customtkinter as ctk
import json
import os
import subprocess
import threading
import time
from plyer import notification
import keyboard

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

KEYBIND_DISPLAY = {
    "TakeSnapshot": "Recognize Text",
    "WriteText": "Start Typing"
}

CONFIG_PATH = "config.json"

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
else:
    config = {
        "WPM": 90,
        "Keybinds": {
            "TakeSnapshot": "F6",
            "WriteText": "F12"
        },
        "UseSnapshotV2": True
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


class mainInterface(ctk.CTk):
    instance = None

    def __init__(self):
        super().__init__()
        mainInterface.instance = self
        self.waiting_for_key = None
        self.overrideredirect(True)
        self.geometry("750x600+300+100")
        self.wm_attributes("-transparentcolor", "white")

        # Main frame
        self.main_frame = ctk.CTkFrame(self, fg_color="#121212", corner_radius=30)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.main_frame.bind("<ButtonPress-1>", self.start_move)
        self.main_frame.bind("<B1-Motion>", self.on_move)

        # Close button
        self.close_btn = ctk.CTkButton(self.main_frame, text="✕", width=30, height=30,
                                       fg_color="#ff4c4c", hover_color="#ff0000", command=self.destroy)
        self.close_btn.place(relx=0.97, rely=0.02, anchor="ne")

        # Title
        self.title_label = ctk.CTkLabel(self.main_frame, text="Vireon",
                                        font=ctk.CTkFont(family="Roboto", size=22, weight="bold"))
        self.title_label.pack(pady=(10, 20))

        # Config Section
        self.config_frame = ctk.CTkFrame(self.main_frame, fg_color="#1b1b1b", corner_radius=20)
        self.config_frame.pack(fill="x", padx=20, pady=10)
        self.config_label = ctk.CTkLabel(self.config_frame, text="Config",
                                         font=ctk.CTkFont(family="Roboto", size=16, weight="bold"))
        self.config_label.pack(anchor="w", pady=(5, 0), padx=10)

        # Settings
        self.settings_frame = ctk.CTkFrame(self.config_frame, fg_color="#242424", corner_radius=15)
        self.settings_frame.pack(fill="x", padx=15, pady=10)
        self.settings_label = ctk.CTkLabel(self.settings_frame, text="Settings",
                                           font=ctk.CTkFont(family="Roboto", size=14, weight="bold"))
        self.settings_label.pack(anchor="w", pady=(5, 5), padx=10)

        # WPM Slider + Entry
        wpm_container = ctk.CTkFrame(self.settings_frame, fg_color="#2c2c2c", corner_radius=10)
        wpm_container.pack(fill="x", padx=10, pady=5)
        self.wpm_label = ctk.CTkLabel(wpm_container, text="WPM", width=100, anchor="w",
                                      font=ctk.CTkFont(family="Roboto", size=12))
        self.wpm_label.pack(side="left", padx=10, pady=5)
        self.wpm_slider = ctk.CTkSlider(wpm_container, from_=20, to=700, number_of_steps=280, command=self.update_wpm)
        self.wpm_slider.set(config.get("WPM", 90))
        self.wpm_slider.pack(side="left", padx=10, fill="x", expand=True)
        self.wpm_entry = ctk.CTkEntry(wpm_container, width=50)
        self.wpm_entry.pack(side="right", padx=10)
        self.wpm_entry.insert(0, str(config.get("WPM", 90)))
        self.wpm_entry.bind("<Return>", self.update_wpm_from_entry)

        # Keybinds
        self.keybinds_label = ctk.CTkLabel(self.settings_frame, text="Keybinds",
                                           font=ctk.CTkFont(family="Roboto", size=14, weight="bold"))
        self.keybinds_label.pack(anchor="w", pady=(10, 5), padx=10)
        self.keybind_labels = {}
        for action, key in config["Keybinds"].items():
            frame = ctk.CTkFrame(self.settings_frame, fg_color="#2c2c2c", corner_radius=15)
            frame.pack(fill="x", padx=15, pady=3)

            display_name = KEYBIND_DISPLAY.get(action, action)

            action_label = ctk.CTkLabel(
                frame,
                text=display_name,
                width=200,
                anchor="w",
                font=ctk.CTkFont(family="Roboto", size=12)
            )
            action_label.pack(side="left", padx=10, pady=5)

            key_label = ctk.CTkLabel(
                frame,
                text=key,
                width=100,
                anchor="center",
                fg_color="#3a3a3a",
                font=ctk.CTkFont(family="Roboto", size=12)
            )
            key_label.pack(side="right", padx=10, pady=5)

        # Outputs section
        self.output_frame = ctk.CTkFrame(self.main_frame, fg_color="#1b1b1b", corner_radius=20)
        self.output_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.output_text = ctk.CTkTextbox(self.output_frame, font=ctk.CTkFont(family="Roboto", size=12))
        self.output_text.pack(fill="both", expand=True, padx=10, pady=10)

        self.bind("<Key>", self.on_key_press)

        # Start background key listener thread
        listener_thread = threading.Thread(target=self.global_hotkey_listener, daemon=True)
        listener_thread.start()

    # --- Keybind editing ---
    def start_rebind(self, action_name):
        self.waiting_for_key = action_name
        self.keybind_labels[action_name].configure(fg_color="#4b4bff")

    def on_key_press(self, event):
        if self.waiting_for_key:
            new_key = event.keysym
            action_name = self.waiting_for_key
            self.waiting_for_key = None
            self.keybind_labels[action_name].configure(text=new_key, fg_color="#3a3a3a")
            config["Keybinds"][action_name] = new_key
            self.save_config()

    # --- WPM slider / entry ---
    def update_wpm(self, value):
        self.wpm_entry.delete(0, "end")
        self.wpm_entry.insert(0, str(int(float(value))))
        config["WPM"] = int(float(value))
        self.save_config()

    def update_wpm_from_entry(self, event):
        try:
            value = int(self.wpm_entry.get())
            if 20 <= value <= 300:
                self.wpm_slider.set(value)
                config["WPM"] = value
                self.save_config()
        except ValueError:
            pass

    # --- Toggle ---
    def toggle_snapshot(self):
        config["UseSnapshotV2"] = bool(self.use_snapshot_toggle.get())
        self.save_config()

    # --- Save config ---
    def save_config(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    # --- Draggable window ---
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    # --- Logging method ---
    @staticmethod
    def log(message: str):
        if mainInterface.instance:
            mainInterface.instance.output_text.insert("end", message + "\n")
            mainInterface.instance.output_text.see("end")

    # --- Global hotkey listener in background ---
    def global_hotkey_listener(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        snapshot_scriptV2 = os.path.join(current_dir, "SnapshotV2.py")
        snapshot_script = os.path.join(current_dir, "Snapshot.py")
        write_text_script = os.path.join(current_dir, "WriteText.py")

        while True:
            try:
                with open(CONFIG_PATH, "r") as f:
                    cfg = json.load(f)
                snapshot_key = cfg["Keybinds"]["TakeSnapshot"]
                write_text_key = cfg["Keybinds"]["WriteText"]

                if keyboard.is_pressed(snapshot_key):
                    mainInterface.log(f"Running Snapshot script...")
                    if cfg.get("UseSnapshotV2", True):
                        notification.notify(
                            title="Snapshot",
                            message="Select the region of text..",
                            timeout=0.2
                        )
                        subprocess.run(["py", snapshot_scriptV2])
                    else:
                        subprocess.run(["py", snapshot_script])
                    while keyboard.is_pressed(snapshot_key):
                        time.sleep(0.1)

                if keyboard.is_pressed(write_text_key):
                    mainInterface.log(f"Running WriteText script...")
                    subprocess.run(["py", write_text_script])
                    while keyboard.is_pressed(write_text_key):
                        time.sleep(0.1)

                time.sleep(0.05)
            except Exception as e:
                mainInterface.log(f"Error in hotkey listener: {e}")
                time.sleep(1)


if __name__ == "__main__":
    app = mainInterface()
    app.mainloop()