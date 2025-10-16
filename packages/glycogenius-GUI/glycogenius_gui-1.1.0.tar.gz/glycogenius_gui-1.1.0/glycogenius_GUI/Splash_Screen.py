from PIL import Image, ImageTk
from tkinter import messagebox
import tkinter as tk
import psutil
import os
import tempfile
import platform

class splash_screen(tk.Toplevel):
    def __init__(self, current_dir, icon_dir):
        super().__init__()
        
        self.current_dir = current_dir
        
        self.exec_check_folder = os.path.join(tempfile.gettempdir())
        
        # If GG is running, do nothing
        if self.gg_is_running():
            return
        
        # Create GG running flag file
        self.create_gg_run_temp_file()
        
        # Determine which path to save GG drawings to
        self.determine_gg_draw_path()
        
        # Hide and load the splash screen
        self.withdraw()
        self.iconphoto(False, ImageTk.PhotoImage(file=icon_dir))
        self.overrideredirect(True)
        self.resizable(False, False)
        self.attributes("-topmost", True)

        # Get the platform at which GG is running on to set whether splash logo can have transparent background
        curr_os = platform.system()
        if curr_os == "Windows":
            self.attributes("-transparentcolor", "white")
            
        self.grab_set()
        
        # Load the splash screen image
        self.splash_image = Image.open(os.path.join(self.current_dir, "Assets/splash.png"))
        splash_size = self.splash_image.size
        self.splash_image = self.splash_image.resize((int(splash_size[0]/1.5), int(splash_size[1]/1.5)))
        self.tk_splash = ImageTk.PhotoImage(self.splash_image)
        
        self.splash_screen_label = tk.Label(self, bg="white", image=self.tk_splash)
        self.splash_screen_label.pack(pady=0, padx=0)
        
        # Update and unhide the splash screen
        self.update_idletasks()
        self.deiconify()
        
        # Center the splash screen on the screen
        self.window_width = self.winfo_width()
        self.window_height = self.winfo_height()
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        self.x_position = (self.screen_width - self.window_width) // 2
        self.y_position = (self.screen_height - self.window_height) // 2
        self.geometry(f"{self.window_width}x{self.window_height}+{self.x_position}+{self.y_position}")

        # Update the GUI manually
        self.update()
        
    def get_gg_draw_path(self):
        # Return the gg_draw_glycans_path
        return self.gg_draw_glycans_path
    
    def gg_is_running(self):
        self.this_process_id = os.getpid()
        this_process = psutil.Process(self.this_process_id)
        self.this_process_ppid = this_process.ppid() # Parent ID
        if f"gg_{self.this_process_ppid}.txt" not in os.listdir(self.exec_check_folder):
            return False
        return True
        
    def create_gg_run_temp_file(self):
        with open(os.path.join(self.exec_check_folder, f"gg_{self.this_process_id}.txt"), 'w') as f:
            f.write("Glycogenius has run")
            f.close()
    
    def determine_gg_draw_path(self):
        # Check if GG folder is writeable
        try:
            self.gg_draw_glycans_path = os.path.join(self.current_dir, "Assets/glycans")
            os.makedirs(self.gg_draw_glycans_path, exist_ok=True)
            with open(os.path.join(self.gg_draw_glycans_path, f"test.txt"), 'w') as f:
                f.write("Glycogenius can access this folder")
                f.close()
            os.remove(os.path.join(self.gg_draw_glycans_path, f"test.txt"))
        except Exception:
            messagebox.showwarning("Warning", "No permission to access GlycoGenius folder to save glycans figures in. Using temporary folder instead. This may lead to the need of building the figures from scratch again in a future activation of GG Draw. GlycoGenius will still work as intended.")
            self.gg_draw_glycans_path = os.path.join(tempfile.gettempdir(), "glycans_gg")
            os.makedirs(self.gg_draw_glycans_path, exist_ok=True)