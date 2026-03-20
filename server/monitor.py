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
            'batch_start': re.compile(r'Now Rendering [^:]+:\s+(\d+)\s+-\s+(\d+)'),
            'batch_name': re.compile(r'Now Rendering ([^:]+):\s+\d+\s+-\s+\d+'),
            'batch_complete': re.compile(r'Finished [^:]+:\s+(\d+)\s+-\s+(\d+)'),
            'batch_priority': re.compile(r'\[Priority:\s*([01HL]|null)\]'),
            'frame_progress': re.compile(r'Fra:(\d+).*Time:([0-9:\.]+).*Remaining:([0-9:\.]+)'),
            'frame_saved': re.compile(r'Saved:.*\.(png|exr|jpg)'),
            'frame_append': re.compile(r'Append frame (\d+)'),
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
            'errors': [],
            'initial_scan_complete': False,
            'batches': [],  # List of all batches: {start, end, priority, completed}
            'current_batch_priority': None,
            'current_batch_name': None
        }

    def start(self):
        """Start monitoring the log file"""
        try:
            if not self.log_file.exists():
                print(f"⚠️  Log file not found: {self.log_file}")
                # Don't wait, just return - file might be created later
                return

            self.running = True

            # Start initial file read FIRST (before polling to avoid double-counting)
            self._read_existing_content()

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

            print(f"✓ Log monitor started successfully")

        except Exception as e:
            print(f"❌ Error starting log monitor: {e}")
            import traceback
            traceback.print_exc()

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
            # Quick count of saved frames using grep (much faster for large files)
            import subprocess

            # Try "Append frame" pattern first (newer Blender versions)
            result = subprocess.run(
                ['grep', '-c', 'Append frame', str(self.log_file)],
                capture_output=True,
                text=True
            )

            saved_frame_count = 0
            if result.returncode == 0 and result.stdout.strip():
                saved_frame_count = int(result.stdout.strip())

            # If no "Append frame" found, try "Saved:" pattern (older versions)
            if saved_frame_count == 0:
                result = subprocess.run(
                    ['grep', '-c', 'Saved:', str(self.log_file)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    saved_frame_count = int(result.stdout.strip())

            if saved_frame_count > 0:
                self.state['frames_completed'] = saved_frame_count
                self.callback({
                    'frames_completed': saved_frame_count
                })
                print(f"✓ Found {saved_frame_count} completed frames in log")

            # Use grep to quickly find batch starts and completions instead of parsing entire file
            # This is much faster for large log files
            batch_starts = subprocess.run(
                ['grep', '-n', 'Now Rendering', str(self.log_file)],
                capture_output=True,
                text=True
            )

            batch_ends = subprocess.run(
                ['grep', '-n', 'Finished', str(self.log_file)],
                capture_output=True,
                text=True
            )

            # Parse batch starts
            completed_ranges = set()
            if batch_ends.returncode == 0:
                for line in batch_ends.stdout.strip().split('\n'):
                    if not line:
                        continue
                    # Extract frame range from "Finished Scenes: X - Y"
                    match = self.patterns['batch_complete'].search(line)
                    if match:
                        start, end = int(match.group(1)), int(match.group(2))
                        completed_ranges.add((start, end))

            # Build batch list from starts
            if batch_starts.returncode == 0:
                for line_num, line in enumerate(batch_starts.stdout.strip().split('\n'), 1):
                    if not line:
                        continue
                    # Extract frame range
                    match = self.patterns['batch_start'].search(line)
                    if match:
                        start, end = int(match.group(1)), int(match.group(2))
                        is_completed = (start, end) in completed_ranges

                        # Extract batch name from the same line
                        name_match = self.patterns['batch_name'].search(line)
                        batch_name = name_match.group(1).strip() if name_match else f'Batch {line_num}'

                        batch_info = {
                            'number': line_num,
                            'start': start,
                            'end': end,
                            'frames': end - start + 1,
                            'priority': '1',  # Default to high priority (will be updated if we see priority markers)
                            'completed': is_completed,
                            'name': batch_name
                        }
                        self.state['batches'].append(batch_info)
                        self.state['current_batch'] = line_num

                        if not is_completed:
                            # This is the current rendering batch
                            self.state['batch_start_frame'] = start
                            self.state['batch_end_frame'] = end

                # Send initial batch stats
                if self.state['batches']:
                    self._send_batch_stats()
                    print(f"✓ Found {len(self.state['batches'])} batches ({len(completed_ranges)} completed)")

                    # Set status to rendering if there are incomplete batches
                    has_incomplete = any(not batch['completed'] for batch in self.state['batches'])
                    if has_incomplete:
                        self.callback({'status': 'rendering'})

                    # Set start time from log filename timestamp (e.g., 2026-02-27_18-07-23)
                    import time
                    import re
                    from datetime import datetime

                    # Extract timestamp from filename like "005_TOR_RER_2026-02-27_18-07-23_render_log.txt"
                    filename = self.log_file.name
                    timestamp_match = re.search(r'(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})', filename)
                    if timestamp_match:
                        year, month, day, hour, minute, second = map(int, timestamp_match.groups())
                        dt = datetime(year, month, day, hour, minute, second)
                        start_time = dt.timestamp()
                        self.callback({'start_time': start_time})
                        print(f"✓ Render started at: {dt.strftime('%Y-%m-%d %H:%M:%S')}")

            # Mark initial scan complete
            self.state['initial_scan_complete'] = True

            # Set file position to end so we only monitor new lines
            with open(self.log_file, 'r') as f:
                f.seek(0, 2)  # Seek to end
                self.last_position = f.tell()

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

        # Check for batch name (appears after batch_start line)
        name_match = self.patterns['batch_name'].search(line)
        if name_match and self.state['batches']:
            # Update the last batch with the name
            batch_name = name_match.group(1).strip()
            self.state['batches'][-1]['name'] = batch_name
            self.state['current_batch_name'] = batch_name

            # Also check for priority on this line (in case it wasn't on the batch_start line)
            priority_match = self.patterns['batch_priority'].search(line)
            if priority_match:
                priority_raw = priority_match.group(1)
                # Normalize: '1' or 'H' = high priority, everything else = low priority
                priority = '1' if priority_raw in ('1', 'H') else '0'
                self.state['batches'][-1]['priority'] = priority
                self.state['current_batch_priority'] = priority
                # Re-send batch stats with updated priority
                self._send_batch_stats()

            return

        # Check for batch start
        match = self.patterns['batch_start'].search(line)
        if match:
            start, end = int(match.group(1)), int(match.group(2))

            # Extract batch name from the same line
            name_match = self.patterns['batch_name'].search(line)
            batch_name = name_match.group(1).strip() if name_match else f'Batch {self.state["current_batch"] + 1}'

            # Check if this batch already exists (from initial scan)
            batch_exists = False
            existing_batch = None
            for batch in self.state['batches']:
                if batch['start'] == start and batch['end'] == end:
                    batch_exists = True
                    existing_batch = batch
                    # Update the name if we didn't have it before
                    if batch['name'].startswith('Batch '):
                        batch['name'] = batch_name
                    break

            # Check for priority in the line
            priority_match = self.patterns['batch_priority'].search(line)
            if priority_match:
                priority_raw = priority_match.group(1)
                priority = '1' if priority_raw in ('1', 'H') else '0'
            else:
                priority = '0'  # Default to low priority (no priority set)

            if not batch_exists:
                self.state['current_batch'] += 1
                self.state['batch_start_frame'] = start
                self.state['batch_end_frame'] = end
                self.state['frame_times'] = []
                self.state['current_batch_priority'] = priority

                # Add batch to batches list with the extracted name
                batch_info = {
                    'number': self.state['current_batch'],
                    'start': start,
                    'end': end,
                    'frames': end - start + 1,
                    'priority': priority,
                    'completed': False,
                    'name': batch_name
                }
                self.state['batches'].append(batch_info)
            else:
                # Update current batch tracking for existing batch
                # Set current_batch to the existing batch's number
                self.state['current_batch'] = existing_batch['number']
                self.state['batch_start_frame'] = start
                self.state['batch_end_frame'] = end
                self.state['frame_times'] = []
                self.state['current_batch_priority'] = existing_batch.get('priority', priority)

            # Set start time if this is the first batch
            import time
            if self.state['current_batch'] == 1:
                self.callback({
                    'start_time': time.time()
                })

            # Send batch stats update
            self._send_batch_stats()

            self.callback({
                'status': 'rendering',
                'current_batch': self.state['current_batch'],
                'batch_start_frame': start,
                'batch_end_frame': end,
                'current_batch_priority': priority
            })
            print(f"📊 Batch #{self.state['current_batch']}: Frames {start}-{end} [Priority: {priority}]")
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

            # Find which batch this frame belongs to
            current_batch_number = None
            batch_start = self.state['batch_start_frame']
            batch_end = self.state['batch_end_frame']

            for batch in self.state['batches']:
                if batch['start'] <= frame <= batch['end'] and not batch['completed']:
                    current_batch_number = batch['number']
                    batch_start = batch['start']
                    batch_end = batch['end']
                    self.state['current_batch'] = batch['number']
                    self.state['batch_start_frame'] = batch_start
                    self.state['batch_end_frame'] = batch_end
                    break

            # Calculate progress
            batch_frames = batch_end - batch_start + 1
            frames_done = frame - batch_start + 1
            batch_progress = int((frames_done / batch_frames) * 100) if batch_frames > 0 else 0

            # Calculate average frame time
            avg_time = sum(self.state['frame_times']) / len(self.state['frame_times']) if self.state['frame_times'] else 0

            self.callback({
                'current_frame': frame,
                'current_batch': self.state['current_batch'],
                'batch_start_frame': batch_start,
                'batch_end_frame': batch_end,
                'batch_progress': batch_progress,
                'avg_frame_time': avg_time,
                'frame_time': frame_seconds
            })

            return

        # Check for frame saved (only count new frames after initial scan)
        match = self.patterns['frame_saved'].search(line)
        if match and self.state['initial_scan_complete']:
            self.state['frames_completed'] += 1
            self.callback({
                'frames_completed': self.state['frames_completed']
            })
            return

        # Check for frame append (Blender 4.x format)
        match = self.patterns['frame_append'].search(line)
        if match and self.state['initial_scan_complete']:
            self.state['frames_completed'] += 1
            self.callback({
                'frames_completed': self.state['frames_completed']
            })
            return

        # Check for batch completion
        match = self.patterns['batch_complete'].search(line)
        if match:
            start, end = int(match.group(1)), int(match.group(2))

            # Mark current batch as completed
            for batch in self.state['batches']:
                if batch['start'] == start and batch['end'] == end:
                    batch['completed'] = True
                    break

            # Check if all batches are complete
            all_complete = all(batch['completed'] for batch in self.state['batches'])

            # Send updated batch stats
            self._send_batch_stats()

            print(f"✓ Batch #{self.state['current_batch']} completed: {start}-{end}")

            callback_data = {
                'batch_complete': True,
                'batch_number': self.state['current_batch']
            }

            # If all batches complete, set end_time and status
            if all_complete:
                import time
                end_time = time.time()
                callback_data['end_time'] = end_time
                callback_data['status'] = 'completed'
                print(f"✅ All batches completed!")

            self.callback(callback_data)
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

    def _send_batch_stats(self):
        """Calculate and send batch statistics by priority"""
        high_priority_pending = 0
        high_priority_frames = 0
        low_priority_pending = 0
        low_priority_frames = 0
        completed_batches = 0
        completed_frames = 0

        # Separate batches by priority
        high_priority_list = []
        low_priority_list = []
        completed_list = []

        # Use set to track seen batches and avoid duplicates
        seen_batches = set()

        for batch in self.state['batches']:
            batch_key = (batch['start'], batch['end'])

            # Skip duplicates
            if batch_key in seen_batches:
                continue
            seen_batches.add(batch_key)

            if batch['completed']:
                completed_batches += 1
                completed_frames += batch['frames']
                completed_list.append(batch)
            elif batch['priority'] == '1':  # High priority
                high_priority_pending += 1
                high_priority_frames += batch['frames']
                high_priority_list.append(batch)
            else:  # '0', 'null', or anything else = low priority
                low_priority_pending += 1
                low_priority_frames += batch['frames']
                low_priority_list.append(batch)

        self.callback({
            'high_priority_batches': high_priority_pending,
            'high_priority_frames': high_priority_frames,
            'low_priority_batches': low_priority_pending,
            'low_priority_frames': low_priority_frames,
            'completed_batches': completed_batches,
            'completed_batch_frames': completed_frames,
            'high_priority_list': high_priority_list,
            'low_priority_list': low_priority_list,
            'completed_list': completed_list
        })

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
