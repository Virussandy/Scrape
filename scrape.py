import os
import json
import getpass
from datetime import datetime
from flask import Flask, request, jsonify
import pyautogui
import threading
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import re
from urllib.parse import urlparse
from flask_cors import CORS
from PIL import Image
from PIL import ImageGrab  # Import ImageGrab from PIL (Pillow)

# Config file to store last selected folder
CONFIG_FILE = "config.json"
app = Flask(__name__)
CORS(app, supports_credentials=True)


def get_downloads_directory():
    """Returns the Downloads directory path for the current user."""
    user_name = getpass.getuser()
    return os.path.join(f"C:\\Users\\{user_name}", "Downloads")

def load_last_folder():
    """Loads the last selected folder from config.json, or resets to Downloads if missing."""
    default_path = get_downloads_directory()

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as file:
                data = json.load(file)
                saved_path = data.get("folder_path", default_path)
                
                # Check if saved folder exists
                if os.path.exists(saved_path):
                    return saved_path
                else:
                    messagebox.showwarning("Warning", "Selected folder not found! Falling back to Downloads.")
        except json.JSONDecodeError:
            pass  # If file is corrupted, reset to default

    return default_path  # Default to Downloads if missing or corrupted

def save_last_folder(folder_path):
    """Saves the last selected folder to config.json."""
    with open(CONFIG_FILE, "w") as file:
        json.dump({"folder_path": folder_path}, file)

# Load the last saved folder (or default)
custom_folder_path = load_last_folder()
auto_folder_mode = True  # Default: Auto mode
current_folder = datetime.now().strftime("%d.%m.%Y")  # Default folder for auto mode

# Flask App
app = Flask(__name__)

def sanitize_url(url):
    """Transforms the URL into a valid filename with dots instead of special characters."""
    parsed_url = urlparse(url)

    # Remove 'www.' if present and capitalize the first letter
    domain = parsed_url.netloc.replace("www.", "").capitalize()

    # Replace special characters with dots
    path = parsed_url.path.replace("/", ".").strip(".")
    query = parsed_url.query.replace("=", ".").replace("&", ".").replace("-", ".").strip(".").replace("_",".")

    # Merge domain, path, and query
    sanitized_filename = f"{domain}.{path}.{query}"

    # Remove multiple consecutive dots
    sanitized_filename = re.sub(r'\.+', '.', sanitized_filename).strip('.')

    return sanitized_filename

@app.route('/capture', methods=['POST'])
def capture_screen():
    """Handles screenshot requests and saves them with URL-based naming."""
    global current_folder

    if auto_folder_mode:
        current_folder = datetime.now().strftime("%d.%m.%Y")

    folder_path = os.path.join(custom_folder_path, current_folder)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Ignore browser-sent images, always take a fresh full-screen screenshot
    url = request.form.get("url", "unknown") if "multipart/form-data" in request.content_type else request.json.get("url", "unknown")

    # Generate filename
    timestamp = datetime.now().strftime("%H.%M.%S.%d.%B.%Y")
    filename = f"{sanitize_url(url)}.{timestamp}.png"
    filepath = os.path.join(folder_path, filename)

    # 🔥 Force full-screen screenshot using PIL.ImageGrab instead of pyautogui
    try:
        screenshot = ImageGrab.grab(all_screens=True)
        screenshot.save(filepath)
    except Exception as e:
        print(f"Error capturing full screen: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

    response = jsonify({"success": True, "filepath": filepath, "url": url})
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response




# --------------------- GUI Setup --------------------- #

def toggle_mode():
    """Switch between Auto and Manual mode"""
    global auto_folder_mode, current_folder
    auto_folder_mode = mode_var.get()

    if auto_folder_mode:
        current_folder = datetime.now().strftime("%d.%m.%Y")  # Reset to today's date
        
        # Enable, clear, and disable the entry field to reset it properly
        folder_name_entry.config(state=tk.NORMAL)
        folder_name_entry.delete(0, tk.END)  # Clear the folder name entry
        folder_name_entry.config(state=tk.DISABLED)
    else:
        folder_name_entry.config(state=tk.NORMAL)  # Enable manual entry

    update_status()



def create_manual_folder():
    """Set a manually created folder"""
    global current_folder
    if auto_folder_mode:
        messagebox.showwarning("Warning", "Auto mode is ON! Disable it to create a custom folder.")
        return
    
    folder_name = folder_name_entry.get().strip()
    if not folder_name:
        messagebox.showerror("Error", "Please enter a folder name.")
        return

    folder_name = sanitize_url(folder_name)
    current_folder = folder_name
    folder_path = os.path.join(custom_folder_path, current_folder)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    update_status()
    messagebox.showinfo("Success", f"Folder '{folder_name}' created successfully.")

def capture_full_screen():
    """Captures a full-screen screenshot including multiple monitors."""
    try:
        # Capture the full screen (including multi-monitor setups)
        screenshot = pyautogui.screenshot()

        # Convert to PIL Image to improve efficiency
        return screenshot
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None


def select_folder():
    """Open a dialog to select a custom folder and save it persistently."""
    global custom_folder_path
    folder_path = filedialog.askdirectory(initialdir=custom_folder_path)  # Open the folder dialog

    if folder_path:
        custom_folder_path = folder_path
        save_last_folder(custom_folder_path)  # Save the folder path persistently
        update_status()

def update_status():
    """Update the status label with the current folder"""
    status_label.config(text=f"Current Folder: {custom_folder_path} - {current_folder}")

def run_flask():
    """Runs the Flask server in a separate thread"""
    app.run(port=5000, debug=True, use_reloader=False)

# Start Flask Server in a Thread
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# --------------------- Tkinter GUI --------------------- #

# Initialize the main window
root = tk.Tk()
root.title("📸 Scrape - Screenshot Saver")
root.geometry("500x500")  # Initial size
root.minsize(500, 500)  # Prevents UI from breaking at very small sizes
root.configure(bg="#1E1E1E")  # Dark background for a modern look

# Configure grid to allow responsiveness but keep things aligned
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Apply style for modern look
style = ttk.Style()
style.configure("TButton", font=("Arial", 11, "bold"), padding=10, relief="flat", background="#7289DA", foreground="white")
style.configure("TLabel", font=("Arial", 11), background="#1E1E1E", foreground="white")
style.configure("TEntry", font=("Arial", 11), fieldbackground="#FFFFFF", foreground="black", padding=5)

# Frame for main layout, centered within the window
main_frame = tk.Frame(root, bg="#1E1E1E", padx=20, pady=20)
main_frame.place(relx=0.5, rely=0.5, anchor="center")  # Keeps everything centered

# Title Label
title_label = tk.Label(main_frame, text="📸 Scrape", font=("Arial", 20, "bold"), fg="#FFD700", bg="#1E1E1E")
title_label.pack(pady=10)

# Mode Toggle
mode_var = tk.BooleanVar(value=True)
mode_frame = tk.Frame(main_frame, bg="#1E1E1E")
mode_frame.pack(pady=5)

tk.Label(mode_frame, text="📂 Folder Mode:", font=("Arial", 11, "bold"), bg="#1E1E1E", fg="#FFD700").pack(side=tk.LEFT, padx=5)
ttk.Radiobutton(mode_frame, text="Auto (Date-Based)", variable=mode_var, value=True, command=lambda: toggle_mode()).pack(side=tk.LEFT, padx=5)
ttk.Radiobutton(mode_frame, text="Manual", variable=mode_var, value=False, command=lambda: toggle_mode()).pack(side=tk.LEFT, padx=5)

# Folder Name Entry (Manual Mode) with Correct Text Visibility
folder_name_entry = ttk.Entry(main_frame, width=40, state=tk.DISABLED, font=("Arial", 12), foreground="black")
folder_name_entry.pack(pady=12, ipady=5)

# Create Folder Button with Hover Effect
def on_enter(e):
    create_folder_button.config(bg="#4CAF50", fg="white")

def on_leave(e):
    create_folder_button.config(bg="#7289DA", fg="white")

create_folder_button = tk.Button(main_frame, text="📂 Create Folder", command=lambda: create_manual_folder(),
                                 font=("Arial", 12, "bold"), bg="#7289DA", fg="white", relief="flat",
                                 activebackground="#4CAF50", activeforeground="white", bd=2, cursor="hand2",
                                 width=30)  # Keeps button size stable
create_folder_button.pack(pady=10)

create_folder_button.bind("<Enter>", on_enter)
create_folder_button.bind("<Leave>", on_leave)

# Select Custom Folder Button
def on_enter_folder(e):
    select_folder_button.config(bg="#FF5733", fg="white")

def on_leave_folder(e):
    select_folder_button.config(bg="#7289DA", fg="white")

select_folder_button = tk.Button(main_frame, text="📁 Select Folder", command=lambda: select_folder(),
                                 font=("Arial", 12, "bold"), bg="#7289DA", fg="white", relief="flat",
                                 activebackground="#FF5733", activeforeground="white", bd=2, cursor="hand2",
                                 width=30)  # Keeps button size stable
select_folder_button.pack(pady=10)

select_folder_button.bind("<Enter>", on_enter_folder)
select_folder_button.bind("<Leave>", on_leave_folder)

# Status Label
status_label = tk.Label(main_frame, text=f"📁 Current Folder: {custom_folder_path}",
                        font=("Arial", 10, "italic"), fg="#FFD700", bg="#1E1E1E")
status_label.pack(pady=15)

# Shortcut Label
shortcut_label_chrome = tk.Label(main_frame, text="⌨️ CHROME : Press Ctrl+Shift+X to take a Screenshot",
                          font=("Arial", 10, "italic"), fg="#99AAB5", bg="#1E1E1E")
shortcut_label_chrome.pack(pady=10)

# Shortcut Label
shortcut_label_firefox = tk.Label(main_frame, text="⌨️ Firefox : Press Ctrl+Shift+Peroid to take a Screenshot",
                          font=("Arial", 10, "italic"), fg="#99AAB5", bg="#1E1E1E")
shortcut_label_firefox.pack(pady=10)

# Run the GUI
root.mainloop()
