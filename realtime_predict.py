import serial
import joblib
import pandas as pd
import time
import requests

# ---------------- SETTINGS ---------------- #
PORT = "COM23"          # Change if COM port changes
BAUD = 115200
BLYNK_TOKEN = "qUZNC4lfUh8T7GdwAhZZSHyT-f4O0hNt"
# ------------------------------------------ #

print("Connecting to ESP32...")

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)
ser.reset_input_buffer()

print("ESP32 connected. Reading data...\n")

# Load trained model
model = joblib.load("final_model.pkl")
le = joblib.load("final_label_encoder.pkl")

previous_status = "normal"
last_alert_time = 0
ALERT_COOLDOWN = 10   # seconds (prevents spam)

while True:
    try:
        line = ser.readline().decode(errors="ignore").strip()

        if line:
            values = line.split(",")

            if len(values) >= 2:
                mq2 = int(float(values[0]))
                mq135 = int(float(values[1]))

                # ML Prediction
                X = pd.DataFrame([[mq2, mq135]], columns=["mq2", "mq135"])
                pred = model.predict(X)
                label = le.inverse_transform(pred)[0]

                print(f"MQ2: {mq2} | MQ135: {mq135} | Prediction: {label}")

                # Send prediction to Blynk (V2)
                requests.get(
                    f"https://blynk.cloud/external/api/update?token={BLYNK_TOKEN}&V2={label}"
                )

                current_status = label.lower()
                current_time = time.time()

                # Trigger notification ONLY once when gas first detected
                if current_status == "gas" and previous_status != "gas":
                    if current_time - last_alert_time > ALERT_COOLDOWN:
                        print("Triggering gas_alert event...")
                        response = requests.get(
    f"https://blynk.cloud/external/api/logEvent?token={BLYNK_TOKEN}&code=gas_alert"
  
                        )

                        print("Event response:", response.text)

                        last_alert_time = current_time

                previous_status = current_status

    except KeyboardInterrupt:
        print("\nStopped.")
        break

    except Exception as e:
        print("Error:", e)