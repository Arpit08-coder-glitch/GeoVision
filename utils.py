import os
import requests
import imageio
import numpy as np
import cv2
from datetime import datetime, timedelta
import tempfile
import zipfile
import fiona
import fiona.crs
import simplekml
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image as ReportLabImage, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as mpatches
import random

def create_static_folder():
    os.makedirs("static", exist_ok=True)

def is_black_image(image_path):
    image = imageio.imread(image_path)
    return np.all(image == 0)

def apply_image_adjustments(image_path):
    img = Image.open(image_path)
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.5)
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.8)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(0.88)
    img_cv = np.array(img)
    lab = cv2.cvtColor(img_cv, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.add(l, 50)
    lab = cv2.merge((l, a, b))
    img_cv = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    img = Image.fromarray(img_cv)
    img.save(image_path)

def create_gif(image_filenames, folder_name, output_path="timelapse.gif"):
    if not image_filenames:
        print("❌ No images to create a GIF!")
        return None
    image_paths = [os.path.join(folder_name, img) for img in image_filenames]
    for path in image_paths:
        if not os.path.exists(path):
            print(f"❌ Missing image: {path}")
            return None
    try:
        images = [imageio.imread(img) for img in image_paths]
        imageio.mimsave(output_path, images, duration=0.5, loop=0)
        print(f"🎥 GIF created: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Error creating GIF: {e}")
        return None

def create_video(image_filenames, folder_name, output_path="timelapse.mp4", fps=2):
    if not image_filenames:
        print("❌ No images to create a video!")
        return None
    image_paths = [os.path.join(folder_name, img) for img in image_filenames]
    for path in image_paths:
        if not os.path.exists(path):
            print(f"❌ Missing image: {path}")
            return None
    try:
        first_img = cv2.imread(image_paths[0])
        height, width, layers = first_img.shape
        size = (width, height)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, size)
        for img_path in image_paths:
            img = cv2.imread(img_path)
            out.write(img)
            for _ in range(3):
                out.write(img)
        out.release()
        print(f"🎥 Video created: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Error creating video: {e}")
        return None
