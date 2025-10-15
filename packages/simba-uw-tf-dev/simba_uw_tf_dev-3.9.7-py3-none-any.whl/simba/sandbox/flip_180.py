import subprocess
from pathlib import Path

# Source folder containing .h264 videos
src_dir = Path("/Users/simon/Downloads/Cage_3_simon_Sep_19")
# Destination folder for flipped videos
dst_dir = Path("/Users/simon/Downloads/Cage_3_simon_Sep_19/flipped")
dst_dir.mkdir(parents=True, exist_ok=True)

# Loop over all .h264 files in the source folder (non-recursive)
for video_path in src_dir.glob("*.mp4"):
    output_path = dst_dir / video_path.name

    # FFmpeg command to flip 180 degrees, lossless H.264
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vf", "transpose=2,transpose=2",  # 180° flip
        "-c:v", "libx264",
        "-crf", "0",           # lossless
        "-preset", "ultrafast",
        str(output_path)
    ]

    print(f"Processing {video_path.name} → {output_path.name}")
    subprocess.run(cmd, check=True)