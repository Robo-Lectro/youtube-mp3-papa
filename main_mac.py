import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import subprocess
import re

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

YT_DLP = resource_path("yt-dlp")
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

        tk.Label(
            header,
            text="YouTube → MP3",
            font=("Helvetica", 22, "bold"),
            bg=BG,
            fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Audio MP3 320 kbps | Simple pour Papa",
            font=("Helvetica", 10),
            bg=BG,
            fg=SUBTEXT
        ).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30, pady=18)

        card = tk.Frame(self, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", padx=30)

        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="x", padx=22, pady=22)
        inner.columnconfigure(0, weight=1)

        tk.Label(
            inner,
            text="Lien YouTube",
            font=("Helvetica", 10, "bold"),
            bg=CARD,
            fg=SUBTEXT
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

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

        tk.Label(
            inner,
            text="Dossier de destination",
            font=("Helvetica", 10, "bold"),
            bg=CARD,
            fg=SUBTEXT
        ).grid(row=2, column=0, sticky="w", pady=(0, 4))

        dir_row = tk.Frame(inner, bg=CARD)
        dir_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        dir_row.columnconfigure(0, weight=1)

        self.dir_label = tk.Label(
            dir_row,
            textvariable=self.output_dir,
            font=("Helvetica", 9),
            bg="#111111",
            fg=TEXT,
            anchor="w",
            padx=10,
            pady=10
        )
        self.dir_label.grid(row=0, column=0, sticky="ew")

        self.choose_btn = tk.Button(
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
        )
        self.choose_btn.grid(row=0, column=1, padx=(10, 0))

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

        self.pbar = ttk.Progressbar(
            self,
            style="fire.Horizontal.TProgressbar",
            variable=self.progress,
            maximum=100
        )
        self.pbar.pack(fill="x", padx=30, pady=(18, 0))

        self.status_lbl = tk.Label(
            self,
            textvariable=self.status_var,
            font=("Helvetica", 9),
            bg=BG,
            fg=SUBTEXT,
            anchor="w"
        )
        self.status_lbl.pack(fill="x", padx=32, pady=(6, 0))

        log_frame = tk.Frame(self, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        log_frame.pack(fill="both", expand=True, padx=30, pady=(10, 24))

        self.log = tk.Text(
            log_frame,
            height=8,
            font=("Courier", 8),
            bg="#0a0a0a",
            fg=SUBTEXT,
            relief="flat",
            bd=8,
            state="disabled",
            wrap="word"
        )
        self.log.pack(fill="both", expand=True)

    def _add_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Coller", command=lambda: self.url_entry.event_generate("<<Paste>>"))
        self.context_menu.add_command(label="Copier", command=lambda: self.url_entry.event_generate("<<Copy>>"))
        self.context_menu.add_command(label="Couper", command=lambda: self.url_entry.event_generate("<<Cut>>"))

        self.url_entry.bind("<Button-2>", self._show_context_menu)
        self.url_entry.bind("<Button-3>", self._show_context_menu)
        self.url_entry.bind("<Control-v>", lambda e: self.url_entry.event_generate("<<Paste>>"))
        self.url_entry.bind("<Command-v>", lambda e: self.url_entry.event_generate("<<Paste>>"))

    def _show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def _log(self, msg):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _set_status(self, msg, color=SUBTEXT):
        self.status_var.set(msg)
        self.status_lbl.config(fg=color)

    def _browse(self):
        folder = filedialog.askdirectory(
            title="Choisir le dossier de destination",
            initialdir=self.output_dir.get()
        )
        if folder:
            self.output_dir.set(folder)

    def _check_deps(self):
        missing = []
        if not os.path.exists(YT_DLP):
            missing.append("yt-dlp")
        if not os.path.exists(FFMPEG):
            missing.append("ffmpeg")

        if missing:
            messagebox.showerror(
                "Dépendances manquantes",
                f"Fichiers manquants : {', '.join(missing)}"
            )
            self._set_status("Fichiers manquants.", ERROR)

    def _start_download(self):
        if self._running:
            return

        url = self.url_var.get().strip()

        if not url:
            messagebox.showwarning("URL manquante", "Colle un lien YouTube dans le champ.")
            return

        if "youtube.com" not in url and "youtu.be" not in url:
            if not messagebox.askyesno(
                "URL inhabituelle",
                "Le lien ne semble pas être YouTube. Continuer quand même?"
            ):
                return

        out_dir = self.output_dir.get()
        os.makedirs(out_dir, exist_ok=True)

        self._running = True
        self.dl_btn.config(state="disabled", text="TÉLÉCHARGEMENT EN COURS...")
        self.progress.set(0)
        self._set_status("Démarrage...")

        threading.Thread(target=self._download_worker, args=(url, out_dir), daemon=True).start()

    def _run_version_test(self, binary, args):
        try:
            result = subprocess.run(
                [binary] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10
            )
            return result.returncode, result.stdout.strip()
        except Exception as e:
            return -1, str(e)

    def _download_worker(self, url, out_dir):
        try:
            self.after(0, self._log, f"URL : {url}")
            self.after(0, self._log, f"Dossier : {out_dir}")
            self.after(0, self._log, "-" * 55)

            yt = YT_DLP
            ff = FFMPEG

            for binary in [yt, ff]:
                if os.path.exists(binary):
                    os.chmod(binary, 0o755)

            self.after(0, self._log, f"yt-dlp path : {yt}")
            self.after(0, self._log, f"ffmpeg path : {ff}")
            self.after(0, self._log, f"yt-dlp existe : {os.path.exists(yt)}")
            self.after(0, self._log, f"ffmpeg existe : {os.path.exists(ff)}")

            yt_code, yt_version = self._run_version_test(yt, ["--version"])
            ff_code, ff_version = self._run_version_test(ff, ["-version"])

            self.after(0, self._log, f"yt-dlp test code : {yt_code}")
            self.after(0, self._log, yt_version.splitlines()[0] if yt_version else "yt-dlp aucune sortie")

            self.after(0, self._log, f"ffmpeg test code : {ff_code}")
            self.after(0, self._log, ff_version.splitlines()[0] if ff_version else "ffmpeg aucune sortie")

            if yt_code != 0:
                raise RuntimeError("Erreur 255 possible : yt-dlp ne peut pas s'exécuter sur ce Mac.")

            if ff_code != 0:
                raise RuntimeError("Erreur 255 possible : ffmpeg ne peut pas s'exécuter sur ce Mac.")

            cmd = [
                yt,
                "--ffmpeg-location", os.path.dirname(ff),
                "--force-ipv4",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "--embed-thumbnail",
                "--add-metadata",
                "--no-playlist",
                "--newline",
                "-o", os.path.join(out_dir, "%(title)s.%(ext)s"),
                url
            ]

            self.after(0, self._log, "-" * 55)
            self.after(0, self._log, "Commande lancée.")
            self.after(0, self._set_status, "Téléchargement...")

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            for line in proc.stdout:
                line = line.rstrip()
                if not line:
                    continue

                self.after(0, self._log, line)

                m = re.search(r"\[download\]\s+([\d.]+)%", line)
                if m:
                    pct = float(m.group(1))
                    self.after(0, self.progress.set, pct)
                    self.after(0, self._set_status, f"Téléchargement : {pct:.1f}%")

                if "[ExtractAudio]" in line or "Destination" in line:
                    self.after(0, self._set_status, "Conversion en MP3...", ACCENT2)
                    self.after(0, self.progress.set, 95)

            proc.wait()

            if proc.returncode == 0:
                self.after(0, self.progress.set, 100)
                self.after(0, self._set_status, "Téléchargement terminé.", SUCCESS)
                self.after(0, self._log, f"MP3 sauvegardé dans : {out_dir}")
                self.after(0, lambda: messagebox.showinfo(
                    "Terminé",
                    f"La musique a été téléchargée.\n\nDossier : {out_dir}"
                ))
            elif proc.returncode == 255:
                raise RuntimeError(
                    "yt-dlp a retourné le code 255. "
                    "Cause probable sur Mac : ffmpeg/yt-dlp bloqué, non exécutable, "
                    "mauvaise architecture, ou app bloquée par macOS Gatekeeper."
                )
            else:
                raise RuntimeError(f"yt-dlp a retourné le code {proc.returncode}")

        except Exception as e:
            self.after(0, self._set_status, f"Erreur : {e}", ERROR)
            self.after(0, self._log, "")
            self.after(0, self._log, f"ERREUR : {e}")
            self.after(0, lambda: messagebox.showerror("Erreur", str(e)))
        finally:
            self.after(0, self._reset_ui)

    def _reset_ui(self):
        self._running = False
        self.dl_btn.config(state="normal", text="TÉLÉCHARGER EN MP3")

if __name__ == "__main__":
    app = App()
    app.mainloop()
