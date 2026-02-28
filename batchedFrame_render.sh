#!/bin/bash

# Ask user for case/game name
echo "================================================================"
echo "             Starting Case Re-Animation Batch Render"
echo "================================================================"
read -p "Enter Case/Game Name (no spaces, use underscores if needed): " CASE_NAME
echo "Case Name Set To: $CASE_NAME"
echo
echo "Preparing to render scenes..."

# Generate timestamp
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)

# Create output directory
OUTPUT_DIR="./renders/${CASE_NAME}_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"
echo "Created output directory at: $OUTPUT_DIR"

# Set log file path
LOGFILE="${OUTPUT_DIR}/${CASE_NAME}_${TIMESTAMP}_render_log.txt"

# Start capturing output
{
    echo "================================================================"
    echo "🎬 Rendering Batch for: $CASE_NAME at $TIMESTAMP"
    echo "================================================================"

    # Define .blend file path & Blender App Path
    BLEND_FILE="/Users/me/Podcast/3D-Animation/WIP - Blender/Delivery/FILE ANIM/TOR_caseSwap.blend"
    BLENDER_PATH="/Applications/Blender.app/Contents/MacOS/Blender"

    # # Batch 5
    echo "--------------------------------------------"
    echo "🎬 Now Rendering Scenes: 973 - 999"
    $BLENDER_PATH -b "$BLEND_FILE" -s 973 -e 999 -a
    echo "✅ Finished Scenes: 973 - 999"
    echo "--------------------------------------------"

    # Batch 8
    echo "--------------------------------------------"
    echo "🎬 Now Rendering Scenes: 001 - 059"
    $BLENDER_PATH -b "$BLEND_FILE" -s 0 -e 59 -a
    echo "✅ Finished Scenes: 001 - 059"
    echo "--------------------------------------------"

    # # Batch 6
    echo "--------------------------------------------"
    echo "🎬 Now Rendering Scenes: 1059 - 1130"
    $BLENDER_PATH -b "$BLEND_FILE" -s 1059 -e 1130 -a
    echo "✅ Finished Scenes: 1059 - 1130"
    echo "--------------------------------------------"

    # # Batch 4
    echo "--------------------------------------------"
    echo "🎬 Now Rendering Scenes: 795 - 869"
    $BLENDER_PATH -b "$BLEND_FILE" -s 795 -e 869 -a
    echo "✅ Finished Scenes: 795 - 869"
    echo "--------------------------------------------"

    # # Batch 7
    echo "--------------------------------------------"
    echo "🎬 Now Rendering Scenes: 1130 - 1230"
    $BLENDER_PATH -b "$BLEND_FILE" -s 1130 -e 1230 -a
    echo "✅ Finished Scenes: 1130 - 1230"
    echo "--------------------------------------------"

    # Batch 2
    echo "--------------------------------------------"
    echo "🎬 Now Rendering Scenes: 642 - 672"
    $BLENDER_PATH -b "$BLEND_FILE" -s 642 -e 672 -a
    echo "✅ Finished Scenes: 642 - 672"
    echo "--------------------------------------------"

    # # Batch 3
    echo "--------------------------------------------"
    echo "🎬 Now Rendering Scenes: 702 - 755"
    $BLENDER_PATH -b "$BLEND_FILE" -s 702 -e 755 -a
    echo "✅ Finished Scenes: 702 - 755"
    echo "--------------------------------------------"

    # # Batch 1
    echo "--------------------------------------------"
    echo "🎬 Now Rendering Scenes: 494 - 600"
    $BLENDER_PATH -b "$BLEND_FILE" -s 494 -e 600 -a
    echo "✅ Finished Scenes: 494 - 600"
    echo "--------------------------------------------"

    echo
    echo "================================================================"
    echo "🏁 ALL RENDERING JOBS COMPLETED SUCCESSFULLY for $CASE_NAME!"
    echo "================================================================"

    # Ding sound
    afplay /System/Library/Sounds/Glass.aiff

} | tee "$LOGFILE"
