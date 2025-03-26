import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torch
import torchvision.transforms as T
from torchvision.models.segmentation import deeplabv3_resnet101, DeepLabV3_ResNet101_Weights
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('agg')
import matplotlib.patches as mpatches

# Load the pre-trained DeepLabV3 model
model = deeplabv3_resnet101(weights=DeepLabV3_ResNet101_Weights.COCO_WITH_VOC_LABELS_V1).eval()

# Define the transformation for the input image
transform = T.Compose([
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def detect_land_types(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
        img_tensor = transform(img).unsqueeze(0)
        with torch.no_grad():
            output = model(img_tensor)['out'][0]
        output_predictions = output.argmax(0)

        # Define masks for different land types (adjust indices as needed)
        open_land_mask = (output_predictions == 0).byte().cpu().numpy() * 255
        green_land_mask = (output_predictions == 1).byte().cpu().numpy() * 255
        infrastructure_mask = (output_predictions == 2).byte().cpu().numpy() * 255

        return open_land_mask, green_land_mask, infrastructure_mask
    except Exception as e:
        print(f"Error in detect_land_types: {e}")
        return None, None, None

def calculate_area(mask):
    try:
        area = np.sum(mask == 255)
        return area
    except Exception as e:
        print(f"Error in calculate_area: {e}")
        return 0

def detect_roads(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
        img_tensor = transform(img).unsqueeze(0)
        with torch.no_grad():
            output = model(img_tensor)['out'][0]
        output_predictions = output.argmax(0)
        road_mask = (output_predictions == 0).byte().cpu().numpy() * 255
        return road_mask
    except Exception as e:
        print(f"Error in detect_roads: {e}")
        return None

def detect_changes(before_image_path, after_image_path):
    try:
        before_img = cv2.imread(before_image_path)
        after_img = cv2.imread(after_image_path)
        if before_img is None or after_img is None:
            print(f"Failed to load images: {before_image_path} or {after_image_path}")
            return None

        if before_img.shape != after_img.shape:
            after_img = cv2.resize(after_img, (before_img.shape[1], before_img.shape[0]))

        before_hsv = cv2.cvtColor(before_img, cv2.COLOR_BGR2HSV)
        after_hsv = cv2.cvtColor(after_img, cv2.COLOR_BGR2HSV)
        lower_green = np.array([35, 50, 50])
        upper_green = np.array([90, 255, 255])
        before_veg_mask = cv2.inRange(before_hsv, lower_green, upper_green)
        after_veg_mask = cv2.inRange(after_hsv, lower_green, upper_green)

        before_gray = cv2.cvtColor(before_img, cv2.COLOR_BGR2GRAY)
        after_gray = cv2.cvtColor(after_img, cv2.COLOR_BGR2GRAY)
        before_urban_mask = cv2.adaptiveThreshold(before_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        after_urban_mask = cv2.adaptiveThreshold(after_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        lower_blue = np.array([90, 50, 50])
        upper_blue = np.array([130, 255, 255])
        before_water_mask = cv2.inRange(before_hsv, lower_blue, upper_blue)
        after_water_mask = cv2.inRange(after_hsv, lower_blue, upper_blue)

        before_road_mask = detect_roads(before_image_path)
        after_road_mask = detect_roads(after_image_path)
        if before_road_mask is None or after_road_mask is None:
            print("Road detection failed")
            return None

        veg_change = cv2.bitwise_xor(before_veg_mask, after_veg_mask)
        urban_change = cv2.bitwise_xor(before_urban_mask, after_urban_mask)
        water_change = cv2.bitwise_xor(before_water_mask, after_water_mask)
        road_change = cv2.bitwise_xor(before_road_mask, after_road_mask)

        change_mask = np.zeros((before_img.shape[0], before_img.shape[1], 3), dtype=np.uint8)
        change_mask[veg_change > 0] = [0, 255, 0]
        change_mask[urban_change > 0] = [255, 0, 0]
        change_mask[water_change > 0] = [0, 0, 255]
        change_mask[road_change > 0] = [255, 255, 0]

        kernel = np.ones((3, 3), np.uint8)
        change_mask = cv2.morphologyEx(change_mask, cv2.MORPH_OPEN, kernel)
        change_mask = cv2.morphologyEx(change_mask, cv2.MORPH_CLOSE, kernel)
        return change_mask
    except Exception as e:
        print(f"Error in detect_changes: {e}")
        return None

def create_overlay_image(image_path, change_mask, output_path, alpha=0.5):
    try:
        if change_mask is None:
            print("Change mask is None, cannot create overlay")
            return None

        original = cv2.imread(image_path)
        if original is None:
            print(f"Failed to load image for overlay: {image_path}")
            return None

        overlay = original.copy()
        overlay = cv2.addWeighted(overlay, 1 - alpha, change_mask, alpha, 0)
        overlay_rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
        overlay_pil = Image.fromarray(overlay_rgb)
        draw = ImageDraw.Draw(overlay_pil)

        legend_height = 20
        legend_width = 150
        legend_margin = 10
        try:
            font = ImageFont.truetype("Arial", 12)
        except IOError:
            font = ImageFont.load_default()

        draw.rectangle(
            [(legend_margin, legend_margin),
             (legend_margin + legend_width, legend_margin + 3 * legend_height)],
            fill=(255, 255, 255, 180),
            outline=(0, 0, 0)
        )
        draw.rectangle([(legend_margin + 5, legend_margin + 5), (legend_margin + 15, legend_margin + 15)], fill=(0, 255, 0))
        draw.text((legend_margin + 20, legend_margin + 2), "Vegetation", font=font, fill=(0, 0, 0))
        draw.rectangle([(legend_margin + 5, legend_margin + legend_height + 5), (legend_margin + 15, legend_margin + legend_height + 15)], fill=(255, 0, 0))
        draw.text((legend_margin + 20, legend_margin + legend_height + 2), "Urban", font=font, fill=(0, 0, 0))
        draw.rectangle([(legend_margin + 5, legend_margin + 2 * legend_height + 5), (legend_margin + 15, legend_margin + 2 * legend_height + 15)], fill=(0, 0, 255))
        draw.text((legend_margin + 20, legend_margin + 2 * legend_height + 2), "Water", font=font, fill=(0, 0, 0))

        overlay = cv2.cvtColor(np.array(overlay_pil), cv2.COLOR_RGB2BGR)
        cv2.imwrite(output_path, overlay)
        print(f"Overlay saved to {output_path}")
        return output_path
    except Exception as e:
        print(f"Error in create_overlay_image: {e}")
        return None

def generate_change_visualization(before_path, after_path, output_path):
    try:
        before_img = cv2.imread(before_path)
        after_img = cv2.imread(after_path)
        if before_img is None or after_img is None:
            print(f"Failed to load images: {before_path} or {after_path}")
            return None

        before_rgb = cv2.cvtColor(before_img, cv2.COLOR_BGR2RGB)
        after_rgb = cv2.cvtColor(after_img, cv2.COLOR_BGR2RGB)
        change_mask = detect_changes(before_path, after_path)
        if change_mask is None:
            print("Change detection failed")
            return None

        change_mask_rgb = cv2.cvtColor(change_mask, cv2.COLOR_BGR2RGB)
        plt.figure(figsize=(15, 5))
        plt.subplot(1, 3, 1)
        plt.imshow(before_rgb)
        plt.title('Before')
        plt.axis('off')
        plt.subplot(1, 3, 2)
        plt.imshow(after_rgb)
        plt.title('After')
        plt.axis('off')
        plt.subplot(1, 3, 3)
        alpha = 0.7
        blended = cv2.addWeighted(after_rgb, 1 - alpha, change_mask_rgb, alpha, 0)
        plt.imshow(blended)
        plt.title('Change Analysis')
        plt.axis('off')

        legend_elements = [
            mpatches.Patch(color='green', label='Vegetation'),
            mpatches.Patch(color='red', label='Urban'),
            mpatches.Patch(color='blue', label='Water')
        ]
        plt.legend(handles=legend_elements, loc='lower right')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Change visualization saved to {output_path}")
        return output_path
    except Exception as e:
        print(f"Error in generate_change_visualization: {e}")
        return None