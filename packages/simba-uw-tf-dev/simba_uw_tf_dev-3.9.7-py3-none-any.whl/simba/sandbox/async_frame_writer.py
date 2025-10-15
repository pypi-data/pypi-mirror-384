import os
import threading
from concurrent.futures import ProcessPoolExecutor, as_completed
from queue import Queue
from typing import Optional, Tuple, Union
import tempfile
import shutil

import numpy as np
import cv2

from simba.utils.checks import check_instance, check_int, check_valid_boolean
from simba.utils.errors import SimBAError
from simba.utils.printing import SimbaTimer
from simba.video_processors.async_frame_reader import AsyncVideoFrameReader


class AsyncVideoFrameWriter:
    """
    Asynchronous video frame writer that takes AsyncVideoFrameReader as input and writes frames in parallel.
    
    :param AsyncVideoFrameReader frame_reader: An instance of AsyncVideoFrameReader to read frames from.
    :param str output_path: Path to the output video file.
    :param int num_workers: Number of parallel processes for writing (default=4).
    :param str codec: Video codec to use (default='mp4v').
    :param int fps: Frames per second for output video (default=30).
    :param bool verbose: Whether to print progress messages (default=True).
    :param int chunk_size: Number of frames per chunk for parallel processing (default=100).
    :param int max_queue_size: Maximum size of internal queues (default=10).
    
    :example:
    >>> video_path = "/path/to/input.mp4"
    >>> reader = AsyncVideoFrameReader(video_path=video_path, batch_size=500)
    >>> writer = AsyncVideoFrameWriter(frame_reader=reader, output_path="/path/to/output.mp4")
    >>> reader.start()
    >>> writer.start()
    >>> # Wait for completion
    >>> writer.wait_for_completion()
    >>> reader.kill()
    >>> writer.cleanup()
    """
    
    def __init__(self,
                 frame_reader: AsyncVideoFrameReader,
                 output_path: Union[str, os.PathLike],
                 num_workers: int = 4,
                 codec: str = 'mp4v',
                 fps: int = 30,
                 verbose: bool = True,
                 chunk_size: int = 100,
                 max_queue_size: int = 10):
        
        # Validate inputs
        check_instance(source=f'{self.__class__.__name__} frame_reader', 
                      instance=frame_reader, 
                      accepted_types=(AsyncVideoFrameReader,), 
                      raise_error=True)
        check_int(name=f'{self.__class__.__name__} num_workers', 
                 value=num_workers, min_value=1, max_value=16, raise_error=True)
        check_int(name=f'{self.__class__.__name__} fps', 
                 value=fps, min_value=1, raise_error=True)
        check_int(name=f'{self.__class__.__name__} chunk_size', 
                 value=chunk_size, min_value=1, raise_error=True)
        check_valid_boolean(value=verbose, source=f'{self.__class__.__name__} verbose', raise_error=True)
        
        self.frame_reader = frame_reader
        self.output_path = str(output_path)
        self.num_workers = num_workers
        self.codec = codec
        self.fps = fps
        self.verbose = verbose
        self.chunk_size = chunk_size
        self.max_queue_size = max_queue_size
        
        # Get video metadata from reader
        self.video_meta_data = frame_reader.video_meta_data
        self.frame_height = self.video_meta_data['height']
        self.frame_width = self.video_meta_data['width']
        
        # Internal state
        self._stop = False
        self._thread = None
        self._process_pool = None
        self._temp_dir = None
        
        # Queues for coordination
        self.write_queue = Queue(maxsize=max_queue_size)
        self.completed_chunks = Queue(maxsize=max_queue_size)
        self.error_queue = Queue(maxsize=max_queue_size)
        
        # Tracking
        self.total_frames_written = 0
        self.total_chunks_processed = 0
        self.chunk_files = []
        
    def _create_temp_directory(self):
        """Create temporary directory for chunk files."""
        self._temp_dir = tempfile.mkdtemp(prefix='simba_video_writer_')
        if self.verbose:
            print(f'[{self.__class__.__name__}] Created temp directory: {self._temp_dir}')
    
    def _write_chunk_worker(self, chunk_data: Tuple[int, int, np.ndarray]) -> Tuple[int, int, str]:
        """
        Worker function for writing a chunk of frames to a temporary file.
        
        :param chunk_data: Tuple of (start_idx, end_idx, frames)
        :return: Tuple of (start_idx, end_idx, temp_file_path)
        """
        start_idx, end_idx, frames = chunk_data
        
        # Create temporary file path
        temp_filename = f"chunk_{start_idx:06d}_{end_idx:06d}.mp4"
        temp_filepath = os.path.join(self._temp_dir, temp_filename)
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        out = cv2.VideoWriter(temp_filepath, fourcc, self.fps, 
                            (self.frame_width, self.frame_height))
        
        try:
            # Write frames
            for frame in frames:
                # Ensure frame is in correct format (BGR for OpenCV)
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    # RGB to BGR conversion if needed
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                else:
                    frame_bgr = frame
                
                out.write(frame_bgr)
            
            out.release()
            return start_idx, end_idx, temp_filepath
            
        except Exception as e:
            if out:
                out.release()
            raise e
    
    def _process_frame_batches(self):
        """Main processing loop that reads from reader and distributes to workers."""
        try:
            from .async_frame_reader import get_async_frame_batch
            
            while not self._stop:
                try:
                    # Get batch from reader
                    start_idx, end_idx, frames = get_async_frame_batch(
                        self.frame_reader, timeout=1
                    )
                    
                    if frames is None:  # End of video
                        break
                    
                    # Split frames into chunks for parallel processing
                    num_frames = len(frames)
                    for i in range(0, num_frames, self.chunk_size):
                        chunk_start = start_idx + i
                        chunk_end = min(start_idx + i + self.chunk_size, end_idx)
                        chunk_frames = frames[i:i + self.chunk_size]
                        
                        # Submit chunk to process pool
                        future = self._process_pool.submit(
                            self._write_chunk_worker, 
                            (chunk_start, chunk_end, chunk_frames)
                        )
                        
                        # Store future for later collection
                        self.write_queue.put(future)
                        
                        if self.verbose:
                            print(f'[{self.__class__.__name__}] Submitted chunk {chunk_start}-{chunk_end}')
                    
                except Exception as e:
                    if self.verbose:
                        print(f'[{self.__class__.__name__}] Error processing batch: {e}')
                    self.error_queue.put(e)
                    break
                    
        except Exception as e:
            if self.verbose:
                print(f'[{self.__class__.__name__}] Fatal error in processing loop: {e}')
            self.error_queue.put(e)
        finally:
            # Signal completion to all workers
            self._stop = True
    
    def _collect_completed_chunks(self):
        """Collect completed chunks and prepare for final assembly."""
        try:
            while not self._stop or not self.write_queue.empty():
                try:
                    # Get future from queue
                    future = self.write_queue.get(timeout=1)
                    
                    # Wait for completion
                    start_idx, end_idx, temp_filepath = future.result(timeout=30)
                    
                    # Store completed chunk info
                    self.chunk_files.append((start_idx, end_idx, temp_filepath))
                    self.total_chunks_processed += 1
                    
                    if self.verbose:
                        print(f'[{self.__class__.__name__}] Completed chunk {start_idx}-{end_idx}')
                        
                except Exception as e:
                    if self.verbose:
                        print(f'[{self.__class__.__name__}] Error collecting chunk: {e}')
                    self.error_queue.put(e)
                    
        except Exception as e:
            if self.verbose:
                print(f'[{self.__class__.__name__}] Error in collection loop: {e}')
            self.error_queue.put(e)
    
    def _assemble_final_video(self):
        """Assemble all chunk files into the final output video."""
        try:
            if self.verbose:
                print(f'[{self.__class__.__name__}] Assembling final video from {len(self.chunk_files)} chunks...')
            
            # Sort chunks by start index to maintain frame order
            self.chunk_files.sort(key=lambda x: x[0])
            
            # Create output video writer
            fourcc = cv2.VideoWriter_fourcc(*self.codec)
            out = cv2.VideoWriter(self.output_path, fourcc, self.fps, 
                                (self.frame_width, self.frame_height))
            
            try:
                # Process each chunk in order
                for start_idx, end_idx, temp_filepath in self.chunk_files:
                    if self.verbose:
                        print(f'[{self.__class__.__name__}] Processing chunk {start_idx}-{end_idx}')
                    
                    # Read frames from temp file and write to output
                    cap = cv2.VideoCapture(temp_filepath)
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        out.write(frame)
                        self.total_frames_written += 1
                    
                    cap.release()
                    
                out.release()
                
                if self.verbose:
                    print(f'[{self.__class__.__name__}] Final video assembled: {self.output_path}')
                    print(f'[{self.__class__.__name__}] Total frames written: {self.total_frames_written}')
                    
            except Exception as e:
                if out:
                    out.release()
                raise e
                
        except Exception as e:
            if self.verbose:
                print(f'[{self.__class__.__name__}] Error assembling final video: {e}')
            raise e
    
    def start(self):
        """Start the parallel writing process."""
        if self._thread is not None and self._thread.is_alive():
            if self.verbose:
                print(f'[{self.__class__.__name__}] Writer already running')
            return
        
        # Create temp directory
        self._create_temp_directory()
        
        # Initialize process pool
        self._process_pool = ProcessPoolExecutor(max_workers=self.num_workers)
        
        # Start processing thread
        self._thread = threading.Thread(target=self._process_frame_batches, daemon=True)
        self._thread.start()
        
        # Start collection thread
        self.collection_thread = threading.Thread(target=self._collect_completed_chunks, daemon=True)
        self.collection_thread.start()
        
        if self.verbose:
            print(f'[{self.__class__.__name__}] Started parallel video writer with {self.num_workers} workers')
    
    def stop(self):
        """Stop the writing process."""
        self._stop = True
        if self.verbose:
            print(f'[{self.__class__.__name__}] Stopping video writer...')
    
    def wait_for_completion(self, timeout: Optional[int] = None):
        """Wait for all writing to complete."""
        if self._thread:
            self._thread.join(timeout=timeout)
        if hasattr(self, 'collection_thread'):
            self.collection_thread.join(timeout=timeout)
        
        # Assemble final video
        self._assemble_final_video()
        
        if self.verbose:
            print(f'[{self.__class__.__name__}] Video writing completed')
    
    def cleanup(self):
        """Clean up temporary files and resources."""
        try:
            # Stop process pool
            if self._process_pool:
                self._process_pool.shutdown(wait=True)
                self._process_pool = None
            
            # Remove temp directory
            if self._temp_dir and os.path.exists(self._temp_dir):
                shutil.rmtree(self._temp_dir)
                self._temp_dir = None
            
            # Clear queues
            while not self.write_queue.empty():
                try:
                    self.write_queue.get_nowait()
                except:
                    pass
            
            while not self.completed_chunks.empty():
                try:
                    self.completed_chunks.get_nowait()
                except:
                    pass
            
            if self.verbose:
                print(f'[{self.__class__.__name__}] Cleanup completed')
                
        except Exception as e:
            if self.verbose:
                print(f'[{self.__class__.__name__}] Error during cleanup: {e}')
    
    def kill(self):
        """Force kill the writer and cleanup."""
        self.stop()
        self.wait_for_completion(timeout=5)
        self.cleanup()
        
        if self.verbose:
            print(f'[{self.__class__.__name__}] Writer killed and cleaned up')
    
    def is_running(self) -> bool:
        """Check if the writer is currently running."""
        return (self._thread is not None and 
                self._thread.is_alive() and 
                not self._stop)
    
    def get_progress(self) -> Tuple[int, int]:
        """Get current progress: (chunks_processed, total_chunks_estimated)."""
        total_estimated = (self.frame_reader.end_idx - self.frame_reader.start_idx) // self.chunk_size
        return self.total_chunks_processed, total_estimated 