# Image Batch Compare

A tool that compares sets of images to identify the best group of images.

## Overview

If you've done AI image generation before, it can be difficult to tell if the small prompt adjustments you're making actually improve the quality of the prompt.

It's common to end up squinting at two images side by side, playing spot-the-difference and struggling. Even when you do identify the better image, a single comparison isn't enough - you need dozens to determine if the improvements are real and consistent or whether it was just random variation. And can you be sure your judgment wasn't biased?

## What This Tool Does

- Lets you switch between images quickly to see differences
- Hides which folder images come from to avoid bias
- Runs many comparisons and keeps track of score

## Instructions

1. Prepare your image sets for comparison:
   - Create separate folders for each set of images you want to compare
   - For fair comparison, use the same seeds across different sets
   - Example:
     - Folder 1: Contains images with seeds 0-9 using Prompt Variation A
     - Folder 2: Contains images with seeds 0-9 using Prompt Variation B
   
   - Another Example:
     - Folder 1: Contains images with seeds 0-24 using Checkpoint A
     - Folder 2: Contains images with seeds 0-24 using Checkpoint B
     - Folder 3: Contains images with seeds 0-24 using Checkpoint C
     - Folder 4: Contains images with seeds 0-24 using Checkpoint D
   
   Each group of images needs their own folder and each folder must have the same number of images in it. Some example folders have been included.

2. Add these folders to the application
3. Start the comparison process
4. For each pair of images shown, select the one you prefer
5. At the end, see which folder had the most winning images

## Getting Started

1. Clone this repository
2. Run `python image-batch-compare.py`
3. Add folders containing images to compare
4. Click "Start Comparison" to begin

## Requirements

- Python 3.x
- Tkinter
- Pillow (PIL)
- tkinterdnd2

## License

[MIT License](LICENSE)
