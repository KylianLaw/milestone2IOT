import json
import time
from datetime import datetime
import logging
from zoneinfo import ZoneInfo
import board
import adafruit_dht

QUEBEC_TZ = ZoneInfo("America/Toronto")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class environmental_module:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.dht = adafruit_dht.DHT11(board.D19, use_pulseio=False)
        self.min_interval_s = float(self.config.get("DHT_MIN_INTERVAL", 2.0))
        self._last_read_ts = 0.0
        self.max_retries = int(self.config.get("DHT_MAX_RETRIES", 5))
        self.retry_delay_s = float(self.config.get("DHT_RETRY_DELAY", 0.5))

    def load_config(self, config_file):
        default_config = {
            "ADAFRUIT_IO_USERNAME": "username",
            "ADAFRUIT_IO_KEY": "userkey",
            "MQTT_BROKER": "io.adafruit.com",
            "MQTT_PORT": 1883,
            "MQTT_KEEPALIVE": 60,
            "DHT_MIN_INTERVAL": 2.0,
            "DHT_MAX_RETRIES": 5,
            "DHT_RETRY_DELAY": 0.5
        }
        try:
            with open(config_file, 'r') as f:
                return {**default_config, **json.load(f)}
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            return default_config

    def _respect_interval(self):
        now = time.time()
        delta = now - self._last_read_ts
        if delta < self.min_interval_s:
            time.sleep(self.min_interval_s - delta)
        self._last_read_ts = time.time()

    def _read_dht_once(self):
        temperature_c = self.dht.temperature
        humidity = self.dht.humidity
        if temperature_c is None or humidity is None:
            raise RuntimeError("DHT returned None")
        return float(temperature_c), float(humidity)

    def get_environmental_data(self):
        self._respect_interval()
        last_exc = None

        for _ in range(self.max_retries):
            try:
                temperature_c, humidity = self._read_dht_once()
                ts_local = datetime.now(QUEBEC_TZ).isoformat()
                return {
                    'timestamp': ts_local,
                    'temperature': temperature_c,
                    'humidity': humidity
                }
            except Exception as e:
                last_exc = e
                logger.debug("DHT read error; retrying: %s", e)
                time.sleep(self.retry_delay_s)

        raise RuntimeError(f"Failed to read DHT11 after retries: {last_exc}")
