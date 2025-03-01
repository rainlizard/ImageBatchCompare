import os
import math
import random
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import sys
import json
from tkinterdnd2 import *
import time
import shutil
import subprocess
import datetime

class ImageBatchCompare:
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("Image Batch Compare")
        self.root.geometry("1440x720")
        
        # Reintroduce the call to set_dpi_awareness
        self.set_dpi_awareness()

        # Get the DPI scaling factor
        dpi_scaling = self.root.tk.call('tk', 'scaling')

        # Get screen resolution
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calculate base font size based on DPI scaling and screen resolution
        self.base_font_size = self.calculate_base_font_size(screen_width, screen_height)
        
        self.folders = []
        self.folder_images = {}
        self.current_images = []
        self.votes = {}
        self.resize_timer = None
        self.total_comparisons = 0
        self.current_comparison = 0
        self.comparisons_within_subgroup = 0
        
        self.current_subgroup_index = 0
        self.current_subgroup = []
        self.subgroup_winner = None
        self.current_screen_images = []
        self.screen_winner = None
        self.current_index = 0
        self.winner_position = None
        
        self.config_file = "ibc-settings.json"
        self.load_config()
        
        # Create results directory if it doesn't exist
        self.results_dir = "Results"
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
        
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

    def calculate_base_font_size(self, screen_width, screen_height):
        # Base font size calculation based on screen resolution
        # You can adjust the logic here to fit your needs
        base_size = 32  # Default base size
        return int(base_size)

    def get_font_size(self, size_factor):
        return int(self.base_font_size * size_factor)

    def setup_ui(self):
        # Enable drop functionality for the main window
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        self.control_frame.columnconfigure(3, weight=1)

        button_style = ttk.Style()
        button_style.configure('Small.TButton', padding=(self.get_font_size(0.5), self.get_font_size(0.5)), font=('Helvetica', self.get_font_size(0.8)))

        ttk.Button(self.control_frame, text="Add Folder", command=self.add_folder, style='Small.TButton').grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(self.control_frame, text="Remove Folder", command=self.remove_folder, style='Small.TButton').grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.control_frame, text="Add Subfolders", command=self.add_subfolders, style='Small.TButton').grid(row=0, column=2, padx=5, pady=5)
        self.start_button = ttk.Button(self.control_frame, text="Start Comparison", command=self.start_comparison, style='Small.TButton')
        self.start_button.grid(row=0, column=4, padx=5, pady=5)

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

        # Create a frame to hold the tree and the folder icons
        self.tree_container = ttk.Frame(self.tree_frame)
        self.tree_container.grid(row=0, column=0, sticky="nsew")
        self.tree_container.grid_columnconfigure(0, weight=1)
        self.tree_container.grid_rowconfigure(0, weight=1)

        self.folder_tree = ttk.Treeview(self.tree_container, columns=("button", "path"), show="headings", style="Treeview")
        self.folder_tree.heading("button", text="")  # Empty header for button column
        self.folder_tree.heading("path", text="List of image groups to compare")
        self.folder_tree.column("#0", width=0, stretch=False)  # Hide the default first column
        self.folder_tree.column("button", anchor="center", width=40, minwidth=40, stretch=False)  # Fixed width for icon
        self.folder_tree.column("path", anchor="w", stretch=True)  # Allow path column to stretch
        self.folder_tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.folder_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.folder_tree.configure(yscrollcommand=scrollbar.set)

        # Add binding for mouse motion instead of tag bindings
        self.folder_tree.bind('<Motion>', self.on_icon_hover)
        
        # Store the last hovered item
        self.last_hovered_item = None
        self.hover_animation_id = None

        # Create folder icon buttons for existing items
        self.update_folder_icons()

        self.image_frame = ttk.Frame(self.root)
        self.image_frame.grid(row=0, column=0, sticky="nsew")
        self.image_frame.grid_remove()

        self.canvas = tk.Canvas(self.image_frame)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.root.bind("<Configure>", self.on_window_configure)
        self.root.bind("<Escape>", lambda e: self.stop_comparison())

        # Add binding for folder icon clicks
        self.folder_tree.bind('<Button-1>', self.open_folder)
        
        # Add binding for Ctrl+A to select all folders
        self.root.bind("<Control-a>", self.select_all_folders)
        
        # Populate the Treeview with folders from config
        for folder in self.folders:
            self.folder_tree.insert("", "end", values=("📂", folder), tags=('folder_icon',))

        # Add right-click binding to the folder tree
        self.folder_tree.bind("<Button-3>", self.on_right_click)

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
                        self.folder_images[folder] = sorted(images)
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
            
            # Insert with folder icon and tag
            item_id = self.folder_tree.insert("", "end", values=("📂", folder), tags=('folder_icon',))
            self.save_config()

    def remove_folder(self):
        selected_items = self.folder_tree.selection()
        if selected_items:
            # Process each selected item individually
            for item in selected_items:
                folder = self.folder_tree.item(item)['values'][1]  # Get path from second column
                if folder in self.folders:
                    # Check if this is a temp directory and delete it
                    if os.path.dirname(folder) == os.environ.get('TEMP', '/tmp') and 'image_batch_' in os.path.basename(folder):
                        try:
                            print(f"Removing temp directory: {folder}")
                            shutil.rmtree(folder)
                        except Exception as e:
                            print(f"Error removing temp directory: {e}")
                    
                    self.folders.remove(folder)
                    self.votes.pop(folder, None)
                    self.folder_images.pop(folder, None)
                    self.folder_tree.delete(item)
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
                    self.folder_tree.insert("", "end", values=("📂", folder))
            self.save_config()

    def start_comparison(self):
        if len(self.folders) < 2:
            messagebox.showwarning("Warning", "Please add at least two folders for comparison.")
            return
        
        # Load images for all folders to check counts
        for folder in self.folders:
            images = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            self.folder_images[folder] = sorted(images)
        
        # Check if all folders have the same number of images
        image_counts = [len(self.folder_images[folder]) for folder in self.folders]
        if len(set(image_counts)) > 1:
            # Create a detailed error message showing the count for each folder
            error_msg = "Folders must contain the same number of images:\n\n"
            for folder in self.folders:
                count = len(self.folder_images[folder])
                folder_name = os.path.basename(folder)
                error_msg += f"{folder_name}: {count} images\n"
            messagebox.showerror("Error", error_msg)
            return
        
        # Maximize the window
        self.root.state('zoomed')  # This works for Windows and some Linux environments
        
        # Use after method to delay the start of comparison
        self.root.after(100, self._start_comparison_after_maximize)

    def _start_comparison_after_maximize(self):
        # Load images for all folders here
        for folder in self.folders:
            images = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            self.folder_images[folder] = sorted(images)
        
        self.main_frame.grid_remove()
        self.image_frame.grid()
        self.reset_comparison_state()
        self.total_comparisons = self.calculate_total_comparisons()
        
        self.root.bind("<BackSpace>", self.skip_current_selection)
        
        self.load_next_subgroup()

    def calculate_total_comparisons(self):
        total = 0
        for i in range(max(len(images) for images in self.folder_images.values())):
            num_images_in_group = sum(1 for folder in self.folders if i < len(self.folder_images[folder]))
            if num_images_in_group > 1:
                total += num_images_in_group - 1  # Each group will have (n-1) comparisons
        return total

    def update_title(self):
        if self.image_frame.winfo_viewable():
            self.root.title(f"Image Batch Compare • Subgroup {self.current_subgroup_index + 1} • {self.current_comparison + 1}/{self.total_comparisons}")
        else:
            self.root.title("Image Batch Compare")

    def stop_comparison(self):
        # Restore the window to its original size
        self.root.state('normal')
        
        self.image_frame.grid_remove()
        self.main_frame.grid()
        self.reset_comparison_state()
        self.root.title("Image Batch Compare")
        
        self.root.unbind("<BackSpace>")

    def skip_current_selection(self, event):
        # The current formula is incorrect - it's calculating too many remaining comparisons
        # remaining_in_subgroup = (len(self.folders) * (len(self.folders) - 1)) // 2 - self.comparisons_within_subgroup
        
        # The correct formula should be based on how many comparisons are left in this subgroup
        # For a tournament style comparison, we need (n-1) comparisons for n items
        total_in_subgroup = len(self.current_subgroup) - 1
        remaining_in_subgroup = total_in_subgroup - self.comparisons_within_subgroup
        
        # Add the remaining comparisons to the counter
        self.current_comparison += remaining_in_subgroup
        
        # Move to the next subgroup
        self.current_subgroup_index += 1
        self.load_next_subgroup()

    def load_next_subgroup(self):
        print(f"Loading next subgroup. Current subgroup index: {self.current_subgroup_index}")
        if self.current_subgroup_index >= max(len(images) for images in self.folder_images.values()):
            self.show_results()
            return

        self.current_subgroup = []
        for folder in self.folders:
            if self.current_subgroup_index < len(self.folder_images[folder]):
                image_name = self.folder_images[folder][self.current_subgroup_index]
                image_path = os.path.join(folder, image_name)
                self.current_subgroup.append((folder, image_path))

        print(f"New subgroup size: {len(self.current_subgroup)}")

        # Shuffle the current subgroup
        random.shuffle(self.current_subgroup)

        self.subgroup_winner = None
        self.current_pair_index = 0
        self.comparisons_within_subgroup = 0
        
        if len(self.current_subgroup) > 1:
            self.load_next_screen()
        else:
            self.current_subgroup_index += 1
            self.load_next_subgroup()

    def load_next_screen(self):
        if self.subgroup_winner is None:
            # First comparison in the subgroup
            self.current_pair = self.current_subgroup[:2]
            print(f"First comparison in subgroup: {self.current_pair[0][0]} vs {self.current_pair[1][0]}")
        elif self.current_pair_index < len(self.current_subgroup) - 1:
            # Compare the winner with the next image
            next_image = self.current_subgroup[self.current_pair_index + 1]
            self.current_pair = [self.subgroup_winner, next_image]
            print(f"Next comparison: {self.subgroup_winner[0]} vs {next_image[0]}")
            
            # Place the winner on the opposite side of the last chosen side
            if self.last_chosen_side == 'left':
                self.current_pair = self.current_pair[::-1]  # Reverse the pair
                print(f"Reversed pair due to last choice being left: {self.current_pair[0][0]} vs {self.current_pair[1][0]}")
        else:
            # We've compared all images in this subgroup
            self.votes[self.subgroup_winner[0]] += 1
            print(f"Added vote for subgroup winner: {self.subgroup_winner[0]}")
            self.current_subgroup_index += 1
            self.load_next_subgroup()
            return

        self.current_screen_images = self.current_pair
        self.display_current_screen()
        self.update_title()

    def display_current_screen(self):
        self.canvas.delete("all")
        self.current_images = []

        window_width = self.canvas.winfo_width()
        window_height = self.canvas.winfo_height()
        
        # Create temporary text objects to measure their width
        font = ('Helvetica', self.get_font_size(1.2), 'bold')
        left_label = "Choose Image A"
        right_label = "Choose Image B"
        
        # Create temporary text objects to measure their width
        temp_left = self.canvas.create_text(0, 0, text=left_label, font=font)
        temp_right = self.canvas.create_text(0, 0, text=right_label, font=font)
        
        # Get the width of each text object
        left_bbox = self.canvas.bbox(temp_left)
        right_bbox = self.canvas.bbox(temp_right)
        left_width = left_bbox[2] - left_bbox[0]
        right_width = right_bbox[2] - right_bbox[0]
        left_height = left_bbox[3] - left_bbox[1]
        right_height = right_bbox[3] - right_bbox[1]
        
        # Delete temporary text objects
        self.canvas.delete(temp_left)
        self.canvas.delete(temp_right)
        
        # Calculate minimum spacing needed between text centers
        min_spacing = left_width/2 + right_width/2 + 20  # Add 20px extra padding
        
        # Calculate positions based on available space
        center_x = window_width / 2
        
        # If window is too narrow, stack the labels vertically
        if window_width < min_spacing * 2:
            left_x = center_x
            right_x = center_x
            left_y = 30
            right_y = 70
        else:
            # Otherwise position them horizontally with proper spacing
            left_x = center_x - min_spacing/2
            right_x = center_x + min_spacing/2
            left_y = right_y = 50
        
        # Add padding for the background rectangles
        padding = 10
        
        # Create background rectangles with semi-transparent black
        # The stipple pattern creates the transparency effect
        self.left_bg = self.canvas.create_rectangle(
            left_x - left_width/2 - padding,
            left_y - left_height/2 - padding,
            left_x + left_width/2 + padding,
            left_y + left_height/2 + padding,
            fill="#000000",  # Pure black
            outline="",
            stipple="gray75",  # This creates 75% opacity (darker)
            tags="text_bg"
        )
        
        self.right_bg = self.canvas.create_rectangle(
            right_x - right_width/2 - padding,
            right_y - right_height/2 - padding,
            right_x + right_width/2 + padding,
            right_y + right_height/2 + padding,
            fill="#000000",  # Pure black
            outline="",
            stipple="gray75",  # This creates 75% opacity (darker)
            tags="text_bg"
        )
        
        # Create the choice text labels
        self.left_text = self.canvas.create_text(
            left_x, left_y,
            text=left_label, 
            fill="#FFFFFF", font=font
        )
        
        self.right_text = self.canvas.create_text(
            right_x, right_y,
            text=right_label, 
            fill="#FFFFFF", font=font
        )
        
        # Load both images as PIL images
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
                            # Use full window height now instead of reserving space
                            new_height = window_height
                            new_width = max(1, int(window_height * aspect_ratio))

                        resized_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
                        photo_img = ImageTk.PhotoImage(resized_img)
                        
                        # Store the folder and path info
                        if i == 0:
                            self.left_image = (photo_img, folder, image_path)
                        else:
                            self.right_image = (photo_img, folder, image_path)
                        
                except Exception as e:
                    print(f"Error loading image: {e}")
        
        # We'll draw the dividing line in on_mouse_move based on mouse position
        # Get current mouse position
        mouse_x = self.root.winfo_pointerx() - self.root.winfo_rootx()
        
        # Initially display based on mouse position
        if mouse_x < window_width // 2:
            self.display_image(self.left_image)
            self.canvas.itemconfig(self.left_text, fill="#FFFFFF")
            self.canvas.itemconfig(self.right_text, fill="#444444")  # Darker inactive text
            self.canvas.itemconfig(self.left_bg, stipple="gray75")   # 25% opaque black background
            self.canvas.itemconfig(self.right_bg, stipple="gray75")  # 25% opaque black background
        else:
            self.display_image(self.right_image)
            self.canvas.itemconfig(self.left_text, fill="#444444")   # Darker inactive text
            self.canvas.itemconfig(self.right_text, fill="#FFFFFF")
            self.canvas.itemconfig(self.left_bg, stipple="gray75")   # 25% opaque black background
            self.canvas.itemconfig(self.right_bg, stipple="gray75")  # 25% opaque black background
        
        # Check if mouse is close to center and draw dividing line if needed
        self.check_and_draw_divider(mouse_x)
        
        self.update_title()
        self.root.update_idletasks()

    def check_and_draw_divider(self, mouse_x):
        """Draw the dividing line only if mouse is close to center"""
        window_width = self.canvas.winfo_width()
        window_height = self.canvas.winfo_height()
        
        # Define the "close to center" threshold (pixels from center)
        center_threshold = window_width * 0.025  # 2.5% of window width
        
        # Calculate distance from center
        center_x = window_width / 2
        distance_from_center = abs(mouse_x - center_x)
        
        # Delete any existing divider
        self.canvas.delete("divider")
        
        # Only draw the divider if mouse is close to center
        if distance_from_center < center_threshold:
            self.canvas.create_line(
                window_width // 2, 0, window_width // 2, window_height,
                fill="#555555", width=2, tags="divider"
            )

    def display_image(self, image_data):
        if image_data:
            img, folder, image_path = image_data
            window_width = self.canvas.winfo_width()
            window_height = self.canvas.winfo_height()
            
            x = (window_width - img.width()) // 2
            y = (window_height - img.height()) // 2
            
            self.canvas.delete("image")
            self.current_image = self.canvas.create_image(x, y, anchor=tk.NW, image=img, tags="image")
            
            # Make sure the text and backgrounds remain visible
            self.canvas.tag_raise("text_bg")
            self.canvas.tag_raise(self.left_text)
            self.canvas.tag_raise(self.right_text)
            
            # Note: We don't redraw the dividing line here anymore
            # It's handled by check_and_draw_divider in on_mouse_move

    def on_mouse_move(self, event):
        """Update the displayed image based on mouse position"""
        window_width = self.canvas.winfo_width()
        
        if event.x < window_width // 2:
            # When mouse is on the left side, show left image and highlight left text
            if self.current_image != self.left_image:
                self.display_image(self.left_image)
            self.canvas.itemconfig(self.left_text, fill="#FFFFFF")
            self.canvas.itemconfig(self.right_text, fill="#444444")  # Darker inactive text
            # For active side: less stippling = more opaque black background
            self.canvas.itemconfig(self.left_bg, stipple="gray75")   # 75% opaque black
            self.canvas.itemconfig(self.right_bg, stipple="gray75")  # 75% opaque black
            self.current_side = 'left'
        else:
            # When mouse is on the right side, show right image and highlight right text
            if self.current_image != self.right_image:
                self.display_image(self.right_image)
            self.canvas.itemconfig(self.left_text, fill="#444444")   # Darker inactive text
            self.canvas.itemconfig(self.right_text, fill="#FFFFFF")
            # For active side: less stippling = more opaque black background
            self.canvas.itemconfig(self.left_bg, stipple="gray75")   # 75% opaque black
            self.canvas.itemconfig(self.right_bg, stipple="gray75")  # 75% opaque black
            self.current_side = 'right'
        
        # Check if mouse is close to center and draw dividing line if needed
        self.check_and_draw_divider(event.x)

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
                
                window_width = self.canvas.winfo_width()
                
                if event.x < window_width / 2:
                    # User clicked on the left side of the screen
                    self.last_chosen_side = 'left'
                    chosen_index = 0  # First image in current_screen_images (left image)
                    print(f"User chose left side, selecting left image: {self.current_screen_images[chosen_index][0]}")
                else:
                    # User clicked on the right side of the screen
                    self.last_chosen_side = 'right'
                    chosen_index = 1  # Second image in current_screen_images (right image)
                    print(f"User chose right side, selecting right image: {self.current_screen_images[chosen_index][0]}")
                
                # Get the chosen image data directly from current_screen_images
                chosen_folder, chosen_path = self.current_screen_images[chosen_index]
                
                # Process the vote without unbinding mouse motion
                self.vote(chosen_folder, chosen_path)
        
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
        print(f"Image path: {chosen_image_path}")
        print(f"Before vote - Current votes: {self.votes}")
        
        # Store the winner as a tuple of (folder, image_path)
        self.subgroup_winner = (chosen_folder, chosen_image_path)
        
        # Increment counters
        self.current_comparison += 1
        self.current_pair_index += 1
        self.comparisons_within_subgroup += 1

        # Check if we've completed all comparisons in this subgroup
        if self.comparisons_within_subgroup >= len(self.current_subgroup) - 1:
            # This was the last comparison in the subgroup
            # Add a vote for the winning folder
            self.votes[chosen_folder] += 1
            print(f"Added vote for subgroup winner: {chosen_folder}")
            
            # Move to the next subgroup
            self.current_subgroup_index += 1
            self.load_next_subgroup()
        else:
            # Continue with the next comparison in this subgroup
            self.load_next_screen()

        print(f"After vote - Current votes: {self.votes}")
        print("--------------------")

    def refresh_current_image(self):
        mouse_x = self.root.winfo_pointerx() - self.root.winfo_rootx()
        window_width = self.canvas.winfo_width()
        if mouse_x < window_width // 2:
            self.display_image(self.left_image)
        else:
            self.display_image(self.right_image)

    def on_window_configure(self, event):
        # Cancel any existing timers
        if self.resize_timer is not None:
            self.root.after_cancel(self.resize_timer)
        if self.click_disable_timer is not None:
            self.root.after_cancel(self.click_disable_timer)
        
        # Recalculate base font size based on screen resolution
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.base_font_size = self.calculate_base_font_size(screen_width, screen_height)
        
        # Update UI elements with new font size
        self.update_ui_font_sizes()

        # Disable clicks
        self.click_disabled = True
        
        # Set timers
        self.resize_timer = self.root.after(200, self.display_current_screen)
        self.click_disable_timer = self.root.after(100, self.enable_clicks)

    def update_ui_font_sizes(self):
        # Update button style
        button_style = ttk.Style()
        button_style.configure('Small.TButton', padding=(self.get_font_size(0.5), self.get_font_size(0.5)), font=('Helvetica', self.get_font_size(0.8)))

        # Update Treeview style
        style = ttk.Style()
        font_size = self.get_font_size(0.8)
        style.configure("Treeview", font=('Helvetica', font_size))
        style.configure("Treeview.Heading", font=('Helvetica', self.get_font_size(0.9), "bold"))

        # Calculate row height based on font size
        row_height = font_size * 2  # Adjust this multiplier as needed
        style.configure("Treeview", rowheight=row_height)

    def enable_clicks(self):
        self.click_disabled = False

    def save_results_to_file(self):
        """Save the comparison results to a timestamped text file in the Results folder."""
        # Create a timestamp for the filename
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        result_file_name = f"comparison_results_{timestamp}.txt"
        result_file_path = os.path.join(self.results_dir, result_file_name)
        
        # Prepare the results content
        result_content = f"Image Batch Compare Results - {timestamp}\n"
        result_content += "=" * 50 + "\n\n"
        
        # Add the comparison details
        result_content += f"Total comparisons: {self.total_comparisons}\n"
        result_content += f"Folders compared: {len(self.folders)}\n\n"
        
        # Add the voting results first (moved to the top)
        result_content += "Results by folder (sorted by votes):\n"
        result_content += "-" * 30 + "\n"
        
        # Sort folders by vote count (descending)
        sorted_folders = sorted(self.votes.items(), key=lambda x: x[1], reverse=True)
        
        for i, (folder, votes) in enumerate(sorted_folders, 1):
            folder_name = os.path.basename(folder)
            result_content += f"{i}. {folder_name}: {votes} votes\n"
        
        result_content += "\n"
        
        # Add detailed folder information after the results
        result_content += "Folders included in comparison:\n"
        result_content += "-" * 30 + "\n"
        for i, folder in enumerate(self.folders, 1):
            folder_name = os.path.basename(folder)
            result_content += f"{i}. {folder_name}\n"
            result_content += f"   Full path: {folder}\n"
            result_content += f"   Image count: {len(self.folder_images.get(folder, []))}\n\n"
        
        # Add timestamp at the end
        result_content += "-" * 50 + "\n"
        result_content += f"Comparison completed at: {timestamp}\n"
        
        # Write the results to the file
        with open(result_file_path, "w") as f:
            f.write(result_content)
        
        # Removed: Save a copy of the configuration file
        
        return result_file_path

    def show_results(self):
        # Save results to file
        result_file_path = self.save_results_to_file()
        
        # Create a message with the sorted results
        result_message = "Results:\n"
        result_message += "-" * 30 + "\n"
        
        # Sort folders by vote count (descending)
        sorted_folders = sorted(self.votes.items(), key=lambda x: x[1], reverse=True)
        
        # Function to get ordinal suffix
        def get_ordinal(n):
            if 10 <= n % 100 <= 20:
                suffix = 'th'
            else:
                suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
            return f"{n}{suffix}"
        
        for i, (folder, votes) in enumerate(sorted_folders, 1):
            folder_name = os.path.basename(folder)
            result_message += f"{get_ordinal(i)}. {folder_name}: {votes} votes\n"
        
        # Add file path information
        result_message += f"\nResults have been saved to:\n{result_file_path}"
        
        # Show the results message box with the sorted vote counts
        messagebox.showinfo("Comparison Complete", result_message)
        
        # Stop the comparison and return to the main screen
        self.stop_comparison()

    def open_file(self, file_path):
        """Open the specified file with the default application."""
        try:
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', file_path])
            return True
        except Exception as e:
            print(f"Error opening file: {e}")
            return False

    def reset_comparison_state(self):
        """Reset the state of the comparison process."""
        self.current_comparison = 0
        self.current_subgroup_index = 0
        self.subgroup_winner = None
        self.current_screen_images = []
        self.screen_winner = None
        self.current_index = 0
        self.winner_position = None
        self.comparisons_within_subgroup = 0
        self.votes = {folder: 0 for folder in self.folders}
        print("Comparison state has been reset.")

    def run(self):
        self.root.mainloop()

    # Reintroduce the set_dpi_awareness method
    def set_dpi_awareness(self):
        if sys.platform.startswith('win'):
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except:
                pass
        elif sys.platform.startswith('linux'):
            # For Linux, we can adjust the scaling factor of the root window
            scale = self.root.winfo_fpixels('1i') / 72.0
            self.root.tk.call('tk', 'scaling', scale)

    def on_right_click(self, event):
        item = self.folder_tree.identify('item', event.x, event.y)
        if item:
            folder = self.folder_tree.item(item)['values'][1]  # Get path from second column
            if folder in self.folders:
                # Check if this is a temp directory and delete it
                if os.path.dirname(folder) == os.environ.get('TEMP', '/tmp') and 'image_batch_' in os.path.basename(folder):
                    try:
                        print(f"Removing temp directory: {folder}")
                        shutil.rmtree(folder)
                    except Exception as e:
                        print(f"Error removing temp directory: {e}")
                
                self.folders.remove(folder)
                self.votes.pop(folder, None)
                self.folder_images.pop(folder, None)
                self.folder_tree.delete(item)
                self.save_config()

    def handle_drop(self, event):
        print("Drop event detected!")
        
        # Get the raw data and clean it up
        raw_data = event.data
        print(f"Raw data: {raw_data}")
        
        # Handle paths with spaces by properly parsing the curly braces
        paths = []
        current_path = ""
        in_braces = False
        
        for char in raw_data:
            if char == '{':
                in_braces = True
            elif char == '}':
                in_braces = False
                if current_path:
                    paths.append(current_path.strip())
                    current_path = ""
            elif char == ' ' and not in_braces:
                if current_path:
                    paths.append(current_path.strip())
                    current_path = ""
            else:
                current_path += char
        
        if current_path:
            paths.append(current_path.strip())
        
        print(f"Parsed paths: {paths}")
        
        # Clean up paths (remove any remaining curly braces)
        paths = [path.strip('{}').strip('"') for path in paths]
        print(f"Cleaned paths: {paths}")
        
        # Reconstruct full file paths if needed
        full_paths = []
        current_dir = None
        
        for path in paths:
            if os.path.isdir(path):
                current_dir = path
            elif current_dir and os.path.isfile(os.path.join(current_dir, path)):
                full_paths.append(os.path.join(current_dir, path))
            elif os.path.isfile(path):
                full_paths.append(path)
        
        print(f"Full paths: {full_paths}")
        
        # Filter for image files
        image_files = [
            path for path in full_paths 
            if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
        ]
        print(f"Found image files: {image_files}")
        
        if image_files:
            # Find the next available batch number
            existing_batches = []
            for folder in self.folders:
                if os.path.dirname(folder) == os.environ.get('TEMP', '/tmp'):
                    try:
                        batch_name = os.path.basename(folder)
                        if batch_name.startswith('image_batch_'):
                            batch_num = int(batch_name.replace('image_batch_', ''))
                            existing_batches.append(batch_num)
                    except ValueError:
                        continue
            
            next_batch = 1
            if existing_batches:
                next_batch = max(existing_batches) + 1
            
            # Create a temp directory with the next batch number
            temp_dir = os.path.join(os.environ.get('TEMP', '/tmp'), f'image_batch_{next_batch}')
            print(f"Creating temp directory: {temp_dir}")
            
            # Create directory if it doesn't exist, or clean it if it does
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        print(f"Error deleting file {file_path}: {e}")
            else:
                os.makedirs(temp_dir, exist_ok=True)
            
            # Copy images to temp directory
            for image_path in image_files:
                filename = os.path.basename(image_path)
                dest_path = os.path.join(temp_dir, filename)
                print(f"Copying {image_path} to {dest_path}")
                shutil.copy2(image_path, dest_path)
            
            # Add the temp directory as a folder
            if temp_dir not in self.folders:
                print(f"Adding temp directory to folders: {temp_dir}")
                self.folders.append(temp_dir)
                self.votes[temp_dir] = 0
                self.folder_tree.insert("", "end", values=("📂", temp_dir))
                self.save_config()
        
        # Handle directories as before
        for path in paths:
            if os.path.isdir(path) and path not in self.folders:
                print(f"Adding directory: {path}")
                self.folders.append(path)
                self.votes[path] = 0
                self.folder_tree.insert("", "end", values=("📂", path))
        
        self.save_config()

    def update_folder_icons(self):
        for item in self.folder_tree.get_children():
            values = list(self.folder_tree.item(item)['values'])
            values[0] = "📂"
            self.folder_tree.item(item, values=values)

    def open_folder(self, event):
        item = self.folder_tree.identify('item', event.x, event.y)
        if item:
            # Get the column that was clicked
            column = self.folder_tree.identify_column(event.x)
            if column == '#1':  # Button column (first column)
                folder_path = self.folder_tree.item(item)['values'][1]  # Get path from second column
                try:
                    if sys.platform == 'win32':
                        os.startfile(folder_path)
                    elif sys.platform == 'darwin':  # macOS
                        subprocess.run(['open', folder_path])
                    else:  # Linux
                        subprocess.run(['xdg-open', folder_path])
                except Exception as e:
                    print(f"Error opening folder: {e}")
                    messagebox.showerror("Error", f"Could not open folder: {str(e)}")

    def on_icon_hover(self, event):
        item = self.folder_tree.identify('item', event.x, event.y)
        column = self.folder_tree.identify_column(event.x)
        
        if column == '#1' and item:  # First column (folder icon)
            if item != self.last_hovered_item:
                # Reset previous hover
                if self.last_hovered_item:
                    values = list(self.folder_tree.item(self.last_hovered_item)['values'])
                    values[0] = "📁"  # Change back to regular folder
                    self.folder_tree.item(self.last_hovered_item, values=values)
                
                # Set new hover
                values = list(self.folder_tree.item(item)['values'])
                values[0] = "✨"  # Change to sparkle
                self.folder_tree.item(item, values=values)
                self.last_hovered_item = item
        elif self.last_hovered_item and (not item or column != '#1'):
            # Mouse moved away from folder icon
            values = list(self.folder_tree.item(self.last_hovered_item)['values'])
            values[0] = "📁"  # Change back to regular folder
            self.folder_tree.item(self.last_hovered_item, values=values)
            self.last_hovered_item = None

    def refresh_display(self):
        """Refresh the display after resize"""
        if self.image_frame.winfo_viewable() and hasattr(self, 'current_screen_images'):
            self.display_current_screen()

    def select_all_folders(self, event):
        """Select all folders in the folder tree when Ctrl+A is pressed"""
        # Only apply if the main frame is visible (not in comparison mode)
        if self.main_frame.winfo_viewable():
            # Get all items in the tree
            all_items = self.folder_tree.get_children()
            # Select all items
            if all_items:
                self.folder_tree.selection_set(all_items)
            return "break"  # Prevent the default Ctrl+A behavior

if __name__ == "__main__":
    tool = ImageBatchCompare()
    tool.run()
