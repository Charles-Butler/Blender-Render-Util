# Blend File Selection - Implementation

## Problem
The blend file dropdown was empty because no recent files were configured.

## Solution

### 1. Added Default File to Config
Updated `server/config.json` to include your default blend file:
```json
{
  "blender": {
    "last_blend_file": "/Users/me/Podcast/3D-Animation/WIP - Blender/Delivery/FILE ANIM/TOR_caseSwap.blend",
    "recent_blend_files": [
      "/Users/me/Podcast/3D-Animation/WIP - Blender/Delivery/FILE ANIM/TOR_caseSwap.blend"
    ]
  }
}
```

### 2. Created File Browser API
Added new endpoint in `server/app.py`:
- `GET /api/blend-files/browse` - Scans common directories for .blend files
- Returns up to 50 most recent .blend files
- Scans:
  - `/Users/me/Podcast/3D-Animation/WIP - Blender`
  - `/Users/me/Podcast/3D-Animation/Scenes`
  - `~/Documents`
  - `~/Desktop`

### 3. Enhanced Frontend UI
Updated `ConfigureRender.jsx`:
- Added "Browse for More Files" button
- Created modal dialog to display available .blend files
- Click any file to select it and add to recent files
- Files sorted by modification date (newest first)

## Usage

### Method 1: Select from Recent Files
1. Open configure page
2. Click dropdown under "Blend File"
3. Select from recently used files

### Method 2: Browse for Files
1. Click "Browse for More Files" button
2. Modal opens showing all .blend files found
3. Click any file to select it
4. File is automatically added to recent files

### Method 3: Manual API Call
```bash
curl -X POST http://localhost:8081/api/blend-files/add \
  -H "Content-Type: application/json" \
  -d '{"filepath": "/path/to/your/file.blend"}'
```

## Files Modified

1. **server/config.json** - Added default blend file
2. **server/app.py** - Added `/api/blend-files/browse` endpoint
3. **frontend/src/pages/ConfigureRender.jsx** - Added file browser modal
4. **frontend/src/pages/ConfigureRender.css** - Added modal styles

## Testing

Restart the backend and frontend servers, then:

1. Navigate to http://localhost:5173
2. You should now see your default file in the dropdown
3. Click "Browse for More Files" to scan for additional files
4. Selected files appear immediately in the dropdown
