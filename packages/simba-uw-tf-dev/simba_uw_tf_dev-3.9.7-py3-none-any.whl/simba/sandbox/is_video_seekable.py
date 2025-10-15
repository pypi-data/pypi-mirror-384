from typing import Union, Optional, Tuple, Dict, List
import os
import numpy as np
from simba.utils.enums import Formats, Options
from simba.utils.read_write import find_files_of_filetypes_in_directory, get_video_meta_data, read_img_batch_from_video_gpu, get_fn_ext
from simba.utils.errors import InvalidInputError, SimBAGPUError, FFMPEGNotFoundError, FrameRangeError
from simba.utils.checks import check_ffmpeg_available, check_nvidea_gpu_available, check_int, check_valid_boolean
from simba.mixins.image_mixin import ImageMixin
from simba.utils.printing import stdout_success


def is_video_seekable(data_path: Union[str, os.PathLike],
                      gpu: bool = False,
                      batch_size: Optional[int] = None,
                      verbose: bool = False,
                      raise_error: bool = True) -> Union[None, bool, Tuple[Dict[str, List[int]]]]:
    """
    Determines if the given video file(s) are seekable and can be processed frame-by-frame without issues.

    This function checks if all frames in the specified video(s) can be read sequentially. It can process videos
    using either CPU or GPU, with optional batch processing to handle memory limitations. If unreadable frames are
    detected, the function can either raise an error or return a result indicating the issue.

    :param Union[str, os.PathLike] data_path: Path to the video file or a path to a directory containing video files.
    :param bool gpu: If True, then use GPU. Else, CPU.
    :param Optional[int] batch_size: Optional int representing the number of frames in each video to process sequentially. If None, all frames in a video is processed at once. Use a smaller value to avoid MemoryErrors. Default None.
    :param bool verbose: If True, prints progress. Default None.
    :param bool raise_error: If True, raises error if not all passed videos are seeakable.

    :example:
    >>> _ = is_video_seekable(data_path='/Users/simon/Desktop/unseekable/20200730_AB_7dpf_850nm_0003_fps_5.mp4', batch_size=400)
    """


    if batch_size is not None:
        check_int(name=f'{is_video_seekable.__name__}', value=batch_size, min_value=1)
    check_valid_boolean(value=[verbose], source=f'{is_video_seekable.__name__} verbose')
    if not check_ffmpeg_available():
        raise FFMPEGNotFoundError(msg='SimBA could not find FFMPEG on the computer.', source=is_video_seekable.__name__)
    if gpu and not check_nvidea_gpu_available():
        raise SimBAGPUError(msg='SimBA could not find a NVIDEA GPU on the computer and GPU is set to True.', source=is_video_seekable.__name__)
    if os.path.isfile(data_path):
        data_paths = [data_path]
    elif os.path.isdir(data_path):
        data_paths = find_files_of_filetypes_in_directory(directory=data_path, extensions=Options.ALL_VIDEO_FORMAT_OPTIONS.value, raise_error=True)
    else:
        raise InvalidInputError(msg=f'{data_path} is not a valid in directory or file path.', source=is_video_seekable.__name__)
    _ = [get_video_meta_data(video_path=x) for x in data_paths]

    results = {}
    for file_cnt, file_path in enumerate(data_paths):
        _, video_name, _ = get_fn_ext(filepath=file_path)
        print(f'Processing video {video_name}...')
        video_meta_data = get_video_meta_data(video_path=file_path)
        video_frm_ranges = np.arange(0, video_meta_data['frame_count']+1)
        if batch_size is not None:
            video_frm_ranges = np.array_split(video_frm_ranges, max(1, int(video_frm_ranges.shape[0]/batch_size)))
        else:
            video_frm_ranges = [video_frm_ranges]
        video_error_frms = []
        for video_frm_range in video_frm_ranges:
            if not gpu:
                imgs = ImageMixin.read_img_batch_from_video(video_path=file_path, start_frm=video_frm_range[0], end_frm=video_frm_range[-1], verbose=verbose)
            else:
                imgs = read_img_batch_from_video_gpu(video_path=file_path, start_frm=video_frm_range[0], end_frm=video_frm_range[-1], verbose=verbose)
            invalid_frms = [k for k, v in imgs.items() if v is None]
            video_error_frms.extend(invalid_frms)
        results[video_name] = video_error_frms

    if all(len(v) == 0 for v in results.values()):
        if verbose:
            stdout_success(msg=f'The {len(data_paths)} videos are valid.', source=is_video_seekable.__name__)
        return True
    else:
        if raise_error:
            raise FrameRangeError(msg=f'{results} The frames in the videos listed are unreadable. Consider re-encoding these videos.', source=is_video_seekable.__name__)
        return (False, results)



#is_video_seekable(data_path='/Users/simon/Desktop/unseekable/20200730_AB_7dpf_850nm_0003_fps_5.mp4', batch_size=400)