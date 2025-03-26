import requests
from config import CLIENT_ID, CLIENT_SECRET
from utils import is_black_image, apply_image_adjustments
from datetime import datetime, timedelta
import os
import random

def get_sentinel_token():
    token_url = "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"
    data = {"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token = response.json().get("access_token")
        print("✅ Token fetched successfully")
        return token
    except requests.exceptions.RequestException as e:
        print(f"❌ Token fetch error: {e}")
        return None

def fetch_satellite_images(polygon_coords, start_date, end_date, folder_name):
    token = get_sentinel_token()
    if not token:
        print("❌ Token not available!")
        return []
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    images = []
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    delta_months = (end_date_obj.year - start_date_obj.year) * 12 + (end_date_obj.month - start_date_obj.month)
    periods_to_fetch = []
    if delta_months > 4:
        print(f"🔍 Long time period detected ({delta_months} months). Optimizing image fetching.")
        middle_date = start_date_obj + (end_date_obj - start_date_obj) / 2
        beginning_start = start_date_obj
        beginning_end = beginning_start + timedelta(days=30)
        middle_start = middle_date - timedelta(days=15)
        middle_end = middle_date + timedelta(days=15)
        end_start = end_date_obj - timedelta(days=30)
        end_end = end_date_obj
        periods_to_fetch = [
            (beginning_start, beginning_end, "beginning"),
            (middle_start, middle_end, "middle"),
            (end_start, end_end, "end")
        ]
        print(f"📅 Fetching images from: Beginning ({beginning_start.strftime('%Y-%m-%d')} to {beginning_end.strftime('%Y-%m-%d')})")
        print(f"📅 Fetching images from: Middle ({middle_start.strftime('%Y-%m-%d')} to {middle_end.strftime('%Y-%m-%d')})")
        print(f"📅 Fetching images from: End ({end_start.strftime('%Y-%m-%d')} to {end_end.strftime('%Y-%m-%d')})")
    else:
        periods_to_fetch = [(start_date_obj, end_date_obj, "full")]
        print(f"📅 Fetching images from entire period: {start_date} to {end_date}")
    for period_start, period_end, period_type in periods_to_fetch:
        current_date = period_start
        if period_type == "full":
            sampling_days = 3
        else:
            sampling_days = 2
        max_images_per_period = 4
        images_fetched_in_period = 0
        while current_date <= period_end and images_fetched_in_period < max_images_per_period:
            date_str = current_date.strftime("%Y-%m-%d")
            print(f"🔍 Trying to fetch image for: {date_str} (period: {period_type})")
            payload = {
                "input": {
                    "bounds": {"geometry": {"type": "Polygon", "coordinates": polygon_coords}},
                    "data": [
                        {
                            "type": "sentinel-2-l2a",
                            "dataFilter": {
                                "timeRange": {"from": f"{date_str}T00:00:00Z", "to": f"{date_str}T23:59:59Z"},
                                "maxCloudCoverage": 10
                            }
                        }
                    ]
                },
                "output": {"width": 512, "height": 512, "format": "png"},
                "evalscript": """
                    function setup() {
                        return {
                            input: ["B04", "B03", "B02"],
                            output: { bands: 3, sampleType: "UINT8" }
                        };
                    }
                    function evaluatePixel(sample) {
                        return [
                            sample.B04 * 255,
                            sample.B03 * 255,
                            sample.B02 * 255
                        ];
                    }
                """
            }
            try:
                response = requests.post("https://services.sentinel-hub.com/api/v1/process", headers=headers, json=payload)
                response.raise_for_status()
                img_filename = f"{date_str}.png"
                img_path = os.path.join(folder_name, img_filename)
                with open(img_path, "wb") as img_file:
                    img_file.write(response.content)
                if is_black_image(img_path):
                    print(f"⚠️ Black image detected for {date_str}, skipping...")
                    os.remove(img_path)
                    current_date += timedelta(days=1)
                    continue
                apply_image_adjustments(img_path)
                images.append(img_filename)
                print(f"✅ Image saved: {img_path}")
                images_fetched_in_period += 1
                current_date += timedelta(days=sampling_days)
            except requests.exceptions.RequestException as e:
                print(f"❌ API Error for {date_str}: {e}")
                current_date += timedelta(days=1)
    if len(images) < 4:
        print(f"⚠️ Only fetched {len(images)} images. Attempting to fill gaps...")
        additional_attempts = 0
        max_additional_attempts = 10
        while len(images) < 4 and additional_attempts < max_additional_attempts:
            random_days = random.randint(0, (end_date_obj - start_date_obj).days)
            random_date = start_date_obj + timedelta(days=random_days)
            date_str = random_date.strftime("%Y-%m-%d")
            if f"{date_str}.png" in images:
                additional_attempts += 1
                continue
            print(f"🔍 Attempting to fetch additional image for: {date_str}")
            payload = {
                "input": {
                    "bounds": {"geometry": {"type": "Polygon", "coordinates": polygon_coords}},
                    "data": [
                        {
                            "type": "sentinel-2-l2a",
                            "dataFilter": {
                                "timeRange": {"from": f"{date_str}T00:00:00Z", "to": f"{date_str}T23:59:59Z"},
                                "maxCloudCoverage": 15
                            }
                        }
                    ]
                },
                "output": {"width": 512, "height": 512, "format": "png"},
                "evalscript": """
                    function setup() {
                        return {
                            input: ["B04", "B03", "B02"],
                            output: { bands: 3, sampleType: "UINT8" }
                        };
                    }
                    function evaluatePixel(sample) {
                        return [
                            sample.B04 * 255,
                            sample.B03 * 255,
                            sample.B02 * 255
                        ];
                    }
                """
            }
            try:
                response = requests.post("https://services.sentinel-hub.com/api/v1/process", headers=headers, json=payload)
                response.raise_for_status()
                img_filename = f"{date_str}.png"
                img_path = os.path.join(folder_name, img_filename)
                with open(img_path, "wb") as img_file:
                    img_file.write(response.content)
                if not is_black_image(img_path):
                    apply_image_adjustments(img_path)
                    images.append(img_filename)
                    print(f"✅ Additional image saved: {img_path}")
                else:
                    print(f"⚠️ Black image detected for {date_str}, skipping...")
                    os.remove(img_path)
            except:
                print(f"❌ Failed to fetch additional image for {date_str}")
            additional_attempts += 1
    images.sort()
    print(f"📊 Total images fetched: {len(images)}")
    return images
