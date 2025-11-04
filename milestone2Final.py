# ===== Imports =====
import json
import time
import threading
import logging
import atexit
import random

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
from smbus2 import SMBus
from paho.mqtt.client import connack_string

# ===== Optional Local Module (MQTT_communicator) =====
try:
    from MQTT_communicator import MQTT_communicator
except Exception as e:
    MQTT_communicator = None
    print("WARNING: MQTT_communicator not found; continuing without it.", e)

# ===== Project Modules =====
from environmental_module import environmental_module
from security_module import security_module
from device_control_module import device_control_module

# ===== Logging Setup =====
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("Milestone2_Full")


# ===== I2C LCD Class =====
class I2CLcd:
    LCD_CLEARDISPLAY = 0x01
    LCD_RETURNHOME = 0x02
    LCD_ENTRYMODESET = 0x04
    LCD_DISPLAYCTRL = 0x08
    LCD_FUNCTIONSET = 0x20
    LCD_SETDDRAMADDR = 0x80

    LCD_ENTRYLEFT = 0x02
    LCD_2LINE = 0x08
    LCD_5x8DOTS = 0x00

    LCD_DISPLAYON = 0x04
    LCD_CURSOROFF = 0x00
    LCD_BLINKOFF = 0x00

    ENABLE = 0b00000100
    BACKLIGHT = 0b00001000

    def __init__(self, bus, addr, cols, rows, backlight: bool = True):
        self.bus, self.addr, self.cols, self.rows = bus, addr, cols, rows
        self.backlight = backlight

        time.sleep(0.05)
        self._write4(0x30)
        time.sleep(0.0045)
        self._write4(0x30)
        time.sleep(0.0045)
        self._write4(0x30)
        time.sleep(0.00015)
        self._write4(0x20)

        self.command(self.LCD_FUNCTIONSET | self.LCD_2LINE | self.LCD_5x8DOTS)
        self.command(
            self.LCD_DISPLAYCTRL
            | self.LCD_DISPLAYON
            | self.LCD_CURSOROFF
            | self.LCD_BLINKOFF
        )
        self.clear()
        self.command(self.LCD_ENTRYMODESET | self.LCD_ENTRYLEFT)

    def _exp(self, data: int) -> None:
        b = data | (self.BACKLIGHT if self.backlight else 0x00)
        self.bus.write_byte(self.addr, b)

    def _pulse(self, data: int) -> None:
        self._exp(data | self.ENABLE)
        time.sleep(0.0005)
        self._exp(data & ~self.ENABLE)
        time.sleep(0.0001)

    def _write4(self, data: int) -> None:
        self._exp(data)
        self._pulse(data)

    def write8(self, val: int, rs: int = 0) -> None:
        self._write4((val & 0xF0) | rs)
        self._write4(((val << 4) & 0xF0) | rs)

    def command(self, cmd: int) -> None:
        self.write8(cmd, rs=0)

    def write_char(self, ch: str) -> None:
        self.write8(ord(ch), rs=1)

    def clear(self) -> None:
        self.command(self.LCD_CLEARDISPLAY)
        time.sleep(0.002)

    def home(self) -> None:
        self.command(self.LCD_RETURNHOME)
        time.sleep(0.002)

    def set_cursor(self, col: int, row: int) -> None:
        row = max(0, min(self.rows - 1, row))
        col = max(0, min(self.cols - 1, col))
        offsets = [0x00, 0x40, 0x14, 0x54]
        self.command(self.LCD_SETDDRAMADDR | (offsets[row] + col))

    def print(self, text: str) -> None:
        for ch in text:
            if ch == "\n":
                self.set_cursor(0, 1)
            else:
                self.write_char(ch)

    def set_backlight(self, on: bool) -> None:
        self.backlight = bool(on)
        self.bus.write_byte(self.addr, 0x00 if not self.backlight else self.BACKLIGHT)


# ===== Buzzer Controller =====
class BuzzerController:
    def __init__(self, pin=18, mode="passive", pwm_freq=2000, duty_percent=70.0):
        self.pin = int(pin)
        self.mode = mode.lower()
        self.pwm_freq = int(pwm_freq)
        self.duty = max(0.0, min(100.0, float(duty_percent)))

        self._lock = threading.Lock()
        self._alarm_active = False
        self._toggle_on = False

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self._pwm = GPIO.PWM(self.pin, self.pwm_freq) if self.mode == "passive" else None
        atexit.register(self.cleanup)

    def _start_pwm(self) -> None:
        if self._pwm:
            self._pwm.ChangeFrequency(self.pwm_freq)
            self._pwm.start(self.duty)

    def _stop_pwm(self) -> None:
        if self._pwm:
            try:
                self._pwm.stop()
            except Exception:
                pass

    def set_on(self) -> None:
        with self._lock:
            self._toggle_on = True
            self._alarm_active = False
        if self.mode == "passive":
            self._start_pwm()
        else:
            GPIO.output(self.pin, GPIO.HIGH)
        log.warning("BUZZER: ON (toggle)")

    def set_off(self) -> None:
        with self._lock:
            self._toggle_on = False
            self._alarm_active = False
        if self.mode == "passive":
            self._stop_pwm()
        GPIO.output(self.pin, GPIO.LOW)
        log.info("BUZZER: OFF (toggle)")

    def _alarm_worker(self, duration_s: int) -> None:
        try:
            with self._lock:
                self._alarm_active = True
            if self.mode == "passive":
                self._start_pwm()
            else:
                GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(duration_s)
        finally:
            with self._lock:
                self._alarm_active = False
                if not self._toggle_on:
                    if self.mode == "passive":
                        self._stop_pwm()
                    GPIO.output(self.pin, GPIO.LOW)
            log.info("BUZZER: momentary alarm finished")

    def alarm(self, duration_s: int = 15) -> bool:
        with self._lock:
            if self._alarm_active:
                return False
            t = threading.Thread(target=self._alarm_worker, args=(duration_s,), daemon=True)
            t.start()
            return True

    def cleanup(self) -> None:
        try:
            self._stop_pwm()
            GPIO.output(self.pin, GPIO.LOW)
        except Exception:
            pass


# ===== LED Bank =====
class LedBank:
    def __init__(self, mapping: dict[str, int]):
        self.mapping = mapping
        GPIO.setmode(GPIO.BCM)
        for _, pin in mapping.items():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

    def set(self, name: str, on: bool) -> None:
        pin = self.mapping.get(name)
        if pin is None:
            return
        GPIO.output(pin, GPIO.HIGH if on else GPIO.LOW)
        log.info(f"LED {name.upper()}: {'ON' if on else 'OFF'}")

    def all(self, on: bool) -> None:
        for name in self.mapping:
            self.set(name, on)


# ===== Main Application (DomiSafeAll) =====
class DomiSafeAll:
    # ---- Init & Hardware/Client Setup ----
    def __init__(self, cfg_path: str = "config.json"):
        self.config = self._load_config(cfg_path)

        self.mqtt_agent = None
        if MQTT_communicator:
            try:
                self.mqtt_agent = MQTT_communicator(cfg_path)
            except Exception as e:
                log.warning("Could not initialize MQTT_communicator: %s", e)

        self.env_data = environmental_module(cfg_path)
        self.security = security_module(cfg_path)
        self.dev_ctrl = device_control_module(cfg_path)

        self.env_interval = int(self.config.get("env_interval", 20))
        self.sec_check_interval = int(self.config.get("security_check_interval", 5))
        self.sync_interval = int(self.config.get("sync_interval", 300))
        self.keepalive = int(self.config.get("MQTT_KEEPALIVE", 60))

        self.user = (self.config.get("ADAFRUIT_IO_USERNAME") or "").strip()
        self.key = (self.config.get("ADAFRUIT_IO_KEY") or "").strip()
        self.broker = (self.config.get("MQTT_BROKER", "io.adafruit.com") or "").strip()
        self.port = int(self.config.get("MQTT_PORT", 1883))

        self.buzzer = BuzzerController(
            pin=int(self.config.get("buzzer_pin", 18)),
            mode=self.config.get("buzzer_mode", "passive"),
            pwm_freq=int(self.config.get("buzzer_freq", 2000)),
            duty_percent=float(self.config.get("buzzer_duty", 70.0)),
        )
        self.buzzer_mode = self.config.get("buzzer_control_mode", "toggle")
        self.buzzer_alarm_seconds = int(self.config.get("buzzer_alarm_seconds", 15))
        self.buzzer_feed = self.config.get("BUZZER_CONTROL_FEED", "buzzer_control")

        self.leds = LedBank(self.config.get("LED_PINS", {"yellow": 16, "red": 20, "green": 21}))
        self.led_feeds = self.config.get(
            "LED_FEEDS", {"yellow": "led_yellow", "red": "led_red", "green": "led_green"}
        )

        self.bus = SMBus(1)
        self.lcd_addr = int(self.config.get("LCD_ADDR", 39))
        self.lcd_cols = int(self.config.get("LCD_COLS", 16))
        self.lcd_rows = int(self.config.get("LCD_ROWS", 2))
        self.lcd_feed = self.config.get("FEED_KEY", "LCD_display")
        self.lcd = I2CLcd(self.bus, self.lcd_addr, self.lcd_cols, self.lcd_rows, backlight=True)
        self.lcd.print("System Ready")
        time.sleep(1)
        self.lcd.clear()

        self._party_on = False
        self._party_thread = None

        self.env_feeds = self.config.get(
            "ENV_FEEDS",
            {
                "temperature_c": "temperature",
                "humidity_pct": "humidity",
                "pressure_hpa": "pressure",
                "gas_ohm": "gas",
                "co2_ppm": "co2",
                "tvoc_ppb": "tvoc",
            },
        )

        sub_cid = f"domisafe-sub-{int(time.time())}-{random.randint(1000, 9999)}"
        self.sub = mqtt.Client(
            client_id=sub_cid,
            protocol=mqtt.MQTTv311,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        self.sub.username_pw_set(self.user, self.key)
        self.sub.on_connect = self._on_connect
        self.sub.on_message = self._on_message

        pub_cid = f"domisafe-pub-{int(time.time())}-{random.randint(1000, 9999)}"
        self.pub = mqtt.Client(
            client_id=pub_cid,
            protocol=mqtt.MQTTv311,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        self.pub.username_pw_set(self.user, self.key)
        self.pub.on_connect = self._on_pub_connect

        self._stop = threading.Event()

    # ---- Config Loader ----
    def _load_config(self, path: str) -> dict:
        with open(path, "r") as f:
            data = json.load(f)
        for k in ("ADAFRUIT_IO_USERNAME", "ADAFRUIT_IO_KEY", "MQTT_BROKER"):
            if k in data and isinstance(data[k], str):
                data[k] = data[k].strip()
        return data

    # ---- MQTT Callbacks (SUB + PUB) ----
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code != 0:
            log.error(
                "Control MQTT connect failed: %s (%s)", reason_code, connack_string(reason_code)
            )
            return
        log.info("Connected to Adafruit IO (control)")
        client.subscribe(f"{self.user}/feeds/{self.buzzer_feed}", qos=1)
        for _, feed in self.led_feeds.items():
            client.subscribe(f"{self.user}/feeds/{feed}", qos=1)
        client.subscribe(f"{self.user}/feeds/{self.lcd_feed}", qos=1)
        log.info("Subscribed to control feeds")

    def _on_pub_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code != 0:
            log.error(
                "Telemetry MQTT connect failed: %s (%s)", reason_code, connack_string(reason_code)
            )
        else:
            log.info("Connected to Adafruit IO (telemetry publisher)")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode("utf-8", errors="ignore").strip()
        log.info(f"[AIO] {topic} -> {payload}")

        if topic.endswith(self.buzzer_feed):
            on = payload.lower() in ("on", "1", "true", "high")
            if self.buzzer_mode == "momentary":
                if on:
                    self.buzzer.alarm(self.buzzer_alarm_seconds)
            else:
                self.buzzer.set_on() if on else self.buzzer.set_off()
            return

        for name, feed in self.led_feeds.items():
            if topic.endswith(feed):
                on = payload.lower() in ("on", "1", "true", "high")
                self.leds.set(name, on)
                return

        if topic.endswith(self.lcd_feed):
            text = payload.replace("\r", "")
            self.lcd.clear()
            self.lcd.home()
            if text:
                self.lcd.set_cursor(0, 0)
                self.lcd.print(text[: self.lcd_cols])
                rest = text[self.lcd_cols :]
                if rest:
                    self.lcd.set_cursor(0, 1)
                    self.lcd.print(rest[: self.lcd_cols])
            return

    # ---- MQTT Publish Helper ----
    def _publish(self, feed_key: str, payload, qos: int = 1, retain: bool = False) -> None:
        if not feed_key:
            return
        topic = f"{self.user}/feeds/{feed_key}"
        try:
            rc, _ = self.pub.publish(topic, str(payload), qos=qos, retain=retain)
            if rc != mqtt.MQTT_ERR_SUCCESS:
                log.warning("Publish to %s failed rc=%s", topic, rc)
        except Exception as e:
            log.exception("Publish error to %s: %s", topic, e)

    # ---- Background Loops ----
    def _env_loop(self) -> None:
        while not self._stop.is_set():
            try:
                data = self.env_data.get_environmental_data()
                if isinstance(data, dict):
                    logging.info("Environment: " + ", ".join(f"{k}={v}" for k, v in data.items()))
                    for key, feed in self.env_feeds.items():
                        if feed and key in data and data[key] is not None:
                            self._publish(feed, data[key], qos=1, retain=False)
                else:
                    logging.info(f"Environment: {data}")
            except Exception as e:
                logging.exception(f"Env loop error: {e}")
            self._stop.wait(self.env_interval)

    def _security_check_loop(self) -> None:
        while not self._stop.is_set():
            try:
                sec = self.security.get_security_data()
                if isinstance(sec, dict):
                    logging.info(
                        "Security: motion=%s, smoke=%s, image=%s",
                        sec.get("motion_detected"),
                        sec.get("smoke_detected"),
                        sec.get("image_path"),
                    )
                else:
                    logging.info(f"Security: {sec}")
            except Exception as e:
                logging.exception(f"Security check error: {e}")
            self._stop.wait(self.sec_check_interval)

    def _device_sync_loop(self) -> None:
        while not self._stop.is_set():
            try:
                states = self.dev_ctrl.get_device_status()
                if isinstance(states, dict):
                    logging.info("Device status: " + ", ".join(f"{k}={v}" for k, v in states.items()))
                else:
                    logging.info(f"Device status entries: {states}")
            except Exception as e:
                logging.exception(f"Device sync error: {e}")
            self._stop.wait(self.sync_interval)

    # ---- LED Party Mode ----
    def _party_worker(self) -> None:
        names = list(self.leds.mapping.keys())
        log.info("PARTY MODE ON")
        while self._party_on and not self._stop.is_set():
            pattern = random.choice(["wave", "strobe", "random", "sequence"])
            if pattern == "wave":
                seq = names + names[::-1]
                for n in seq:
                    if not self._party_on:
                        break
                    self.leds.all(False)
                    self.leds.set(n, True)
                    time.sleep(0.15)
            elif pattern == "strobe":
                for _ in range(6):
                    if not self._party_on:
                        break
                    self.leds.all(True)
                    time.sleep(0.08)
                    self.leds.all(False)
                    time.sleep(0.08)
            elif pattern == "random":
                for _ in range(12):
                    if not self._party_on:
                        break
                    choice = random.choice(names)
                    self.leds.set(choice, True)
                    time.sleep(0.08)
                    self.leds.set(choice, False)
            elif pattern == "sequence":
                for n in names:
                    if not self._party_on:
                        break
                    self.leds.set(n, True)
                    time.sleep(0.2)
                    self.leds.set(n, False)
        self.leds.all(False)
        log.info("PARTY MODE OFF")

    def toggle_party(self) -> None:
        if self._party_on:
            self._party_on = False
            if self._party_thread and self._party_thread.is_alive():
                self._party_thread.join(timeout=1.0)
        else:
            self._party_on = True
            self._party_thread = threading.Thread(target=self._party_worker, daemon=True)
            self._party_thread.start()

    # ---- CLI Menu ----
    def _show_menu(self) -> None:
        print("\n--- Device Control Menu ---")
        print("s. Show status")
        print("a. Turn ALL LEDs ON")
        print("o. Turn ALL LEDs OFF")
        print("p. Toggle PARTY MODE")
        print("l. LCD: Clear")
        print("b. LCD: Toggle backlight")
        print("q. Quit")

    def _show_status(self) -> None:
        print("\n--- Current Status ---")
        for name, pin in self.leds.mapping.items():
            state = "ON" if GPIO.input(pin) else "OFF"
            print(f"  LED {name}: {state} (GPIO {pin})")
        print(f"  Buzzer pin {self.buzzer.pin} mode {self.buzzer.mode}")
        print(f"  LCD @ 0x{self.lcd_addr:02X} ({self.lcd_cols}x{self.lcd_rows})")

    # ---- Lifecycle (start/stop) ----
    def start(self) -> None:
        log.info("Starting ALL modules (env + motion/camera + sync + controls)")
        log.info("Connecting SUB to %s:%s as %s …", self.broker, self.port, self.user)
        self.sub.connect(self.broker, self.port, keepalive=self.keepalive)
        self.sub.loop_start()

        log.info("Connecting PUB to %s:%s as %s …", self.broker, self.port, self.user)
        self.pub.connect(self.broker, self.port, keepalive=self.keepalive)
        self.pub.loop_start()

        threading.Thread(target=self._env_loop, daemon=True).start()
        threading.Thread(target=self._security_check_loop, daemon=True).start()
        threading.Thread(target=self._device_sync_loop, daemon=True).start()

        try:
            while not self._stop.is_set():
                self._show_menu()
                choice = input("\nEnter command: ").strip().lower()

                if choice == "q":
                    break
                elif choice == "s":
                    self._show_status()
                elif choice == "a":
                    self.leds.all(True)
                    print("✓ All LEDs ON")
                elif choice == "o":
                    self.leds.all(False)
                    print("✓ All LEDs OFF")
                elif choice == "p":
                    self.toggle_party()
                elif choice == "l":
                    self.lcd.clear()
                    self.lcd.home()
                    print("✓ LCD cleared")
                elif choice == "b":
                    new_state = not self.lcd.backlight
                    self.lcd.set_backlight(new_state)
                    print(f"✓ LCD backlight {'ON' if new_state else 'OFF'}")
                else:
                    print(" Invalid command!")
                time.sleep(0.2)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self) -> None:
        if hasattr(self, "_stop") and self._stop.is_set():
            return

        self._stop = threading.Event()
        self._stop.set()

        try:
            self.sub.loop_stop()
            self.sub.disconnect()
        except Exception:
            pass

        try:
            self.pub.loop_stop()
            self.pub.disconnect()
        except Exception:
            pass

        try:
            self.buzzer.cleanup()
        except Exception:
            pass

        self._party_on = False
        self.leds.all(False)

        try:
            GPIO.cleanup()
        except Exception:
            pass

        log.info("Stopped cleanly.")


# ===== Entrypoint =====
if __name__ == "__main__":
    app = DomiSafeAll("config.json")
    app.start()
