import os
import subprocess
from typing import Optional, Tuple, Union
from simba.utils.read_write import recursive_file_search, get_video_meta_data, get_fn_ext
from simba.utils.enums import Options
from simba.utils.printing import SimbaTimer
#from simba.utils.checks import

def lossless_mp4_conversion(directory: Union[str, os.PathLike],
                            save_dir: Optional[Union[str, os.PathLike]] = None,
                            file_extensions: Optional[Tuple[str, ...]] = None,
                            overwrite: bool = True,
                            remove_original: bool = False):

    file_extensions = Options.ALL_VIDEO_FORMAT_OPTIONS.value if file_extensions is None else file_extensions
    file_paths = recursive_file_search(directory=directory, extensions=file_extensions, as_dict=True)

    for file_cnt, (file_name, file_path) in enumerate(file_paths.items()):
        print(f'{file_cnt+1}/{len(file_paths.keys())}')
        video_timer = SimbaTimer(start=True)
        try:
            video_meta = get_video_meta_data(video_path=file_path, fps_as_int=False)
        except:
            continue
        if save_dir is not None:
            save_path = os.path.join(save_dir, f'{file_name}.mp4')
        else:
            in_dir, _, _ = get_fn_ext(filepath=file_path)
            save_path = os.path.join(in_dir, f'{file_name}.mp4')
        if os.path.isfile(save_path) and not overwrite:
            pass
        else:
            cmd = f"ffmpeg -fflags +genpts -r {video_meta['fps']} -i '{file_path}' -c copy -movflags +faststart '{save_path}' -loglevel error -stats -hide_banner -y"
            subprocess.call(cmd, shell=True)
        video_timer.stop_timer()
        if remove_original:
            os.remove(file_path)
            print(f'removed {file_path}')
        print(f'{video_meta["video_name"]}: {video_timer.elapsed_time_str}s')

DIRECTORY = r'/Users/simon/Downloads/Cage_3_simon_Sep_19'
FILE_EXTENSTIONS = ('.h264',)

lossless_mp4_conversion(directory=DIRECTORY, file_extensions=FILE_EXTENSTIONS, remove_original=False)