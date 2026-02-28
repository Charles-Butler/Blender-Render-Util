#!/bin/bash

# Render Monitor Script
# Monitors Blender batch rendering and estimates time remaining

echo "================================================================"
echo "           Blender Batch Render Monitor"
echo "================================================================"

# Parse batch configuration from batchedFrame_render.sh
RENDER_SCRIPT="./batchedFrame_render.sh"
declare -a BATCH_RANGES=()
declare -a BATCH_NAMES=()
TOTAL_FRAMES=0

if [ -f "$RENDER_SCRIPT" ]; then
    echo "📋 Reading batch configuration from $RENDER_SCRIPT..."

    # Extract batch ranges from Blender command flags: -s START -e END
    while IFS= read -r line; do
        if [[ $line =~ -s\ ([0-9]+)\ -e\ ([0-9]+)\ -a ]]; then
            START=${BASH_REMATCH[1]}
            END=${BASH_REMATCH[2]}

            # Strip leading zeros to prevent octal interpretation
            START=$((10#$START))
            END=$((10#$END))

            BATCH_RANGES+=("$START:$END")
            FRAMES=$((END - START + 1))
            TOTAL_FRAMES=$((TOTAL_FRAMES + FRAMES))
            BATCH_NAMES+=("Batch: $START-$END ($FRAMES frames)")
        fi
    done < "$RENDER_SCRIPT"

    echo "✓ Found ${#BATCH_RANGES[@]} batches totaling $TOTAL_FRAMES frames"
    echo
else
    echo "⚠️  Warning: Could not find $RENDER_SCRIPT"
    echo "   Using auto-detection mode"
    echo
fi

# Initialize variables
current_batch=0
batch_start_time=$(date +%s)
overall_start_time=$(date +%s)
frame_times=()
last_frame=-1
batch_start_frame=0
batch_end_frame=0
frames_in_batch=0
render_failed=0
display_height=18  # Number of lines in progress display (increased for dual bars)
total_frames_rendered=${PRESCANNED_FRAMES:-0}  # Start with prescanned count if available
completed_frames_list=""  # Track completed frames as space-separated string (bash 3 compatible)

# Check if input is piped or if we need to prompt for log file
if [ -t 0 ]; then
    # No piped input - prompt for log file or auto-detect
    echo "No input piped. Searching for active render logs..."
    echo

    # Check if there's an argument (log file path)
    if [ -n "$1" ] && [ "$1" != "--piped" ]; then
        LOG_FILE="$1"
        if [ ! -f "$LOG_FILE" ]; then
            echo "❌ Log file not found: $LOG_FILE"
            exit 1
        fi
        echo "📊 Monitoring: $LOG_FILE"
        echo "================================================================"
        echo
        exec tail -f "$LOG_FILE" | bash "$0" --piped
    fi

    # Find all render logs (compatible with older bash)
    ALL_LOGS=()
    while IFS= read -r line; do
        ALL_LOGS+=("$line")
    done < <(ls -t ./renders/*/*_render_log.txt 2>/dev/null)

    if [ ${#ALL_LOGS[@]} -eq 0 ]; then
        echo "❌ No render logs found in ./renders/"
        echo
        echo "Usage:"
        echo "  Option 1: Pipe render output:"
        echo "    ./gameCase_batch_render.sh | tee >(./watch_render_progress.sh)"
        echo
        echo "  Option 2: Monitor existing log:"
        echo "    tail -f ./renders/CASE_NAME/log_file.txt | ./watch_render_progress.sh"
        echo
        echo "  Option 3: Provide log file as argument:"
        echo "    ./watch_render_progress.sh /path/to/render_log.txt"
        exit 1
    fi

    # Check if Blender is currently running
    RUNNING_BLENDER=$(ps aux | grep -i "Blender -b" | grep -v grep)

    if [ -n "$RUNNING_BLENDER" ]; then
        echo "✅ Active Blender render detected!"
        echo
        MOST_RECENT="${ALL_LOGS[0]}"
        echo "Most recent log: $MOST_RECENT"
        echo
        read -p "Monitor this log? (Y/n/search): " CHOICE

        if [[ "$CHOICE" =~ ^[Nn] ]]; then
            CHOICE="search"
        elif [[ -z "$CHOICE" ]] || [[ "$CHOICE" =~ ^[Yy] ]]; then
            LOG_FILE="$MOST_RECENT"
        fi
    else
        echo "⚠️  No active Blender render detected"
        CHOICE="search"
    fi

    # If user wants to search or no active render
    if [[ "$CHOICE" == "search" ]]; then
        echo
        echo "Available render logs:"
        echo

        # Extract game names from directories
        for i in "${!ALL_LOGS[@]}"; do
            LOG="${ALL_LOGS[$i]}"
            DIR=$(dirname "$LOG")
            BASENAME=$(basename "$DIR")
            GAME_NAME=$(echo "$BASENAME" | sed 's/_[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}_.*$//')
            TIMESTAMP=$(echo "$BASENAME" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2}')
            printf "%2d. %-30s (%s)\n" $((i+1)) "$GAME_NAME" "$TIMESTAMP"
        done

        echo
        read -p "Enter game name to search, or number to select: " SELECTION

        # Check if it's a number
        if [[ "$SELECTION" =~ ^[0-9]+$ ]]; then
            IDX=$((SELECTION - 1))
            if [ $IDX -ge 0 ] && [ $IDX -lt ${#ALL_LOGS[@]} ]; then
                LOG_FILE="${ALL_LOGS[$IDX]}"
            else
                echo "❌ Invalid selection"
                exit 1
            fi
        else
            # Search by game name
            FOUND_LOG=""
            for LOG in "${ALL_LOGS[@]}"; do
                if [[ "$LOG" =~ $SELECTION ]]; then
                    FOUND_LOG="$LOG"
                    break
                fi
            done

            if [ -z "$FOUND_LOG" ]; then
                echo "❌ No log found matching: $SELECTION"
                exit 1
            fi
            LOG_FILE="$FOUND_LOG"
        fi
    fi

    echo "📊 Monitoring: $LOG_FILE"
    echo "================================================================"
    echo

    # Pre-scan log to count already completed frames for accurate overall progress
    echo "📊 Scanning log for completed frames..."

    # Look for "Saved:" lines which confirm a frame was successfully rendered
    COMPLETED_COUNT=$(grep -E "Saved:.*\.(png|exr|jpg)" "$LOG_FILE" 2>/dev/null | wc -l | tr -d ' ')

    if [ "$COMPLETED_COUNT" -gt 0 ]; then
        echo "✓ Found $COMPLETED_COUNT frames already rendered"
    else
        # Fallback: count unique Fra: entries
        COMPLETED_COUNT=$(grep "^Fra:" "$LOG_FILE" 2>/dev/null | awk '{print $1}' | sed 's/Fra://' | sort -n | uniq | wc -l | tr -d ' ')
        if [ "$COMPLETED_COUNT" -gt 0 ]; then
            echo "✓ Found approximately $COMPLETED_COUNT frames in progress"
        fi
    fi
    echo

    # Export the completed count so the monitoring process can use it
    export PRESCANNED_FRAMES="$COMPLETED_COUNT"

    # Tail the log file and pipe to ourselves
    exec tail -f "$LOG_FILE" | bash "$0" --piped
fi

# If --piped flag is present, we're in the second invocation, proceed normally
if [ "$1" = "--piped" ]; then
    echo "Monitoring Blender output for progress tracking..."
    echo
fi

# Function to parse time string (HH:MM:SS or MM:SS.MS) to seconds
time_to_seconds() {
    local time_str=$1
    # Remove milliseconds if present
    time_str=${time_str%.*}

    IFS=':' read -ra PARTS <<< "$time_str"
    local seconds=0

    if [ ${#PARTS[@]} -eq 3 ]; then
        # HH:MM:SS
        seconds=$((${PARTS[0]} * 3600 + ${PARTS[1]} * 60 + ${PARTS[2]}))
    elif [ ${#PARTS[@]} -eq 2 ]; then
        # MM:SS
        seconds=$((${PARTS[0]} * 60 + ${PARTS[1]}))
    else
        seconds=${PARTS[0]}
    fi

    echo $seconds
}

# Function to format seconds to HH:MM:SS
seconds_to_time() {
    local total_seconds=$1
    local hours=$((total_seconds / 3600))
    local minutes=$(((total_seconds % 3600) / 60))
    local seconds=$((total_seconds % 60))
    printf "%02d:%02d:%02d" $hours $minutes $seconds
}

# Function to detect batch information from output
detect_batch() {
    local line=$1

    # Match pattern like "🎬 Now Rendering Scenes: 973 - 999" or "Now Rendering Scenes: 973 - 999"
    if [[ $line =~ Now\ Rendering\ Scenes:\ ([0-9]+)\ -\ ([0-9]+) ]]; then
        local start_raw=${BASH_REMATCH[1]}
        local end_raw=${BASH_REMATCH[2]}

        # Strip leading zeros
        batch_start_frame=$((10#$start_raw))
        batch_end_frame=$((10#$end_raw))
        frames_in_batch=$((batch_end_frame - batch_start_frame + 1))
        current_batch=$((current_batch + 1))
        batch_start_time=$(date +%s)
        frame_times=()
        last_frame=-1

        echo "════════════════════════════════════════════════════════════════"
        echo "📊 BATCH #$current_batch DETECTED"
        echo "   Frame Range: $batch_start_frame → $batch_end_frame ($frames_in_batch frames)"
        echo "════════════════════════════════════════════════════════════════"
        return 0
    fi

    # Fallback: If we see frame rendering but no batch detected yet
    if [[ $current_batch -eq 0 ]] && [[ $line =~ Fra:([0-9]+) ]]; then
        # Try to detect batch from BATCH_RANGES if available
        if [ ${#BATCH_RANGES[@]} -gt 0 ]; then
            # Use first batch as default
            IFS=':' read -r batch_start_frame batch_end_frame <<< "${BATCH_RANGES[0]}"
            frames_in_batch=$((batch_end_frame - batch_start_frame + 1))
        else
            # Complete fallback
            batch_start_frame=0
            batch_end_frame=9999
            frames_in_batch=9999
        fi

        current_batch=1
        batch_start_time=$(date +%s)
        frame_times=()
        last_frame=-1

        echo "════════════════════════════════════════════════════════════════"
        echo "⚠️  BATCH AUTO-DETECTED: $batch_start_frame → $batch_end_frame"
        echo "   Monitoring frames as they render..."
        echo "════════════════════════════════════════════════════════════════"
        return 0
    fi

    return 1
}

# Function to clear previous display
clear_display() {
    # Move cursor up and clear lines
    for ((i=0; i<display_height; i++)); do
        tput cuu1 2>/dev/null  # Move cursor up
        tput el 2>/dev/null     # Clear line
    done
}

# Function to update progress
update_progress() {
    local line=$1

    # Parse Blender output: Fra:651 Mem:... | Time:00:58.60 | Remaining:08:07.08 | ...
    if [[ $line =~ Fra:([0-9]+).*Time:([0-9:\.]+).*Remaining:([0-9:\.]+) ]]; then
        local current_frame=${BASH_REMATCH[1]}
        local frame_time=${BASH_REMATCH[2]}
        local remaining=${BASH_REMATCH[3]}

        # Only process if this is a new frame
        if [ $current_frame -ne $last_frame ]; then
            last_frame=$current_frame

            # Track this frame as completed (bash 3 compatible - check if in list)
            if ! echo " $completed_frames_list " | grep -q " $current_frame "; then
                completed_frames_list="$completed_frames_list $current_frame"
                total_frames_rendered=$((total_frames_rendered + 1))
            fi

            # Calculate frames completed in this batch
            local frames_done=$((current_frame - batch_start_frame + 1))
            local frames_left=$((batch_end_frame - current_frame))

            # Prevent division by zero
            if [ $frames_in_batch -eq 0 ]; then
                return
            fi

            # Calculate batch percentage
            local batch_percent=$((frames_done * 100 / frames_in_batch))

            # Calculate overall percentage
            local overall_percent=0
            if [ $TOTAL_FRAMES -gt 0 ]; then
                overall_percent=$((total_frames_rendered * 100 / TOTAL_FRAMES))
            fi

            # Store frame render time
            local frame_seconds=$(time_to_seconds "$frame_time")
            frame_times+=($frame_seconds)

            # Calculate average time per frame using bc for precision
            local total_time=0
            for time in "${frame_times[@]}"; do
                total_time=$((total_time + time))
            done

            # Use bc for decimal precision with error handling
            local avg_time="0"
            local avg_time_int=0
            if [ ${#frame_times[@]} -gt 0 ]; then
                avg_time=$(echo "scale=2; $total_time / ${#frame_times[@]}" | bc 2>/dev/null || echo "0")
                avg_time_int=${avg_time%.*}  # Integer part for display function
                if [ -z "$avg_time_int" ]; then avg_time_int=0; fi
            fi

            # Estimate remaining time for batch
            local batch_est_remaining=0
            if [ "$avg_time" != "0" ] && [ $frames_left -gt 0 ]; then
                batch_est_remaining=$(echo "scale=0; $frames_left * $avg_time" | bc 2>/dev/null || echo "0")
                batch_est_remaining=${batch_est_remaining%.*}  # Remove decimal
                if [ -z "$batch_est_remaining" ]; then batch_est_remaining=0; fi
            fi

            # Estimate remaining time for overall render
            local overall_frames_left=$((TOTAL_FRAMES - total_frames_rendered))
            local overall_est_remaining=0
            if [ "$avg_time" != "0" ] && [ $overall_frames_left -gt 0 ]; then
                overall_est_remaining=$(echo "scale=0; $overall_frames_left * $avg_time" | bc 2>/dev/null || echo "0")
                overall_est_remaining=${overall_est_remaining%.*}
                if [ -z "$overall_est_remaining" ]; then overall_est_remaining=0; fi
            fi

            # Calculate elapsed times
            local current_time=$(date +%s)
            local batch_elapsed=$((current_time - batch_start_time))
            local overall_elapsed=$((current_time - overall_start_time))

            # Batch progress bar
            local bar_width=40
            local batch_filled=$((batch_percent * bar_width / 100))
            local batch_empty=$((bar_width - batch_filled))
            local batch_bar=$(printf "%${batch_filled}s" | tr ' ' '█')
            local batch_empty_bar=$(printf "%${batch_empty}s" | tr ' ' '░')

            # Overall progress bar
            local overall_filled=$((overall_percent * bar_width / 100))
            local overall_empty=$((bar_width - overall_filled))
            local overall_bar=$(printf "%${overall_filled}s" | tr ' ' '█')
            local overall_empty_bar=$(printf "%${overall_empty}s" | tr ' ' '░')

            # Clear previous display (skip on first frame)
            if [ $total_frames_rendered -gt 1 ]; then
                clear_display
            fi

            # Print progress
            echo "┌────────────────────────────────────────────────────────────────┐"
            echo "│ 🎬 BATCH #$current_batch: Frame $current_frame/$batch_end_frame"
            echo "│ [$batch_bar$batch_empty_bar] $batch_percent%"
            echo "│"
            echo "│ 🌍 OVERALL: $total_frames_rendered / $TOTAL_FRAMES frames"
            echo "│ [$overall_bar$overall_empty_bar] $overall_percent%"
            echo "├────────────────────────────────────────────────────────────────┤"
            echo "│ ⏱️  Frame Time:     $(seconds_to_time $frame_seconds)"
            echo "│ 📈 Avg/Frame:      $(seconds_to_time $avg_time_int) (${avg_time}s)"
            echo "│ ⏳ Batch ETA:      $(seconds_to_time $batch_est_remaining)"
            echo "│ 🌍 Overall ETA:    $(seconds_to_time $overall_est_remaining)"
            echo "│ 🕐 Batch Time:     $(seconds_to_time $batch_elapsed)"
            echo "│ 🌐 Total Time:     $(seconds_to_time $overall_elapsed)"
            echo "│ 🎯 Blender Est:    $remaining (per frame)"
            echo "└────────────────────────────────────────────────────────────────┘"
            echo
            echo  # Extra line for spacing
            echo  # Extra line for spacing
        fi
    fi

    # Check for frame save confirmation (only count saved frames for overall progress)
    if [[ $line =~ Saved:.*\.png ]] || [[ $line =~ Saved:.*\.exr ]] || [[ $line =~ Saved:.*\.jpg ]]; then
        # Frame successfully saved - this is the definitive completion marker
        # We already counted it in the Fra: handler above
        :
    fi
}

# Function to detect batch completion
detect_completion() {
    local line=$1

    if [[ $line =~ Finished\ Scenes:\ ([0-9]+)\ -\ ([0-9]+) ]]; then
        local total_batch_time=$(($(date +%s) - batch_start_time))
        echo "════════════════════════════════════════════════════════════════"
        echo "✅ BATCH #$current_batch COMPLETE!"
        echo "   Total Batch Time: $(seconds_to_time $total_batch_time)"
        echo "   Average per Frame: $(seconds_to_time $((total_batch_time / frames_in_batch)))"
        echo "════════════════════════════════════════════════════════════════"
        echo
    fi
}

# Function to detect errors
detect_error() {
    local line=$1

    # Check for critical Blender errors
    if [[ $line =~ ^Error: ]] || [[ $line =~ Blender\ quit ]]; then
        render_failed=1
        echo
        echo "════════════════════════════════════════════════════════════════"
        echo "❌ RENDER ERROR DETECTED!"
        echo "════════════════════════════════════════════════════════════════"
        echo "$line"
        echo "════════════════════════════════════════════════════════════════"
        echo
        return 0
    fi

    # Check for texture size errors
    if [[ $line =~ Texture\ exceeds\ maximum\ allowed\ size ]]; then
        render_failed=1
        echo
        echo "════════════════════════════════════════════════════════════════"
        echo "❌ TEXTURE SIZE ERROR!"
        echo "════════════════════════════════════════════════════════════════"
        echo "$line"
        echo "Resize textures to 16384x16384 or smaller"
        echo "════════════════════════════════════════════════════════════════"
        echo
        return 0
    fi

    # Check for out of memory errors
    if [[ $line =~ out\ of\ memory ]] || [[ $line =~ OutOfMemoryError ]]; then
        render_failed=1
        echo
        echo "════════════════════════════════════════════════════════════════"
        echo "❌ OUT OF MEMORY ERROR!"
        echo "════════════════════════════════════════════════════════════════"
        echo "$line"
        echo "Reduce scene complexity or increase available memory"
        echo "════════════════════════════════════════════════════════════════"
        echo
        return 0
    fi

    return 1
}

# Main monitoring loop
# This script should be run in parallel with the render script
# Usage: tail -f your_render_log.txt | ./watch_render_progress.sh
# Or: ./gameCase_batch_render.sh | tee >(./watch_render_progress.sh)

while IFS= read -r line; do
    # Echo the original line for logging
    # echo "$line"

    # Detect errors first
    if detect_error "$line"; then
        # Error detected, continue showing error output
        continue
    fi

    # Detect batch changes
    detect_batch "$line"

    # Update progress for current frame
    update_progress "$line"

    # Detect batch completion
    detect_completion "$line"
done

echo "════════════════════════════════════════════════════════════════"
if [ $render_failed -eq 1 ]; then
    echo "⚠️  Monitoring Complete - Errors Detected!"
else
    echo "🏁 Monitoring Complete!"
fi
echo "════════════════════════════════════════════════════════════════"
