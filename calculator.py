import tkinter as tk
import json
import os
import re
import sys
from pages import CalculatorPage, CapPage, RCPage, LCPage, DivPage

BASE_W, BASE_H = 520, 610


def _config_path():
    if getattr(sys, "frozen", False):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.path.dirname(__file__)
    d = os.path.join(base, "calculator")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "calc_config.json")


class App:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)
        self.root.resizable(True, True)
        self.root.minsize(400, 480)
        self.root.configure(bg="#1e1e1e")

        self._drag_data = {"x": 0, "y": 0}
        self._nav_btns = {}
        self.current_page = None
        self.config = self._load_config()

        self._setup_geometry()
        self._create_title_bar()
        self._create_container()
        self._create_pages()
        self._show_page(self.config.get("page", "calc"))
        self.root.bind("<Configure>", self._on_resize)

    # ── Config ─────────────────────────────────────────────────

    def _load_config(self):
        path = _config_path()
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"x": None, "y": None, "w": BASE_W, "h": BASE_H, "page": "calc"}

    def _save_config(self):
        geo = self.root.geometry()
        m = re.match(r"(\d+)x(\d+)[+]?(-?\d+)?[+]?(-?\d+)?", geo)
        if m:
            w, h, x, y = m.groups()
            self.config.update(w=int(w), h=int(h), page=self.current_page)
            if x is not None:
                self.config["x"] = int(x)
            if y is not None:
                self.config["y"] = int(y)
        try:
            path = _config_path()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _setup_geometry(self):
        w = self.config.get("w", BASE_W)
        h = self.config.get("h", BASE_H)
        x, y = self.config.get("x"), self.config.get("y")
        if x is not None and y is not None:
            self.root.geometry(f"{w}x{h}+{x}+{y}")
        else:
            self.root.geometry(f"{w}x{h}")

    # ── Title Bar ──────────────────────────────────────────────

    def _create_title_bar(self):
        bar = tk.Frame(self.root, bg="#2d2d2d", height=34)
        bar.pack(fill=tk.X, side=tk.TOP)
        bar.pack_propagate(False)

        title = tk.Label(bar, text="\u79d1\u5b66\u8ba1\u7b97\u5668", bg="#2d2d2d",
                         fg="#c8c8c8", font=("Segoe UI", 10))
        title.pack(side=tk.LEFT, padx=8)

        nav_frame = tk.Frame(bar, bg="#2d2d2d")
        nav_frame.pack(side=tk.LEFT, padx=4)

        pages = [
            ("calc", "\u8ba1\u7b97\u5668"),
            ("cap", "\u7535\u5bb9"),
            ("rc", "RC\u6ee4\u6ce2"),
            ("lc", "LC\u6ee4\u6ce2"),
            ("div", "\u5206\u538b"),
        ]

        for key, label in pages:
            btn = tk.Button(nav_frame, text=label, bg="#3c3c3c", fg="#a0a0a0",
                            font=("Segoe UI", 9), relief=tk.FLAT,
                            activebackground="#4a4a4a", cursor="hand2",
                            command=lambda k=key: self._show_page(k))
            btn.pack(side=tk.LEFT, padx=1, pady=3)
            self._nav_btns[key] = btn

        close_btn = tk.Button(bar, text="\u2715", bg="#a04040", fg="white",
                              font=("Segoe UI", 10), relief=tk.FLAT,
                              activebackground="#c05050", cursor="hand2",
                              command=self._on_close)
        close_btn.pack(side=tk.RIGHT, padx=4, pady=2)

        for w in (bar, title):
            w.bind("<Button-1>", self._start_move)
            w.bind("<B1-Motion>", self._do_move)

    def _start_move(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _do_move(self, event):
        x = self.root.winfo_x() + event.x - self._drag_data["x"]
        y = self.root.winfo_y() + event.y - self._drag_data["y"]
        self.root.geometry(f"+{x}+{y}")

    # ── Pages ──────────────────────────────────────────────────

    def _create_container(self):
        self.container = tk.Frame(self.root, bg="#1e1e1e")
        self.container.pack(fill=tk.BOTH, expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def _create_pages(self):
        items = [("calc", CalculatorPage), ("cap", CapPage),
                 ("rc", RCPage), ("lc", LCPage), ("div", DivPage)]
        self.pages = {}
        for key, cls in items:
            page = cls(self.container)
            page.frame.grid(row=0, column=0, sticky="nsew")
            page.frame.grid_remove()
            self.pages[key] = page

    def _show_page(self, key):
        if self.current_page == key:
            return
        if self.current_page and self.pages.get(self.current_page):
            self.pages[self.current_page].hide()
        self.current_page = key
        if key in self.pages:
            self.pages[key].show()
        for k, btn in self._nav_btns.items():
            if k == key:
                btn.config(bg="#4a7eb5", fg="white")
            else:
                btn.config(bg="#3c3c3c", fg="#a0a0a0")

    # ── Resize ─────────────────────────────────────────────────

    def _on_resize(self, event):
        if event.widget is not self.root:
            return
        w = max(event.width, self.root.minsize()[0])
        scale = w / BASE_W
        for p in self.pages.values():
            p.scale_fonts(scale)

    # ── Close ──────────────────────────────────────────────────

    def _on_close(self):
        self._save_config()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
