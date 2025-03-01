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
        self.comparisons_within_group = 0
        
        self.current_group_index = 0
        self.current_group = []
        self.group_winner = None
        self.current_screen_images = []
        self.screen_winner = None
        self.current_index = 0
        self.winner_position = None
        
        self.config_file = "ibc-settings.json"
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
        selected_item = self.folder_tree.selection()
        if selected_item:
            folder = self.folder_tree.item(selected_item)['values'][1]  # Get path from second column
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
                    self.folder_tree.insert("", "end", values=("📂", folder))
            self.save_config()

    def start_comparison(self):
        if len(self.folders) < 2:
            messagebox.showwarning("Warning", "Please add at least two folders for comparison.")
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
            print(f"First comparison in group: {self.current_pair[0][0]} vs {self.current_pair[1][0]}")
        elif self.current_pair_index < len(self.current_group) - 1:
            # Compare the winner with the next image
            next_image = self.current_group[self.current_pair_index + 1]
            self.current_pair = [self.group_winner, next_image]
            print(f"Next comparison: {self.group_winner[0]} vs {next_image[0]}")
            
            # Place the winner on the opposite side of the last chosen side
            if self.last_chosen_side == 'left':
                self.current_pair = self.current_pair[::-1]  # Reverse the pair
                print(f"Reversed pair due to last choice being left: {self.current_pair[0][0]} vs {self.current_pair[1][0]}")
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
        
        # Create the choice text at the top with updated labels
        self.left_text = self.canvas.create_text(
            window_width * 0.25, 50, 
            text="Choose Image A", 
            fill="#555555", font=('Helvetica', self.get_font_size(1.2), 'bold')
        )
        
        self.right_text = self.canvas.create_text(
            window_width * 0.75, 50, 
            text="Choose Image B", 
            fill="#555555", font=('Helvetica', self.get_font_size(1.2), 'bold')
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
                        
                        # Store the folder and path info
                        if i == 0:
                            self.left_folder = folder
                            self.left_path = image_path
                            self.left_pil_img = resized_img
                        else:
                            self.right_folder = folder
                            self.right_path = image_path
                            self.right_pil_img = resized_img
                        
                except Exception as e:
                    print(f"Error loading image: {e}")
        
        # Store dimensions for later use
        if hasattr(self, 'left_pil_img'):
            self.img_width = self.left_pil_img.width
            self.img_height = self.left_pil_img.height
            
            # Pre-calculate the center position for images
            self.x_offset = (window_width - self.img_width) // 2
            self.y_offset = (window_height - self.img_height) // 2
        
        # Create the slider
        self.slider_width = 4
        self.slider = self.canvas.create_line(
            window_width // 2, 0, window_width // 2, window_height,
            fill="#FFFFFF", width=self.slider_width
        )
        
        # Add slider handle for better visibility
        self.slider_handle_radius = 10
        self.slider_handle = self.canvas.create_oval(
            window_width // 2 - self.slider_handle_radius, 
            window_height // 2 - self.slider_handle_radius,
            window_width // 2 + self.slider_handle_radius, 
            window_height // 2 + self.slider_handle_radius,
            fill="#FFFFFF", outline="#000000", width=2
        )
        
        # Create a throttling mechanism for mouse movement
        self.last_update_time = 0
        self.update_interval = 1/60  # Target 60 FPS
        
        # Initially display both images with the slider in the middle
        self.display_split_view(window_width // 2)
        
        # Bring text to front to ensure it overlaps the images
        self.canvas.tag_raise(self.left_text)
        self.canvas.tag_raise(self.right_text)
        
        self.update_title()
        self.root.update_idletasks()

    def display_split_view(self, slider_x):
        """Display both images with a slider at the given x position"""
        if not hasattr(self, 'left_pil_img') or not hasattr(self, 'right_pil_img'):
            return
        
        window_width = self.canvas.winfo_width()
        window_height = self.canvas.winfo_height()
        
        # Move the slider to the current mouse position
        self.canvas.coords(self.slider, slider_x, 0, slider_x, window_height)
        self.canvas.coords(
            self.slider_handle,
            slider_x - self.slider_handle_radius, 
            window_height // 2 - self.slider_handle_radius,
            slider_x + self.slider_handle_radius, 
            window_height // 2 + self.slider_handle_radius
        )
        
        # Update text colors based on slider position
        # INVERTED: Highlight the text for the OPPOSITE image that would be chosen if clicked
        if slider_x < window_width // 2:
            # When slider is on the left side, highlight the RIGHT text (Image B)
            self.canvas.itemconfig(self.left_text, fill="#555555")
            self.canvas.itemconfig(self.right_text, fill="#FFFFFF")
        else:
            # When slider is on the right side, highlight the LEFT text (Image A)
            self.canvas.itemconfig(self.left_text, fill="#FFFFFF")
            self.canvas.itemconfig(self.right_text, fill="#555555")
        
        # Update the image
        self._update_split_image(slider_x)

    def on_mouse_move(self, event):
        """Move the slider to the left or right side when the mouse enters that side"""
        if not self.image_frame.winfo_viewable():
            return
            
        window_width = self.canvas.winfo_width()
        
        # Determine which side of the screen the mouse is on
        current_side = 'left' if event.x < window_width // 2 else 'right'
        
        # Update text colors immediately based on which side the cursor is on
        # This provides instant visual feedback even before the animation starts
        if current_side == 'left':
            # When cursor is on left side, highlight the RIGHT text (Image B)
            self.canvas.itemconfig(self.left_text, fill="#555555")
            self.canvas.itemconfig(self.right_text, fill="#FFFFFF")
        else:
            # When cursor is on right side, highlight the LEFT text (Image A)
            self.canvas.itemconfig(self.left_text, fill="#FFFFFF")
            self.canvas.itemconfig(self.right_text, fill="#555555")
        
        # Check if the side has changed
        side_changed = not hasattr(self, 'current_side') or current_side != self.current_side
        self.current_side = current_side
        
        # Set target position based on side
        target_x = 0 if current_side == 'left' else window_width
        
        # Always cancel any existing animation
        if hasattr(self, 'animation_id'):
            self.root.after_cancel(self.animation_id)
        
        # If the side has changed, clear animation variables to force a fresh start
        if side_changed:
            if hasattr(self, 'animation_start_time'):
                delattr(self, 'animation_start_time')
            if hasattr(self, 'animation_start_x'):
                delattr(self, 'animation_start_x')
            if hasattr(self, 'animation_target_x'):
                delattr(self, 'animation_target_x')
            if hasattr(self, 'animation_distance'):
                delattr(self, 'animation_distance')
        
        # Always start the animation to the target position
        self.animate_slider(target_x)

    def animate_slider(self, target_x, total_duration=500):
        """Smoothly animate the slider to the target position
        
        Uses a time-based approach to ensure the animation takes exactly 0.5 seconds (500ms)
        regardless of the distance the slider needs to travel.
        """
        # Check if the target has changed during animation
        if hasattr(self, 'animation_target_x') and self.animation_target_x != target_x:
            # Target changed - reset animation with current position as start
            slider_coords = self.canvas.coords(self.slider)
            start_x = slider_coords[0] if slider_coords else self.canvas.winfo_width() // 2
            
            self.animation_start_time = time.time()
            self.animation_start_x = start_x
            self.animation_target_x = target_x
            self.animation_distance = target_x - start_x
        # Initialize animation start time and position if this is the first call
        elif not hasattr(self, 'animation_start_time') or not hasattr(self, 'animation_start_x'):
            # Get current slider position
            slider_coords = self.canvas.coords(self.slider)
            start_x = slider_coords[0] if slider_coords else self.canvas.winfo_width() // 2
            
            self.animation_start_time = time.time()
            self.animation_start_x = start_x
            self.animation_target_x = target_x
            self.animation_distance = target_x - start_x
        
        # Calculate how much time has elapsed since animation started
        current_time = time.time()
        elapsed_time = (current_time - self.animation_start_time) * 1000  # Convert to ms
        
        # Calculate progress (0.0 to 1.0)
        progress = min(elapsed_time / total_duration, 1.0)
        
        # Use easing function for smoother animation (ease-out)
        # This makes the animation start fast and slow down at the end
        t = 1.0 - (1.0 - progress) * (1.0 - progress)  # Quadratic ease-out
        
        # Calculate current position
        current_x = self.animation_start_x + (self.animation_distance * t)
        
        # Update the display
        self.display_split_view(int(current_x))
        
        # Check if animation is complete
        if progress >= 1.0:
            # Animation complete - ensure we're exactly at the target
            self.display_split_view(self.animation_target_x)
            
            # Clean up animation variables
            delattr(self, 'animation_start_time')
            delattr(self, 'animation_start_x')
            delattr(self, 'animation_target_x')
            delattr(self, 'animation_distance')
            return
        
        # Schedule next frame (aim for 60fps - ~16.7ms per frame)
        self.animation_id = self.root.after(16, lambda: self.animate_slider(target_x, total_duration))

    def _delayed_update(self, x_pos):
        """Handle delayed updates for mouse movement throttling"""
        self.pending_update = False
        self.last_update_time = time.time()
        self._update_split_image(x_pos)

    def _update_split_image(self, slider_x):
        """Update only the composite image based on slider position"""
        if not hasattr(self, 'left_pil_img') or not hasattr(self, 'right_pil_img'):
            return
        
        # Delete previous composite image
        self.canvas.delete("composite")
        
        # Calculate the split position in image coordinates
        split_pos = slider_x - self.x_offset
        split_pos = max(0, min(split_pos, self.img_width))
        
        # Create a composite image
        composite = Image.new('RGB', (self.img_width, self.img_height))
        
        # Paste left image on the left side
        left_part = self.left_pil_img.crop((0, 0, split_pos, self.img_height))
        composite.paste(left_part, (0, 0))
        
        # Paste right image on the right side
        if split_pos < self.img_width:
            right_part = self.right_pil_img.crop((split_pos, 0, self.img_width, self.img_height))
            composite.paste(right_part, (split_pos, 0))
        
        # Convert to PhotoImage and display
        self.composite_img = ImageTk.PhotoImage(composite)
        self.canvas.create_image(self.x_offset, self.y_offset, anchor=tk.NW, image=self.composite_img, tags="composite")
        
        # Bring text and slider to front
        self.canvas.tag_raise(self.left_text)
        self.canvas.tag_raise(self.right_text)
        self.canvas.tag_raise(self.slider)
        self.canvas.tag_raise(self.slider_handle)

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
                
                # INVERTED LOGIC: When clicking on the left side, we want to choose the RIGHT image
                # When clicking on the right side, we want to choose the LEFT image
                if event.x < window_width / 2:
                    # User clicked on the left side of the screen - choose RIGHT image
                    self.last_chosen_side = 'left'
                    chosen_index = 1  # Second image in current_screen_images (right image)
                    print(f"User chose left side, selecting right image: {self.current_screen_images[chosen_index][0]}")
                else:
                    # User clicked on the right side of the screen - choose LEFT image
                    self.last_chosen_side = 'right'
                    chosen_index = 0  # First image in current_screen_images (left image)
                    print(f"User chose right side, selecting left image: {self.current_screen_images[chosen_index][0]}")
                
                # Get the chosen image data directly from current_screen_images
                chosen_folder, chosen_path = self.current_screen_images[chosen_index]
                
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
        self.group_winner = (chosen_folder, chosen_image_path)
        
        # Increment counters
        self.current_comparison += 1
        self.current_pair_index += 1
        self.comparisons_within_group += 1

        # Check if we've completed all comparisons in this group
        if self.comparisons_within_group >= len(self.current_group) - 1:
            # This was the last comparison in the group
            # Add a vote for the winning folder
            self.votes[chosen_folder] += 1
            print(f"Added vote for group winner: {chosen_folder}")
            
            # Move to the next group
            self.current_group_index += 1
            self.load_next_group()
        else:
            # Continue with the next comparison in this group
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

    def display_image(self, image_data):
        if image_data:
            img, folder, image_path = image_data
            window_width = self.canvas.winfo_width()
            window_height = self.canvas.winfo_height()
            
            x = (window_width - img.width()) // 2
            y = (window_height - img.height()) // 2
            
            self.canvas.delete("all")
            self.current_image = self.canvas.create_image(x, y, anchor=tk.NW, image=img)

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

    def show_results(self):
        result = "Results:\n"
        for folder, votes in self.votes.items():
            result += f"{os.path.basename(folder)}: {votes} votes\n"
        messagebox.showinfo("Comparison Complete", result)
        self.stop_comparison()

    def reset_comparison_state(self):
        """Reset the state of the comparison process."""
        self.current_comparison = 0
        self.current_group_index = 0
        self.group_winner = None
        self.current_screen_images = []
        self.screen_winner = None
        self.current_index = 0
        self.winner_position = None
        self.comparisons_within_group = 0
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

if __name__ == "__main__":
    tool = ImageBatchCompare()
    tool.run()
