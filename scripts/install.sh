#!/bin/bash
#
# RGB-Rebuilt-1806 Installation Script
# For Orange Pi 5 and Raspberry Pi 5
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "RGB-Rebuilt-1806 Installation"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

# Detect platform
echo -e "${GREEN}Detecting platform...${NC}"
if grep -q "orangepi" /proc/device-tree/model 2>/dev/null || grep -q "Orange Pi" /etc/os-release 2>/dev/null; then
    PLATFORM="orangepi"
    echo "Detected: Orange Pi"
elif grep -q "Raspberry Pi 5" /proc/device-tree/model 2>/dev/null; then
    PLATFORM="rpi5"
    echo "Detected: Raspberry Pi 5"
elif grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    PLATFORM="rpi"
    echo "Detected: Raspberry Pi (older model)"
else
    PLATFORM="unknown"
    echo -e "${YELLOW}Warning: Could not detect platform, assuming generic Linux${NC}"
fi

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-$USER}"
if [ "$ACTUAL_USER" = "root" ]; then
    echo -e "${YELLOW}Warning: Could not determine actual user, defaulting to 'pi'${NC}"
    ACTUAL_USER="pi"
fi

echo "Installing for user: $ACTUAL_USER"
echo ""

# Update package lists
echo -e "${GREEN}Updating package lists...${NC}"
apt-get update

# Install system dependencies
echo -e "${GREEN}Installing system dependencies...${NC}"
apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    git

# Enable SPI interface
echo -e "${GREEN}Configuring SPI interface...${NC}"

if [ "$PLATFORM" = "orangepi" ]; then
    # Orange Pi SPI setup
    if [ -f "/boot/orangepiEnv.txt" ]; then
        echo "Checking Orange Pi SPI overlay..."
        if ! grep -q "^overlays=.*spi-spidev" /boot/orangepiEnv.txt; then
            echo "Enabling SPI overlay in orangepiEnv.txt..."
            sed -i 's/^overlays=\(.*\)/overlays=\1 spi-spidev/' /boot/orangepiEnv.txt
            echo -e "${YELLOW}Note: Reboot required for SPI changes to take effect${NC}"
        else
            echo "SPI overlay already enabled"
        fi
    else
        echo -e "${YELLOW}Warning: Could not find /boot/orangepiEnv.txt${NC}"
        echo "You may need to enable SPI manually using orangepi-config"
    fi
elif [ "$PLATFORM" = "rpi5" ] || [ "$PLATFORM" = "rpi" ]; then
    # Raspberry Pi SPI setup
    if [ -f "/boot/config.txt" ]; then
        echo "Checking Raspberry Pi SPI configuration..."
        if ! grep -q "^dtparam=spi=on" /boot/config.txt; then
            echo "Enabling SPI in /boot/config.txt..."
            echo "dtparam=spi=on" >> /boot/config.txt
            echo -e "${YELLOW}Note: Reboot required for SPI changes to take effect${NC}"
        else
            echo "SPI already enabled"
        fi
    elif [ -f "/boot/firmware/config.txt" ]; then
        echo "Checking Raspberry Pi SPI configuration (new location)..."
        if ! grep -q "^dtparam=spi=on" /boot/firmware/config.txt; then
            echo "Enabling SPI in /boot/firmware/config.txt..."
            echo "dtparam=spi=on" >> /boot/firmware/config.txt
            echo -e "${YELLOW}Note: Reboot required for SPI changes to take effect${NC}"
        else
            echo "SPI already enabled"
        fi
    else
        echo -e "${YELLOW}Warning: Could not find config.txt${NC}"
    fi
fi

# Add user to spi group (if it exists)
if getent group spi > /dev/null 2>&1; then
    echo "Adding $ACTUAL_USER to spi group..."
    usermod -a -G spi "$ACTUAL_USER"
else
    echo "spi group does not exist, skipping..."
fi

# Add user to dialout group (for serial/USB if needed)
if getent group dialout > /dev/null 2>&1; then
    echo "Adding $ACTUAL_USER to dialout group..."
    usermod -a -G dialout "$ACTUAL_USER"
fi

# Install Python packages
echo -e "${GREEN}Installing Python dependencies...${NC}"

# Get project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Project directory: $PROJECT_DIR"

# Install as the actual user (not root)
echo "Installing RGB-Rebuilt-1806 Python package..."
sudo -u "$ACTUAL_USER" pip3 install --user -e "$PROJECT_DIR"

# Install systemd service
echo -e "${GREEN}Installing systemd service...${NC}"

SERVICE_FILE="$PROJECT_DIR/scripts/systemd/rgb-reefscape.service"
if [ -f "$SERVICE_FILE" ]; then
    # Replace placeholder username in service file
    sed "s/USER_PLACEHOLDER/$ACTUAL_USER/g" "$SERVICE_FILE" > /etc/systemd/system/rgb-reefscape.service
    sed -i "s|WORKING_DIR_PLACEHOLDER|$PROJECT_DIR|g" /etc/systemd/system/rgb-reefscape.service

    systemctl daemon-reload
    echo "Service installed: /etc/systemd/system/rgb-reefscape.service"
else
    echo -e "${YELLOW}Warning: Service file not found at $SERVICE_FILE${NC}"
fi

# Check if SPI device exists
echo ""
echo -e "${GREEN}Verifying SPI device...${NC}"
if [ -e "/dev/spidev0.0" ]; then
    echo -e "${GREEN}✓ SPI device /dev/spidev0.0 found${NC}"
    ls -l /dev/spidev0.0
else
    echo -e "${YELLOW}✗ SPI device /dev/spidev0.0 not found${NC}"
    echo "  You may need to reboot for SPI to be enabled"
fi

# Create config if it doesn't exist in user's home
USER_CONFIG_DIR="/home/$ACTUAL_USER/.config/rgb-reefscape"
if [ ! -f "$USER_CONFIG_DIR/config.yaml" ]; then
    echo ""
    echo "Creating user config directory..."
    sudo -u "$ACTUAL_USER" mkdir -p "$USER_CONFIG_DIR"
    if [ -f "$PROJECT_DIR/config.yaml" ]; then
        sudo -u "$ACTUAL_USER" cp "$PROJECT_DIR/config.yaml" "$USER_CONFIG_DIR/config.yaml"
        echo "Copied default config to $USER_CONFIG_DIR/config.yaml"
    fi
fi

# Installation complete
echo ""
echo "======================================"
echo -e "${GREEN}Installation Complete!${NC}"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit configuration: nano $PROJECT_DIR/config.yaml"
echo "   - Update team_number"
echo "   - Adjust LED count if needed"
echo "   - Configure section layout"
echo ""
echo "2. Wire your LEDs (see WIRING.md):"
echo "   - Connect LED data to SPI MOSI"
echo "   - Connect 12V power supply"
echo "   - Connect common ground"
echo ""
echo "3. Test the installation:"
echo "   python3 -m rgb_reefscape.main --simulate --verbose"
echo ""
echo "4. Enable and start the service:"
echo "   sudo systemctl enable rgb-reefscape"
echo "   sudo systemctl start rgb-reefscape"
echo ""
echo "5. Check service status:"
echo "   sudo systemctl status rgb-reefscape"
echo "   sudo journalctl -u rgb-reefscape -f"
echo ""

if [ ! -e "/dev/spidev0.0" ]; then
    echo -e "${YELLOW}⚠ Important: SPI device not found. Reboot required!${NC}"
    echo "   sudo reboot"
    echo ""
fi

echo "For more information, see README.md"
echo ""
