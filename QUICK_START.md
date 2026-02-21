# RGB-Rebuilt-1806 Quick Start Guide

Fast installation and setup for competition day.

## Pre-Installation Checklist

- [ ] Orange Pi 5 with Orange Pi OS or Ubuntu
- [ ] 150 LED WS2812B strip (12V)
- [ ] Logic level shifter (74HCT245)
- [ ] 12V 5A power supply
- [ ] Wires and connectors
- [ ] Access to robot network (10.18.6.x)

## Installation (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/swat1806/RGB-Rebuilt-1806.git
cd RGB-Rebuilt-1806

# 2. Run installer
chmod +x scripts/install.sh
sudo ./scripts/install.sh

# 3. Reboot (if SPI was enabled)
sudo reboot
```

## Wiring (Quick Reference)

```
Orange Pi 5 Pin 19 (SPI MOSI) → Level Shifter A1
Orange Pi 5 Pin 6 (GND)       → Common Ground
Orange Pi 5 Pin 17 (3.3V)     → Level Shifter LV
Orange Pi 5 Pin 2 (5V)        → Level Shifter HV

Level Shifter B1              → LED Strip DIN
12V Power (+)                 → LED Strip +12V
12V Power (-)                 → Common Ground
```

**Full diagrams**: See [WIRING.md](WIRING.md)

## Configuration (2 minutes)

```bash
# Edit config
nano config.yaml

# Key settings:
# - team_number: 1806
# - led_count: 150
# - spi_dev: "/dev/spidev0.0"
```

## Testing (1 minute)

```bash
# Activate virtual environment
source venv/bin/activate

# Test simulation mode
python3 -m rgb_reefscape.main --simulate --verbose

# Test with hardware
python3 -m rgb_reefscape.main --verbose
```

## Enable Service (1 minute)

```bash
# Start on boot
sudo systemctl enable rgb-reefscape
sudo systemctl start rgb-reefscape

# Check status
sudo systemctl status rgb-reefscape

# View live logs
sudo journalctl -u rgb-reefscape -f
```

## Troubleshooting

### LEDs Don't Light

```bash
# Check SPI device
ls -l /dev/spidev0.0

# If missing, enable SPI and reboot
sudo nano /boot/orangepiEnv.txt
# Add 'spi-spidev' to overlays line
sudo reboot
```

### Network Tables Won't Connect

```bash
# Check network
ping 10.18.6.2

# Check config
nano config.yaml
# Verify team_number: 1806

# Check RoboRio is running and publishing data
```

### Service Won't Start

```bash
# Check logs
sudo journalctl -u rgb-reefscape -n 50

# Try manual run (activate venv first)
source venv/bin/activate
python3 -m rgb_reefscape.main --verbose

# Check Python installation in venv
source venv/bin/activate
pip list | grep -E "ws2812|pyntcore|PyYAML"
```

## Network Tables Topics (for Robot Code)

Your RoboRio must publish these topics:

```java
// Time & Match State
NetworkTableInstance.getDefault().getEntry("Robot/MatchState").setString("teleop");
NetworkTableInstance.getDefault().getEntry("Robot/Timer/GoalActive").setBoolean(true);
NetworkTableInstance.getDefault().getEntry("Robot/Timer/TimeRemaining").setNumber(120.0);

// Vision
NetworkTableInstance.getDefault().getEntry("Robot/Vision/Connected").setBoolean(true);
NetworkTableInstance.getDefault().getEntry("Robot/Vision/HasTargets").setBoolean(false);

// Swerve
boolean[] aligned = {true, true, false, true};
NetworkTableInstance.getDefault().getEntry("Robot/Swerve/ModuleAligned").setBooleanArray(aligned);

// Mechanisms
NetworkTableInstance.getDefault().getEntry("Robot/Flywheel/AtSpeed").setBoolean(true);
NetworkTableInstance.getDefault().getEntry("Robot/Climb/Complete").setBoolean(false);
```

## Competition Day Checklist

### Before Match
- [ ] Orange Pi powered on
- [ ] Service running: `systemctl status rgb-reefscape`
- [ ] LEDs respond to test patterns
- [ ] Network Tables connected to RoboRio
- [ ] PhotonVision also running (if applicable)

### Match Verification
- [ ] White/Green countdown visible during periods
- [ ] Vision status indicates correctly
- [ ] Pre-match swerve alignment shows correctly
- [ ] Notifications appear for robot events

### Post-Match
- [ ] Check logs: `journalctl -u rgb-reefscape -n 100`
- [ ] Note any errors or issues
- [ ] Verify LEDs stayed powered entire match

## Emergency Recovery

```bash
# Stop service
sudo systemctl stop rgb-reefscape

# Run manually to debug
source venv/bin/activate
python3 -m rgb_reefscape.main --verbose

# Reset to defaults
cp config.yaml config.yaml.backup
git checkout config.yaml

# Reinstall
sudo ./scripts/install.sh
```

## Contact & Support

- GitHub: https://github.com/swat1806/RGB-Rebuilt-1806
- README: [README.md](README.md)
- Wiring: [WIRING.md](WIRING.md)
- Config: [config.yaml](config.yaml)

## LED Display Reference

| Display Mode | When | Colors | Animation |
|-------------|------|--------|-----------|
| Time Countdown | Match active | White (inactive) / Green (active) | Countdown bar |
| Vision Status | During match | Green (targets) / Yellow (connected) / Red (error) | Pulse/Flash |
| Swerve Align | Pre-match | Green (aligned) / Red (not aligned) | Static, 4 sections |
| Flywheel Ready | Active | Rainbow | Spinning |
| Climb Complete | Endgame | Green | Sparkle pulse |

---

**For detailed information, always refer to the main [README.md](README.md)**
