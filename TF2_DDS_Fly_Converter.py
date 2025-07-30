import sys
import os
import subprocess
import tkinter as tk
from tkinter import filedialog, BooleanVar
from PIL import Image  # pip install pillow or pillow-dds

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

TEXCONV_PATH = os.path.join(base_path, "texconv.exe")

TEXTURE_TYPES = {
    "_col": "BC1_UNORM_SRGB",
    "_spc": "BC1_UNORM_SRGB",
    "_ilm": "BC1_UNORM_SRGB",
    "_ao":  "BC1_UNORM_SRGB",
    "_cav": "BC1_UNORM_SRGB",
    "_gls": "BC4_UNORM",
    "_nml": "BC5_UNORM"
}

selected_files = {}
DND_AVAILABLE = False
DND_FILES = None
srgb_vars = {}

def has_alpha_transparency(img_path):
    try:
        img = Image.open(img_path)
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            alpha = img.convert("RGBA").split()[-1]
            if alpha.getextrema()[0] < 255:
                return True
        return False
    except Exception as e:
        print(f"Failed to check alpha for {img_path}: {e}")
        return False

def run_texconv(input_path, output_dir, format_code, extra_flags=None):
    args = [
        TEXCONV_PATH,
        "-f", format_code,
        "-o", output_dir,
        input_path
    ]
    if extra_flags:
        args.extend(extra_flags)
    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to convert {input_path}:\n{e}")

def update_go_button_visibility(go_button):
    if any(selected_files.values()):
        go_button.pack(pady=20)
    else:
        go_button.pack_forget()

def select_file(suffix, label, go_button):
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.dds")])
    if file_path:
        selected_files[suffix] = file_path
        label.config(text=os.path.basename(file_path))
        update_go_button_visibility(go_button)

def convert_images():
    for suffix, path in selected_files.items():
        if not path:
            continue

        ext = os.path.splitext(path)[1].lower()
        input_folder = os.path.dirname(path)
        output_folder = os.path.join(input_folder, "output")
        os.makedirs(output_folder, exist_ok=True)

        if ext == ".dds":
            # Use texconv to convert DDS to PNG
            try:
                args = [
                    TEXCONV_PATH,
                    "-ft", "PNG",  # output format type
                    "-o", output_folder,
                    path
                ]
                subprocess.run(args, check=True)
                print(f"Converted DDS to PNG: {os.path.basename(path)}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to convert DDS to PNG: {e}")
            continue  # skip DDS→DDS

        # Handle PNG/JPG inputs for DDS export
        format_code = TEXTURE_TYPES[suffix]
        extra_flags = []

        if format_code == "BC1_UNORM_SRGB":
            if suffix == "_col" and has_alpha_transparency(path):
                format_code = "BC3_UNORM_SRGB"
            if srgb_vars.get(suffix, None) and srgb_vars[suffix].get():
                extra_flags.append("-srgb")
            else:
                extra_flags.append("-nosrgb")

        run_texconv(path, output_folder, format_code, extra_flags)

    print("All selected images converted.")



def on_drop(event, suffix, label, go_button):
    raw = event.data.strip("{}")
    if not os.path.isfile(raw):
        return

    ext = os.path.splitext(raw)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".dds"):
        print(f"Unsupported file type dropped: {ext}")
        return

    selected_files[suffix] = raw
    label.config(text=os.path.basename(raw))
    update_go_button_visibility(go_button)

def enable_drag_and_drop(widget, suffix, label, go_button):
    if DND_AVAILABLE:
        widget.drop_target_register(DND_FILES)
        widget.dnd_bind("<<Drop>>", lambda e: on_drop(e, suffix, label, go_button))

def create_ui():
    global DND_AVAILABLE, DND_FILES, srgb_vars

    icon_path = os.path.join(base_path, "fly.ico")

    try:
        import tkinterdnd2 as tkdnd
        try:
            root = tkdnd.TkinterDnD.Tk()
            DND_AVAILABLE = True
            DND_FILES = tkdnd.DND_FILES
        except Exception as e:
            print("Failed to initialize tkinterdnd2 drag-and-drop root window:")
            print(e)
            root = tk.Tk()
            print("⚠ Drag-and-drop disabled. Install tkinterdnd2 with: pip install tkinterdnd2")
    except ImportError as e:
        print("tkinterdnd2 import failed:")
        print(e)
        root = tk.Tk()
        print("⚠ Drag-and-drop disabled. Install tkinterdnd2 with: pip install tkinterdnd2")

    root.title("TF2 DDS Converter")
    root.configure(bg="#2e2e2e")

    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)

    try:
        from PIL import ImageTk
        icon_img = Image.open(icon_path)
        icon_img_48 = icon_img.copy()
        icon_img_48.thumbnail((48, 48), Image.LANCZOS)
        icon_img_tk = ImageTk.PhotoImage(icon_img_48)
        icon_label = tk.Label(root, image=icon_img_tk, bg="#2e2e2e")
        icon_label.image = icon_img_tk
        icon_label.pack(pady=(25, 10))
    except Exception as e:
        print(f"Failed to load icon image: {e}")

    tk.Label(root, text="TF2 DDS Converter", font=("Helvetica", 20, "bold"),
             bg="#2e2e2e", fg="white").pack(pady=(0, 10))

    go_button = tk.Button(root, text="Go", command=convert_images,
                          bg="#4caf50", fg="white", font=("Helvetica", 14, "bold"))

    tk.Label(root, text="Made by StormShockMods", font=("Helvetica", 12, "italic", "bold"),
             bg="#2e2e2e", fg="white").pack(pady=(0, 20))

    for suffix in TEXTURE_TYPES:
        frame = tk.Frame(root, bg="#2e2e2e")
        frame.pack(pady=6, fill="x", padx=30)

        tk.Label(frame, text=suffix, width=6, anchor="w",
                 bg="#2e2e2e", fg="white", font=("Helvetica", 12)).pack(side="left")

        slot = tk.Label(frame, text="(drag or browse)", bg="#444", fg="white",
                        relief="sunken", width=30, anchor="w", padx=5)
        slot.pack(side="left", padx=5)

        browse_btn = tk.Button(frame, text="Browse",
                               command=lambda s=suffix, l=slot: select_file(s, l, go_button))
        browse_btn.pack(side="right")

        selected_files[suffix] = None

        enable_drag_and_drop(slot, suffix, slot, go_button)

        if TEXTURE_TYPES[suffix] == "BC1_UNORM_SRGB":
            var = BooleanVar(value=True)
            srgb_vars[suffix] = var
            cb = tk.Checkbutton(frame, text="Force sRGB", variable=var,
                                bg="#2e2e2e", fg="white", activebackground="#2e2e2e",
                                activeforeground="white", selectcolor="#2e2e2e",
                                font=("Helvetica", 10, "italic"))
            cb.pack(side="left", padx=10)

    update_go_button_visibility(go_button)
    root.mainloop()

if __name__ == "__main__":
    create_ui()
