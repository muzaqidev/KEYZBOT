"""Media processing tools — image, video, audio."""

import subprocess, os, json

TOOL_DEFS = [
    {"type": "function", "function": {"name": "image_resize", "description": "Resize an image to specified dimensions.", "parameters": {"type": "object", "properties": {"input": {"type": "string", "description": "Input image path"}, "output": {"type": "string", "description": "Output image path"}, "width": {"type": "integer", "description": "Target width"}, "height": {"type": "integer", "description": "Target height"}, "quality": {"type": "integer", "description": "JPEG quality 1-100 (default 85)"}}, "required": ["input", "output"]}}},
    {"type": "function", "function": {"name": "image_convert", "description": "Convert image between formats (PNG, JPG, WebP, BMP, GIF).", "parameters": {"type": "object", "properties": {"input": {"type": "string", "description": "Input image path"}, "output": {"type": "string", "description": "Output image path with target extension"}}, "required": ["input", "output"]}}},
    {"type": "function", "function": {"name": "image_crop", "description": "Crop an image to specified coordinates.", "parameters": {"type": "object", "properties": {"input": {"type": "string", "description": "Input image path"}, "output": {"type": "string", "description": "Output image path"}, "x": {"type": "integer", "description": "Left x coordinate"}, "y": {"type": "integer", "description": "Top y coordinate"}, "width": {"type": "integer", "description": "Crop width"}, "height": {"type": "integer", "description": "Crop height"}}, "required": ["input", "output", "x", "y", "width", "height"]}}},
    {"type": "function", "function": {"name": "image_info", "description": "Get image metadata: dimensions, format, size, color space.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Image file path"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "image_compress", "description": "Compress an image to reduce file size.", "parameters": {"type": "object", "properties": {"input": {"type": "string", "description": "Input image path"}, "output": {"type": "string", "description": "Output image path"}, "quality": {"type": "integer", "description": "Quality 1-100 (default 70)"}, "max_width": {"type": "integer", "description": "Max width (resizes if larger)"}}, "required": ["input", "output"]}}},
    {"type": "function", "function": {"name": "video_info", "description": "Get video metadata: duration, resolution, codec, bitrate, fps.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Video file path"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "video_to_gif", "description": "Convert a video clip to animated GIF.", "parameters": {"type": "object", "properties": {"input": {"type": "string", "description": "Input video path"}, "output": {"type": "string", "description": "Output GIF path"}, "start": {"type": "string", "description": "Start time (e.g. '00:00:05')"}, "duration": {"type": "integer", "description": "Duration in seconds"}, "fps": {"type": "integer", "description": "GIF fps (default 10)"}, "width": {"type": "integer", "description": "GIF width (default 480)"}}, "required": ["input", "output"]}}},
    {"type": "function", "function": {"name": "audio_info", "description": "Get audio file metadata: duration, bitrate, sample rate, channels.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Audio file path"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "audio_convert", "description": "Convert audio between formats (MP3, WAV, OGG, FLAC, AAC).", "parameters": {"type": "object", "properties": {"input": {"type": "string", "description": "Input audio path"}, "output": {"type": "string", "description": "Output audio path"}, "bitrate": {"type": "string", "description": "Bitrate (e.g. '128k', '320k')"}}, "required": ["input", "output"]}}},
    {"type": "function", "function": {"name": "audio_extract", "description": "Extract audio track from a video file.", "parameters": {"type": "object", "properties": {"input": {"type": "string", "description": "Input video path"}, "output": {"type": "string", "description": "Output audio path"}}, "required": ["input", "output"]}}},
    {"type": "function", "function": {"name": "qr_generate", "description": "Generate a QR code image from text or URL.", "parameters": {"type": "object", "properties": {"data": {"type": "string", "description": "Text or URL to encode"}, "output": {"type": "string", "description": "Output image path (PNG)"}, "size": {"type": "integer", "description": "Image size in pixels (default 300)"}}, "required": ["data", "output"]}}},
    {"type": "function", "function": {"name": "qr_read", "description": "Read/decode QR code from an image file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Image file with QR code"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "video_thumbnail", "description": "Extract a thumbnail frame from a video.", "parameters": {"type": "object", "properties": {"input": {"type": "string", "description": "Video file path"}, "output": {"type": "string", "description": "Output image path"}, "time": {"type": "string", "description": "Timestamp (e.g. '00:01:30' or '90')"}}, "required": ["input", "output"]}}},
    {"type": "function", "function": {"name": "screenshot", "description": "Take a screenshot of the current screen (if display available).", "parameters": {"type": "object", "properties": {"output": {"type": "string", "description": "Output image path"}}, "required": ["output"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        if name == "image_resize":
            cmd = ["ffmpeg", "-y", "-i", args["input"], "-vf", f"scale={args.get('width', -1)}:{args.get('height', -1)}"]
            if args.get("quality"):
                cmd += ["-q:v", str(args["quality"])]
            cmd.append(args["output"])
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return f"Resized to {args['output']}" if os.path.exists(args["output"]) else f"Error: {r.stderr[-500:]}"

        elif name == "image_convert":
            r = subprocess.run(["ffmpeg", "-y", "-i", args["input"], args["output"]], capture_output=True, text=True, timeout=30)
            return f"Converted to {args['output']} ({os.path.getsize(args['output'])} bytes)" if os.path.exists(args["output"]) else f"Error: {r.stderr[-500:]}"

        elif name == "image_crop":
            x, y, w, h = args["x"], args["y"], args["width"], args["height"]
            r = subprocess.run(["ffmpeg", "-y", "-i", args["input"], "-vf", f"crop={w}:{h}:{x}:{y}", args["output"]], capture_output=True, text=True, timeout=30)
            return f"Cropped to {args['output']}" if os.path.exists(args["output"]) else f"Error: {r.stderr[-500:]}"

        elif name == "image_info":
            r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", args["path"]], capture_output=True, text=True, timeout=10)
            try:
                data = json.loads(r.stdout)
                stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
                fmt = data.get("format", {})
                return f"Format: {stream.get('codec_name', 'N/A')}\nDimensions: {stream.get('width', '?')}x{stream.get('height', '?')}\nSize: {int(fmt.get('size', 0)) // 1024}KB\nDuration: {float(fmt.get('duration', 0)):.1f}s"
            except:
                return r.stdout or r.stderr or "Could not read image info"

        elif name == "image_compress":
            cmd = ["ffmpeg", "-y", "-i", args["input"]]
            if args.get("max_width"):
                cmd += ["-vf", f"scale='min({args['max_width']},iw)':-1"]
            cmd += ["-q:v", str(args.get("quality", 70)), args["output"]]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            orig = os.path.getsize(args["input"])
            comp = os.path.getsize(args["output"]) if os.path.exists(args["output"]) else 0
            return f"Compressed: {orig//1024}KB -> {comp//1024}KB ({comp*100//orig}%)" if comp else f"Error: {r.stderr[-500:]}"

        elif name == "video_info":
            r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", args["path"]], capture_output=True, text=True, timeout=10)
            try:
                data = json.loads(r.stdout)
                vs = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
                as_ = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
                fmt = data.get("format", {})
                dur = float(fmt.get("duration", 0))
                lines = [
                    f"Duration: {int(dur//60)}m {int(dur%60)}s",
                    f"Resolution: {vs.get('width', '?')}x{vs.get('height', '?')}",
                    f"Video: {vs.get('codec_name', 'N/A')} {vs.get('r_frame_rate', '')} fps",
                    f"Audio: {as_.get('codec_name', 'N/A')} {as_.get('sample_rate', '?')}Hz {as_.get('channels', '?')}ch",
                    f"Size: {int(fmt.get('size', 0)) // (1024*1024)}MB",
                    f"Bitrate: {int(fmt.get('bit_rate', 0)) // 1000}kbps",
                ]
                return "\n".join(lines)
            except:
                return r.stdout or r.stderr

        elif name == "video_to_gif":
            cmd = ["ffmpeg", "-y"]
            if args.get("start"):
                cmd += ["-ss", args["start"]]
            cmd += ["-i", args["input"]]
            fps = args.get("fps", 10)
            width = args.get("width", 480)
            vf = f"fps={fps},scale={width}:-1:flags=lanczos"
            if args.get("duration"):
                cmd += ["-t", str(args["duration"])]
            cmd += ["-vf", vf, args["output"]]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return f"GIF created: {args['output']} ({os.path.getsize(args['output'])//1024}KB)" if os.path.exists(args["output"]) else f"Error: {r.stderr[-500:]}"

        elif name == "audio_info":
            r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", args["path"]], capture_output=True, text=True, timeout=10)
            try:
                data = json.loads(r.stdout)
                s = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
                fmt = data.get("format", {})
                dur = float(fmt.get("duration", 0))
                return f"Duration: {int(dur//60)}m {int(dur%60)}s\nCodec: {s.get('codec_name', 'N/A')}\nSample rate: {s.get('sample_rate', '?')}Hz\nChannels: {s.get('channels', '?')}\nBitrate: {int(fmt.get('bit_rate', 0))//1000}kbps\nSize: {int(fmt.get('size', 0))//1024}KB"
            except:
                return r.stdout or r.stderr

        elif name == "audio_convert":
            cmd = ["ffmpeg", "-y", "-i", args["input"]]
            if args.get("bitrate"):
                cmd += ["-b:a", args["bitrate"]]
            cmd.append(args["output"])
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return f"Converted to {args['output']} ({os.path.getsize(args['output'])//1024}KB)" if os.path.exists(args["output"]) else f"Error: {r.stderr[-500:]}"

        elif name == "audio_extract":
            r = subprocess.run(["ffmpeg", "-y", "-i", args["input"], "-vn", "-acodec", "copy", args["output"]], capture_output=True, text=True, timeout=120)
            return f"Audio extracted to {args['output']}" if os.path.exists(args["output"]) else f"Error: {r.stderr[-500:]}"

        elif name == "qr_generate":
            try:
                import qrcode
                img = qrcode.make(args["data"])
                img.save(args["output"])
                return f"QR code saved to {args['output']}"
            except ImportError:
                r = subprocess.run(["qrencode", "-o", args["output"], "-s", "10", args["data"]], capture_output=True, text=True, timeout=10)
                return f"QR code saved to {args['output']}" if r.returncode == 0 else "Error: qrencode or qrcode lib not available"

        elif name == "qr_read":
            try:
                from pyzbar.pyzbar import decode
                from PIL import Image
                img = Image.open(args["path"])
                results = decode(img)
                if results:
                    return "\n".join(r.data.decode() for r in results)
                return "(no QR code found)"
            except ImportError:
                r = subprocess.run(["zbarimg", "--raw", args["path"]], capture_output=True, text=True, timeout=10)
                return r.stdout.strip() or "Error: zbarimg or pyzbar not available"

        elif name == "video_thumbnail":
            time = args.get("time", "00:00:01")
            r = subprocess.run(["ffmpeg", "-y", "-i", args["input"], "-ss", time, "-vframes", "1", args["output"]], capture_output=True, text=True, timeout=30)
            return f"Thumbnail saved to {args['output']}" if os.path.exists(args["output"]) else f"Error: {r.stderr[-500:]}"

        elif name == "screenshot":
            output = args["output"]
            r = subprocess.run(["scrot", output], capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                return f"Screenshot saved to {output}"
            r = subprocess.run(["import", "-window", "root", output], capture_output=True, text=True, timeout=10)
            return f"Screenshot saved to {output}" if r.returncode == 0 else "Error: No display available or screenshot tools not installed"

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
