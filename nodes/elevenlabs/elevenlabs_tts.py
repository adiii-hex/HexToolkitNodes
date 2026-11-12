# ElevenLabs text to speech: type text, pick a voice, get an mp3.
import json
import subprocess
import tempfile
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk

import requests

ROOT = Path(__file__).resolve().parents[2]
API_KEY = json.loads((ROOT / "keys" / "keys.json").read_text())["elevenlabs_key"]
HEADERS = {"xi-api-key": API_KEY}
OUTPUT_DIR = ROOT / "outputs" / "elevenlabs"


def get_voices():
    response = requests.get("https://api.elevenlabs.io/v1/voices", headers=HEADERS, timeout=30)
    response.raise_for_status()
    voices = [v for v in response.json()["voices"] if v["category"] == "premade" and v.get("preview_url")]
    return sorted(voices, key=lambda v: v["name"])


def pick_voice(voices):
    names = [v["name"] for v in voices]
    chosen = {}
    player = {"process": None}

    def stop_audio():
        if player["process"] and player["process"].poll() is None:
            player["process"].terminate()

    def play_sample():
        voice = voices[names.index(dropdown.get())]
        stop_audio()
        sample = Path(tempfile.gettempdir()) / f"sample_{voice['voice_id']}.mp3"
        if not sample.exists():
            sample.write_bytes(requests.get(voice["preview_url"], timeout=30).content)
        player["process"] = subprocess.Popen(["afplay", str(sample)])

    def select():
        stop_audio()
        chosen["voice"] = voices[names.index(dropdown.get())]
        window.destroy()

    window = tk.Tk()
    window.title("Choose a voice")
    window.protocol("WM_DELETE_WINDOW", lambda: (stop_audio(), window.destroy()))

    frame = ttk.Frame(window, padding=16)
    frame.pack()
    ttk.Label(frame, text="Voice").pack(anchor="w")
    dropdown = ttk.Combobox(frame, values=names, state="readonly", width=45)
    dropdown.current(0)
    dropdown.pack(pady=(4, 12))
    ttk.Button(frame, text="▶  Play sample", command=play_sample).pack(fill="x")
    ttk.Button(frame, text="Use this voice", command=select).pack(fill="x", pady=(6, 0))

    window.lift()
    window.attributes("-topmost", True)
    window.after(200, lambda: window.attributes("-topmost", False))
    window.mainloop()
    return chosen.get("voice")


def text_to_speech(text, voice):
    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice['voice_id']}",
        headers={**HEADERS, "Accept": "audio/mpeg"},
        json={"text": text, "model_id": "eleven_multilingual_v2"},
        timeout=120,
    )
    response.raise_for_status()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    name = voice["name"].split(" - ")[0].lower()
    output_file = OUTPUT_DIR / f"{name}_{int(time.time())}.mp3"
    output_file.write_bytes(response.content)
    return output_file


def main():
    text = input("Enter the text to convert to speech: ").strip()
    if not text:
        print("No text entered.")
        return

    print("Choose a voice in the window that opened...")
    voice = pick_voice(get_voices())
    if not voice:
        print("No voice selected.")
        return

    print(f"Converting with {voice['name']}...")
    output_file = text_to_speech(text, voice)
    print(f"Saved: {output_file}")
    subprocess.run(["afplay", str(output_file)])


if __name__ == "__main__":
    main()
