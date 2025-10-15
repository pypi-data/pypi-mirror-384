import cv2
import os
from pathlib import Path


def extract_every_nth_frame(video_dir, output_dir, n=10, exts=(".mp4", ".avi", ".mov")):
    """
    Extract every n-th frame from all videos in a directory.

    Parameters
    ----------
    video_dir : str or Path
        Directory containing video files.
    output_dir : str or Path
        Directory where extracted frames will be saved.
    n : int, optional
        Interval of frames to extract (default=10).
    exts : tuple, optional
        Video file extensions to consider.
    """
    video_dir = Path(video_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for video_path in video_dir.iterdir():
        if video_path.suffix.lower() not in exts:
            continue

        cap = cv2.VideoCapture(str(video_path))
        frame_count = 0
        saved_count = 0

        if not cap.isOpened():
            print(f"⚠️ Could not open {video_path}")
            continue

        video_name = video_path.stem
        video_out_dir = output_dir / video_name
        #video_out_dir.mkdir(parents=True, exist_ok=True)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % n == 0:
                frame_filename = output_dir / f"{video_name}_{frame_count:06d}.jpg"
                cv2.imwrite(str(frame_filename), frame)
                saved_count += 1

            frame_count += 1

        cap.release()
        print(f"✅ {video_path.name}: saved {saved_count} frames to {video_out_dir}")



extract_every_nth_frame(video_dir=r'/Users/simon/Downloads/Cage_3_simon_Sep_19/flipped', output_dir=r'/Users/simon/Downloads/Cage_3_simon_Sep_19/frames_092225', n=50)