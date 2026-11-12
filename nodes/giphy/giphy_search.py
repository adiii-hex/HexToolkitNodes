# Giphy search: type a keyword, click a GIF to select it, press Delete to clear it.
import base64
import json
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tkinter import ttk

import requests

ROOT = Path(__file__).resolve().parents[2]
API_KEY = json.loads((ROOT / "keys" / "keys.json").read_text())["giphy_key"]
RESULTS = 12
COLUMNS = 4
MAX_FRAMES = 60
FRAME_DELAY_MS = 80
SELECTED_COLOR = "#2f7cf6"


def search_gifs(keyword):
    response = requests.get(
        "https://api.giphy.com/v1/gifs/search",
        params={"api_key": API_KEY, "q": keyword, "limit": RESULTS, "rating": "g"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["data"]


def download(url):
    return base64.b64encode(requests.get(url, timeout=30).content).decode()


def load_frames(data):
    frames = []
    for i in range(MAX_FRAMES):
        try:
            part = tk.PhotoImage(data=data, format=f"gif -index {i}")
        except tk.TclError:
            break
        frame = tk.PhotoImage(width=part.width(), height=part.height())
        if frames:
            frame.tk.call(frame, "copy", frames[-1])
        frame.tk.call(frame, "copy", part, "-compositingrule", "overlay")
        frames.append(frame)
    return frames


class GiphyWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Giphy search")
        self.tiles = []
        self.selected = None

        top = ttk.Frame(self.window, padding=12)
        top.pack(fill="x")
        self.search_box = ttk.Entry(top, width=40)
        self.search_box.pack(side="left", fill="x", expand=True)
        self.search_box.bind("<Return>", lambda e: self.search())
        ttk.Button(top, text="Search", command=self.search).pack(side="left", padx=(8, 0))

        self.status = ttk.Label(self.window, text="Type a keyword and press Enter", padding=(12, 0))
        self.status.pack(anchor="w")

        self.grid = tk.Frame(self.window, padx=12, pady=12)
        self.grid.pack()

        self.window.bind_all("<BackSpace>", self.delete_selected)
        self.window.bind_all("<Delete>", self.delete_selected)
        self.window.lift()
        self.window.attributes("-topmost", True)
        self.window.after(200, lambda: self.window.attributes("-topmost", False))
        self.search_box.focus_set()

    def search(self):
        keyword = self.search_box.get().strip()
        if not keyword:
            return
        self.status.config(text=f"Searching for “{keyword}”...")
        self.window.update()
        self.clear_selection()
        for tile in self.tiles:
            tile["frame"].destroy()
        self.tiles = []

        gifs = search_gifs(keyword)
        urls = [g["images"]["fixed_height_small"]["url"] for g in gifs]
        with ThreadPoolExecutor(max_workers=6) as pool:
            images = list(pool.map(download, urls))

        for index, (gif, data) in enumerate(zip(gifs, images)):
            frames = load_frames(data)
            if not frames:
                continue
            frame = tk.Frame(self.grid)
            frame.grid(row=index // COLUMNS, column=index % COLUMNS, padx=2, pady=2)
            label = tk.Label(frame, image=frames[0], bd=0, cursor="hand2")
            label.pack(padx=4, pady=4)
            tile = {"frame": frame, "label": label, "frames": frames, "gif": gif, "index": 0}
            label.bind("<Button-1>", lambda e, t=tile: self.select(t))
            self.tiles.append(tile)
            self.animate(tile)

        self.status.config(text=f"{len(self.tiles)} GIFs for “{keyword}”. Click one to select, Delete to clear.")

    def animate(self, tile):
        if not tile["label"].winfo_exists():
            return
        tile["index"] = (tile["index"] + 1) % len(tile["frames"])
        tile["label"].config(image=tile["frames"][tile["index"]])
        self.window.after(FRAME_DELAY_MS, lambda: self.animate(tile))

    def select(self, tile):
        self.clear_selection()
        self.selected = tile
        tile["frame"].config(bg=SELECTED_COLOR)
        self.window.focus_set()
        print("gif selected: paste on the canvas", flush=True)

    def clear_selection(self):
        if self.selected and self.selected["frame"].winfo_exists():
            self.selected["frame"].config(bg=self.grid.cget("bg"))
        self.selected = None

    def delete_selected(self, event):
        if event.widget is self.search_box or not self.selected:
            return
        self.clear_selection()
        print("gif deleted", flush=True)

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    GiphyWindow().run()
