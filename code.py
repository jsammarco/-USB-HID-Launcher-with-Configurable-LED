import time
import random
import usb_hid
import board
import neopixel

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

from adafruit_led_animation.animation.solid import Solid
from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation import Animation
from adafruit_led_animation import color as led_color_mod

# ==============================
# PIXEL / LED SETUP
# ==============================

# Your RGB LED data pin:
PIXEL_PIN = board.GP16
NUM_PIXELS = 1

# Initial brightness will be overridden from config
pixels = neopixel.NeoPixel(
    PIXEL_PIN,
    NUM_PIXELS,
    brightness=0.5,
    auto_write=False,  # animations call show()
)


def get_color_from_name(name: str):
    """Map FastLED-style color name to an RGB tuple."""
    if not name:
        return led_color_mod.RED
    attr_name = name.strip().upper()
    return getattr(led_color_mod, attr_name, led_color_mod.RED)


class RainbowBlink(Animation):
    """
    Blink on/off while stepping through rainbow colors.
    """

    def __init__(self, pixel_object, speed=0.1):
        super().__init__(pixel_object, speed=speed, color=0)
        self._colors = [
            led_color_mod.RED,
            led_color_mod.ORANGE,
            led_color_mod.YELLOW,
            led_color_mod.GREEN,
            led_color_mod.CYAN,
            led_color_mod.BLUE,
            led_color_mod.PURPLE,
            led_color_mod.MAGENTA,
        ]
        self._index = 0
        self._on = True

    def draw(self):
        if self._on:
            self.pixel_object.fill(self._colors[self._index])
        else:
            self.pixel_object.fill((0, 0, 0))

        self._on = not self._on
        if self._on:
            self._index = (self._index + 1) % len(self._colors)


# ==============================
# CONFIG LOADING
# ==============================

def str_to_bool(value: str) -> bool:
    v = value.strip().lower()
    return v in ("1", "true", "yes", "on", "y")


def load_config(path="config.txt"):
    """
    Load settings from a simple key=value config file.

    Supported keys:
        COMMAND        - the full command to type into Win+R
        MIN_DELAY      - minimum delay between runs (seconds, int)
        MAX_DELAY      - maximum delay between runs (seconds, int)
        RUN_ONCE       - if true/1, run once and then idle
        RUN_DELAY      - initial delay before the FIRST run (seconds, int)

        LED_MODE       - Off, Solid, Rainbow, Rainbow Blink, Breath, Blink
        LED_COLOR      - FastLED-style color name for Solid/Breath/Blink
        LED_SPEED      - speed in milliseconds for LED patterns
        LED_BRIGHTNESS - 0.0–1.0, or 0–255 (scaled)
    """
    cfg = {
        "command": "msedge --kiosk https://stlgotit.com/RickAstley.mp4 --edge-kiosk-type=fullscreen",
        "min_delay": 100,
        "max_delay": 1000,
        "run_once": False,
        "run_delay": 0,          # seconds

        "led_mode": "off",       # off, solid, rainbow, rainbow_blink, breath, blink
        "led_color_name": "RED",
        "led_speed": 150,        # ms
        "led_brightness": 0.5,   # 0.0–1.0 (or 0–255 in file)
    }

    try:
        # utf-8-sig strips BOM if present
        with open(path, "r", encoding="utf-8-sig") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue

                key, value = line.split("=", 1)

                # Clean key (remove BOM just in case, strip, lower)
                key = key.replace("\ufeff", "").strip().lower()

                # Strip inline comments from the value:
                # everything after '#' is treated as comment.
                value = value.split("#", 1)[0].strip()

                if key == "command":
                    cfg["command"] = value

                elif key == "min_delay":
                    try:
                        cfg["min_delay"] = int(value)
                    except ValueError:
                        pass

                elif key == "max_delay":
                    try:
                        cfg["max_delay"] = int(value)
                    except ValueError:
                        pass

                elif key == "run_once":
                    cfg["run_once"] = str_to_bool(value)

                elif key == "run_delay":
                    try:
                        cfg["run_delay"] = int(value)
                    except ValueError:
                        pass

                elif key == "led_mode":
                    v = value.lower()
                    if v in ("off", "none"):
                        cfg["led_mode"] = "off"
                    elif v == "solid":
                        cfg["led_mode"] = "solid"
                    elif v == "rainbow":
                        cfg["led_mode"] = "rainbow"
                    elif v in ("rainbow blink", "rainbow_blink", "rainbowblink"):
                        cfg["led_mode"] = "rainbow_blink"
                    elif v == "breath":
                        cfg["led_mode"] = "breath"
                    elif v == "blink":
                        cfg["led_mode"] = "blink"

                elif key == "led_color":
                    cfg["led_color_name"] = value

                elif key == "led_speed":
                    try:
                        cfg["led_speed"] = int(value)
                    except ValueError:
                        pass

                elif key == "led_brightness":
                    try:
                        b = float(value)
                        cfg["led_brightness"] = b
                    except ValueError:
                        pass

        # Make sure min_delay <= max_delay
        if cfg["min_delay"] > cfg["max_delay"]:
            cfg["min_delay"], cfg["max_delay"] = cfg["max_delay"], cfg["min_delay"]

    except OSError:
        # No config file / not readable – stick with defaults
        pass

    # Resolve actual color
    cfg["led_color"] = get_color_from_name(cfg["led_color_name"])

    # Normalize brightness:
    # - If <= 1.0: treat as 0.0–1.0
    # - If > 1.0: assume 0–255 and scale
    b = cfg.get("led_brightness", 0.5)
    try:
        b = float(b)
    except Exception:
        b = 0.5
    if b > 1.0:
        b = b / 255.0
    if b < 0.0:
        b = 0.0
    if b > 1.0:
        b = 1.0
    cfg["led_brightness"] = b

    return cfg


config = load_config()
last_config_check = time.monotonic()
CHECK_INTERVAL = 5  # seconds between config reloads

has_run_once = False
current_animation = None

# Signature of the last LED config used to build the animation:
# (mode, color_name, speed_ms, brightness)
prev_led_signature = None


def build_animation_from_config():
    """
    Create/update the LED animation object based on current config,
    but ONLY if the LED-related config actually changed.
    """
    global current_animation, prev_led_signature

    mode = config.get("led_mode", "off").lower()
    color_name = config.get("led_color_name")
    color = config.get("led_color", led_color_mod.RED)
    speed_ms = max(config.get("led_speed", 150), 20)
    brightness = config.get("led_brightness", 0.5)

    # LED_SPEED is in ms; animations use seconds
    speed_s = speed_ms / 1000.0

    # Build a signature to detect changes
    new_sig = (mode, color_name, speed_ms, round(brightness, 3))

    # If nothing changed, do nothing (prevents flicker/red flash)
    if new_sig == prev_led_signature and current_animation is not None:
        return

    # Debug so you can see what it thinks the config is:
    print(
        "LED MODE:", mode,
        "COLOR:", color_name,
        "SPEED_MS:", speed_ms,
        "BRIGHTNESS:", brightness
    )

    # Update brightness first
    pixels.brightness = brightness

    # Build the appropriate animation
    if mode == "off":
        current_animation = None
        pixels.fill((0, 0, 0))
        pixels.show()
    elif mode == "solid":
        current_animation = Solid(pixels, color=color)
    elif mode == "blink":
        current_animation = Blink(pixels, speed=speed_s, color=color)
    elif mode == "rainbow":
        current_animation = Rainbow(pixels, speed=speed_s, period=2)
    elif mode == "rainbow_blink":
        current_animation = RainbowBlink(pixels, speed=speed_s)
    elif mode == "breath":
        current_animation = Pulse(pixels, speed=speed_s, color=color, period=3)
    else:
        # Fallback: unknown mode -> solid red
        current_animation = Solid(pixels, color=led_color_mod.RED)

    # Store signature so we only rebuild when something actually changes
    prev_led_signature = new_sig


build_animation_from_config()


def sleep_with_animation(duration):
    """
    Sleep for 'duration' seconds while:
      - animating the LED
      - periodically reloading config.txt and updating animation (only on change)
    """
    global config, last_config_check

    end_time = time.monotonic() + duration
    while True:
        now = time.monotonic()
        if now >= end_time:
            break

        if now - last_config_check >= CHECK_INTERVAL:
            config = load_config()
            build_animation_from_config()
            last_config_check = now

        if current_animation is not None:
            current_animation.animate()

        time.sleep(0.02)


# ==============================
# HID SETUP
# ==============================

kbd = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(kbd)
layout.key_delay = 0.001      # or 0.001

def win_r():
    """Press Win + R (Run dialog)."""
    kbd.press(Keycode.WINDOWS, Keycode.R)
    time.sleep(0.15)
    kbd.release_all()
    time.sleep(0.3)


def gogogadget():
    """Open Win+R and type the configured command."""
    win_r()
    layout.write(config["command"], delay=0.001)
    time.sleep(0.15)
    kbd.press(Keycode.ENTER)
    kbd.release_all()


# Give host time to recognize the device while LED animates
sleep_with_animation(4)

# ==============================
# MAIN LOOP
# ==============================

while True:
    # If RUN_ONCE is enabled and we've already run once, just idle with LED
    if config["run_once"] and has_run_once:
        sleep_with_animation(60)
        continue

    # Delay BEFORE running:
    #   First run: use RUN_DELAY if > 0
    #   Later runs: random MIN_DELAY..MAX_DELAY
    if not has_run_once and config["run_delay"] > 0:
        delay = config["run_delay"]
    else:
        delay = random.randint(config["min_delay"], config["max_delay"])

    sleep_with_animation(delay)

    # Run payload
    gogogadget()
    has_run_once = True

    # If RUN_ONCE, we never schedule another run – just idle forever
    if config["run_once"]:
        while True:
            sleep_with_animation(60)
