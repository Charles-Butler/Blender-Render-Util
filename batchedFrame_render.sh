#!/bin/bash

# Blender Batch Render Script with Interactive Queue System
# Version 5.3.1 - Web-managed via Blender Render Util server

echo "================================================================"
echo "        Blender Batch Render - Interactive Queue System"
echo "================================================================"
echo

# Initialize batch arrays
declare -a BATCH_STARTS=()
declare -a BATCH_ENDS=()
declare -a BATCH_NAMES=()
declare -a BATCH_PRIORITIES=()
BATCH_COUNT=0
CONFIG_MODE=false

# ================================================================
#  NON-INTERACTIVE MODE — launched from Blender Render Util app
# ================================================================
if [ -n "$RENDER_CONFIG_FILE" ] && [ -f "$RENDER_CONFIG_FILE" ]; then
    echo "📋 Loading render configuration from:"
    echo "   $RENDER_CONFIG_FILE"
    echo

    # Extract scalar fields via python3 (always available on macOS)
    PROJECT_NAME=$(python3 -c "import json; d=json.load(open('$RENDER_CONFIG_FILE')); print(d['project_name'])")
    BLEND_FILE=$(python3   -c "import json; d=json.load(open('$RENDER_CONFIG_FILE')); print(d['blend_file'])")
    BLENDER_PATH=$(python3 -c "import json; d=json.load(open('$RENDER_CONFIG_FILE')); print(d.get('blender_path','/Applications/Blender.app/Contents/MacOS/Blender'))")
    OUTPUT_DIR=$(python3   -c "import json; d=json.load(open('$RENDER_CONFIG_FILE')); print(d['output_dir'])")
    LOGFILE=$(python3      -c "import json; d=json.load(open('$RENDER_CONFIG_FILE')); print(d['log_file'])")
    TIMESTAMP=$(python3    -c "import json; d=json.load(open('$RENDER_CONFIG_FILE')); print(d['timestamp'])")
    BATCH_COUNT=$(python3  -c "import json; d=json.load(open('$RENDER_CONFIG_FILE')); print(len(d['batches']))")

    # Populate batch arrays from JSON
    while IFS='|' read -r b_start b_end b_name b_priority; do
        BATCH_STARTS+=("$b_start")
        BATCH_ENDS+=("$b_end")
        BATCH_NAMES+=("$b_name")
        BATCH_PRIORITIES+=("$b_priority")
    done < <(python3 -c "
import json
d = json.load(open('$RENDER_CONFIG_FILE'))
for i, b in enumerate(d['batches']):
    name = b.get('name') or 'Batch ' + str(i+1)
    priority = b.get('priority') or 'null'
    print(f\"{b['start']}|{b['end']}|{name}|{priority}\")
")

    echo "Project:     $PROJECT_NAME"
    echo "Blend File:  $BLEND_FILE"
    echo "Blender:     $BLENDER_PATH"
    echo "Output Dir:  $OUTPUT_DIR"
    echo "Batches:     $BATCH_COUNT"
    echo

    CONFIG_MODE=true
fi

# ================================================================
#  INTERACTIVE MODE — run directly from Terminal (no config file)
# ================================================================
if [ "$CONFIG_MODE" = false ]; then

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

    echo "================================================================"
    echo "                    Batch Queue Setup"
    echo "================================================================"
    echo "Define frame ranges for rendering batches."
    echo "You can add as many batches as needed."
    echo

    # Interactive batch input loop
    while true; do
        BATCH_NUM=$((BATCH_COUNT + 1))
        echo "────────────────────────────────────────────────────────────────"
        echo "Batch #$BATCH_NUM"
        echo

        # Get start frame
        while true; do
            read -p "  Start Frame (or 'done' to finish, 'cancel' to abort): " START_INPUT

            if [[ "$START_INPUT" == "done" ]] || [[ "$START_INPUT" == "d" ]]; then
                if [ $BATCH_COUNT -eq 0 ]; then
                    echo "  ⚠️  You must add at least one batch before finishing."
                    continue
                fi
                break 2
            fi

            if [[ "$START_INPUT" == "cancel" ]] || [[ "$START_INPUT" == "c" ]]; then
                echo
                echo "❌ Batch setup cancelled."
                exit 0
            fi

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

            if [[ "$END_INPUT" =~ ^[0-9]+$ ]]; then
                END_FRAME=$END_INPUT

                if [ $END_FRAME -lt $START_FRAME ]; then
                    echo "  ⚠️  End frame must be >= start frame ($START_FRAME)"
                    continue
                fi
                break
            else
                echo "  ⚠️  Invalid input. Please enter a number."
            fi
        done

        FRAME_COUNT=$((END_FRAME - START_FRAME + 1))

        read -p "  Batch Name (optional, press Enter to skip): " BATCH_NAME
        if [ -z "$BATCH_NAME" ]; then
            BATCH_NAME="Batch $BATCH_NUM"
        fi

        while true; do
            read -p "  Priority (1=High, 0=Low, or press Enter to skip) [skip]: " PRIORITY_INPUT

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

        BATCH_STARTS+=($START_FRAME)
        BATCH_ENDS+=($END_FRAME)
        BATCH_NAMES+=("$BATCH_NAME")
        BATCH_PRIORITIES+=("$PRIORITY")
        BATCH_COUNT=$((BATCH_COUNT + 1))

        echo "  ✅ Added: $BATCH_NAME [Priority: $PRIORITY] (Frames $START_FRAME-$END_FRAME, $FRAME_COUNT frames)"
        echo
    done

fi  # end interactive mode

# ================================================================
#  Verify paths (both modes)
# ================================================================
if [ ! -f "$BLENDER_PATH" ]; then
    echo "❌ Error: Blender not found at $BLENDER_PATH"
    exit 1
fi

if [ ! -f "$BLEND_FILE" ]; then
    echo "❌ Error: Blend file not found at $BLEND_FILE"
    exit 1
fi

# Ensure output directory exists (may already exist in config mode)
mkdir -p "$OUTPUT_DIR"

# ================================================================
#  Sort batches by priority (High → Low) then frame count (small → large)
# ================================================================
echo
echo "🔄 Sorting batches by priority (High→Low) and frame count (small→large)..."

declare -a SORT_INDICES=()
for i in "${!BATCH_STARTS[@]}"; do
    SORT_INDICES+=($i)
done

for ((i=0; i<${#SORT_INDICES[@]}; i++)); do
    for ((j=i+1; j<${#SORT_INDICES[@]}; j++)); do
        idx_i=${SORT_INDICES[$i]}
        idx_j=${SORT_INDICES[$j]}

        priority_i=${BATCH_PRIORITIES[$idx_i]}
        priority_j=${BATCH_PRIORITIES[$idx_j]}

        frames_i=$(( BATCH_ENDS[$idx_i] - BATCH_STARTS[$idx_i] + 1 ))
        frames_j=$(( BATCH_ENDS[$idx_j] - BATCH_STARTS[$idx_j] + 1 ))

        [[ "$priority_i" == "1" ]] && pri_val_i=3 || { [[ "$priority_i" == "0" ]] && pri_val_i=2 || pri_val_i=1; }
        [[ "$priority_j" == "1" ]] && pri_val_j=3 || { [[ "$priority_j" == "0" ]] && pri_val_j=2 || pri_val_j=1; }

        SHOULD_SWAP=0
        if [ $pri_val_j -gt $pri_val_i ]; then
            SHOULD_SWAP=1
        elif [ $pri_val_j -eq $pri_val_i ] && [ $frames_j -lt $frames_i ]; then
            SHOULD_SWAP=1
        fi

        if [ $SHOULD_SWAP -eq 1 ]; then
            temp=${SORT_INDICES[$i]}
            SORT_INDICES[$i]=${SORT_INDICES[$j]}
            SORT_INDICES[$j]=$temp
        fi
    done
done

# Calculate total frames
TOTAL_FRAMES=0
for i in "${!BATCH_STARTS[@]}"; do
    FRAMES=$(( BATCH_ENDS[$i] - BATCH_STARTS[$i] + 1 ))
    TOTAL_FRAMES=$((TOTAL_FRAMES + FRAMES))
done

# ================================================================
#  Summary table
# ================================================================
echo
echo "================================================================"
echo "              Batch Queue Summary (Sorted by Priority)"
echo "================================================================"
echo "Total Batches: $BATCH_COUNT"
echo "Total Frames:  $TOTAL_FRAMES"
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

# In interactive mode, confirm before starting
if [ "$CONFIG_MODE" = false ]; then
    read -p "Start rendering? (Y/n): " CONFIRM
    if [[ "$CONFIRM" =~ ^[Nn] ]]; then
        echo "❌ Render cancelled."
        exit 0
    fi
fi

echo
echo "================================================================"
echo "                  Starting Render Process"
echo "================================================================"
echo

# ================================================================
#  Render loop — output tee'd to log file
# ================================================================
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
