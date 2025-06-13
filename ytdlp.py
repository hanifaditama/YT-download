import subprocess
import sys
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter.ttk import Combobox, Progressbar
import os
import threading

def is_yt_dlp_installed():
    return shutil.which("yt-dlp") is not None

def install_or_update_yt_dlp():
    if is_yt_dlp_installed():
        try:
            subprocess.run(["yt-dlp", "-U"], check=True)
        except subprocess.CalledProcessError:
            print("Failed to update yt-dlp.")
    else:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"], check=True)
        except subprocess.CalledProcessError:
            print("yt-dlp installation failed.")

def run_yt_dlp_command(cmd, on_progress_update):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    for line in process.stdout:
        if "[download]" in line and "%" in line:
            try:
                percent_str = line.split('%')[0].split()[-1]
                percent = float(percent_str)
                on_progress_update(percent)
            except:
                continue
    process.wait()
    return process.returncode == 0

def download_videos(links, start_time, end_time, quality, format_type, output_path, on_progress_update, on_finish):
    section = f"*{start_time}-{end_time}" if start_time and end_time else ""
    output_template = os.path.join(output_path, "%(title).70s.%(ext)s")

    for url in links:
        cmd = [
            "yt-dlp",
            url,
            "-f", quality,
            "-o", output_template,
            "--no-overwrites"
        ]

        if format_type == "Audio":
            cmd += ["--extract-audio", "--audio-format", "mp3"]

        if section:
            cmd += ["--download-sections", section]

        success = run_yt_dlp_command(cmd, on_progress_update)
        if not success:
            messagebox.showerror("Download Error", f"Failed to download:\n{url}")

    on_finish()

def start_gui():
    def browse_output():
        path = filedialog.askdirectory()
        if path:
            output_var.set(path)

    def start_download_thread():
        urls = links_text.get("1.0", tk.END).strip().splitlines()
        if not urls or not output_var.get():
            messagebox.showwarning("Input Error", "Please provide links and a save location.")
            return

        progress_bar["value"] = 0
        download_btn.config(state="disabled")

        def update_progress(p):
            progress_bar["value"] = p
            root.update_idletasks()

        def download_complete():
            messagebox.showinfo("Done", "All downloads completed!")
            download_btn.config(state="normal")
            progress_bar["value"] = 0

        threading.Thread(
            target=download_videos,
            args=(urls, start_var.get(), end_var.get(), quality_var.get(),
                  format_var.get(), output_var.get(), update_progress, download_complete),
            daemon=True
        ).start()

    root = tk.Tk()
    root.title("YouTube Downloader")
    root.geometry("600x600")
    root.resizable(False, False)

    tk.Label(root, text="YouTube Links (one per line):").pack(pady=(10, 0))
    links_text = scrolledtext.ScrolledText(root, width=70, height=8)
    links_text.pack()

    tk.Label(root, text="Start Time (mm:ss):").pack(pady=(10, 0))
    start_var = tk.StringVar()
    tk.Entry(root, textvariable=start_var, width=20).pack()

    tk.Label(root, text="End Time (mm:ss):").pack()
    end_var = tk.StringVar()
    tk.Entry(root, textvariable=end_var, width=20).pack()

    tk.Label(root, text="Quality (e.g. best, 22, 18):").pack(pady=(10, 0))
    quality_var = tk.StringVar(value="best")
    Combobox(root, textvariable=quality_var, values=["best", "22", "18", "140"]).pack()

    tk.Label(root, text="Format:").pack(pady=(10, 0))
    format_var = tk.StringVar(value="Video")
    Combobox(root, textvariable=format_var, values=["Video", "Audio"]).pack()

    tk.Label(root, text="Save to Folder:").pack(pady=(10, 0))
    output_frame = tk.Frame(root)
    output_frame.pack(pady=(0, 5))
    output_var = tk.StringVar()
    tk.Entry(output_frame, textvariable=output_var, width=45).pack(side="left", padx=(0, 5))
    tk.Button(output_frame, text="Browse", command=browse_output).pack(side="left")

    progress_bar = Progressbar(root, length=400, mode="determinate")
    progress_bar.pack(pady=(10, 5))

    download_btn = tk.Button(root, text="Download", command=start_download_thread)
    download_btn.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    install_or_update_yt_dlp()
    start_gui()
