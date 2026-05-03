import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import yt_dlp

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

FFMPEG = resource_path("ffmpeg")

BG = "#0f0f0f"
CARD = "#1a1a1a"
BORDER = "#2a2a2a"
TEXT = "#f0ece4"
SUBTEXT = "#a8a8a0"
ACCENT = "#ff4d00"
ACCENT2 = "#ff8c42"
SUCCESS = "#4caf50"
ERROR = "#f44336"

class TkLogger:
    def __init__(self, app):
        self.app = app

    def debug(self, msg):
        if msg.strip():
            self.app.after(0, self.app._log, msg)

    def warning(self, msg):
        self.app.after(0, self.app._log, "WARNING: " + msg)

    def error(self, msg):
        self.app.after(0, self.app._log, "ERROR: " + msg)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube → MP3 | Pour Papa")
        self.geometry("640x520")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.output_dir = tk.StringVar(value=os.path.expanduser("~/Music"))
        self.url_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Prêt.")
        self.progress = tk.DoubleVar(value=0)
        self._running = False

        self._build_ui()
        self._add_context_menu()
        self._check_deps()

    def _build_ui(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=30, pady=(28, 0))

        tk.Label(header, text="YouTube → MP3", font=("Helvetica", 22, "bold"), bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(header, text="Audio MP3 320 kbps | Simple pour Papa", font=("Helvetica", 10), bg=BG, fg=SUBTEXT).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30, pady=18)

        card = tk.Frame(self, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", padx=30)

        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="x", padx=22, pady=22)
        inner.columnconfigure(0, weight=1)

        tk.Label(inner, text="Lien YouTube", font=("Helvetica", 10, "bold"), bg=CARD, fg=SUBTEXT).grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.url_entry = tk.Entry(
            inner,
            textvariable=self.url_var,
            font=("Courier", 11),
            bg="#111111",
            fg=TEXT,
            insertbackground=ACCENT,
            relief="flat",
            bd=10
        )
        self.url_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        tk.Label(inner, text="Dossier de destination", font=("Helvetica", 10, "bold"), bg=CARD, fg=SUBTEXT).grid(row=2, column=0, sticky="w", pady=(0, 4))

        dir_row = tk.Frame(inner, bg=CARD)
        dir_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        dir_row.columnconfigure(0, weight=1)

        tk.Label(
            dir_row,
            textvariable=self.output_dir,
            font=("Helvetica", 9),
            bg="#111111",
            fg=TEXT,
            anchor="w",
            padx=10,
            pady=10
        ).grid(row=0, column=0, sticky="ew")

        tk.Button(
            dir_row,
            text="Choisir...",
            command=self._browse,
            font=("Helvetica", 10, "bold"),
            bg="#3a3a3a",
            fg="white",
            activebackground=ACCENT,
            activeforeground="white",
            relief="raised",
            bd=2,
            padx=16,
            pady=8,
            cursor="hand2"
        ).grid(row=0, column=1, padx=(10, 0))

        self.dl_btn = tk.Button(
            inner,
            text="TÉLÉCHARGER EN MP3",
            command=self._start_download,
            font=("Helvetica", 13, "bold"),
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT2,
            activeforeground="white",
            relief="raised",
            bd=2,
            pady=14,
            cursor="hand2"
        )
        self.dl_btn.grid(row=4, column=0, columnspan=2, sticky="ew")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "fire.Horizontal.TProgressbar",
            troughcolor=CARD,
            background=ACCENT,
            bordercolor=BORDER,
            lightcolor=ACCENT2,
            darkcolor=ACCENT,
            thickness=10
        )

        ttk.Progressbar(self, style="fire.Horizontal.TProgressbar", variable=self.progress, maximum=100).pack(fill="x", padx=30, pady=(18, 0))

        self.status_lbl = tk.Label(self, textvariable=self.status_var, font=("Helvetica", 9), bg=BG, fg=SUBTEXT, anchor="w")
        self.status_lbl.pack(fill="x", padx=32, pady=(6, 0))

        log_frame = tk.Frame(self, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        log_frame.pack(fill="both", expand=True, padx=30, pady=(10, 24))

        self.log = tk.Text(log_frame, height=8, font=("Courier", 8), bg="#0a0a0a", fg=SUBTEXT, relief="flat", bd=8, state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True)

    def _add_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Coller", command=lambda: self.url_entry.event_generate("<<Paste>>"))
        self.context_menu.add_command(label="Copier", command=lambda: self.url_entry.event_generate("<<Copy>>"))
        self.context_menu.add_command(label="Couper", command=lambda: self.url_entry.event_generate("<<Cut>>"))

        self.url_entry.bind("<Button-2>", self._show_context_menu)
        self.url_entry.bind("<Button-3>", self._show_context_menu)
        self.url_entry.bind("<Command-v>", lambda e: self.url_entry.event_generate("<<Paste>>"))
        self.url_entry.bind("<Control-v>", lambda e: self.url_entry.event_generate("<<Paste>>"))

    def _show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def _log(self, msg):
        self.log.config(state="normal")
        self.log.insert("end", str(msg) + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _set_status(self, msg, color=SUBTEXT):
        self.status_var.set(msg)
        self.status_lbl.config(fg=color)

    def _browse(self):
        folder = filedialog.askdirectory(title="Choisir le dossier de destination", initialdir=self.output_dir.get())
        if folder:
            self.output_dir.set(folder)

    def _check_deps(self):
        if not os.path.exists(FFMPEG):
            messagebox.showerror("Dépendance manquante", "ffmpeg est manquant dans l'application.")
            self._set_status("ffmpeg manquant.", ERROR)
            return

        try:
            os.chmod(FFMPEG, 0o755)
            self._log(f"ffmpeg trouvé: {FFMPEG}")
            self._log("yt-dlp utilisé comme module Python.")
        except Exception as e:
            self._log(f"Erreur chmod ffmpeg: {e}")

    def _start_download(self):
        if self._running:
            return

        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("URL manquante", "Colle un lien YouTube dans le champ.")
            return

        out_dir = self.output_dir.get()
        os.makedirs(out_dir, exist_ok=True)

        self._running = True
        self.dl_btn.config(state="disabled", text="TÉLÉCHARGEMENT EN COURS...")
        self.progress.set(0)
        self._set_status("Démarrage...")

        threading.Thread(target=self._download_worker, args=(url, out_dir), daemon=True).start()

    def _hook(self, d):
        status = d.get("status")

        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0

            if total > 0:
                pct = downloaded / total * 100
                self.after(0, self.progress.set, pct)
                self.after(0, self._set_status, f"Téléchargement : {pct:.1f}%")

        elif status == "finished":
            self.after(0, self.progress.set, 95)
            self.after(0, self._set_status, "Conversion en MP3...", ACCENT2)
            self.after(0, self._log, "Téléchargement terminé, conversion en MP3...")

    def _download_worker(self, url, out_dir):
        try:
            os.chmod(FFMPEG, 0o755)

            self.after(0, self._log, "-" * 55)
            self.after(0, self._log, f"URL : {url}")
            self.after(0, self._log, f"Dossier : {out_dir}")
            self.after(0, self._log, f"ffmpeg : {FFMPEG}")
            self.after(0, self._log, "yt-dlp : module Python")
            self.after(0, self._log, "-" * 55)

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
                "ffmpeg_location": os.path.dirname(FFMPEG),
                "noplaylist": True,
                "quiet": False,
                "no_warnings": False,
                "logger": TkLogger(self),
                "progress_hooks": [self._hook],
                "force_ipv4": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "320",
                    },
                    {
                        "key": "FFmpegMetadata",
                    },
                ],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.after(0, self.progress.set, 100)
            self.after(0, self._set_status, "Téléchargement terminé.", SUCCESS)
            self.after(0, self._log, f"MP3 sauvegardé dans : {out_dir}")
            self.after(0, lambda: messagebox.showinfo("Terminé", f"La musique a été téléchargée.\n\nDossier : {out_dir}"))

        except Exception as e:
            msg = str(e)
            self.after(0, self._set_status, f"Erreur : {msg}", ERROR)
            self.after(0, self._log, "")
            self.after(0, self._log, f"ERREUR : {msg}")
            self.after(0, lambda: messagebox.showerror("Erreur", msg))
        finally:
            self.after(0, self._reset_ui)

    def _reset_ui(self):
        self._running = False
        self.dl_btn.config(state="normal", text="TÉLÉCHARGER EN MP3")

if __name__ == "__main__":
    App().mainloop()
