import os
import math
import random
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import sys
import json

class SimultaneousComparisonTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Multi-Folder Image Comparison")
        self.root.geometry("1440x720")
        
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
        self.resize_timer = None
        self.total_comparisons = 0
        self.total_screens = 0
        self.current_screen = 0
        
        self.current_group = []
        self.current_screen_images = []
        self.screen_winner = None
        self.group_winner = None
        self.current_index = 0
        self.winner_position = None
        
        self.config_file = "image-batch-compare.json"
        self.load_config()
        
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
        font_size = self.get_font_size(0.8)
        
        style.configure("Treeview", font=('Helvetica', font_size))
        style.configure("Treeview.Heading", font=('Helvetica', self.get_font_size(0.9), "bold"))

        # Calculate row height based on font size
        row_height = font_size * 2  # Adjust this multiplier as needed

        # Configure row height and padding
        style.configure("Treeview", rowheight=row_height)

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

        # Populate the Treeview with folders from config
        for folder in self.folders:
            self.folder_tree.insert("", "end", values=(folder,))

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.folders = config.get('folders', [])
                for folder in self.folders:
                    self.votes[folder] = 0
                    images = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
                    self.folder_images[folder] = sorted(images, key=lambda x: os.path.getmtime(os.path.join(folder, x)))

    def save_config(self):
        config = {'folders': self.folders}
        with open(self.config_file, 'w') as f:
            json.dump(config, f)

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder and folder not in self.folders:
            self.folders.append(folder)
            self.votes[folder] = 0
            
            images = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            self.folder_images[folder] = sorted(images, key=lambda x: os.path.getmtime(os.path.join(folder, x)))

            self.folder_tree.insert("", "end", values=(folder,))
            self.save_config()

    def remove_folder(self):
        selected_item = self.folder_tree.selection()
        if selected_item:
            folder = self.folder_tree.item(selected_item)['values'][0]
            if folder in self.folders:
                self.folders.remove(folder)
                del self.votes[folder]
                del self.folder_images[folder]
                self.folder_tree.delete(selected_item)
                self.save_config()

    def calculate_total_screens(self):
        num_folders = len(self.folders)
        if num_folders <= 4:
            return self.total_comparisons
        else:
            # Calculate the group number (1-based)
            group = (num_folders - 2) // 3
            return self.total_comparisons * (group + 1)

    def start_comparison(self):
        if len(self.folders) < 2:
            messagebox.showwarning("Warning", "Please add at least two folders for comparison.")
            return
        
        self.set_dpi_awareness(False)
        
        self.main_frame.grid_remove()
        self.image_frame.grid()
        self.current_index = 0
        self.current_screen = 0
        self.total_comparisons = max(len(images) for images in self.folder_images.values())
        self.total_screens = self.calculate_total_screens()
        
        self.load_next_group()

    def stop_comparison(self):
        self.set_dpi_awareness(True)
        
        self.image_frame.grid_remove()
        self.main_frame.grid()
        self.current_index = 0
        self.current_screen = 0
        self.votes = {folder: 0 for folder in self.folders}
        self.current_group = []
        self.current_screen_images = []
        self.screen_winner = None
        self.group_winner = None
        self.winner_position = None
        self.root.title("Multi-Folder Image Comparison")

    def load_next_group(self):
        if not self.folder_images:
            self.show_results()
            return

        if self.current_index >= self.total_comparisons:
            self.show_results()
            return

        self.current_group = []
        for folder in self.folders:
            if self.current_index < len(self.folder_images[folder]):
                image_name = self.folder_images[folder][self.current_index]
                image_path = os.path.join(folder, image_name)
                self.current_group.append((folder, image_path))

        self.group_winner = None
        self.screen_winner = None
        self.winner_position = None
        self.load_next_screen()

    def load_next_screen(self):
        if not self.current_group:
            if self.group_winner:
                self.votes[self.group_winner[0]] += 1
            self.current_index += 1
            self.load_next_group()
            return

        self.current_screen += 1
        max_images = 2 if len(self.folders) == 2 else 4
        self.current_screen_images = [None] * max_images
        if self.screen_winner and self.winner_position is not None:
            self.current_screen_images[self.winner_position] = self.screen_winner

        available_positions = [i for i in range(max_images) if self.current_screen_images[i] is None]
        num_to_select = min(len(available_positions), len(self.current_group))
        selected_images = random.sample(self.current_group, num_to_select)

        for img, pos in zip(selected_images, available_positions):
            self.current_screen_images[pos] = img
            self.current_group.remove(img)

        # Ensure the winner stays in its position even if there are fewer than max_images
        self.current_screen_images = [img for img in self.current_screen_images if img is not None]
        if self.screen_winner and len(self.current_screen_images) < max_images:
            full_screen = [None] * max_images
            full_screen[self.winner_position] = self.screen_winner
            for img in self.current_screen_images:
                if img != self.screen_winner:
                    empty_pos = next(i for i, x in enumerate(full_screen) if x is None)
                    full_screen[empty_pos] = img
            self.current_screen_images = full_screen

        self.display_current_screen()

    def display_current_screen(self):
        self.canvas.delete("all")
        self.current_images = []

        window_width = self.canvas.winfo_width()
        window_height = self.canvas.winfo_height()
        
        if len(self.folders) == 2:
            grid_size = (1, 2)  # 2x1 grid
            cell_width = window_width // 2
            cell_height = window_height
        else:
            grid_size = (2, 2)  # 2x2 grid
            cell_width = window_width // 2
            cell_height = window_height // 2

        for i, image_data in enumerate(self.current_screen_images):
            if image_data is not None:
                folder, image_path = image_data
                
                if len(self.folders) == 2:
                    row, col = 0, i
                else:
                    row, col = divmod(i, 2)
                
                try:
                    with Image.open(image_path) as pil_img:
                        if pil_img.mode != 'RGB':
                            pil_img = pil_img.convert('RGB')
                        
                        img_width, img_height = pil_img.size
                        aspect_ratio = img_width / img_height

                        if aspect_ratio > cell_width / cell_height:
                            new_width = cell_width
                            new_height = max(1, int(cell_width / aspect_ratio))
                        else:
                            new_height = cell_height
                            new_width = max(1, int(cell_height * aspect_ratio))

                        pil_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
                        
                        img = ImageTk.PhotoImage(pil_img)
                        
                        if len(self.folders) == 2:
                            # For 2x1 grid, center the images
                            x = col * cell_width + (cell_width - new_width) // 2
                        else:
                            # For 2x2 grid, align left images to right, right images to left
                            if col == 0:  # Left column
                                x = cell_width - new_width
                            else:  # Right column
                                x = cell_width
                        
                        y = row * cell_height + (cell_height - new_height) // 2
                        
                        image_item = self.canvas.create_image(x, y, anchor=tk.NW, image=img)
                        self.canvas.tag_bind(image_item, "<Button-1>", lambda e, f=folder, ip=image_path, pos=i: self.vote(f, ip, pos))
                        self.current_images.append((img, image_item))
                except Exception as e:
                    pass

        self.update_title()
        self.root.update_idletasks()

    def vote(self, chosen_folder, chosen_image_path, position):
        self.screen_winner = (chosen_folder, chosen_image_path)
        self.group_winner = (chosen_folder, chosen_image_path)
        self.winner_position = position

        if self.current_group:
            self.load_next_screen()
        else:
            self.votes[self.group_winner[0]] += 1
            self.current_index += 1
            self.group_winner = None
            self.screen_winner = None
            self.winner_position = None
            self.load_next_group()

    def update_title(self):
        self.root.title(f"Multi-Folder Image Comparison - {self.current_screen}/{self.total_screens}")

    def on_window_resize(self, event):
        if self.resize_timer is not None:
            self.root.after_cancel(self.resize_timer)
        self.resize_timer = self.root.after(200, self.display_current_screen)

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