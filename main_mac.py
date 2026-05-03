import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import subprocess
import re

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

YT_DLP = resource_path("yt-dlp")
FFMPEG = resource_path("ffmpeg")

BG      = "#0f0f0f"
ACCENT  = "#ff4d00"
ACCENT2 = "#ff8c42"
TEXT    = "#f0ece4"
SUBTEXT = "#888880"
CARD    = "#1a1a1a"
BORDER  = "#2a2a2a"
SUCCESS = "#4caf50"
ERROR   = "#f44336"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎵 YouTube → MP3  |  Pour Papa")
        self.geometry("620x500")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.output_dir = tk.StringVar(value=os.path.expanduser("~/Music"))
        self.url_var    = tk.StringVar()
        self.status_var = tk.StringVar(value="Prêt.")
        self.progress   = tk.DoubleVar(value=0)
        self._running   = False

        self._build_ui()
        self._check_deps()

    def _build_ui(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=30, pady=(28, 0))

        tk.Label(header, text="🎵", font=("Helvetica", 32), bg=BG, fg=ACCENT).pack(side="left")
        title_frame = tk.Frame(header, bg=BG)
        title_frame.pack(side="left", padx=14)
        tk.Label(title_frame, text="YouTube → MP3", font=("Helvetica", 20, "bold"),
                 bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(title_frame, text="Meilleure qualité  •  320 kbps  •  Sans virus",
                 font=("Helvetica", 9), bg=BG, fg=SUBTEXT).pack(anchor="w")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30, pady=18)

        card = tk.Frame(self, bg=CARD, bd=0, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="x", padx=30)

        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="x", padx=22, pady=22)

        tk.Label(inner, text="Lien YouTube", font=("Helvetica", 10, "bold"),
                 bg=CARD, fg=SUBTEXT).grid(row=0, column=0, sticky="w", pady=(0, 4))

        url_frame = tk.Frame(inner, bg=BORDER)
        url_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        inner.columnconfigure(0, weight=1)

        self.url_entry = tk.Entry(url_frame, textvariable=self.url_var,
                                  font=("Courier", 11), bg="#111", fg=TEXT,
                                  insertbackground=ACCENT, relief="flat",
                                  bd=10, width=55)
        self.url_entry.pack(fill="x")

        tk.Label(inner, text="Dossier de destination", font=("Helvetica", 10, "bold"),
                 bg=CARD, fg=SUBTEXT).grid(row=2, column=0, sticky="w", pady=(0, 4))

        dir_row = tk.Frame(inner, bg=CARD)
        dir_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        dir_row.columnconfigure(0, weight=1)

        dir_frame = tk.Frame(dir_row, bg=BORDER)
        dir_frame.grid(row=0, column=0, sticky="ew")

        tk.Label(dir_frame, textvariable=self.output_dir,
                 font=("Helvetica", 9), bg="#111", fg=TEXT,
                 anchor="w", padx=10, pady=8, width=40).pack(side="left", fill="x", expand=True)

        tk.Button(dir_row, text="Choisir…", command=self._browse,
                  font=("Helvetica", 9, "bold"), bg=BORDER, fg=TEXT,
                  activebackground=ACCENT, activeforeground="white",
                  relief="flat", padx=14, pady=8, cursor="hand2",
                  bd=0).grid(row=0, column=1, padx=(8, 0))

        self.dl_btn = tk.Button(inner, text="⬇  TÉLÉCHARGER EN MP3",
                                 command=self._start_download,
                                 font=("Helvetica", 12, "bold"),
                                 bg=ACCENT, fg="white",
                                 activebackground=ACCENT2, activeforeground="white",
                                 relief="flat", pady=14, cursor="hand2", bd=0)
        self.dl_btn.grid(row=4, column=0, columnspan=2, sticky="ew")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30, pady=18)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("fire.Horizontal.TProgressbar",
                         troughcolor=CARD, background=ACCENT,
                         lightcolor=ACCENT2, darkcolor=ACCENT,
                         bordercolor=BORDER, thickness=8)

        self.pbar = ttk.Progressbar(self, style="fire.Horizontal.TProgressbar",
                                     variable=self.progress, maximum=100)
        self.pbar.pack(fill="x", padx=30)

        self.status_lbl = tk.Label(self, textvariable=self.status_var,
                                    font=("Helvetica", 9), bg=BG, fg=SUBTEXT, anchor="w")
        self.status_lbl.pack(fill="x", padx=32, pady=(6, 0))

        log_frame = tk.Frame(self, bg=CARD, highlightthickness=1,
                              highlightbackground=BORDER)
        log_frame.pack(fill="both", expand=True, padx=30, pady=(10, 24))

        self.log = tk.Text(log_frame, height=6, font=("Courier", 8),
                            bg="#0a0a0a", fg=SUBTEXT, relief="flat",
                            bd=8, state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True)

    def _log(self, msg):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _set_status(self, msg, color=SUBTEXT):
        self.status_var.set(msg)
        self.status_lbl.config(fg=color)

    def _browse(self):
        folder = filedialog.askdirectory(title="Choisir le dossier de destination",
                                          initialdir=self.output_dir.get())
        if folder:
            self.output_dir.set(folder)

    def _check_deps(self):
        missing = []
        if not os.path.exists(YT_DLP):
            missing.append("yt-dlp")
        if not os.path.exists(FFMPEG):
            missing.append("ffmpeg")
        if missing:
            messagebox.showerror("Dépendances manquantes",
                                  f"Fichiers manquants : {', '.join(missing)}")
            self._set_status("⚠  Fichiers manquants.", ERROR)

    def _start_download(self):
        if self._running:
            return
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("URL manquante", "Colle un lien YouTube dans le champ!")
            return
        if "youtube.com" not in url and "youtu.be" not in url:
            if not messagebox.askyesno("URL inhabituelle", "Le lien ne semble pas être YouTube. Continuer?"):
                return

        out_dir = self.output_dir.get()
        os.makedirs(out_dir, exist_ok=True)

        self._running = True
        self.dl_btn.config(state="disabled", text="⏳  Téléchargement en cours…")
        self.progress.set(0)
        self._set_status("Démarrage…")

        threading.Thread(target=self._download_worker, args=(url, out_dir), daemon=True).start()

    def _download_worker(self, url, out_dir):
        try:
            self._log(f"▶ URL : {url}")
            self._log(f"▶ Dossier : {out_dir}")
            self._log("─" * 50)

            # S'assurer que les binaires sont executables
            for binary in [YT_DLP, FFMPEG]:
                if os.path.exists(binary):
                    os.chmod(binary, 0o755)

            cmd = [
                YT_DLP,
                "--ffmpeg-location", os.path.dirname(FFMPEG),
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
                    self.after(0, self._set_status, "Conversion en MP3…", ACCENT2)
                    self.after(0, self.progress.set, 95)

            proc.wait()

            if proc.returncode == 0:
                self.after(0, self.progress.set, 100)
                self.after(0, self._set_status, "✅  Téléchargement terminé!", SUCCESS)
                self.after(0, self._log, f"\n✅  MP3 sauvegardé dans : {out_dir}")
                self.after(0, lambda: messagebox.showinfo("Terminé! 🎵",
                    f"La musique a été téléchargée!\n\nDossier : {out_dir}"))
            else:
                raise RuntimeError(f"yt-dlp a retourné le code {proc.returncode}")

        except Exception as e:
            self.after(0, self._set_status, f"❌  Erreur : {e}", ERROR)
            self.after(0, self._log, f"\n❌  ERREUR : {e}")
            self.after(0, lambda: messagebox.showerror("Erreur", str(e)))
        finally:
            self.after(0, self._reset_ui)

    def _reset_ui(self):
        self._running = False
        self.dl_btn.config(state="normal", text="⬇  TÉLÉCHARGER EN MP3")


if __name__ == "__main__":
    app = App()
    app.mainloop()
