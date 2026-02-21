# Installation Scripts

This directory contains installation and deployment scripts for RGB-Rebuilt-1806.

## Files

### install.sh
Main installation script for Orange Pi 5 and Raspberry Pi 5.

**Usage**:
```bash
chmod +x install.sh
sudo ./install.sh
```

**What it does**:
- Detects platform (Orange Pi 5, Raspberry Pi 5, or generic Linux)
- Installs system dependencies (Python 3, pip, dev tools)
- Enables SPI interface
- Creates Python virtual environment
- Installs Python packages in venv
- Sets up systemd service
- Configures user groups and permissions

**Requirements**:
- Must be run as root (sudo)
- Internet connection for package downloads
- Debian/Ubuntu-based Linux distribution

### run_headless.sh
Simple script to run RGB-Reefscape in headless mode with logging.

**Usage**:
```bash
chmod +x run_headless.sh
./run_headless.sh
```

**Features**:
- Automatic log file creation
- Timestamped logging
- Falls back to simulation if SPI not available
- Can be used for manual testing

### systemd/rgb-reefscape.service
Systemd service unit file for automatic startup.

**Installation**:
Service is automatically installed by install.sh

**Manual installation**:
```bash
sudo cp systemd/rgb-reefscape.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rgb-reefscape
sudo systemctl start rgb-reefscape
```

**Management**:
```bash
# Start
sudo systemctl start rgb-reefscape

# Stop
sudo systemctl stop rgb-reefscape

# Restart
sudo systemctl restart rgb-reefscape

# Status
sudo systemctl status rgb-reefscape

# View logs
sudo journalctl -u rgb-reefscape -f

# Enable auto-start on boot
sudo systemctl enable rgb-reefscape

# Disable auto-start
sudo systemctl disable rgb-reefscape
```

## Platform Support

| Platform | Tested | Notes |
|----------|--------|-------|
| Orange Pi 5 | ✓ | Primary target platform |
| Raspberry Pi 5 | ✓ | Fully supported |
| Raspberry Pi 4 | ✓ | Should work (untested) |
| Raspberry Pi 3 | ✓ | Should work (untested) |
| Other SBCs | ? | May work if SPI is available |

## Troubleshooting

### install.sh fails with "permission denied"
Make script executable:
```bash
chmod +x install.sh
```

Run as root:
```bash
sudo ./install.sh
```

### SPI not enabled after installation
Reboot is required:
```bash
sudo reboot
```

### Service fails to start
Check logs:
```bash
sudo journalctl -u rgb-reefscape -n 50
```

Test manually:
```bash
python3 -m rgb_reefscape.main --verbose
```

### Python packages not found
The project uses a virtual environment. Reinstall:
```bash
# Remove old venv
rm -rf venv

# Reinstall
sudo ./install.sh
```

Or activate venv and install manually:
```bash
source venv/bin/activate
pip install -e .
```

## Development

### Testing install script
Test in simulation mode:
```bash
# Edit config.yaml
simulation:
  enabled: true
  mock_network_tables: true

# Run install
sudo ./install.sh

# Activate venv and test
source venv/bin/activate
python3 -m rgb_reefscape.main --simulate
```

### Manual development setup
For development without running install script:
```bash
# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Install in editable mode
pip install -e .

# Run
python3 -m rgb_reefscape.main --simulate --verbose
```

### Modifying systemd service
1. Edit `systemd/rgb-reefscape.service`
2. Reinstall:
   ```bash
   sudo cp systemd/rgb-reefscape.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl restart rgb-reefscape
   ```

## Files Structure

```
scripts/
├── README.md              # This file
├── install.sh             # Main installation script
├── run_headless.sh        # Headless runner script
└── systemd/
    └── rgb-reefscape.service  # Systemd service unit
```

## See Also

- [Main README](../README.md) - Full project documentation
- [WIRING.md](../WIRING.md) - Wiring diagrams and pinouts
- [QUICK_START.md](../QUICK_START.md) - Quick start guide
- [config.yaml](../config.yaml) - Configuration file
