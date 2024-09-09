import os
import math
import random
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import sys

class ImageComparisonTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Image Comparison Tool")
        self.root.geometry("1280x720")
        
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.base_font_size = min(self.screen_width // 100, self.screen_height // 100)
        
        self.set_dpi_awareness(True)
        
        self.folders = []
        self.folder_images = {}
        self.current_images = []
        self.current_index = 0
        self.resize_timer = None
        self.total_comparisons = 0
        self.comparisons_made = 0
        
        self.current_pool = []
        self.current_comparison = None
        self.choice_made = None
        self.folder_scores = {}
        
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

        style = ttk.Style()
        font_size = self.get_font_size(0.8)
        style.configure("Treeview", font=('Helvetica', font_size))
        style.configure("Treeview.Heading", font=('Helvetica', self.get_font_size(0.9), "bold"))
        style.configure("Treeview", rowheight=font_size * 2)

        self.folder_tree = ttk.Treeview(self.tree_frame, columns=("path",), show="headings", style="Treeview")
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
            images = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            self.folder_images[folder] = sorted(images, key=lambda x: os.path.getmtime(os.path.join(folder, x)))
            self.folder_tree.insert("", "end", values=(folder,))

    def remove_folder(self):
        selected_item = self.folder_tree.selection()
        if selected_item:
            folder = self.folder_tree.item(selected_item)['values'][0]
            if folder in self.folders:
                self.folders.remove(folder)
                del self.folder_images[folder]
                self.folder_tree.delete(selected_item)

    def start_comparison(self):
        if len(self.folders) < 2:
            messagebox.showwarning("Warning", "Please add at least two folders for comparison.")
            return
        
        self.set_dpi_awareness(False)
        self.main_frame.grid_remove()
        self.image_frame.grid()
        self.current_index = 0
        self.comparisons_made = 0
        self.folder_scores = {folder: 0 for folder in self.folders}
        self.total_comparisons = min(len(images) for images in self.folder_images.values())
        self.update_title()
        self.load_next_image_pool()

    def stop_comparison(self):
        self.set_dpi_awareness(True)
        self.image_frame.grid_remove()
        self.main_frame.grid()
        self.current_index = 0
        self.root.title("Image Comparison Tool")

    def update_title(self):
        self.root.title(f"Image Comparison - Progress: {self.current_index}/{self.total_comparisons}")

    def load_next_image_pool(self):
        if self.current_index >= self.total_comparisons:
            self.show_results()
            return

        self.current_pool = []
        for folder in self.folders:
            image_name = self.folder_images[folder][self.current_index]
            image_path = os.path.join(folder, image_name)
            self.current_pool.append((folder, image_path))

        self.compare_image_pool()

    def compare_image_pool(self):
        pool_size = len(self.current_pool)
        comparison_results = {folder: 0 for folder, _ in self.current_pool}

        for i in range(pool_size):
            for j in range(i + 1, pool_size):
                self.current_comparison = [self.current_pool[i], self.current_pool[j]]
                random.shuffle(self.current_comparison)
                self.display_comparison()
                user_choice = self.wait_for_user_choice()

                winner = self.current_comparison[0 if user_choice == "left" else 1]
                comparison_results[winner[0]] += 1

        # Sort the pool based on comparison results
        sorted_pool = sorted(self.current_pool, key=lambda x: comparison_results[x[0]], reverse=True)

        # Assign points and update scores
        for rank, (folder, _) in enumerate(sorted_pool):
            points = max(pool_size - rank - 1, 0)  # Subtract 1 from previous formula, ensure minimum is 0
            self.folder_scores[folder] += points

        self.current_index += 1
        self.update_title()
        self.load_next_image_pool()

    def display_comparison(self):
        if self.current_comparison is None:
            return

        self.canvas.delete("all")
        self.current_images = []

        window_width = self.canvas.winfo_width()
        window_height = self.canvas.winfo_height()
        
        for i, (folder, image_path) in enumerate(self.current_comparison):
            try:
                with Image.open(image_path) as pil_img:
                    if pil_img.mode != 'RGB':
                        pil_img = pil_img.convert('RGB')
                    
                    img_width, img_height = pil_img.size
                    aspect_ratio = img_width / img_height

                    new_width = window_width // 2
                    new_height = int(new_width / aspect_ratio)

                    if new_height > window_height:
                        new_height = window_height
                        new_width = int(new_height * aspect_ratio)

                    pil_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
                    
                    img = ImageTk.PhotoImage(pil_img)
                    x = i * (window_width // 2) + (window_width // 4 - new_width // 2)
                    y = (window_height - new_height) // 2
                    image_item = self.canvas.create_image(x, y, anchor=tk.NW, image=img)
                    self.canvas.tag_bind(image_item, "<Button-1>", lambda e, side=("left" if i == 0 else "right"): self.make_choice(side))
                    self.current_images.append((img, image_item))
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")
                self.canvas.create_text(i * (window_width // 2) + (window_width // 4), 
                                        window_height // 2,
                                        text="Error loading image", anchor=tk.CENTER,
                                        font=('Helvetica', self.get_font_size(0.8)))

        self.root.update_idletasks()

    def make_choice(self, choice):
        self.user_choice = choice
        if self.choice_made:
            self.choice_made.set(True)

    def wait_for_user_choice(self):
        self.user_choice = None
        self.choice_made = tk.BooleanVar(value=False)
        self.root.wait_variable(self.choice_made)
        return self.user_choice

    def show_results(self):
        result = "Final scores:\n"
        for folder, score in sorted(self.folder_scores.items(), key=lambda x: x[1], reverse=True):
            result += f"{os.path.basename(folder)}: {score} points\n"
        messagebox.showinfo("Comparison Complete", result)
        self.stop_comparison()

    def on_window_resize(self, event):
        if self.resize_timer is not None:
            self.root.after_cancel(self.resize_timer)
        self.resize_timer = self.root.after(200, self.display_comparison)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    tool = ImageComparisonTool()
    tool.run()