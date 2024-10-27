import os
import math
import random
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import sys
import json

class ImageBatchCompare:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Image Batch Compare")
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
        self.current_comparison = 0
        self.comparisons_within_group = 0
        
        self.current_group_index = 0
        self.current_group = []
        self.group_winner = None
        self.current_screen_images = []
        self.screen_winner = None
        self.current_index = 0
        self.winner_position = None
        
        self.config_file = "image-batch-compare.json"
        self.load_config()
        
        self.root.bind("<BackSpace>", self.skip_current_selection)

        self.current_image = None
        self.left_image = None
        self.right_image = None

        self.group_comparisons = 0

        self.click_start_x = None
        self.click_start_y = None

        self.click_disabled = False
        self.click_disable_timer = None

        self.last_chosen_side = None  # Add this line

        self.setup_ui()

        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        # Remove the existing binding for "<Button-1>"
        # self.canvas.bind("<Button-1>", self.handle_click)

        self.reset_comparison_state()

        self.root.bind("<Configure>", self.on_window_configure)

    def reset_comparison_state(self):
        self.current_group_index = 0
        self.current_group = []
        self.group_winner = None
        self.current_screen_images = []
        self.screen_winner = None
        self.current_index = 0
        self.winner_position = None
        self.comparisons_within_group = 0
        self.current_comparison = 0
        self.votes = {folder: 0 for folder in self.folders}

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
        ttk.Button(self.control_frame, text="Add Subfolders", command=self.add_subfolders, style='Large.TButton').grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(self.control_frame, text="Remove Folder", command=self.remove_folder, style='Large.TButton').grid(row=0, column=2, padx=10, pady=10)
        self.start_button = ttk.Button(self.control_frame, text="Start Comparison", command=self.start_comparison, style='Large.TButton')
        self.start_button.grid(row=0, column=3, padx=10, pady=10)

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

        self.root.bind("<Configure>", self.on_window_configure)
        self.root.bind("<Escape>", lambda e: self.stop_comparison())

        # Populate the Treeview with folders from config
        for folder in self.folders:
            self.folder_tree.insert("", "end", values=(folder,))

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.folders = []
                for folder in config.get('folders', []):
                    if os.path.exists(folder):
                        self.folders.append(folder)
                        self.votes[folder] = 0
                        images = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
                        self.folder_images[folder] = sorted(images, key=lambda x: os.path.getmtime(os.path.join(folder, x)))
                    else:
                        print(f"Warning: Folder '{folder}' not found. Skipping.")
            
            if not self.folders:
                print("No valid folders found in the configuration.")

    def save_config(self):
        config = {'folders': [folder for folder in self.folders if os.path.exists(folder)]}
        with open(self.config_file, 'w') as f:
            json.dump(config, f)

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder and folder not in self.folders:
            self.folders.append(folder)
            self.votes[folder] = 0
            
            self.folder_tree.insert("", "end", values=(folder,))
            self.save_config()

    def remove_folder(self):
        selected_item = self.folder_tree.selection()
        if selected_item:
            folder = self.folder_tree.item(selected_item)['values'][0]
            if folder in self.folders:
                self.folders.remove(folder)
                self.votes.pop(folder, None)
                self.folder_images.pop(folder, None)  # Use pop with a default value
                self.folder_tree.delete(selected_item)
                self.save_config()

    def add_subfolders(self):
        root_folder = filedialog.askdirectory()
        if root_folder:
            subfolders = [os.path.join(root_folder, d) for d in os.listdir(root_folder) 
                          if os.path.isdir(os.path.join(root_folder, d))]
            for folder in subfolders:
                if folder not in self.folders:
                    self.folders.append(folder)
                    self.votes[folder] = 0
                    self.folder_tree.insert("", "end", values=(folder,))
            self.save_config()

    def start_comparison(self):
        if len(self.folders) < 2:
            messagebox.showwarning("Warning", "Please add at least two folders for comparison.")
            return
        
        self.set_dpi_awareness(False)
        
        # Maximize the window
        self.root.state('zoomed')  # This works for Windows and some Linux environments
        
        # Use after method to delay the start of comparison
        self.root.after(100, self._start_comparison_after_maximize)

    def _start_comparison_after_maximize(self):
        # Load images for all folders here
        for folder in self.folders:
            images = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            self.folder_images[folder] = sorted(images, key=lambda x: os.path.getmtime(os.path.join(folder, x)))
        
        self.main_frame.grid_remove()
        self.image_frame.grid()
        self.reset_comparison_state()
        self.total_comparisons = self.calculate_total_comparisons()
        
        self.root.bind("<BackSpace>", self.skip_current_selection)
        
        self.load_next_group()

    def calculate_total_comparisons(self):
        total = 0
        for i in range(max(len(images) for images in self.folder_images.values())):
            num_images_in_group = sum(1 for folder in self.folders if i < len(self.folder_images[folder]))
            if num_images_in_group > 1:
                total += num_images_in_group - 1  # Each group will have (n-1) comparisons
        return total

    def update_title(self):
        if self.image_frame.winfo_viewable():  # Only show comparison number if we're in comparison mode
            self.root.title(f"Image Batch Compare - Comparison {self.current_comparison + 1}/{self.total_comparisons}")
        else:
            self.root.title("Image Batch Compare")

    def stop_comparison(self):
        self.set_dpi_awareness(True)
        
        # Restore the window to its original size
        self.root.state('normal')
        
        self.image_frame.grid_remove()
        self.main_frame.grid()
        self.reset_comparison_state()
        self.root.title("Image Batch Compare")
        
        self.root.unbind("<BackSpace>")

    def skip_current_selection(self, event):
        remaining_in_group = (len(self.folders) * (len(self.folders) - 1)) // 2 - self.comparisons_within_group
        self.current_comparison += remaining_in_group
        self.current_group_index += 1
        self.load_next_group()

    def load_next_group(self):
        print(f"Loading next group. Current group index: {self.current_group_index}")
        if self.current_group_index >= max(len(images) for images in self.folder_images.values()):
            self.show_results()
            return

        self.current_group = []
        for folder in self.folders:
            if self.current_group_index < len(self.folder_images[folder]):
                image_name = self.folder_images[folder][self.current_group_index]
                image_path = os.path.join(folder, image_name)
                self.current_group.append((folder, image_path))

        print(f"New group size: {len(self.current_group)}")

        # Shuffle the current group
        random.shuffle(self.current_group)

        self.group_winner = None
        self.current_pair_index = 0
        self.comparisons_within_group = 0
        
        if len(self.current_group) > 1:
            self.load_next_screen()
        else:
            self.current_group_index += 1
            self.load_next_group()

    def load_next_screen(self):
        if self.group_winner is None:
            # First comparison in the group
            self.current_pair = self.current_group[:2]
        elif self.current_pair_index < len(self.current_group) - 1:
            # Compare the winner with the next image
            self.current_pair = [self.group_winner, self.current_group[self.current_pair_index + 1]]
            
            # Place the winner on the opposite side of the last chosen side
            if self.last_chosen_side == 'left':
                self.current_pair = self.current_pair[::-1]  # Reverse the pair
        else:
            # We've compared all images in this group
            self.votes[self.group_winner[0]] += 1
            print(f"Added vote for group winner: {self.group_winner[0]}")
            self.current_group_index += 1
            self.load_next_group()
            return

        self.current_screen_images = self.current_pair
        self.display_current_screen()
        self.update_title()

    def display_current_screen(self):
        self.canvas.delete("all")
        self.current_images = []

        window_width = self.canvas.winfo_width()
        window_height = self.canvas.winfo_height()
        
        for i, image_data in enumerate(self.current_screen_images):
            if image_data is not None:
                folder, image_path = image_data
                
                try:
                    with Image.open(image_path) as pil_img:
                        if pil_img.mode != 'RGB':
                            pil_img = pil_img.convert('RGB')
                        
                        img_width, img_height = pil_img.size
                        aspect_ratio = img_width / img_height

                        if aspect_ratio > window_width / window_height:
                            new_width = window_width
                            new_height = max(1, int(window_width / aspect_ratio))
                        else:
                            new_height = window_height
                            new_width = max(1, int(window_height * aspect_ratio))

                        pil_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
                        
                        img = ImageTk.PhotoImage(pil_img)
                        
                        # Store the images
                        if i == 0:
                            self.left_image = (img, folder, image_path)
                        else:
                            self.right_image = (img, folder, image_path)
                        
                except Exception as e:
                    print(f"Error loading image: {e}")

        # Initially display the left image
        self.display_image(self.left_image)

        self.update_title()
        self.root.update_idletasks()

    def display_image(self, image_data):
        if image_data:
            img, folder, image_path = image_data
            window_width = self.canvas.winfo_width()
            window_height = self.canvas.winfo_height()
            
            x = (window_width - img.width()) // 2
            y = (window_height - img.height()) // 2
            
            self.canvas.delete("all")
            self.current_image = self.canvas.create_image(x, y, anchor=tk.NW, image=img)

    def on_mouse_press(self, event):
        self.click_start_x = event.x
        self.click_start_y = event.y

    def on_mouse_release(self, event):
        if self.click_disabled:
            return
        
        if self.click_start_x is not None and self.click_start_y is not None:
            # Check if both press and release occurred within the canvas
            if (0 <= self.click_start_x < self.canvas.winfo_width() and
                0 <= self.click_start_y < self.canvas.winfo_height() and
                0 <= event.x < self.canvas.winfo_width() and
                0 <= event.y < self.canvas.winfo_height()):
                self.handle_click(event)
        
        # Reset the click start coordinates
        self.click_start_x = None
        self.click_start_y = None

    def handle_click(self, event):
        window_width = self.canvas.winfo_width()
        if event.x < window_width // 2:
            chosen_image = self.left_image
            self.last_chosen_side = 'left'
        else:
            chosen_image = self.right_image
            self.last_chosen_side = 'right'
        
        if chosen_image:
            _, folder, image_path = chosen_image
            self.vote(folder, image_path)

    def vote(self, chosen_folder, chosen_image_path):
        print(f"Vote called for folder: {chosen_folder}")
        print(f"Before vote - Current votes: {self.votes}")
        print(f"Current group index: {self.current_group_index}")
        print(f"Current pair index: {self.current_pair_index}")
        print(f"Group size: {len(self.current_group)}")

        self.group_winner = (chosen_folder, chosen_image_path)
        self.current_comparison += 1
        self.current_pair_index += 1
        self.comparisons_within_group += 1

        if self.comparisons_within_group >= len(self.current_group) - 1:
            # This was the last comparison in the group
            self.votes[chosen_folder] += 1
            print(f"Added vote for group winner: {chosen_folder}")
            self.current_group_index += 1
            self.load_next_group()
        else:
            self.load_next_screen()

        print(f"After vote - Current votes: {self.votes}")
        print("--------------------")

        # Refresh the current image based on mouse position
        self.refresh_current_image()

    def refresh_current_image(self):
        mouse_x = self.root.winfo_pointerx() - self.root.winfo_rootx()
        window_width = self.canvas.winfo_width()
        if mouse_x < window_width // 2:
            self.display_image(self.left_image)
        else:
            self.display_image(self.right_image)

    def on_mouse_move(self, event):
        window_width = self.canvas.winfo_width()
        if event.x < window_width // 2:
            if self.current_image != self.left_image:
                self.canvas.delete("all")
                self.display_image(self.left_image)
        else:
            if self.current_image != self.right_image:
                self.canvas.delete("all")
                self.display_image(self.right_image)

    def update_title(self):
        if self.image_frame.winfo_viewable():  # Only show comparison number if we're in comparison mode
            self.root.title(f"Image Batch Compare - Comparison {self.current_comparison + 1}/{self.total_comparisons}")
        else:
            self.root.title("Image Batch Compare")

    def on_window_configure(self, event):
        # Cancel any existing timers
        if self.resize_timer is not None:
            self.root.after_cancel(self.resize_timer)
        if self.click_disable_timer is not None:
            self.root.after_cancel(self.click_disable_timer)
        
        # Disable clicks
        self.click_disabled = True
        
        # Set timers
        self.resize_timer = self.root.after(200, self.display_current_screen)
        self.click_disable_timer = self.root.after(100, self.enable_clicks)

    def enable_clicks(self):
        self.click_disabled = False

    def show_results(self):
        result = "Results:\n"
        for folder, votes in self.votes.items():
            result += f"{os.path.basename(folder)}: {votes} votes\n"
        messagebox.showinfo("Comparison Complete", result)
        self.stop_comparison()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    tool = ImageBatchCompare()
    tool.run()
