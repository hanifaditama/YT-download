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
    try:
        if is_yt_dlp_installed():
            subprocess.run(["yt-dlp", "-U"], check=True)
        else:
            subprocess.run([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"], check=True)
    except subprocess.CalledProcessError:
        print("Failed to install or update yt-dlp.")


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


def hms_string(hour, minute, second):
    return f"{int(hour):02}:{int(minute):02}:{int(second):02}"


def download_videos(links, start_hms, end_hms, quality_code, format_type, output_path, on_progress_update, on_finish):
    section = f"*{start_hms}-{end_hms}" if start_hms and end_hms else ""
    output_template = os.path.join(output_path, "%(title).70s.%(ext)s")

    for url in links:
        cmd = [
            "yt-dlp",
            url,
            "-f", quality_code,
            "-o", output_template,
            "--merge-output-format", "mp4",
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

        start_time = hms_string(start_hour.get(), start_min.get(), start_sec.get())
        end_time = hms_string(end_hour.get(), end_min.get(), end_sec.get())
        quality_code = quality_map[quality_var.get()]

        def update_progress(p):
            progress_bar["value"] = p
            root.update_idletasks()

        def download_complete():
            messagebox.showinfo("Done", "All downloads completed!")
            download_btn.config(state="normal")
            progress_bar["value"] = 0

        threading.Thread(
            target=download_videos,
            args=(urls, start_time, end_time, quality_code, format_var.get(), output_var.get(), update_progress, download_complete),
            daemon=True
        ).start()

    root = tk.Tk()
    root.title("YouTube Downloader")
    root.geometry("600x700")
    root.resizable(False, False)

    tk.Label(root, text="YouTube Links (one per line):").pack(pady=(10, 0))
    links_text = scrolledtext.ScrolledText(root, width=70, height=8)
    links_text.pack()

    def time_input_frame(label_text):
        frame = tk.Frame(root)
        tk.Label(frame, text=label_text).pack()
        hour = tk.Spinbox(frame, from_=0, to=23, width=5)
        minute = tk.Spinbox(frame, from_=0, to=59, width=5)
        second = tk.Spinbox(frame, from_=0, to=59, width=5)
        hour.pack(side="left", padx=2)
        minute.pack(side="left", padx=2)
        second.pack(side="left", padx=2)
        frame.pack(pady=5)
        return hour, minute, second

    start_hour, start_min, start_sec = time_input_frame("Start Time (HH:MM:SS)")
    end_hour, end_min, end_sec = time_input_frame("End Time (HH:MM:SS)")

    tk.Label(root, text="Video Quality:").pack(pady=(10, 0))
    quality_var = tk.StringVar(value="Best Quality")
    quality_map = {
        "Best Quality": "bestvideo+bestaudio",
        "1440p (2K)": "137+bestaudio",
        "1080p (HD)": "22+bestaudio",
        "720p (HD)": "18",
        "480p": "135",
        "360p": "134",
        "240p": "133"
    }
    Combobox(root, textvariable=quality_var, values=list(quality_map.keys())).pack()

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
