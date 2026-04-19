#!/bin/bash

# Blender Batch Render Script with Interactive Queue System
# Version 5.2.1 - Web-managed via Blender Render Util server

echo "================================================================"
echo "        Blender Batch Render - Interactive Queue System"
echo "================================================================"
echo

# Ask user for project name
read -p "Enter Project Name (no spaces, use underscores if needed): " PROJECT_NAME
echo "Project Name Set To: $PROJECT_NAME"
echo

# Generate timestamp
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)

# Create output directory
OUTPUT_DIR="./renders/${PROJECT_NAME}_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"
echo "Created output directory at: $OUTPUT_DIR"
echo

# Set log file path
LOGFILE="${OUTPUT_DIR}/${PROJECT_NAME}_${TIMESTAMP}_render_log.txt"

# Define .blend file path & Blender App Path
BLEND_FILE="/Users/me/Podcast/3D-Animation/WIP - Blender/Delivery/FILE ANIM/TOR_caseSwap.blend"
BLENDER_PATH="/Applications/Blender.app/Contents/MacOS/Blender"

# Verify Blender executable exists
if [ ! -f "$BLENDER_PATH" ]; then
    echo "❌ Error: Blender not found at $BLENDER_PATH"
    echo "Please update BLENDER_PATH in the script"
    exit 1
fi

# Verify .blend file exists
if [ ! -f "$BLEND_FILE" ]; then
    echo "❌ Error: Blend file not found at $BLEND_FILE"
    echo "Please update BLEND_FILE in the script"
    exit 1
fi

echo "================================================================"
echo "                    Batch Queue Setup"
echo "================================================================"
echo "Define frame ranges for rendering batches."
echo "You can add as many batches as needed."
echo

# Initialize batch arrays
declare -a BATCH_STARTS=()
declare -a BATCH_ENDS=()
declare -a BATCH_NAMES=()
declare -a BATCH_PRIORITIES=()
BATCH_COUNT=0

# Interactive batch input loop
while true; do
    BATCH_NUM=$((BATCH_COUNT + 1))
    echo "────────────────────────────────────────────────────────────────"
    echo "Batch #$BATCH_NUM"
    echo

    # Get start frame
    while true; do
        read -p "  Start Frame (or 'done' to finish, 'cancel' to abort): " START_INPUT

        # Check for done/cancel
        if [[ "$START_INPUT" == "done" ]] || [[ "$START_INPUT" == "d" ]]; then
            if [ $BATCH_COUNT -eq 0 ]; then
                echo "  ⚠️  You must add at least one batch before finishing."
                continue
            fi
            break 2  # Exit both loops
        fi

        if [[ "$START_INPUT" == "cancel" ]] || [[ "$START_INPUT" == "c" ]]; then
            echo
            echo "❌ Batch setup cancelled."
            exit 0
        fi

        # Validate numeric input
        if [[ "$START_INPUT" =~ ^[0-9]+$ ]]; then
            START_FRAME=$START_INPUT
            break
        else
            echo "  ⚠️  Invalid input. Please enter a number, 'done', or 'cancel'."
        fi
    done

    # Get end frame
    while true; do
        read -p "  End Frame (inclusive): " END_INPUT

        # Validate numeric input
        if [[ "$END_INPUT" =~ ^[0-9]+$ ]]; then
            END_FRAME=$END_INPUT

            # Validate end >= start
            if [ $END_FRAME -lt $START_FRAME ]; then
                echo "  ⚠️  End frame must be >= start frame ($START_FRAME)"
                continue
            fi
            break
        else
            echo "  ⚠️  Invalid input. Please enter a number."
        fi
    done

    # Calculate frame count
    FRAME_COUNT=$((END_FRAME - START_FRAME + 1))

    # Optional: Get batch name/description
    read -p "  Batch Name (optional, press Enter to skip): " BATCH_NAME
    if [ -z "$BATCH_NAME" ]; then
        BATCH_NAME="Batch $BATCH_NUM"
    fi

    # Get priority
    while true; do
        read -p "  Priority (1=High, 0=Low, or press Enter to skip) [skip]: " PRIORITY_INPUT

        # If empty, set to null (no priority)
        if [ -z "$PRIORITY_INPUT" ]; then
            PRIORITY="null"
            break
        fi

        if [[ "$PRIORITY_INPUT" == "1" ]]; then
            PRIORITY="1"
            break
        elif [[ "$PRIORITY_INPUT" == "0" ]]; then
            PRIORITY="0"
            break
        else
            echo "  ⚠️  Invalid input. Please enter '1' for High, '0' for Low, or press Enter to skip."
        fi
    done

    # Add to arrays
    BATCH_STARTS+=($START_FRAME)
    BATCH_ENDS+=($END_FRAME)
    BATCH_NAMES+=("$BATCH_NAME")
    BATCH_PRIORITIES+=("$PRIORITY")
    BATCH_COUNT=$((BATCH_COUNT + 1))

    echo "  ✅ Added: $BATCH_NAME [Priority: $PRIORITY] (Frames $START_FRAME-$END_FRAME, $FRAME_COUNT frames)"
    echo
done

# Sort batches by priority and frame count
# Priority: H (high) comes before L (low)
# Within same priority: fewer frames come first
echo
echo "🔄 Sorting batches by priority (H->L) and frame count (low->high)..."

# Create indexed array for sorting
declare -a SORT_INDICES=()
for i in "${!BATCH_STARTS[@]}"; do
    SORT_INDICES+=($i)
done

# Bubble sort based on priority and frame count
for ((i=0; i<${#SORT_INDICES[@]}; i++)); do
    for ((j=i+1; j<${#SORT_INDICES[@]}; j++)); do
        idx_i=${SORT_INDICES[$i]}
        idx_j=${SORT_INDICES[$j]}

        priority_i=${BATCH_PRIORITIES[$idx_i]}
        priority_j=${BATCH_PRIORITIES[$idx_j]}

        start_i=${BATCH_STARTS[$idx_i]}
        end_i=${BATCH_ENDS[$idx_i]}
        frames_i=$((end_i - start_i + 1))

        start_j=${BATCH_STARTS[$idx_j]}
        end_j=${BATCH_ENDS[$idx_j]}
        frames_j=$((end_j - start_j + 1))

        # Swap if:
        # 1. j has higher priority (1 > 0 > null), OR
        # 2. Same priority but j has fewer frames
        SHOULD_SWAP=0

        # Convert priority to numeric for comparison: 1=3, 0=2, null=1
        [[ "$priority_i" == "1" ]] && pri_val_i=3 || [[ "$priority_i" == "0" ]] && pri_val_i=2 || pri_val_i=1
        [[ "$priority_j" == "1" ]] && pri_val_j=3 || [[ "$priority_j" == "0" ]] && pri_val_j=2 || pri_val_j=1

        if [ $pri_val_j -gt $pri_val_i ]; then
            SHOULD_SWAP=1
        elif [ $pri_val_j -eq $pri_val_i ] && [ $frames_j -lt $frames_i ]; then
            SHOULD_SWAP=1
        fi

        if [ $SHOULD_SWAP -eq 1 ]; then
            # Swap indices
            temp=${SORT_INDICES[$i]}
            SORT_INDICES[$i]=${SORT_INDICES[$j]}
            SORT_INDICES[$j]=$temp
        fi
    done
done

# Calculate total frames
TOTAL_FRAMES=0
for i in "${!BATCH_STARTS[@]}"; do
    START=${BATCH_STARTS[$i]}
    END=${BATCH_ENDS[$i]}
    FRAMES=$((END - START + 1))
    TOTAL_FRAMES=$((TOTAL_FRAMES + FRAMES))
done

echo
echo "================================================================"
echo "              Batch Queue Summary (Sorted by Priority)"
echo "================================================================"
echo "Total Batches: $BATCH_COUNT"
echo "Total Frames:  $TOTAL_FRAMES"
echo
echo "Sort Order: High Priority (smallest first) → Low Priority (largest first)"
echo
echo "┌────┬──────────────────────────┬──────┬─────────────┬────────┐"
echo "│ #  │ Batch Name               │ Pri  │ Range       │ Frames │"
echo "├────┼──────────────────────────┼──────┼─────────────┼────────┤"

for i in "${!SORT_INDICES[@]}"; do
    IDX=$((i + 1))
    ORIG_IDX=${SORT_INDICES[$i]}
    NAME="${BATCH_NAMES[$ORIG_IDX]}"
    PRIORITY="${BATCH_PRIORITIES[$ORIG_IDX]}"
    START=${BATCH_STARTS[$ORIG_IDX]}
    END=${BATCH_ENDS[$ORIG_IDX]}
    FRAMES=$((END - START + 1))
    printf "│ %-2d │ %-24s │ %-4s │ %4d - %4d │ %6d │\n" $IDX "$NAME" "$PRIORITY" $START $END $FRAMES
done

echo "└────┴──────────────────────────┴──────┴─────────────┴────────┘"
echo

# Confirm before starting
read -p "Start rendering? (Y/n): " CONFIRM
if [[ "$CONFIRM" =~ ^[Nn] ]]; then
    echo "❌ Render cancelled."
    exit 0
fi

echo
echo "================================================================"
echo "                  Starting Render Process"
echo "================================================================"
echo

# Start capturing output to log file
{
    echo "================================================================"
    echo "🎬 Rendering Batch for: $PROJECT_NAME at $TIMESTAMP"
    echo "================================================================"
    echo "Blend File: $BLEND_FILE"
    echo "Output Dir: $OUTPUT_DIR"
    echo "Total Batches: $BATCH_COUNT"
    echo "Total Frames: $TOTAL_FRAMES"
    echo "================================================================"
    echo

    # Process each batch in the queue (using sorted order)
    for i in "${!SORT_INDICES[@]}"; do
        BATCH_NUM=$((i + 1))
        ORIG_IDX=${SORT_INDICES[$i]}
        BATCH_NAME="${BATCH_NAMES[$ORIG_IDX]}"
        PRIORITY="${BATCH_PRIORITIES[$ORIG_IDX]}"
        START=${BATCH_STARTS[$ORIG_IDX]}
        END=${BATCH_ENDS[$ORIG_IDX]}
        FRAMES=$((END - START + 1))

        echo "────────────────────────────────────────────────────────────────"
        echo "🎬 Now Rendering Scenes: $START - $END"
        echo "   Batch: $BATCH_NAME ($BATCH_NUM/$BATCH_COUNT) [Priority: $PRIORITY]"
        echo "   Frames: $FRAMES"
        echo "────────────────────────────────────────────────────────────────"

        # Execute Blender render
        $BLENDER_PATH -b "$BLEND_FILE" -s $START -e $END -a

        RENDER_EXIT_CODE=$?

        if [ $RENDER_EXIT_CODE -eq 0 ]; then
            echo "✅ Finished Scenes: $START - $END"
        else
            echo "❌ Error rendering batch $BATCH_NUM (exit code: $RENDER_EXIT_CODE)"
            echo "⚠️  Continuing with next batch..."
        fi

        echo
    done

    echo "================================================================"
    echo "🏁 ALL RENDERING JOBS COMPLETED for $PROJECT_NAME!"
    echo "================================================================"
    echo "Total Batches Processed: $BATCH_COUNT"
    echo "Total Frames Rendered: $TOTAL_FRAMES"
    echo "Output Directory: $OUTPUT_DIR"
    echo "Log File: $LOGFILE"
    echo "================================================================"

    # Play completion sound
    afplay /System/Library/Sounds/Glass.aiff 2>/dev/null

} | tee "$LOGFILE"

echo
echo "✅ Render complete! Log saved to:"
echo "   $LOGFILE"
