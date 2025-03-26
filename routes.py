from flask import jsonify, request, send_file, send_from_directory
from utils import create_static_folder, create_gif, create_video  # Assumed imports
from sentinel import fetch_satellite_images  # Assumed import
from image_processing import detect_changes, create_overlay_image, generate_change_visualization
from report_generation import generate_pdf_report
import os
from datetime import datetime
import simplekml

def init_routes(app):
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory('static', filename)

    @app.route('/get_images', methods=["POST"])
    def get_images():
        data = request.json
        polygon = data.get("polygon")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        if not polygon or not start_date or not end_date:
            return jsonify({"error": "Missing required parameters"}), 400

        folder_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        folder_path = os.path.join("static", folder_timestamp)
        os.makedirs(folder_path, exist_ok=True)

        image_filenames = fetch_satellite_images(polygon, start_date, end_date, folder_path)
        additional_files = {
            "timelapse_gif": os.path.exists(os.path.join(folder_path, "timelapse.gif")),
            "timelapse_video": os.path.exists(os.path.join(folder_path, "timelapse.mp4")),
            "kml": os.path.exists(os.path.join(folder_path, "polygon.kml"))
        }

        if image_filenames:
            image_urls = [f"/static/{folder_timestamp}/{img}" for img in image_filenames]
            return jsonify({
                "images": image_filenames,
                "image_urls": image_urls,
                "folder_name": folder_timestamp,
                "additional_files": additional_files
            })
        return jsonify({"error": "No clear images found", "additional_files": additional_files}), 404

    @app.route("/generate_timelapse", methods=["POST"])
    def generate_timelapse():
        data = request.json
        polygon = data.get("polygon")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        existing_images = data.get("existing_images")
        folder_name = data.get("folder_name")

        if not polygon or not start_date or not end_date:
            return jsonify({"error": "Missing required parameters"}), 400

        folder_path = os.path.join("static", folder_name or datetime.now().strftime("%Y%m%d%H%M%S"))
        os.makedirs(folder_path, exist_ok=True)

        image_filenames = existing_images or fetch_satellite_images(polygon, start_date, end_date, folder_path)
        if not image_filenames:
            return jsonify({"error": "No clear images found for timelapse"}), 404

        gif_path = create_gif(image_filenames, folder_path)
        if gif_path and os.path.exists(gif_path):
            folder_name = os.path.basename(folder_path)
            return jsonify({"success": True, "gif_url": f"/static/{folder_name}/timelapse.gif"})
        return jsonify({"error": "Failed to create"})

        return jsonify({"error": "Failed to create timelapse"}), 500

    @app.route("/generate_video", methods=["POST"])
    def generate_video():
        data = request.json
        polygon = data.get("polygon")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        existing_images = data.get("existing_images")
        folder_name = data.get("folder_name")
        fps = data.get("fps", 2)

        if not polygon or not start_date or not end_date:
            return jsonify({"error": "Missing required parameters"}), 400

        folder_path = os.path.join("static", folder_name or datetime.now().strftime("%Y%m%d%H%M%S"))
        os.makedirs(folder_path, exist_ok=True)

        image_filenames = existing_images or fetch_satellite_images(polygon, start_date, end_date, folder_path)
        if not image_filenames:
            return jsonify({"error": "No clear images found for video"}), 404

        video_path = create_video(image_filenames, folder_path, fps=fps)
        if video_path and os.path.exists(video_path):
            folder_name = os.path.basename(folder_path)
            return jsonify({"success": True, "video_url": f"/static/{folder_name}/timelapse.mp4"})
        return jsonify({"error": "Failed to create video"}), 500

    @app.route("/download_media", methods=["GET"])
    def download_media():
        media_type = request.args.get("type", "gif")
        folder_name = request.args.get("folder_name")
        if not folder_name:
            return jsonify({"error": "Missing folder name"}), 400

        folder_path = os.path.join("static", folder_name)
        if media_type == "gif":
            file_path = os.path.join(folder_path, "timelapse.gif")
            mimetype = "image/gif"
            filename = "satellite_timelapse.gif"
        elif media_type == "video":
            file_path = os.path.join(folder_path, "timelapse.mp4")
            mimetype = "video/mp4"
            filename = "satellite_timelapse.mp4"
        else:
            return jsonify({"error": "Invalid media type"}), 400

        if not os.path.exists(file_path):
            return jsonify({"error": f"No {media_type} file found"}), 404

        return send_file(file_path, mimetype=mimetype, as_attachment=True, download_name=filename)

    @app.route("/download_kml", methods=["POST"])
    def download_kml():
        data = request.json
        polygon_coords = data.get("polygon")
        folder_name = data.get("folder_name")

        if not polygon_coords:
            return jsonify({"error": "Missing polygon coordinates"}), 400

        folder_path = os.path.join("static", folder_name or datetime.now().strftime("%Y%m%d%H%M%S"))
        os.makedirs(folder_path, exist_ok=True)

        try:
            kml = simplekml.Kml()
            pol = kml.newpolygon(name="Selected Area")
            kml_coords = [(coord[0], coord[1]) for coord in polygon_coords[0]]
            pol.outerboundaryis = kml_coords
            kml_path = os.path.join(folder_path, "polygon.kml")
            kml.save(kml_path)
            return send_file(kml_path, as_attachment=True, download_name="polygon.kml")
        except Exception as e:
            print(f"Error creating KML: {e}")
            return jsonify({"error": "Failed to create KML"}), 500

    @app.route("/list_existing_images", methods=["GET"])
    def list_existing_images():
        try:
            static_dirs = [d for d in os.listdir("static")
                          if os.path.isdir(os.path.join("static", d))
                          and d.isdigit() and len(d) == 14]
            static_dirs.sort(reverse=True)

            all_images = []
            folder_name = None
            additional_files = {"timelapse_gif": False, "timelapse_video": False, "kml": False}

            if static_dirs:
                folder_name = static_dirs[0]
                folder_path = os.path.join("static", folder_name)
                image_files = [f for f in os.listdir(folder_path) if f.endswith('.png')]
                image_files.sort()
                additional_files = {
                    "timelapse_gif": os.path.exists(os.path.join(folder_path, "timelapse.gif")),
                    "timelapse_video": os.path.exists(os.path.join(folder_path, "timelapse.mp4")),
                    "kml": os.path.exists(os.path.join(folder_path, "polygon.kml"))
                }
                all_images = image_files
            else:
                image_files = [f for f in os.listdir("static") if f.endswith('.png')]
                image_files.sort()
                additional_files = {
                    "timelapse_gif": os.path.exists(os.path.join("static", "timelapse.gif")),
                    "timelapse_video": os.path.exists(os.path.join("static", "timelapse.mp4")),
                    "kml": os.path.exists(os.path.join("static", "polygon.kml"))
                }
                all_images = image_files

            return jsonify({
                "images": all_images,
                "folder_name": folder_name,
                "additional_files": additional_files
            })
        except Exception as e:
            print(f"Error listing existing images: {e}")
            return jsonify({"error": "Failed to list existing images"}), 500

    @app.route("/generate_report", methods=["POST"])
    def generate_report():
        data = request.json
        polygon = data.get("polygon")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        existing_images = data.get("existing_images")
        folder_name = data.get("folder_name")

        if not polygon or not start_date or not end_date:
            return jsonify({"error": "Missing required parameters"}), 400

        folder_path = os.path.join("static", folder_name or datetime.now().strftime("%Y%m%d%H%M%S"))
        os.makedirs(folder_path, exist_ok=True)

        image_filenames = existing_images or fetch_satellite_images(polygon, start_date, end_date, folder_path)
        print(f"Generating report with {len(image_filenames)} images")
        
        if not image_filenames or len(image_filenames) < 4:
            return jsonify({"error": "Not enough images found for change analysis (minimum 4 required)"}), 404

        report_path = generate_pdf_report(image_filenames, polygon, start_date, end_date, folder_path)
        if report_path and os.path.exists(report_path):
            return send_file(
                report_path,
                mimetype="application/pdf",
                as_attachment=True,
                download_name="satellite_change_report.pdf"
            )
        print("Report generation failed")
        return jsonify({"error": "Failed to generate report"}), 500

    @app.route("/download_report", methods=["GET"])
    def download_report():
        folder_name = request.args.get("folder_name")
        if not folder_name:
            return jsonify({"error": "Missing folder name"}), 400

        folder_path = os.path.join("static", folder_name)
        report_path = os.path.join(folder_path, "satellite_report.pdf")
        if not os.path.exists(report_path):
            return jsonify({"error": "Report not found"}), 404

        return send_file(
            report_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="satellite_change_report.pdf"
        )