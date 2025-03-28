# Image Batch Compare

A simple tool that compares sets of images to determine the best group of images.

https://github.com/user-attachments/assets/56b6959d-845e-41f5-997b-31df7aacb95f

## Overview

If you do local image generation it can be difficult to tell if the small adjustments you're making actually improve the quality of the output, it's common to end up squinting at two images side by side playing spot-the-difference. Even when you do choose the better image, a single comparison is rarely enough - you need dozens to be sure the improvements are real and consistent or whether you're being misled by random seed variation. And your judgement may also be affected by subconscious bias.

## What This Tool Does

- Select multiple folders containing images to compare against each other to determine the best folder
- Quickly switches between a pair of images by simply moving the mouse left or right
- Hides which folder images come from to avoid bias
- Keeps track of score and saves it to a text file at the end

## Instructions

1. Prepare your image sets for comparison:
   - Create separate folders for each group of images you want to compare
   - For fair comparison, use the same seeds across different sets
   - Example:
     - Folder 1: Contains images with seeds 0 to 14 using Prompt Variation A
     - Folder 2: Contains images with seeds 0 to 14 using Prompt Variation B
   
   - Another Example:
     - Folder 1: Contains images with seeds 0 to 9 using Checkpoint A
     - Folder 2: Contains images with seeds 0 to 9 using Checkpoint B
     - Folder 3: Contains images with seeds 0 to 9 using Checkpoint C
     - Folder 4: Contains images with seeds 0 to 9 using Checkpoint D
   
   Each group of images needs their own folder and each folder must have the same number of images in it. An example of this has been included in the `/Example/` directory.

2. Add your chosen folders to the application. You can also drag folders into the window and right click on a path to quickly remove it
3. Click "Start Comparison"
4. For each pair of images shown, select the one you prefer
5. At the end, you will be shown which folder had the most winning images

## Installation

### Windows
- **Without Python**: Download the [latest release](https://github.com/rainlizard/ImageBatchCompare/releases) and run the executable.
- **Or with Python**: Clone the source code and run `start.bat`

### Linux
Untested but probably compatible if you launch the Python file:
```bash
pip install -r requirements.txt
python image-batch-compare.py
```

## License

[MIT License](LICENSE)
