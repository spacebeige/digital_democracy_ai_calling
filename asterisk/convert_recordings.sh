#!/bin/bash
# GSM to MP4 Recording Converter Script
# Monitors the recordings folder and converts new GSM files to MP4

RECORDINGS_DIR="/var/lib/asterisk/sounds/recordings"
WINDOWS_RECORDINGS="/mnt/c/asterrisk-innovates/recordings"
LOG_FILE="/var/log/asterisk-convert.log"

# Create log file
touch "$LOG_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Recording converter started" >> "$LOG_FILE"

# Function to convert GSM to MP4
convert_gsm_to_mp4() {
    local gsm_file="$1"
    local filename=$(basename "$gsm_file" .gsm)
    local mp4_file="${RECORDINGS_DIR}/${filename}.mp4"
    local windows_mp4="${WINDOWS_RECORDINGS}/${filename}.mp4"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Converting: $gsm_file" >> "$LOG_FILE"
    
    # Convert GSM to MP4 using ffmpeg
    ffmpeg -i "$gsm_file" \
           -c:a aac \
           -b:a 128k \
           -pix_fmt yuv420p \
           "$mp4_file" -y 2>> "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ Conversion successful: $mp4_file" >> "$LOG_FILE"
        
        # Copy to Windows folder
        cp "$mp4_file" "$windows_mp4" 2>> "$LOG_FILE"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ Copied to Windows: $windows_mp4" >> "$LOG_FILE"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✗ Conversion FAILED: $gsm_file" >> "$LOG_FILE"
    fi
}

# Check if inotifywait is installed
if ! command -v inotifywait &> /dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Installing inotify-tools..." >> "$LOG_FILE"
    sudo apt-get update -qq >> "$LOG_FILE" 2>&1
    sudo apt-get install -y inotify-tools >> "$LOG_FILE" 2>&1
fi

# Monitor directory for new GSM files
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Monitoring $RECORDINGS_DIR for new recordings..." >> "$LOG_FILE"

inotifywait -m -e close_write -e moved_to --format '%w%f' "$RECORDINGS_DIR" |
while read -r new_file; do
    # Only process GSM files
    if [[ "$new_file" == *.gsm ]]; then
        # Wait a moment to ensure file is fully written
        sleep 1
        convert_gsm_to_mp4 "$new_file"
    fi
done
