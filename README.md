# RGB-Rebuilt-1806

FRC Robot LED Controller for Orange Pi 5 controlling WS2811/WS2812B RGB LEDs with Network Tables integration for the 2026 FIRST Robotics Competition season. Designed to run alongside PhotonVision on the same device.

## Features

- **Network Tables Integration**: Communicates with RoboRio via Network Tables (pyntcore)
- **Time Display**: Visual countdown for active/inactive game periods
- **Multiple Sections**: Support for multiple sections of same type (e.g., time displays on 2+ sides)
- **Vision Status**: Real-time PhotonVision connection and target indicators
- **Swerve Alignment**: Pre-match display showing module alignment status
- **Notification System**: Priority-based queue for robot status notifications
- **Asyncio Architecture**: Efficient I/O handling without threading complexity
- **SPI-Based Control**: Uses SPI interface (no root required, compatible with PhotonVision)
- **Headless Operation**: Runs as systemd service on Orange Pi 5
- **FRC Compliant**: Uses only approved Network Tables protocol
- **Configurable**: YAML-based configuration for easy customization

## Hardware Requirements

- Orange Pi 5
- BTF-LIGHTING WS2811/WS2812B IC RGB LED Strip (150 LEDs)
- 12VDC Power Supply for LEDs (5A+ recommended)
- Logic Level Shifter (74HCT245 or similar)
- SPI connection (uses /dev/spidev0.0)

**📘 See [WIRING.md](WIRING.md) for complete wiring diagrams and pinouts!**

## Installation

### On Orange Pi 5

1. **Clone the repository**:
   ```bash
   git clone https://github.com/swat1806/RGB-Rebuilt-1806.git
   cd RGB-Rebuilt-1806
   ```

2. **Run the installation script**:
   ```bash
   sudo chmod +x scripts/install.sh
   sudo ./scripts/install.sh
   ```

   This will:
   - Install system dependencies
   - Set up Python environment
   - Enable and configure SPI interface
   - Install systemd service

3. **Wire your LEDs**:
   - Follow the detailed wiring guide: [WIRING.md](WIRING.md)
   - Connect LED data to SPI MOSI (Pin 19)
   - Connect 12V external power supply
   - Establish common ground

4. **Edit configuration**:
   ```bash
   nano config.yaml
   ```
   Update team number, LED count, SPI device, and other settings as needed.

5. **Enable and start the service**:
   ```bash
   sudo systemctl enable rgb-reefscape
   sudo systemctl start rgb-reefscape
   ```

### Manual Installation

If you prefer manual installation:

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip

# Enable SPI interface (if not already enabled)
# This varies by Orange Pi configuration tool
# On some systems: sudo orangepi-config -> System -> Hardware -> spi-spidev

# Install Python packages
pip3 install -r requirements.txt

# Install the package
pip3 install -e .

# Set up SPI permissions (if needed)
sudo usermod -a -G spi $USER

# Reboot for SPI and group changes to take effect
sudo reboot
```

## Configuration

Edit [config.yaml](config.yaml) to customize:

- **LED Hardware**: SPI device, LED count, brightness
- **Network Tables**: Team number or server address
- **Sections**: How to partition the LED strip (supports multiple sections of same type!)
- **Colors**: RGB values for different states
- **Notifications**: Priorities and durations

Example configuration structure:
```yaml
hardware:
  led_count: 150
  spi_dev: "/dev/spidev0.0"
  brightness: 128

network_tables:
  team_number: 1806

sections:
  # Supports multiple sections with same type for wrapping around robot
  time_display_left:
    type: time_display    # Groups sections by purpose
    start: 0
    length: 50
    direction: "right"

  notifications:
    type: notifications
    start: 50
    length: 50

  time_display_right:
    type: time_display    # Second time display on opposite side
    start: 100
    length: 50
    direction: "left"
```

**📘 For detailed section configuration guide with examples, see [docs/SECTIONS.md](docs/SECTIONS.md)**

## Network Tables Topics

RGB-Rebuilt-1806 subscribes to the following Network Tables topics from the RoboRio:

### FMS Information
- `/FMSInfo/MatchNumber` (int)
- `/FMSInfo/EventName` (string)

### Robot State
- `/Robot/MatchState` (string): "pre-match", "auto", "teleop", "endgame"
- `/Robot/Timer/GoalActive` (boolean): Whether goal is currently active
- `/Robot/Timer/TimeRemaining` (float): Seconds remaining in period

### Vision
- `/Robot/Vision/Connected` (boolean): PhotonVision connection status
- `/Robot/Vision/HasTargets` (boolean): Whether targets are detected

### Swerve Drive
- `/Robot/Swerve/ModuleAligned` (boolean array): Alignment status for each module [FL, FR, BL, BR]

### Mechanisms
- `/Robot/Flywheel/AtSpeed` (boolean): Flywheel ready status
- `/Robot/Climb/Complete` (boolean): Climb completion status

### Notifications
- `/Robot/Notifications/*`: Custom notification topics

### Published Topics
RGB-Reefscape publishes:
- `/LED/Status/Connected` (boolean): LED controller connection status
- `/LED/Status/Error` (string): Error messages

## Usage

### Running Manually

```bash
# Run with default config
python3 -m rgb_reefscape.main

# Run with custom config
python3 -m rgb_reefscape.main --config /path/to/config.yaml

# Run in simulation mode (no hardware required)
python3 -m rgb_reefscape.main --simulate
```

### Running as Service

```bash
# Start service
sudo systemctl start rgb-reefscape

# Stop service
sudo systemctl stop rgb-reefscape

# Check status
sudo systemctl status rgb-reefscape

# View logs
sudo journalctl -u rgb-reefscape -f
```

## Display Modes

### Time Display
- **Inactive Period**: White LEDs counting down
- **Active Period**: Green LEDs counting down
- **Direction**: Configurable (left, right, center)

### Vision Status
- **Green Pulse**: Connected with targets
- **Yellow Pulse**: Connected, no targets
- **Red Flash**: Disconnected or error

### Swerve Alignment (Pre-match)
- 4 sections showing each swerve module
- **Green**: Module aligned
- **Red**: Module not aligned

### Notifications
Priority-based display for:
- Climb complete (success animation)
- Flywheel at speed (spinning animation)
- Vision target acquired
- Custom notifications

## Development

### Running Tests

```bash
# Install development dependencies
pip3 install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=rgb_reefscape tests/
```

### Simulation Mode

For development without Orange Pi hardware:

```python
# In config.yaml
simulation:
  enabled: true
  mock_network_tables: true
```

Or run with `--simulate` flag:
```bash
python3 -m rgb_reefscape.main --simulate
```

### USB Simulator

For driver station testing, use the USB simulator:

```bash
# On driver station laptop
python3 simulator/desktop_app.py --team 1806

# Connect Pi via USB and it will receive NT data over serial
```

## Troubleshooting

### LEDs don't light up
- Check SPI is enabled: `ls /dev/spidev*` should show `/dev/spidev0.0`
- Verify SPI permissions: User should have access to SPI device
- Check power supply: LEDs need separate 12V power
- Verify wiring: Data line to SPI MOSI, common ground
- Test manual run: `python3 -m rgb_reefscape.main --simulate --verbose`

### Network Tables connection fails
- Verify team number in config.yaml
- Check network connectivity: `ping 10.18.6.2`
- Ensure RoboRio is publishing expected topics
- Check firewall settings
- Verify PhotonVision isn't blocking ports

### Service won't start
- Check logs: `sudo journalctl -u rgb-reefscape -n 50`
- Verify installation: `systemctl status rgb-reefscape`
- Test manual run: `python3 -m rgb_reefscape.main`

### Orange Pi 5 SPI issues
- Enable SPI in boot config if not already enabled
- Check SPI device exists: `ls -l /dev/spidev0.0`
- Add user to spi group if needed: `sudo usermod -a -G spi $USER`
- Ensure `ws2812-spi` library is installed correctly

### PhotonVision conflicts
- RGB controller runs independently alongside PhotonVision
- Both can coexist on Orange Pi 5
- Check system resources if performance issues occur

## Project Structure

```
RGB-Rebuilt-1806/
├── rgb_reefscape/          # Main package
│   ├── main.py             # Entry point
│   ├── led_controller.py   # LED hardware interface
│   ├── nt_client.py        # Network Tables client
│   ├── config.py           # Configuration management
│   ├── section_manager.py  # LED section partitioning
│   ├── notification_queue.py  # Priority queue
│   └── display_modes/      # Display mode implementations
├── tests/                  # Unit tests
├── scripts/                # Installation and deployment
│   ├── install.sh
│   ├── run_headless.sh
│   └── systemd/
└── simulator/              # USB simulator for testing
```

## FRC Compliance

This project complies with FRC control system rules:
- Uses only Network Tables for communication (approved protocol)
- Does not interfere with robot control systems
- Operates on Orange Pi 5 alongside PhotonVision, not on RoboRio
- No custom network protocols
- SPI-based LED control does not conflict with other processes

## Contributing

This is a team project for SWAT Team 1806. For issues or suggestions, please contact the programming team.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- FIRST Robotics Competition for the game and rules
- WPILib for Network Tables (ntcore)
- rpi-ws281x library for LED control
- SWAT Team 1806 for design and implementation
