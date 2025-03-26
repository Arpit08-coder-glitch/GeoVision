# Satellite Imagery Analysis and Visualization App

## Overview
This Flask application enables users to analyze and visualize satellite imagery over a specified area and time range. It provides functionalities to:
- Fetch satellite images
- Generate timelapse GIFs and videos
- Create PDF reports
- Download shapefiles and KML files
- Interact with an intuitive map interface for selecting areas of interest

## Features
- Fetch Sentinel-2 satellite images using user-specified date ranges and polygon coordinates.
- Generate timelapse GIFs and videos from the fetched images.
- Create detailed PDF reports highlighting vegetation changes, urban development, and water bodies.
- Download geospatial data in the form of shapefiles and KML files.
- Utilize an interactive map interface for selecting areas of interest.

## Installation

### Prerequisites
Ensure you have the following installed on your system:
- Python 3.x
- Node.js (for frontend dependencies)

### Steps
1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/satellite-imagery-app.git
   cd satellite-imagery-app
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install required Python packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies:**
   ```bash
   npm install
   ```

5. **Set up environment variables:**
   - Create a `.env` file in the root directory and add your Sentinel API credentials:
   ```ini
   CLIENT_ID=your_sentinel_client_id
   CLIENT_SECRET=your_sentinel_client_secret
   ```

## Running the Application

1. **Start the Flask server:**
   ```bash
   flask run
   ```
2. **Open the application in your browser:**
   ```
   http://127.0.0.1:5000
   ```

## Usage

### Select an Area on the Map
- Use the interactive map to draw a polygon or rectangle over the area of interest.

### Set the Date Range
- Specify the start and end dates for fetching satellite images.

### Fetch Images
- Click the **"Get Images"** button to retrieve satellite images for the selected area and date range.

### Generate Timelapse GIF/Video
- Click **"Generate Timelapse GIF"** or **"Generate Video"** to create a timelapse visualization.

### Create PDF Report
- Click **"Generate PDF Report"** to generate an analytical report based on the satellite imagery.

### Download Shapefile/KML
- Use the **"Download Shapefile"** or **"Download KML"** buttons to download geospatial data.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/get_images` | Fetch satellite images based on polygon coordinates and date range |
| `/generate_timelapse` | Generate a timelapse GIF from the fetched images |
| `/generate_video` | Generate a timelapse video from the fetched images |
| `/generate_report` | Generate a PDF report analyzing the satellite images |
| `/download_shapefile` | Download the selected area as a shapefile |
| `/download_kml` | Download the selected area as a KML file |
| `/download_media` | Download generated media files (GIF, video, PDF) |

## Technologies Used
- **Backend:** Flask, Flask-CORS, Sentinel API
- **Frontend:** HTML, CSS, JavaScript, Leaflet.js, jQuery
- **Image Processing:** OpenCV, PIL, imageio
- **PDF Generation:** ReportLab
- **Data Visualization:** Matplotlib

## Contributing
1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-branch
   ```
3. Commit your changes:
   ```bash
   git commit -am 'Add new feature'
   ```
4. Push to the branch:
   ```bash
   git push origin feature-branch
   ```
5. Create a pull request.

## License
This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Acknowledgments
- **Sentinel-2** for providing high-quality satellite imagery.
- **Flask and Flask-CORS** for simplifying backend development.
- **Leaflet.js** for the interactive map interface.

