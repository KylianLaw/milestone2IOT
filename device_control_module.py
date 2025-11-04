
# Ilian Adeleke (2330261) — Lab 8 modules — device_control_module.py
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class device_control_module:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)

    def load_config(self, config_file):
        """Load configuration from JSON file"""
        default_config = {
            "ADAFRUIT_IO_USERNAME": "username",
            "ADAFRUIT_IO_KEY": "userkey",
            "MQTT_BROKER": "io.adafruit.com",
            "MQTT_PORT": 1883,
            "MQTT_KEEPALIVE": 60,
            "devices": ["living_room_light", "bedroom_fan", "front_door", "garage_door"],
            "camera_enabled": True,
            "capturing_interval": 900,
            "flushing_interval": 10,
            "sync_interval": 300
        }
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                return {**default_config, **config}
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            return default_config

    def generate_device_status(self):
        """Generate device status data based on last known state (default: off)."""
        device_data = []
        for device in self.config.get('devices', []):
            status = 'off'  # default off
            device_data.append({
                'timestamp': datetime.now().isoformat(),
                'device_name': device,
                'status': status
            })
        return device_data

    def get_device_status(self):
        """Return current device statuses (no file I/O here; caller decides persistence)."""
        try:
            dev_data_list = self.generate_device_status()
            logger.info("Device status requested: %d devices", len(dev_data_list))
            return dev_data_list
        except Exception as e:
            logger.error(f"Error getting device status: {e}", exc_info=True)
            return []
