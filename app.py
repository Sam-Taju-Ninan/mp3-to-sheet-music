# MP3 TO SHEET MUSIC - Desktop Launcher
# A simple window with a Browse button to pick an MP3, instead of editing the
# file path in code every time. Save this in the SAME FOLDER as your pipeline script.
#
# >>> ONE THING TO CHECK: the line marked [EDIT THIS] below must match your
#     pipeline file's name (without the .py).

import sys
import queue
import threading
import traceback
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, ttk

# ----------------------------------------------------------------------------
# [EDIT THIS] Import your pipeline functions.
# If your script is called "mp3_to_sheet.py", leave this as mp3_to_sheet.
# If it's called something else (e.g. main.py), change the name here.
# ----------------------------------------------------------------------------
import mp3_to_sheet as pipeline   # <-- change "mp3_to_sheet" to your file's name


# ----------------------------------------------------------------------------
# The pipeline, factored out of main() so it can take any MP3 path + options.
# This mirrors your main() exactly, just parameterised.
# ----------------------------------------------------------------------------
def run_pipeline(mp3_path: str, keep_vocals: bool):
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    print("\nSeparating stems...")
    clean_audio = pipeline.separate_stems(mp3_path, output_dir, keep_vocals=keep_vocals)

    print("\nTranscribing to MIDI...")
    midi_path = pipeline.transcribe_to_midi(clean_audio, output_dir)

    print("\nRemoving harmonics...")
    midi_path = pipeline.remove_harmonics(midi_path, output_dir)

    print("\nQuantizing to beats...")
    midi_path = pipeline.quantize_to_beats(midi_path, clean_audio, output_dir)

    print("\nGenerating score...")
    score = pipeline.generate_score(midi_path, output_dir)

    print("\nAnalyzing score with LLM...")
    feedback = pipeline.analyze_score_with_llm(score)
    print("\n=== LLM Music Analysis ===")
    print(feedback)

    print("\nCorrecting score with LLM...")
    score = pipeline.correct_score_with_llm(score, feedback)

    print("\nExtracting properties...")
    pipeline.extract_properties(score, mp3_path)

    print("\n[DONE] Sheet music generated and opened in MuseScore 4.")


# ----------------------------------------------------------------------------
# A tiny object that makes print() write into the on-screen log instead of a
# terminal (so it works even when you double-click the app with no console).
# ----------------------------------------------------------------------------
class QueueWriter:
    def __init__(self, q):
        self.q = q

    def write(self, text):
        if text:
            self.q.put(text)

    def flush(self):
        pass


class App:
    def __init__(self, root):
        self.root = root
        root.title("MP3 to Sheet Music")
        root.geometry("640x460")
        root.configure(padx=16, pady=16)

        self.mp3_path = None
        self.log_queue = queue.Queue()
        self.running = False

        # --- File picker row ---
        top = tk.Frame(root)
        top.pack(fill="x")

        self.file_label = tk.Label(top, text="No file selected",
                                   anchor="w", fg="#555")
        self.file_label.pack(side="left", fill="x", expand=True)

        tk.Button(top, text="Browse…", command=self.browse).pack(side="right")

        # --- Options row ---
        opts = tk.Frame(root)
        opts.pack(fill="x", pady=(10, 0))

        self.keep_vocals = tk.BooleanVar(value=False)
        tk.Checkbutton(opts, text="Keep vocals (melody line) instead of instrumental",
                       variable=self.keep_vocals).pack(side="left")

        # --- Run button ---
        self.run_btn = tk.Button(root, text="Generate Sheet Music",
                                 command=self.start, state="disabled",
                                 height=2)
        self.run_btn.pack(fill="x", pady=12)

        # --- Progress bar (indeterminate: just shows it's working) ---
        self.progress = ttk.Progressbar(root, mode="indeterminate")
        self.progress.pack(fill="x")

        # --- Log output ---
        self.log = tk.Text(root, height=14, wrap="word", bg="#1e1e1e",
                           fg="#d4d4d4", insertbackground="#d4d4d4")
        self.log.pack(fill="both", expand=True, pady=(12, 0))
        self.log.insert("end", "Pick an MP3 with Browse, then click Generate.\n")
        self.log.configure(state="disabled")

        # Poll the log queue so background-thread prints appear in the window.
        self.root.after(100, self.drain_log)

    def browse(self):
        path = filedialog.askopenfilename(
            title="Choose an MP3 file",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")],
        )
        if path:
            self.mp3_path = path
            self.file_label.config(text=Path(path).name, fg="#000")
            self.run_btn.config(state="normal")

    def start(self):
        if self.running or not self.mp3_path:
            return
        self.running = True
        self.run_btn.config(state="disabled")
        self.progress.start(12)
        self._append(f"\n=== Processing: {Path(self.mp3_path).name} ===\n")

        # Run the heavy pipeline on a background thread so the window stays responsive.
        t = threading.Thread(target=self._worker, daemon=True)
        t.start()

    def _worker(self):
        # Send this thread's print() output into the GUI log.
        old_stdout = sys.stdout
        sys.stdout = QueueWriter(self.log_queue)
        try:
            run_pipeline(self.mp3_path, self.keep_vocals.get())
        except Exception:
            self.log_queue.put("\n[ERROR] Something failed:\n")
            self.log_queue.put(traceback.format_exc())
        finally:
            sys.stdout = old_stdout
            self.log_queue.put("__DONE__")

    def drain_log(self):
        try:
            while True:
                item = self.log_queue.get_nowait()
                if item == "__DONE__":
                    self.running = False
                    self.progress.stop()
                    self.run_btn.config(state="normal")
                else:
                    self._append(item)
        except queue.Empty:
            pass
        self.root.after(100, self.drain_log)

    def _append(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
