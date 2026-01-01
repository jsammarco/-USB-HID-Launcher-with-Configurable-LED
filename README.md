# USB HID Launcher with Configurable LED Status (CircuitPython)

This project turns a **Raspberry Pi Pico (RP2040)** (or similar CircuitPython-compatible board) into a USB HID keyboard device that:
- Opens a command via `Win + R`
- Types a configurable command (e.g., kiosk browser URL)
- Runs at controllable intervals (initial delay, random delay, or once-only)
- Uses a **NeoPixel RGB LED** on **GPIO 16** for status indication
- Reloads configuration from `config.txt` automatically
- Supports multiple LED animation modes with adjustable speed and brightness

---

## 🚀 Features

| Feature | Description |
|---------|--------------|
| Auto-launch command | Sends Win+R and executes a customizable command |
| Hot reload config | Reads options from `config.txt` every 5 seconds |
| Run modes | Run once, run after initial delay, randomized intervals |
| Status LED | Solid / Breath / Blink / Rainbow / Rainbow Blink |
| Brightness control | 0–255 or 0.0–1.0 |
| Comment-friendly config | Inline comments allowed in `config.txt` |

---

## 🛠 Requirements

- Raspberry Pi Pico / RP2040 board flashed with **CircuitPython**
- USB connection to a Windows PC (for command execution)
- **1 NeoPixel RGB LED** (WS2812 or SK6812) connected to:
  - **Data → GP16**
  - **5V / 3.3V → VBUS or 3V3**
  - **Ground → GND**

---

## 📁 File Layout

```
CIRCUITPY/
│
├── code.py          # Main program
├── config.txt       # User settings
└── lib/             # Required libraries
    ├── neopixel.mpy
    ├── adafruit_led_animation/
    └── adafruit_hid/
```

---

## ⚙️ config.txt Options

Example:

```ini
COMMAND=msedge --kiosk https://example.com --edge-kiosk-type=fullscreen

RUN_DELAY=10       # Seconds before FIRST run
MIN_DELAY=20       # Min random delay between runs
MAX_DELAY=40       # Max random delay between runs
RUN_ONCE=false     # If true, only launch once then idle

LED_MODE=Rainbow Blink     # Off, Solid, Rainbow, Rainbow Blink, Breath, Blink
LED_COLOR=RED              # FastLED-style colors (RED, BLUE, CYAN, YELLOW, etc)
LED_SPEED=150              # Animation speed in ms
LED_BRIGHTNESS=64          # 0–255 or 0.0–1.0
```

---

## 💡 LED Modes Available

| Mode | Behavior |
|------|-----------|
| Off | LED disabled |
| Solid | Constant color |
| Blink | On/off in chosen color |
| Breath | Fade in/out |
| Rainbow | Cycling RGB spectrum |
| Rainbow Blink | Blink + change color each blink |

---

## 🔄 How It Works

1. Wait for Windows to recognize the HID device
2. Apply LED animation based on config
3. If `RUN_DELAY > 0`, wait before the first run
4. Execute command
5. If `RUN_ONCE=true`, stay idle, LED continues
6. Otherwise, wait a **random time** between `MIN_DELAY` & `MAX_DELAY`
7. Repeat

---

## 🧩 Debugging

Open the CircuitPython REPL / serial console.  
You should see debug output like:

```
LED MODE: rainbow COLOR: RED SPEED_MS: 150 BRIGHTNESS: 0.5
Checking for config updates...
```

If LED shows **red for one frame**, ensure:
- LED is a **NeoPixel-type**, not a common RGB LED
- Data pin is correct (GP16)
- Libraries are in `/lib/`

---

## 🧰 Troubleshooting

| Issue | Solution |
|-------|-----------|
| LED stuck off | Check wiring and that LED is NeoPixel compatible |
| Windows doesn't launch | Make sure driver recognized `Keyboard HID` |
| Config ignored | Save file as UTF-8 or UTF-8 without BOM |
| LED flashes red on reload | Fixed after adding signature check |

---

## 📜 Licensing

This project is intended for personal and educational use.  
If integrating commercially or reselling, attribution is appreciated.

---

## 🙌 Credits

Created with assistance from ChatGPT.

---

## 🧾 Version History

| Version | Update |
|---------|---------|
| v1.0 | Initial build |
| v1.1 | Auto-refresh settings + BOM-safe config reads |
| v1.2 | LED brightness support + no flicker on reload |
| v1.3 | README added |

---

## 🎉 Enjoy!

Plug it in — watch the LED pulse — and let automation take over.
