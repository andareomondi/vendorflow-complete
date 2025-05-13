---

# **MQTT Relay Control System**
🚀 **A lightweight, real-time relay control system using Django & MQTT.**

## 📌 **Overview**
This project enables **remote relay control** via **MQTT messaging** in **Django**. It utilizes **Mosquitto (MQTT broker)** and **MQTTX (GUI client)** for testing, while Django serves as the backend logic to process commands and update relay states dynamically.

## ⚙️ **Tech Stack**
✅ **Django** → Backend framework  
✅ **HTMX** → Smooth UI updates  
✅ **Mosquitto** → MQTT broker for message handling  
✅ **MQTTX** → GUI-based MQTT client for testing  
✅ **Paho MQTT** → Python MQTT client  
✅ **Bootstrap** → Frontend styling  

## 🚀 **Setup Instructions**
### **1️⃣ Install Requirements**
```bash
pip install -r requirements.txt
```
Ensure you have Django and **Paho MQTT** installed.

### **2️⃣ Install Mosquitto (MQTT Broker)**
Download and install [Mosquitto](https://mosquitto.org/download/), then start the broker:
```bash
mosquitto -v
```

### **3️⃣ Configure Mosquitto for Local Testing**
Modify `mosquitto.conf` to allow connections:
```text
listener 1883
allow_anonymous true
log_type all
```

### **4️⃣ Run Django Server**
```bash
python manage.py runserver
```

### **5️⃣ MQTT Subscription for Relay Updates**
Use `mosquitto_sub` to listen for relay commands:
```bash
mosquitto_sub -h 127.0.0.1 -t "RELAY_CONTROLLER/+/command" -v
```

### **6️⃣ Publish Test MQTT Messages**
Trigger relay updates via **MQTTX** or CLI:
```bash
mosquitto_pub -h 127.0.0.1 -t "RELAY_CONTROLLER/0677FF56516585496705413/command" -m '{"channel_2": "ON"}'
```

## 🎨 **HTMX Auto-Reload for UI Updates**
The frontend refreshes relay statuses **without full page reloads**:
```html
<script>
    async function checkForUpdates() {
        const response = await fetch("{% url 'relay-status-check' device.id %}");
        const data = await response.json();

        if (data.updated) {
            location.reload();
        }
    }
    setInterval(checkForUpdates, 3000);  // ✅ Auto-refresh every 3 seconds
</script>
```

## 🛠 **Troubleshooting**
🔹 **Django not connecting to MQTT?**  
✔️ Run manually:
```python
import paho.mqtt.client as mqtt

mqtt_client = mqtt.Client()
mqtt_client.connect("127.0.0.1", 1883, 60)
mqtt_client.publish("RELAY_CONTROLLER/0677FF56516585496705413/command", '{"channel_2": "ON"}')
```
🔹 **Mosquitto not receiving messages?**  
✔️ Check logs with:
```bash
mosquitto -v
```

## 🎯 **Next Features**
✔️ WebSocket support for **instant relay state updates**  
✔️ Enhanced MQTT authentication **using username/password**  
✔️ Multi-device support for **IoT relay control**  

---
