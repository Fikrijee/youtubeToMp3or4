import os
import uuid
import logging
from flask import Flask, request, send_file, jsonify, url_for, send_from_directory
import yt_dlp

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[logging.FileHandler('converter.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder='static', static_url_path='')

# Setup download folder
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

def get_mp4_download_options(unique_id):
    return {
        'format': 'best[ext=mp4]/best',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, f"{unique_id}.%(ext)s"),
        'retries': 10,
        'fragment_retries': 10,
        'extractor_retries': 3,
        'concurrent_fragment_downloads': 4,
        'http_chunk_size': 1048576,
        'noplaylist': True,
        'merge_output_format': 'mp4',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4'
        }],
        'postprocessor_args': ['-movflags', '+faststart'],
        'verbose': True
    }

def get_mp3_download_options(unique_id):
    return {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, f"{unique_id}.%(ext)s"),
        'retries': 10,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

@app.route('/download', methods=['POST', 'OPTIONS'])
def download():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        url = data.get('url')
        format_type = data.get('format', 'mp4').lower()

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        unique_id = str(uuid.uuid4())
        ydl_opts = get_mp4_download_options(unique_id) if format_type == 'mp4' else get_mp3_download_options(unique_id)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if format_type == 'mp3':
                final_filename = filename.rsplit('.', 1)[0] + '.mp3'
            else:
                final_filename = filename

        if not os.path.exists(final_filename):
            return jsonify({'error': 'File not found after download'}), 404

        download_url = url_for('serve_file', filename=os.path.basename(final_filename), _external=True)
        return jsonify({'download_url': download_url})

    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/file/<filename>')
def serve_file(filename):
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return "File not found", 404

    ext = os.path.splitext(filename)[-1].lower()
    mimetype = 'video/mp4' if ext == '.mp4' else 'audio/mpeg'
    return send_file(filepath, as_attachment=True, download_name=filename, mimetype=mimetype)

# Serve React App (this part is added for frontend)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
