from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
from uuid import uuid4

app = Flask(__name__)

# Directory to save downloaded videos
download_dir = "downloads"
os.makedirs(download_dir, exist_ok=True)

@app.route('/')
def hi():
    return ('85665667676576576576576576576576')

@app.route('/download', methods=['POST'])
def download_video():
    try:
        data = request.json
        url = data.get('url')
        resolution = data.get('resolution')

        if not url:
            return jsonify({"error": "No URL provided."}), 400

        if not resolution:
            return jsonify({"error": "No resolution provided."}), 400

        # yt-dlp options to fetch video formats
        ydl_opts = {"quiet": True, "extract_flat": False}
        selected_format = None

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])

            for fmt in formats:
                if fmt.get('height') and f"{fmt['height']}p" == resolution:
                    selected_format = fmt
                    break

        if not selected_format:
            return jsonify({"error": f"Resolution {resolution} not available."}), 400

        # Generate a unique filename
        unique_id = str(uuid4())
        filename = os.path.join(download_dir, f"{unique_id}.mp4")

        # yt-dlp options for downloading the selected format
        ydl_opts = {
            'format': selected_format['format_id'],
            'outtmpl': filename,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return jsonify({"message": "Download successful.", "file": filename}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/audio_file_details', methods=['POST'])
def audio_file_details():
    try:
        data = request.json
        url = data.get('url')
        if not url:
            return jsonify({"error": "No URL provided."}), 400

        audio_formats = []

        # yt-dlp options to fetch audio formats
        ydl_opts = {"quiet": True, "extract_flat": False}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])

            # Check for MP3 formats
            for fmt in formats:
                if fmt.get('vcodec') == 'none' and fmt.get('ext') == 'mp3':
                    size = fmt.get('filesize') or 0  # Fallback if filesize is not available
                    audio_formats.append({
                        "format": "mp3",
                        "size_mb": round(size / (1024 * 1024), 2) if size > 0 else "Unknown"
                    })

            # If no MP3 formats, check for M4A
            if not audio_formats:
                for fmt in formats:
                    if fmt.get('vcodec') == 'none' and fmt.get('ext') == 'm4a':
                        size = fmt.get('filesize') or 0
                        audio_formats.append({
                            "format": "m4a",
                            "size_mb": round(size / (1024 * 1024), 2) if size > 0 else "Unknown"
                        })

        # If no audio formats are available
        if not audio_formats:
            return jsonify({"message": "No suitable audio formats found."}), 400

        return jsonify(audio_formats), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/audio_download', methods=['POST'])
def audio_download():
    try:
        data = request.json
        url = data.get('url')
        audio_format = data.get('audio_format')

        if not url:
            return jsonify({"error": "No URL provided."}), 400

        if not audio_format:
            return jsonify({"error": "No audio format provided."}), 400

        # yt-dlp options to fetch audio formats
        ydl_opts = {"quiet": True, "extract_flat": False}
        selected_format = None

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])

            for fmt in formats:
                if fmt.get('vcodec') == 'none' and fmt.get('ext') == audio_format:
                    selected_format = fmt
                    break

        if not selected_format:
            return jsonify({"error": f"Audio format {audio_format} not available."}), 400

        # Generate a unique filename
        unique_id = str(uuid4())
        raw_filename = os.path.join(download_dir, f"{unique_id}.{audio_format}")
        final_filename = os.path.join(download_dir, f"{unique_id}.mp3")

        # yt-dlp options for downloading the selected format
        ydl_opts = {
            'format': selected_format['format_id'],
            'outtmpl': raw_filename
        }

        # Download the audio file
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Convert M4A to MP3 if necessary
        if audio_format == 'm4a':
            conversion_command = f"ffmpeg -i {raw_filename} -vn -ar 44100 -ac 2 -b:a 192k {final_filename} -y"
            os.system(conversion_command)
            os.remove(raw_filename)  # Remove the original M4A file
        else:
            final_filename = raw_filename

        return jsonify({"message": "Download successful.", "file": final_filename}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


        # Download the audio file
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return jsonify({"message": "Download successful.", "file": filename}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_video/<filename>', methods=['GET'])
def get_video(filename):
    filepath = os.path.join(download_dir, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found."}), 404

    return send_file(filepath, as_attachment=True)

@app.route('/get_audio/<filename>', methods=['GET'])
def get_audio(filename):
    filepath = os.path.join(download_dir, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found."}), 404

    return send_file(filepath, as_attachment=True)

@app.route('/cleanup', methods=['DELETE'])
def cleanup_download():
    try:
        filename = request.args.get('filename')
        if not filename:
            return jsonify({"error": "No filename provided."}), 400

        file_path = os.path.join(download_dir, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            os.unlink(file_path)
            return jsonify({"message": f"File {filename} has been deleted."}), 200
        else:
            return jsonify({"error": "File not found."}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/list_videos', methods=['POST'])
def list_videos():
    try:
        data = request.json
        url = data.get('url')
        if not url:
            return jsonify({"error": "No URL provided."}), 400

        resolutions = set()
        videos = []

        # yt-dlp options to fetch video formats
        ydl_opts = {
            "quiet": True,
            "extract_flat": False
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])

            for fmt in formats:
                resolution = fmt.get('height')
                size = fmt.get('filesize') or 0  # Fallback if filesize is not available

                if resolution and resolution not in resolutions:
                    resolutions.add(resolution)
                    videos.append({
                        "resolution": f"{resolution}p",
                        "size_mb": round(size / (1024 * 1024), 2) if size > 0 else "Unknown"
                    })

        return jsonify(videos), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
