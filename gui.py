import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
from poster_engine import process_poster_csv


HOT_FOLDER = "C:/Users/DTFPrintBar/AppData/Local/PosterEngine/HotFolder/"
APP_DIR = "C:/Users/DTFPrintBar/AppData/Local/PosterEngine/"

os.makedirs(HOT_FOLDER, exist_ok=True)


def start_app():
    ### ROOT WINDOW SETTINGS
    root = tk.Tk()
    root.title("TPB POSTER ENGINE")
    root.geometry("320x300")
    root.resizable(False, False)
    root.attributes("-topmost", True)
    
    ### BRANDING IMAGES
    tpb_img = ImageTk.PhotoImage(Image.open(APP_DIR + "TPB_logo_f0f0f0.png"))
    fr_img = ImageTk.PhotoImage(Image.open(APP_DIR + "posterEngineLogo_2.5cm.png"))

    ### STYLING SETTINGS
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("My.TButton", font=("Arial", 12, "bold"))
    style.configure("White.TFrame", background="#f0f0f0")

    ### MAIN WINDOW FRAME
    mainFrame = ttk.Frame(root)
    mainFrame.configure(style="White.TFrame", relief='ridge', borderwidth=1)
    mainFrame.pack(padx=5, pady=5, fill="both", expand=True)

    ## LABEL
    tk.Label(mainFrame, image=fr_img).pack(pady=3)
    tk.Label(mainFrame, image=tpb_img).pack()

    progress_label = ttk.Label(mainFrame, text="")
    progress_bar = ttk.Progressbar(mainFrame, mode="indeterminate", length=250)

    def update_progress(msg):
        root.after(0, lambda: progress_label.config(text=msg))

    def csvUpload_click():
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        upload_button.config(state="disabled")
        progress_label.pack(pady=5)
        progress_bar.pack(pady=5)
        progress_bar.start(10)

        def worker():
            try:
                process_poster_csv(file_path, HOT_FOLDER, update_progress)
            finally:
                root.after(0, lambda: (
                    upload_button.config(state="normal"),
                    progress_bar.stop(),
                    progress_bar.pack_forget(),
                    progress_label.config(text="Upload complete ✅")
                ))

        threading.Thread(target=worker, daemon=True).start()

    upload_button = ttk.Button(
        mainFrame,
        text="Upload .csv File",
        style="My.TButton",
        command=csvUpload_click
    )
    upload_button.pack(pady=5)

    root.mainloop()
