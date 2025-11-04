# PiGuardian  
Smart Home IoT Security System — Raspberry Pi Project  
**Authors:** Ilian Adeleke & Cedric Augustin  

---

## Team Members
| Name | 
|------|
| Ilian Adeleke |
| Cedric Augustin | 

---

## System Overview
PiGuardian is an IoT-based home security and environment monitoring system built on Raspberry Pi OS.  
It collects real-time environmental and security data (temperature, humidity, motion, images) and controls devices (lights, fan, buzzer, LCD) via Adafruit IO MQTT.

### Functional Modules
- `environmental_module.py` — reads DHT11 sensor data (temperature, humidity)
- `security_module.py` — detects motion using PIR sensor and captures an image
- `device_control_module.py` — monitors status of connected devices (lights, fan, doors)
- `MQTT_communicator.py` — handles secure MQTT connection and publishing to Adafruit IO
- `milestoneLastTry.py` — main orchestrator combining all modules, with local LCD and buzzer feedback
- `cam.py` / `buzzer.py` — standalone hardware testing utilities

---



## System Block Diagram

<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/e25ef9ea-754e-454a-972c-3213c476a603" />

![20251104_174111](https://github.com/user-attachments/assets/571eaf85-38bc-422a-8aee-2add86f720aa)
![20251104_174107](https://github.com/user-attachments/assets/719a01c5-e275-43e1-b84e-e09975b1179c)
![20251104_174047](https://github.com/user-attachments/assets/dd2fcba5-ea82-49e8-bce6-0f05a6c299fc)


---

## Bill of Materials (BOM)

- Raspberry Pi 4 Model B (4GB RAM) — main controller board  
- DHT11 sensor — digital temperature and humidity measurement  
- PIR motion sensor (HC-SR501) — detects movement  
- I²C LCD display (16×2 with PCF8574 backpack) — displays system messages  
- Passive buzzer (KY-006 or equivalent) — audible alerts  
- LEDs (red, yellow, green) — indicate system and device states  
- 220 Ω resistors (×3) — protect LEDs from overcurrent  
- Jumper wires (male-to-male and male-to-female, ~15 total) — for all GPIO connections  
- Female connector wires — used with modules and sensors that have female headers  
- Breadboard — prototyping base for the circuit  
- Optional camera module (Raspberry Pi Camera v2) — captures images when motion is detected  

---

## Wiring Diagram / Schematics

| Component | GPIO Pin | Notes |
|------------|-----------|-------|
| DHT11 | GPIO 19 | Data pin |
| PIR Sensor | GPIO 6 | Motion input |
| Buzzer | GPIO 18 | PWM-capable |
| LED Red | GPIO 20 | Output |
| LED Yellow | GPIO 16 | Output |
| LED Green | GPIO 21 | Output |
| LCD SDA | GPIO 2 (SDA) | I²C |
| LCD SCL | GPIO 3 (SCL) | I²C |
| 5V & GND | — | Common power rail |

(Include a breadboard photo or circuit image in your repository’s `/media` folder.)

---

## Setup Instructions

### 1. OS Preparation
- Install Raspberry Pi OS (Bookworm or Bullseye).  
- Enable I²C, Camera, and SSH using:
  ```bash
  sudo raspi-config
  sudo apt update && sudo apt upgrade -y

### 2. Install Dependencies
  ```bash
  sudo apt install python3-pip python3-smbus i2c-tools -y
  pip3 install paho-mqtt adafruit-circuitpython-dht adafruit-blinka
  ```
### 3. Environment Variables / Config

- Edit your config.json and fill in your Adafruit credentials:
  ```bash
  {
    "ADAFRUIT_IO_USERNAME": "YourUser",
    "ADAFRUIT_IO_KEY": "YourKey"
  }
    ```

### How to Run

Run the main controller program:
```bash
  python3 milestoneLastTry.py
```
### Environmental Feed

| Field       | Type   | Unit    | Example               |
| ----------- | ------ | ------- | --------------------- |
| timestamp   | string | ISO8601 | "2025-11-04T16:22:15" |
| temperature | float  | °C      | 22.7                  |
| humidity    | float  | %       | 55.2                  |

### Security Feed
| Field           | Type   | Description                         |
| --------------- | ------ | ----------------------------------- |
| motion_detected | bool   | true when PIR triggered             |
| smoke_detected  | bool   | not yet implemented                 |
| image_path      | string | Local image or `.txt` fallback file |

### File Rotation Policy

Each day the system creates new files:
```bash

YYYYMMDD_environmental_data.txt

YYYYMMDD_security_data.txt

YYYYMMDD_device_status.txt

```


Files are flushed every 10 seconds and rotated daily.


Known Limitations

    -No smoke or CO₂ sensor implemented yet

    -Camera capture fails gracefully if rpicam-still isn’t installed

    -DHT11 accuracy limited (±2°C, ±5% RH)

    -LCD limited to 16×2 display size (no scrolling)

    -Requires stable internet for MQTT communication



  Future Work

      -Add CO₂ / VOC sensors for air quality tracking

      -Integrate face recognition using OpenCV

      -Develop local Flask web dashboard

      -Add email/SMS push notifications for alerts

      -Integrate voice control (Google Assistant / Alexa)
