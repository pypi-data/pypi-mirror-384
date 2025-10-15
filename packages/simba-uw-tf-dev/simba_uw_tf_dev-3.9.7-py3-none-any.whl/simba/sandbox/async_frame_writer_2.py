import os
import threading
from concurrent.futures import ProcessPoolExecutor, as_completed
from queue import Queue
from typing import Optional, Tuple, Union
import tempfile
import shutil
from simba.utils.checks import check_instance, check_int, check_valid_boolean
from simba.video_processors.async_frame_reader import AsyncVideoFrameReader, get_async_frame_batch


class AsyncVideoFrameWriter:

    def __init__(self,
                 frame_reader: AsyncVideoFrameReader,
                 output_path: Union[str, os.PathLike],
                 num_workers: int = 4,
                 codec: str = 'mp4v',
                 fps: int = 30,
                 verbose: bool = True,
                 chunk_size: int = 100,
                 max_queue_size: int = 10):

        check_instance(source=f'{self.__class__.__name__} frame_reader', instance=frame_reader, accepted_types=(AsyncVideoFrameReader,), raise_error=True)
        self._thread, self.verbose = None, verbose
        self._process_pool = None
        self.frame_reader = frame_reader

    def run(self):
        for batch_cnt in range(self.frame_reader.batch_cnt):
            results = get_async_frame_batch(batch_reader=self.frame_reader, timeout=10)
            if results is None:
                print("Reader finished, no more frames")
                break


    def start(self) -> None:
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self.run, daemon=True)
            self._thread.start()
        else:
            if self.verbose: print(f'[{self.__class__.__name__}] Writer already running')
            return





if __name__ == "__main__":
    video_path = "/Users/simon/Desktop/Together_4_res_2.mp4"
    reader = AsyncVideoFrameReader(video_path=video_path, batch_size=100, gpu=False)
    reader.start()
    import time

    time.sleep(10)  # Give reader time to start

    writer = AsyncVideoFrameWriter(frame_reader=reader, output_path="/path/to/output.mp4", verbose=True)
    writer.start()