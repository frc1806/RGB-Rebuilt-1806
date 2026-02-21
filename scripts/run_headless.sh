#!/bin/bash
#
# RGB-Rebuilt-1806 Headless Runner
# Simple script to run RGB controller in headless mode
#

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project directory
cd "$PROJECT_DIR"

# Set Python unbuffered for real-time logging
export PYTHONUNBUFFERED=1

# Log file
LOG_FILE="/var/log/rgb-reefscape.log"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "RGB-Rebuilt-1806 Starting"
log "========================================="
log "Project directory: $PROJECT_DIR"
log "Python: $(which python3)"
log "User: $USER"

# Check if config exists
if [ -f "$PROJECT_DIR/config.yaml" ]; then
    log "Config file found: $PROJECT_DIR/config.yaml"
else
    log "WARNING: Config file not found at $PROJECT_DIR/config.yaml"
fi

# Check SPI device
if [ -e "/dev/spidev0.0" ]; then
    log "SPI device found: /dev/spidev0.0"
else
    log "WARNING: SPI device not found at /dev/spidev0.0"
    log "Running in simulation mode..."
    SIMULATE_FLAG="--simulate"
fi

# Run the application
log "Starting RGB-Rebuilt-1806..."
python3 -m rgb_reefscape.main $SIMULATE_FLAG 2>&1 | tee -a "$LOG_FILE"

# Capture exit code
EXIT_CODE=$?

log "RGB-Rebuilt-1806 exited with code: $EXIT_CODE"

exit $EXIT_CODE
