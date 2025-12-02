# 🛡️ PiGuardian — IoT Home Automation & Security System  
### Raspberry Pi • Flask • Chart.js • Adafruit IO • Neon DB  
**Team Members:**  
- Ilian Adeleke     2330261 
- Cedric Augustin   2233427

---

# 📌 Project Overview  
PiGuardian is a smart IoT security and automation system built on Raspberry Pi OS.  
It collects **environmental data**, detects **motion intrusions**, controls **three IoT devices**,  
and displays everything through a cloud-deployed **Flask dashboard (Render.com)**.

The system communicates using:
- **MQTT → Adafruit IO** (live sensor publishing + device control)  
- **REST → Neon PostgreSQL** (historical storage + queries for charts)  
- **Flask + Chart.js** (web dashboard with analytics)

---

# 🏗️ System Architecture (Required in Milestone 3)
📌 <img width="307" height="764" alt="image" src="https://github.com/user-attachments/assets/105bf9b1-1a4f-418f-ad29-f9defb873b68" />



---

# 🧰 Hardware Used (Bill of Materials)
| Component | Purpose |
|----------|---------|
| Raspberry Pi 4B | Main controller |
| DHT11 Sensor | Temperature + humidity |
| PIR Motion Sensor | Detects motion |
| I2C LCD 16×2 | Displays local system messages |
| LEDs (Red/Yellow/Green) | Device feedback |
| Buzzer (PWM) | Audible alerts |
| Breadboard + Wires | Circuit foundation |
| Pi Camera (optional) | Intrusion snapshots |

📌 **INSERT REAL-WORLD WIRING PHOTO HERE**  
<img width="955" height="654" alt="image" src="https://github.com/user-attachments/assets/aa2d19e7-cff0-4ca0-bc92-ab89448bd834" />
<img width="951" height="638" alt="image" src="https://github.com/user-attachments/assets/58d71b9c-94fa-4bd9-a356-7f735e20c937" />
<img width="951" height="602" alt="image" src="https://github.com/user-attachments/assets/77003e76-9e10-4a8d-9ae2-5ef9ee7cc30c" />


---

# 🔌 Wiring Diagram  
| Component | GPIO Pin | Notes |
|----------|----------|-------|
| DHT11 | GPIO 19 | Data |
| PIR Sensor | GPIO 6 | Motion |
| LCD SDA | GPIO 2 | I²C |
| LCD SCL | GPIO 3 | I²C |
| Buzzer | GPIO 18 | PWM |
| LED Red | GPIO 20 | Output |
| LED Yellow | GPIO 16 | Output |
| LED Green | GPIO 21 | Output |



---

# 🧪 Raspberry Pi Software Modules  
| File | Description |
|------|-------------|
| `environmental_module.py` | Reads DHT11, sends to Adafruit + Neon |
| `security_module.py` | PIR detection, intrusion logging |
| `device_control_module.py` | Sends device commands to Adafruit IO |
| `milestoneLastTry.py` | Main controller orchestrator |
| `MQTT_communicator.py` | Handles MQTT connection & publishing |
| `lcd.py`, `buzzer.py` | Local feedback via LCD + buzzer |

---

# ☁️ Cloud Components

## 🌩️ Adafruit IO Dashboard (Live Data + Device Control)
📌 <img width="1843" height="675" alt="image" src="https://github.com/user-attachments/assets/f150ad85-aaef-4dab-9a28-3582b0f0d0c5" />


---

## 🗄️ Neon PostgreSQL Database (Historical Storage)
Stores:
- environmental_readings  
- security_events  

📌 **INSERT TABLE STRUCTURE SCREENSHOT HERE**  
<img width="318" height="219" alt="image" src="https://github.com/user-attachments/assets/e688fb7a-f00f-4393-aba0-8e715506863f" />


📌 **INSERT LIVE DATA INSERT SCREENSHOT HERE**  
<img width="1583" height="808" alt="image" src="https://github.com/user-attachments/assets/c8b07f53-2525-4424-a82f-cd566a02c610" />
<img width="1549" height="806" alt="image" src="https://github.com/user-attachments/assets/34bb99be-e844-469a-b131-6c2a4378bac4" />



---

# 🌐 Flask Web Application (Deployed on Render)

### ✔️ Home Page  
- Animated banner  
- Live system summary  
📌 <img width="1859" height="899" alt="image" src="https://github.com/user-attachments/assets/c990dba7-8f19-40cd-ab8c-e67b921fc874" />


---

### ✔️ Environment Page  
- Date selector  
- Historical data loaded from Neon  
- Chart.js graphs  
📌 <img width="1705" height="854" alt="image" src="https://github.com/user-attachments/assets/4ff1f736-f2c2-4593-bc16-f8a68104c180" />


---

### ✔️ Device Control Page  
- Buttons controlling 3 devices  
- Direct API calls to Adafruit IO  
📌 <img width="1794" height="921" alt="image" src="https://github.com/user-attachments/assets/d4630d51-e421-4646-ab8a-91fdc0e8a2b1" />


---

### ✔️ Security Page  
- Arm/disarm system  
- Logs per selected date  
- Motion graph (24h)  
📌 <img width="1560" height="898" alt="image" src="https://github.com/user-attachments/assets/5ddfb440-aa71-40f7-aabf-2c5aab153877" />
    <img width="1547" height="489" alt="image" src="https://github.com/user-attachments/assets/04b1d951-301e-4bf8-9545-647cba4860f7" />



---

### ✔️ About Page  
- Team information  
- Project description  
📌 <img width="1401" height="914" alt="image" src="https://github.com/user-attachments/assets/f70eb4c0-0406-454e-9a3a-98438eae069f" />
    <img width="1653" height="726" alt="image" src="https://github.com/user-attachments/assets/cfc5eb1f-1a8b-4cba-82a8-b9001f201fc1" />



---

# 🗄️ Local & Cloud Data Storage
- Automatically writes to local SQLite if offline  
- Sends data to Neon PostgreSQL when online  

*(We didnt implement offline sync )*

---

# ▶️ Running the System

## 🎛️ Running on Raspberry Pi:
```bash
sudo apt update && sudo apt upgrade -y
python3 milestoneLastTry.py

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
  pip install -r requirements.txt
  flask run
```

📊 Data Formats

Environmental Readings:
Field        | Type     | Example
-------------|----------|-------------------------
timestamp    | ISO8601  | "2025-11-27T16:22:15"
temperature  | float    | 24.6
humidity     | float    | 45.1

Security Events: 
Field         | Description
--------------|-----------------------------------------
event_type    | "motion" or "smoke"
raw_timestamp | ISO timestamp
image_path    | optional camera capture

🗂️ Daily Log Files (Auto Rotated) | 
----------------------------------|
YYYYMMDD_environmental_data.txt   | 
YYYYMMDD_security_data.txt        |
YYYYMMDD_device_status.txt        | 


🌟 Future Work
- Add more sensors (CO₂, VOC, MQ-135)
- Real-time SMS or email alerts
- Face recognition
- Voice assistant control
- Advanced UI with animations







