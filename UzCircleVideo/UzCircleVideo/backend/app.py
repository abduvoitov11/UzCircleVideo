import os
import subprocess
import uuid
import shutil
from flask import Flask, request, send_file, jsonify, abort

app = Flask(__name__)
UPLOAD_DIR = "/tmp/uzcircle_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_SECONDS = 120  # 2 minutes

def get_duration(path):
    try:
        res = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15
        )
        return float(res.stdout.strip())
    except Exception:
        return None

@app.route("/health", methods=["GET"])
def health():
    return "ok"

@app.route("/process", methods=["POST"])
def process():
    if 'file' not in request.files:
        return jsonify({"error":"No file part"}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({"error":"No selected file"}), 400

    # save input
    uid = uuid.uuid4().hex
    in_path = os.path.join(UPLOAD_DIR, f"{uid}_input")
    out_path = os.path.join(UPLOAD_DIR, f"{uid}_output.webm")
    f.save(in_path)

    # check duration
    duration = get_duration(in_path)
    if duration is None:
        # cleanup
        try:
            os.remove(in_path)
        except: pass
        return jsonify({"error":"Could not read video duration"}), 400
    if duration > MAX_SECONDS:
        try:
            os.remove(in_path)
        except: pass
        return jsonify({"error":"Video longer than 2 minutes (120s)"}), 400

    # run ffmpeg to create circular alpha webm (720x720)
    # command builds a circular mask and merges alpha, encodes with vp9 (libvpx-vp9) and opus audio
    cmd = [
        "ffmpeg", "-y", "-i", in_path,
        "-filter_complex",
        "[0:v]format=rgba,crop='min(iw,ih)':'min(iw,ih)':(iw-min(iw,ih))/2:(ih-min(iw,ih))/2,scale=720:720,geq='if(lte(hypot(X-360,Y-360),360),255,0)':128:128:128[mask];"
        "[0:v]format=rgba,crop='min(iw,ih)':'min(iw,ih)':(iw-min(iw,ih))/2:(ih-min(iw,ih))/2,scale=720:720[sq];"
        "[sq][mask]alphamerge",
        "-map", "[v]", "-map", "0:a?",
        "-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0",
        "-c:a", "libopus", "-b:a", "64k",
        out_path
    ]

    # Some ffmpeg builds may not allow named map "[v]" from complex filter; use output without map
    # We'll attempt a simpler command if the complex map fails.
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
        if proc.returncode != 0:
            # fallback: produce webm without map, using filter applied as -vf and alphamerge then output
            cmd2 = [
                "ffmpeg", "-y", "-i", in_path,
                "-vf",
                "format=rgba,crop='min(iw,ih)':'min(iw,ih)':(iw-min(iw,ih))/2:(ih-min(iw,ih))/2,scale=720:720,geq='if(lte(hypot(X-360,Y-360),360),255,0)':128:128:128,alphamerge",
                "-c:v","libvpx-vp9","-crf","30","-b:v","0",
                "-c:a","libopus","-b:a","64k",
                out_path
            ]
            proc2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
            if proc2.returncode != 0:
                # cleanup and return error with ffmpeg stderr
                err = proc2.stderr.decode('utf-8', errors='replace')
                try:
                    os.remove(in_path)
                except: pass
                return jsonify({"error":"ffmpeg failed","detail":err}), 500
    except subprocess.TimeoutExpired:
        try:
            os.remove(in_path)
        except: pass
        return jsonify({"error":"Processing timed out"}), 500

    # return file
    if not os.path.exists(out_path):
        try:
            os.remove(in_path)
        except: pass
        return jsonify({"error":"Output not created"}), 500

    # send file
    try:
        return send_file(out_path, as_attachment=True, attachment_filename="uzcircle_720p.webm")
    finally:
        # cleanup - attempt to remove files after sending
        try:
            os.remove(in_path)
        except: pass
        # don't remove out_path immediately because send_file may still be streaming; schedule deletion
        # best-effort: remove after a short delay in background (not implemented here)
