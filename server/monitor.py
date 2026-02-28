#!/usr/bin/env python3
"""
Log Monitor Service
Watches Blender render log files and extracts progress information
"""

import re
import time
import threading
from pathlib import Path
from typing import Callable, Dict, Any

# Simple file monitoring without watchdog
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠️  watchdog not available, using polling mode")


class LogMonitor:
    """Monitors Blender render log file for progress updates"""

    def __init__(self, log_file: str, callback: Callable[[Dict[str, Any]], None]):
        self.log_file = Path(log_file)
        self.callback = callback
        self.observer = None
        self.file_handler = None
        self.last_position = 0
        self.running = False

        # Regex patterns for parsing Blender output
        self.patterns = {
            'batch_start': re.compile(r'Now Rendering Scenes:\s+(\d+)\s+-\s+(\d+)'),
            'batch_complete': re.compile(r'Finished Scenes:\s+(\d+)\s+-\s+(\d+)'),
            'frame_progress': re.compile(r'Fra:(\d+).*Time:([0-9:\.]+).*Remaining:([0-9:\.]+)'),
            'frame_saved': re.compile(r'Saved:.*\.(png|exr|jpg)'),
            'error': re.compile(r'^Error:'),
            'texture_error': re.compile(r'Texture exceeds maximum'),
            'memory_error': re.compile(r'out of memory')
        }

        # State tracking
        self.state = {
            'current_batch': 0,
            'batch_start_frame': 0,
            'batch_end_frame': 0,
            'current_frame': 0,
            'frames_completed': 0,
            'last_frame_time': 0,
            'frame_times': [],
            'errors': []
        }

    def start(self):
        """Start monitoring the log file"""
        if not self.log_file.exists():
            print(f"⚠️  Log file not found: {self.log_file}")
            print(f"   Waiting for log file to be created...")

            # Wait for log file to be created
            while not self.log_file.exists():
                time.sleep(1)

            print(f"✓ Log file created: {self.log_file}")

        self.running = True

        if WATCHDOG_AVAILABLE:
            # Set up file watcher
            self.file_handler = LogFileHandler(self.log_file, self.process_new_lines)
            self.observer = Observer()
            self.observer.schedule(
                self.file_handler,
                str(self.log_file.parent),
                recursive=False
            )
            self.observer.start()
            print(f"📊 Monitoring log file (watchdog): {self.log_file}")
        else:
            # Use polling mode
            print(f"📊 Monitoring log file (polling): {self.log_file}")
            self._start_polling()

        # Start initial file read
        self._read_existing_content()

    def _start_polling(self):
        """Start polling the log file for changes"""
        def poll_loop():
            while self.running:
                self.process_new_lines()
                time.sleep(0.5)  # Poll every 500ms

        poll_thread = threading.Thread(target=poll_loop, daemon=True)
        poll_thread.start()

    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        print("✓ Log monitor stopped")

    def _read_existing_content(self):
        """Read any existing content in the log file"""
        try:
            with open(self.log_file, 'r') as f:
                f.seek(self.last_position)
                lines = f.readlines()
                self.last_position = f.tell()

                for line in lines:
                    self.parse_line(line.strip())

        except Exception as e:
            print(f"Error reading log file: {e}")

    def process_new_lines(self):
        """Process new lines added to the log file"""
        try:
            with open(self.log_file, 'r') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()

                for line in new_lines:
                    self.parse_line(line.strip())

        except Exception as e:
            print(f"Error processing new lines: {e}")

    def parse_line(self, line: str):
        """Parse a single log line and extract information"""
        if not line:
            return

        # Check for batch start
        match = self.patterns['batch_start'].search(line)
        if match:
            start, end = int(match.group(1)), int(match.group(2))
            self.state['current_batch'] += 1
            self.state['batch_start_frame'] = start
            self.state['batch_end_frame'] = end
            self.state['frame_times'] = []

            self.callback({
                'status': 'rendering',
                'current_batch': self.state['current_batch'],
                'batch_start_frame': start,
                'batch_end_frame': end
            })
            print(f"📊 Batch #{self.state['current_batch']}: Frames {start}-{end}")
            return

        # Check for frame progress
        match = self.patterns['frame_progress'].search(line)
        if match:
            frame = int(match.group(1))
            frame_time = match.group(2)
            remaining = match.group(3)

            # Parse time to seconds
            frame_seconds = self._time_to_seconds(frame_time)
            self.state['frame_times'].append(frame_seconds)
            self.state['current_frame'] = frame

            # Calculate progress
            batch_frames = self.state['batch_end_frame'] - self.state['batch_start_frame'] + 1
            frames_done = frame - self.state['batch_start_frame'] + 1
            batch_progress = int((frames_done / batch_frames) * 100) if batch_frames > 0 else 0

            # Calculate average frame time
            avg_time = sum(self.state['frame_times']) / len(self.state['frame_times']) if self.state['frame_times'] else 0

            self.callback({
                'current_frame': frame,
                'batch_progress': batch_progress,
                'avg_frame_time': avg_time,
                'frame_time': frame_seconds
            })

            return

        # Check for frame saved
        match = self.patterns['frame_saved'].search(line)
        if match:
            self.state['frames_completed'] += 1
            self.callback({
                'frames_completed': self.state['frames_completed']
            })
            return

        # Check for batch completion
        match = self.patterns['batch_complete'].search(line)
        if match:
            start, end = int(match.group(1)), int(match.group(2))
            print(f"✓ Batch #{self.state['current_batch']} completed: {start}-{end}")
            self.callback({
                'batch_complete': True,
                'batch_number': self.state['current_batch']
            })
            return

        # Check for errors
        if self.patterns['error'].search(line):
            error_msg = line
            self.state['errors'].append(error_msg)
            self.callback({
                'error': error_msg,
                'errors': self.state['errors']
            })
            print(f"❌ Error detected: {error_msg}")
            return

        if self.patterns['texture_error'].search(line):
            error_msg = "Texture size exceeds maximum allowed"
            self.state['errors'].append(error_msg)
            self.callback({
                'error': error_msg,
                'errors': self.state['errors']
            })
            print(f"❌ Texture error: {error_msg}")
            return

        if self.patterns['memory_error'].search(line):
            error_msg = "Out of memory error"
            self.state['errors'].append(error_msg)
            self.callback({
                'error': error_msg,
                'errors': self.state['errors']
            })
            print(f"❌ Memory error: {error_msg}")
            return

    def _time_to_seconds(self, time_str: str) -> float:
        """Convert time string (HH:MM:SS.MS or MM:SS.MS) to seconds"""
        try:
            parts = time_str.replace('.', ':').split(':')

            if len(parts) == 4:  # HH:MM:SS:MS
                hours, minutes, seconds, ms = map(float, parts)
                return hours * 3600 + minutes * 60 + seconds + ms / 100
            elif len(parts) == 3:  # MM:SS:MS
                minutes, seconds, ms = map(float, parts)
                return minutes * 60 + seconds + ms / 100
            elif len(parts) == 2:  # SS:MS
                seconds, ms = map(float, parts)
                return seconds + ms / 100
            else:
                return float(parts[0])
        except Exception:
            return 0.0


if WATCHDOG_AVAILABLE:
    class LogFileHandler(FileSystemEventHandler):
        """File system event handler for log file changes"""

        def __init__(self, log_file: Path, callback: Callable):
            self.log_file = log_file
            self.callback = callback

        def on_modified(self, event):
            """Called when the log file is modified"""
            if isinstance(event, FileModifiedEvent) and Path(event.src_path) == self.log_file:
                self.callback()
