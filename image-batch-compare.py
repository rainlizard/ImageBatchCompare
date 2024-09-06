import os
import math
import random
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

class SimultaneousComparisonTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Multi-Folder Image Comparison")
        self.root.geometry("800x600")
        self.folders = []
        self.folder_images = {}
        self.current_images = []
        self.votes = {}
        self.current_index = 0
        self.resize_timer = None
        self.current_image_set = []
        self.setup_ui()

    def setup_ui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.control_frame.columnconfigure(1, weight=1)

        ttk.Button(self.control_frame, text="Add Folder", command=self.add_folder).grid(row=0, column=0, padx=5)
        ttk.Button(self.control_frame, text="Remove Folder", command=self.remove_folder).grid(row=0, column=1, padx=5)
        self.start_button = ttk.Button(self.control_frame, text="Start Comparison", command=self.start_comparison)
        self.start_button.grid(row=0, column=2, padx=5)

        self.tree_frame = ttk.Frame(self.main_frame)
        self.tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

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
        self.main_frame.grid_remove()
        self.image_frame.grid()
        self.current_index = 0
        self.load_next_image_set()
        self.display_current_set()

    def stop_comparison(self):
        self.image_frame.grid_remove()
        self.main_frame.grid()
        self.current_index = 0
        self.votes = {folder: 0 for folder in self.folders}
        self.current_image_set = []

    def load_next_image_set(self):
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

    def display_current_set(self):
        self.canvas.delete("all")
        self.current_images = []

        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        max_grid_width = int(window_width * 0.8)
        num_images = len(self.current_image_set)
        
        # Add a safety check to prevent division by zero
        self.grid_size = max(1, math.ceil(math.sqrt(num_images)))
        
        rows = math.ceil(num_images / self.grid_size)
        cols = min(num_images, self.grid_size)
        cell_width = min(max_grid_width // cols, window_height // rows) if cols > 0 and rows > 0 else 0
        cell_height = window_height // rows if rows > 0 else 0

        total_grid_width = cols * cell_width
        left_margin = (window_width - total_grid_width) // 2

        for i, (folder, image_path) in enumerate(self.current_image_set):
            row = i // self.grid_size
            col = i % self.grid_size
            
            if image_path:
                try:
                    pil_img = Image.open(image_path)
                    img_width, img_height = pil_img.size
                    aspect_ratio = img_width / img_height

                    new_height = cell_height
                    new_width = int(cell_height * aspect_ratio)

                    if new_width > cell_width:
                        new_width = cell_width
                        new_height = int(cell_width / aspect_ratio)

                    pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    img = ImageTk.PhotoImage(pil_img)
                    x = left_margin + col * cell_width + (cell_width - new_width) // 2
                    y = row * cell_height + (cell_height - new_height) // 2
                    image_item = self.canvas.create_image(x, y, anchor=tk.NW, image=img)
                    self.canvas.tag_bind(image_item, "<Button-1>", lambda e, f=folder: self.vote(f))
                    self.current_images.append((img, image_item))
                except Exception as e:
                    print(f"Error loading image {image_path}: {e}")
                    self.canvas.create_text(left_margin + col * cell_width + cell_width // 2, 
                                            row * cell_height + cell_height // 2,
                                            text="Error loading image", anchor=tk.CENTER)
            else:
                self.canvas.create_text(left_margin + col * cell_width + cell_width // 2, 
                                        row * cell_height + cell_height // 2,
                                        text="No image", anchor=tk.CENTER)

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
