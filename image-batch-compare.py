import os
import math
import random
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import sys

class SimultaneousComparisonTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Multi-Folder Image Comparison")
        self.root.geometry("1280x720")
        
        # Get screen resolution
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # Calculate base font size
        self.base_font_size = min(self.screen_width // 100, self.screen_height // 100)
        
        # Set initial DPI awareness
        self.set_dpi_awareness(True)
        
        self.folders = []
        self.folder_images = {}
        self.current_images = []
        self.votes = {}
        self.current_index = 0
        self.resize_timer = None
        self.current_image_set = []
        
        self.setup_ui()

    def set_dpi_awareness(self, aware):
        if sys.platform.startswith('win'):
            try:
                import ctypes
                if aware:
                    ctypes.windll.shcore.SetProcessDpiAwareness(1)
                else:
                    ctypes.windll.shcore.SetProcessDpiAwareness(0)
            except:
                pass
        elif sys.platform.startswith('linux'):
            # For Linux, we can adjust the scaling factor of the root window
            scale = self.root.winfo_fpixels('1i') / 72.0 if aware else 1.0
            self.root.tk.call('tk', 'scaling', scale)

    def get_font_size(self, size_factor):
        return int(self.base_font_size * size_factor * 4)

    def setup_ui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        self.control_frame.columnconfigure(1, weight=1)

        # Configure button style
        button_style = ttk.Style()
        button_style.configure('Large.TButton', padding=(self.get_font_size(1.0), self.get_font_size(1.0)), font=('Helvetica', self.get_font_size(1)))

        ttk.Button(self.control_frame, text="Add Folder", command=self.add_folder, style='Large.TButton').grid(row=0, column=0, padx=10, pady=10)
        ttk.Button(self.control_frame, text="Remove Folder", command=self.remove_folder, style='Large.TButton').grid(row=0, column=1, padx=10, pady=10)
        self.start_button = ttk.Button(self.control_frame, text="Start Comparison", command=self.start_comparison, style='Large.TButton')
        self.start_button.grid(row=0, column=2, padx=10, pady=10)

        self.tree_frame = ttk.Frame(self.main_frame)
        self.tree_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        # Configure Treeview style
        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', self.get_font_size(0.8)))
        style.configure("Treeview.Heading", font=('Helvetica', self.get_font_size(0.9), "bold"))

        self.folder_tree = ttk.Treeview(self.tree_frame, columns=("path",), show="headings")
        self.folder_tree.heading("path", text="Folder Paths")
        self.folder_tree.column("path", anchor="w")
        self.folder_tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.folder_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.folder_tree.configure(yscrollcommand=scrollbar.set)

        self.image_frame = ttk.Frame(self.root)
        self.image_frame.grid(row=0, column=0, sticky="nsew")
        self.image_frame.grid_remove()

        self.canvas = tk.Canvas(self.image_frame)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.root.bind("<Configure>", self.on_window_resize)
        self.root.bind("<Escape>", lambda e: self.stop_comparison())

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder and folder not in self.folders:
            self.folders.append(folder)
            self.votes[folder] = 0
            
            images = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            self.folder_images[folder] = sorted(images, key=lambda x: os.path.getmtime(os.path.join(folder, x)))

            self.folder_tree.insert("", "end", values=(folder,))

    def remove_folder(self):
        selected_item = self.folder_tree.selection()
        if selected_item:
            folder = self.folder_tree.item(selected_item)['values'][0]
            if folder in self.folders:
                self.folders.remove(folder)
                del self.votes[folder]
                del self.folder_images[folder]
                self.folder_tree.delete(selected_item)

    def start_comparison(self):
        if len(self.folders) < 2:
            messagebox.showwarning("Warning", "Please add at least two folders for comparison.")
            return
        
        # Disable DPI awareness when starting comparison
        self.set_dpi_awareness(False)
        
        self.main_frame.grid_remove()
        self.image_frame.grid()
        self.current_index = 0
        self.load_next_image_set()
        self.display_current_set()

    def stop_comparison(self):
        # Re-enable DPI awareness when stopping comparison
        self.set_dpi_awareness(True)
        
        self.image_frame.grid_remove()
        self.main_frame.grid()
        self.current_index = 0
        self.votes = {folder: 0 for folder in self.folders}
        self.current_image_set = []

    def load_next_image_set(self):
        if not self.folder_images:  # Check if there are any folders with images
            self.show_results()
            return

        max_images = max(len(images) for images in self.folder_images.values())
        if self.current_index >= max_images:
            self.show_results()
            return

        self.current_image_set = []
        random_folders = random.sample(self.folders, len(self.folders))

        for folder in random_folders:
            if self.current_index < len(self.folder_images[folder]):
                image_name = self.folder_images[folder][self.current_index]
                image_path = os.path.join(folder, image_name)
                self.current_image_set.append((folder, image_path))
            else:
                self.current_image_set.append((folder, None))

        if not any(image_path for _, image_path in self.current_image_set):
            self.show_results()  # If no valid images in this set, show results

    def display_current_set(self):
        self.canvas.delete("all")
        self.current_images = []

        window_width = self.canvas.winfo_width()
        window_height = self.canvas.winfo_height()
        num_images = len(self.current_image_set)
        
        if num_images == 0:
            # Display a message when there are no images
            self.canvas.create_text(window_width // 2, window_height // 2,
                                    text="No images to display", anchor=tk.CENTER,
                                    font=('Helvetica', self.get_font_size(1)))
            return

        cols = min(3, num_images)  # Maximum of 3 columns
        rows = math.ceil(num_images / cols)
        
        cell_width = window_width // cols
        cell_height = window_height // rows

        for i, (folder, image_path) in enumerate(self.current_image_set):
            row = i // cols
            col = i % cols
            
            if image_path:
                try:
                    with Image.open(image_path) as pil_img:
                        if pil_img.mode != 'RGB':
                            pil_img = pil_img.convert('RGB')
                        
                        img_width, img_height = pil_img.size
                        aspect_ratio = img_width / img_height

                        if aspect_ratio > cell_width / cell_height:
                            new_width = cell_width
                            new_height = int(cell_width / aspect_ratio)
                        else:
                            new_height = cell_height
                            new_width = int(cell_height * aspect_ratio)

                        pil_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
                        
                        img = ImageTk.PhotoImage(pil_img)
                        x = col * cell_width + (cell_width - new_width) // 2
                        y = row * cell_height + (cell_height - new_height) // 2
                        image_item = self.canvas.create_image(x, y, anchor=tk.NW, image=img)
                        self.canvas.tag_bind(image_item, "<Button-1>", lambda e, f=folder: self.vote(f))
                        self.current_images.append((img, image_item))
                except Exception as e:
                    print(f"Error loading image {image_path}: {e}")
                    self.canvas.create_text(col * cell_width + cell_width // 2, 
                                            row * cell_height + cell_height // 2,
                                            text="Error loading image", anchor=tk.CENTER,
                                            font=('Helvetica', self.get_font_size(0.8)))
            else:
                self.canvas.create_text(col * cell_width + cell_width // 2, 
                                        row * cell_height + cell_height // 2,
                                        text="No image", anchor=tk.CENTER,
                                        font=('Helvetica', self.get_font_size(0.8)))

        self.root.update_idletasks()

    def on_window_resize(self, event):
        if self.resize_timer is not None:
            self.root.after_cancel(self.resize_timer)
        self.resize_timer = self.root.after(200, self.display_current_set)

    def vote(self, chosen_folder):
        self.votes[chosen_folder] += 1
        self.current_index += 1
        self.load_next_image_set()
        self.display_current_set()

    def show_results(self):
        result = "Results:\n"
        for folder, votes in self.votes.items():
            result += f"{os.path.basename(folder)}: {votes} votes\n"
        messagebox.showinfo("Comparison Complete", result)
        self.stop_comparison()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    tool = SimultaneousComparisonTool()
    tool.run()
