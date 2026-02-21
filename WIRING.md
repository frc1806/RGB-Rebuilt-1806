# RGB-Reefscape-1806 Wiring Guide

Complete wiring instructions for connecting WS2812B LED strips to Orange Pi 5 or Raspberry Pi 5 using SPI interface.

## ⚠️ Safety Warnings

- **NEVER** connect 12V directly to the SBC (Orange Pi/Raspberry Pi)
- **ALWAYS** use separate power for the LEDs (12V) and SBC (5V)
- **ALWAYS** connect common ground between all power supplies
- **DO NOT** power more than 150 LEDs from a single injection point without additional power injection
- Use proper gauge wire for LED power (14-16 AWG recommended for 150 LEDs)
- Add fuses to your power connections

## Component List

### Required Components
- Orange Pi 5 or Raspberry Pi 5
- BTF-LIGHTING WS2811/WS2812B 12V LED Strip (150 LEDs, 9.8ft)
- 12V Power Supply (minimum 3A for 150 LEDs, 5A+ recommended)
  - Wall adapter: 12V 5A DC power supply with barrel jack
  - Robot: Connect to robot 12V power rail with appropriate fuse/breaker
- Logic Level Shifter (recommended: 74HCT245, 74AHCT125, or TXB0104)
- Connecting wires (various gauges)
- Heat shrink tubing 
- Optional: Terminal blocks, JST connectors

### Recommended but Optional
- 1000µF capacitor (16V+) across LED power rails
- 470Ω resistor inline with data signal

---

## Orange Pi 5 Wiring

### Orange Pi 5 SPI Pinout

```
Orange Pi 5 GPIO Header (40-pin)
(View from top, USB ports facing down)

         3.3V [ 1] [ 2] 5V
        GPIO2 [ 3] [ 4] 5V
        GPIO3 [ 5] [ 6] GND  ← Connect to common ground
        GPIO4 [ 7] [ 8] GPIO14
          GND [ 9] [10] GPIO15
       GPIO17 [11] [12] GPIO18
       GPIO27 [13] [14] GND
       GPIO22 [15] [16] GPIO23
         3.3V [17] [18] GPIO24
   SPI0_MOSI* [19] [20] GND  ← Connect to common ground
   SPI0_MISO  [21] [22] GPIO25
   SPI0_SCLK  [23] [24] SPI0_CS0
          GND [25] [26] SPI0_CS1
        GPIO5 [27] [28] GPIO6
        GPIO13[29] [30] GND
        GPIO19[31] [32] GPIO12
        GPIO16[33] [34] GND
        GPIO26[35] [36] GPIO20
        GPIO21[37] [38] GPIO1
          GND [39] [40] GPIO11

* Pin 19 (SPI0_MOSI) - Data signal to LEDs
```

### Orange Pi 5 Wiring Diagram

```
                    ┌──────────────────────────┐
                    │    Orange Pi 5           │
                    │                          │
                    │   Pin 19 (SPI0_MOSI) ────┼─┐
                    │   Pin 6 or 20 (GND)  ────┼─┼─┐
                    │                          │ │ │
                    └──────────────────────────┘ │ │
                                                 │ │
                            ┌────────────────────┘ │
                            │    ┌─────────────────┘
                            │    │
                            ↓    ↓
                    ┌───────────────────┐
                    │  Logic Level      │
                    │  Shifter          │
                    │  (74HCT245)       │
                    │                   │
                    │  HV ← 5V          │←── 5V from Pi or separate 5V supply
                    │  LV ← 3.3V        │←── 3.3V from Pin 17
                    │  A  ← MOSI        │
                    │  B  → LED Data    │───┐
                    │  GND              │   │
                    └───────────────────┘   │
                            │               │
                            └───────────────┼───────┐
                                            │       │
                                            ↓       ↓
                    ┌───────────────────────────────────────┐
                    │  WS2812B LED Strip (150 LEDs)         │
                    │                                       │
                    │  DIN  ←─────────────────(Data)        │
                    │  +12V ←──┐                            │
                    │  GND  ←──┼──┐                         │
                    └──────────┼──┼─────────────────────────┘
                               │  │
                               │  │  ┌───────────────────────────┐
                               │  └──┤ GND (Common Ground)       │
                               │     └───────────────────────────┘
                               │            │
                    ┌──────────┴───┐        │
                    │  12V Power   │        │
                    │  Supply      │        │
                    │  (5A)        │        │
                    │              │        │
                    │  + ──────────┘        │
                    │  - ───────────────────┘
                    └──────────────┘

        From wall adapter or robot 12V rail
```

### Orange Pi 5 Connection Steps

1. **Power Down**: Ensure Orange Pi is powered off

2. **Connect Level Shifter**:
   - **74HCT245 / 74AHCT125**:
     - LV (Low Voltage) → Orange Pi Pin 17 (3.3V)
     - HV (High Voltage) → 5V source (can use Pi Pin 2/4, or separate 5V supply)
     - A1 (Input) → Orange Pi Pin 19 (SPI0_MOSI)
     - B1 (Output) → LED strip DIN (Data In)
     - GND (both sides) → Common ground
     - DIR → HV (for 74HCT245 only)

   - **TXB0104** (alternative):
     - VCCA → Orange Pi Pin 17 (3.3V)
     - VCCB → Orange Pi Pin 2 or 4 (5V)
     - A1 → Orange Pi Pin 19 (SPI0_MOSI)
     - B1 → LED strip DIN (Data In)
     - OE → VCCB (5V) for always-on
     - GND → Common ground

3. **Connect LED Strip**:
   - DIN (Data In) → Level shifter output (B1)
   - +12V → 12V power supply positive
   - GND → Common ground rail

4. **Connect Power**:
   - 12V Supply + → LED strip +12V
   - 12V Supply - → Common ground rail
   - Orange Pi GND (Pin 6, 9, 14, 20, 25, 30, 34, or 39) → Common ground rail

5. **Optional Components**:
   - 1000µF capacitor across LED +12V and GND (close to strip)
   - 470Ω resistor inline between level shifter output and LED DIN

---

## Raspberry Pi 5 Wiring

### Raspberry Pi 5 SPI Pinout

```
Raspberry Pi 5 GPIO Header (40-pin)
(View from top, USB ports and Ethernet facing down)

         3.3V [ 1] [ 2] 5V
   GPIO2/SDA [ 3] [ 4] 5V
   GPIO3/SCL [ 5] [ 6] GND  ← Connect to common ground
   GPIO4/GPK [ 7] [ 8] GPIO14/TXD
          GND [ 9] [10] GPIO15/RXD
       GPIO17 [11] [12] GPIO18/PWM0
       GPIO27 [13] [14] GND
       GPIO22 [15] [16] GPIO23
         3.3V [17] [18] GPIO24
   SPI0_MOSI* [19] [20] GND  ← Connect to common ground
   SPI0_MISO  [21] [22] GPIO25
   SPI0_SCLK  [23] [24] SPI0_CE0
          GND [25] [26] SPI0_CE1
        GPIO0 [27] [28] GPIO1
        GPIO5 [29] [30] GND
        GPIO6 [31] [32] GPIO12
       GPIO13 [33] [34] GND
       GPIO19 [35] [36] GPIO16
       GPIO26 [37] [38] GPIO20
          GND [39] [40] GPIO21

* Pin 19 (SPI0_MOSI/GPIO10) - Data signal to LEDs
```

### Raspberry Pi 5 Wiring Diagram

```
                    ┌──────────────────────────┐
                    │    Raspberry Pi 5        │
                    │                          │
                    │   Pin 19 (SPI0_MOSI) ────┼─┐
                    │   Pin 6 or 20 (GND)  ────┼─┼─┐
                    │                          │ │ │
                    └──────────────────────────┘ │ │
                                                 │ │
                            ┌────────────────────┘ │
                            │    ┌─────────────────┘
                            │    │
                            ↓    ↓
                    ┌───────────────────┐
                    │  Logic Level      │
                    │  Shifter          │
                    │  (74HCT245)       │
                    │                   │
                    │  HV ← 5V          │←── 5V from Pi Pin 2 or 4
                    │  LV ← 3.3V        │←── 3.3V from Pin 1 or 17
                    │  A  ← MOSI        │
                    │  B  → LED Data    │───┐
                    │  GND              │   │
                    └───────────────────┘   │
                            │               │
                            └───────────────┼───────┐
                                            │       │
                                            ↓       ↓
                    ┌───────────────────────────────────────┐
                    │  WS2812B LED Strip (150 LEDs)         │
                    │                                       │
                    │  DIN  ←─────────────────(Data)        │
                    │  +12V ←──┐                            │
                    │  GND  ←──┼──┐                         │
                    └──────────┼──┼─────────────────────────┘
                               │  │
                               │  │  ┌───────────────────────────┐
                               │  └──┤ GND (Common Ground)       │
                               │     └───────────────────────────┘
                               │            │
                    ┌──────────┴───┐        │
                    │  12V Power   │        │
                    │  Supply      │        │
                    │  (5A)        │        │
                    │              │        │
                    │  + ──────────┘        │
                    │  - ───────────────────┘
                    └──────────────┘

        From wall adapter or robot 12V rail
```

### Raspberry Pi 5 Connection Steps

Same as Orange Pi 5 (see above section), using Raspberry Pi pinout instead.

---

## Robot Installation (FRC Competition)

### Power Source Options

#### Option 1: 12V Power Distribution Panel (PDP/PDH)
```
Robot Battery (12V)
       │
       ↓
┌─────────────────┐
│  PDP/PDH        │
│  (with breaker) │
│                 │
│  12V Out  ──────┼─→ To LED Strip +12V
│  GND      ──────┼─→ Common Ground
└─────────────────┘
       │
       ↓
  To other robot loads
```

**Steps**:
1. Connect to available 12V output on PDP/PDH
2. Use appropriate breaker rating (5A recommended for 150 LEDs)
3. Route wires safely away from moving parts
4. Connect ground to PDP/PDH ground terminal

#### Option 2: VRM (Voltage Regulator Module) 12V Output
```
Robot Battery
       │
       ↓
┌─────────────────┐
│  VRM            │
│                 │
│  12V/2A Out ────┼─→ To LED Strip +12V
│  GND        ────┼─→ Common Ground
└─────────────────┘
```

**Note**: VRM 12V is typically limited to 2A. For 150 LEDs, use PDP/PDH instead.

### Orange Pi 5 Mounting on Robot

1. **Mount Location**:
   - Away from extremely high-vibration areas
   - Protected from impacts

2. **Power**:
   - Use VRM 5V/2A output for Orange Pi 5 USB-C power
   - Ensure stable 5V supply (Orange Pi needs 2A minimum) (Redux Zinc-V)

3. **Network Connection**:
   - Ethernet cable to robot radio/switch

4. **LED Strip Routing**:
   - Use cable management to prevent snagging
   - Keep LED power wires away from signal wires
   - Secure strip to robot frame

---

## Testing Procedure

### 1. Visual Inspection
- [ ] All connections tight and secure
- [ ] No exposed wire touching conductive surfaces
- [ ] Polarity correct on all power connections
- [ ] Common ground established between all components

### 2. Power-On Sequence
1. Connect 12V power to LED strip (strip should NOT light yet)
2. Power on Orange Pi/Raspberry Pi
3. Check SPI device exists: `ls -l /dev/spidev0.0`
4. Run in simulation mode: `python3 -m rgb_reefscape.main --simulate --verbose`
5. Run with hardware: `python3 -m rgb_reefscape.main --verbose`

### 3. Verify LEDs
- First few LEDs should light up
- Colors should match configuration
- No flickering or random colors
- All 150 LEDs respond

### 4. Troubleshooting

| Problem | Possible Cause | Solution |
|---------|---------------|----------|
| No LEDs light | No power to strip | Check 12V power supply and connections |
| | SPI not enabled | Run install.sh, reboot |
| | Wrong SPI device | Check /dev/spidev0.0 exists |
| Flickering/random colors | Bad data connection | Check level shifter, add 470Ω resistor |
| | Ground issue | Verify common ground |
| | Power supply noise | Add capacitor across LED power |
| Only first few LEDs work | Insufficient power | Add power injection, larger supply |
| | Bad LED strip | Test with shorter segment |
| LEDs wrong colors | Wrong color order | May need to adjust library settings |

---

## Advanced: Power Injection for Long Runs

If using more than 150 LEDs or experiencing dimming at the end:

```
        ┌──────────────────────────────────────┐
        │     LED Strip (300 LEDs)             │
        │                                      │
12V ────┤ +12V (Start)                         │
GND ────┤ GND                                  │
        │        Power Injection Point         │
12V ────┤ +12V (Middle) ←───────────────┐      │
GND ────┤ GND                           │      │
        │                               │      │
        └───────────────────────────────┼──────┘
                                        │
                              ┌─────────┴─────┐
                              │  12V Supply   │
                              │  (10A)        │
                              └───────────────┘
```

---

## Wire Gauge Reference

| Wire Purpose | Length | Recommended Gauge |
|--------------|--------|-------------------|
| LED 12V Power | < 3ft | 16 AWG |
| LED 12V Power | 3-6ft | 14 AWG |
| LED Ground | < 3ft | 16 AWG |
| LED Ground | 3-6ft | 14 AWG |
| Data Signal | Any | 22-26 AWG |
| Logic Level Power | < 1ft | 22-24 AWG |

---

## Component Sources

### Logic Level Shifter Options
- **74HCT245** - Octal bus transceiver (recommended, most common for LEDs)
- **74AHCT125** - Quad buffer (also excellent choice)
- **TXB0104** - 4-bit bidirectional (works well, connect OE to VCCB)
- **TXS0108E** - 8-bit bidirectional (be careful with voltage)
- Pre-made level shifter modules from Adafruit, SparkFun, etc.

**Note**: For TXB0104, connect the OE (Output Enable) pin to VCCB (5V) for always-on operation.

### Capacitor Specifications
- **Type**: Electrolytic
- **Value**: 1000µF or higher
- **Voltage**: 16V minimum (25V recommended)
- **Purpose**: Smooths power supply, prevents voltage spikes

### Resistor Specifications
- **Value**: 470Ω
- **Power**: 1/4W
- **Purpose**: Protects data line, reduces reflections

---

## Additional Notes

- **WS2812B vs WS2811**: This guide works for both. WS2811 is the external driver IC version.
- **12V vs 5V LEDs**: These instructions are for 12V LED strips. 5V strips work similarly but require 5V power supply and may need higher current.
- **PhotonVision**: LED controller runs alongside PhotonVision without conflicts. Both use different interfaces (SPI vs USB/Ethernet).
- **Multiple strips**: Can control multiple separate strips by using multiple SPI devices (/dev/spidev0.0, /dev/spidev1.0, etc.)

---

## Safety Checklist

Before powering on:
- [ ] 12V power NOT connected to SBC
- [ ] Common ground established
- [ ] All connections insulated
- [ ] Fuses/breakers in place
- [ ] Wires secured and not under strain
- [ ] No short circuits visible
- [ ] Power supply rated for load (5A+ for 150 LEDs)
- [ ] Mounting secure (robot application)

---

For software configuration, see [README.md](README.md) and [config.yaml](config.yaml).
