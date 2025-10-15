import os
from typing import Union

from simba.utils.read_write import read_json, find_core_cnt

from simba.utils.checks import (check_valid_boolean,
                                check_if_dir_exists,
                                check_float,
                                check_file_exist_and_readable,
                                check_if_keys_exist_in_dict,
                                check_valid_dict,
                                check_int)
from simba.video_processors.blob_tracking_executor import BlobTrackingExecutor
from simba.utils.read_write import get_video_meta_data

def start_blob_tracking(config_path: Union[str, os.PathLike]) -> None:
    """
    Method to access blob detection through CLI or notebook

    .. note::
       For an example blob detection config file, see `https://github.com/sgoldenlab/simba/blob/master/misc/blob_definitions_ex.json <https://github.com/sgoldenlab/simba/blob/master/misc/blob_definitions_ex.json>`__.

    :param Union[str, os.PathLike] config_path: Path to json file holding blob detection setting
    :returns: None. The blob detection data is saved at the location specified in the ``config_path``.
    :rtype: None

    :example:
    >>> start_blob_tracking('/Users/simon/Downloads/result_bg/blob_definitions.json')
    """

    REQUIRED_KEYS = ['video_data', 'input_dir', 'output_dir', 'gpu', 'save_bg_videos', 'core_cnt', 'core_cnt', 'vertice_cnt', 'open_iterations', 'close_iterations', 'video_data']
    VIDEO_KEYS = ['video_path', 'threshold', 'smoothing_time', 'buffer_size', "reference", 'close_kernel', 'open_kernel']
    check_file_exist_and_readable(file_path=config_path)
    data = read_json(x=config_path)
    check_if_keys_exist_in_dict(data=data, key=REQUIRED_KEYS, name=config_path, raise_error=True)
    check_if_dir_exists(in_dir=data['input_dir'], source=f'{config_path} input_dir')
    check_if_dir_exists(in_dir=data['output_dir'], source=f'{config_path} output_dir')
    check_valid_boolean(value=data['gpu'], source=f'{config_path} gpu')
    check_valid_boolean(value=data['save_bg_videos'], source=f'{config_path} save_bg_videos')
    check_int(name=f'{config_path} core_cnt', value=data['core_cnt'], min_value=1, max_value=find_core_cnt()[0])
    check_int(name=f'{config_path} vertice_cnt', value=data['vertice_cnt'], min_value=4)
    check_int(name=f'{config_path} close_iterations', value=data['close_iterations'], min_value=1)
    check_int(name=f'{config_path} open_iterations', value=data['open_iterations'], min_value=1)

    check_valid_dict(x=data['video_data'], valid_key_dtypes=(str,))
    for video_name, video_data in data['video_data'].items():
        check_if_keys_exist_in_dict(data=video_data, key=VIDEO_KEYS, name=f'{config_path} {video_name}', raise_error=True)
        check_file_exist_and_readable(file_path=video_data['video_path'])
        check_file_exist_and_readable(file_path=video_data['reference'])
        video_meta_data = get_video_meta_data(video_path=video_data['video_path'])
        max_dim = max(video_meta_data['width'], video_meta_data['height'])
        check_int(name=f'{video_name} threshold', value=video_data['threshold'], min_value=1, max_value=100)
        data['video_data'][video_name]['threshold'] = int((video_data['threshold'] / 100) * 255)
        if video_data['smoothing_time'] is not None:
            check_float(name=f'{video_name} smoothing_time', value=video_data['smoothing_time'], min_value=0.0)
            data['video_data'][video_name]['smoothing_time'] = int(float(video_data['smoothing_time']) * 1000)
        if video_data['buffer_size'] is not None:
            check_float(name=f'{video_name} buffer_size', value=video_data['buffer_size'], min_value=0.0)
        if video_data['close_kernel'] is not None:
            check_float(name=f'{video_name} close_kernel', value=video_data['close_kernel'], min_value=0.0)
            w = ((max_dim * float(video_data['close_kernel'])) / 100) / 4
            h = ((max_dim * float(video_data['close_kernel'])) / 100) / 4
            k = (int(max(h, 1)), int(max(w, 1)))
            data['video_data'][video_name]['close_kernel'] = tuple(k)
        if video_data['open_kernel'] is not None:
            check_float(name=f'{video_name} open_kernel', value=video_data['open_kernel'], min_value=0.0)
            w = ((max_dim * float(video_data['open_kernel'])) / 100) / 4
            h = ((max_dim * float(video_data['open_kernel'])) / 100) / 4
            k = (int(max(h, 1)), int(max(w, 1)))
            data['video_data'][video_name]['open_kernel'] = tuple(k)

    blob_tracker = BlobTrackingExecutor(data=data)
    blob_tracker.run()



#start_blob_tracking('/Users/simon/Downloads/result_bg/blob_definitions.json')





