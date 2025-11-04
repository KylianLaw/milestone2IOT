import RPi.GPIO as GPIO
import time

# Use BCM pin numbering
GPIO.setmode(GPIO.BCM)

# Set up GPIO 18 as output
BUZZER_PIN = 18
GPIO.setup(BUZZER_PIN, GPIO.OUT)

print("=== Buzzer Test Started ===")
print("If you do NOT hear the buzzer, check wiring or buzzer connection.")
print("Press CTRL+C to stop.\n")

try:
    while True:
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        print("Buzzer ON → You should hear sound now!")
        time.sleep(1)

        GPIO.output(BUZZER_PIN, GPIO.LOW)
        print("Buzzer OFF → Silence expected.")
        time.sleep(1)

except KeyboardInterrupt:
    print("\nTest stopped by user.")

finally:
    GPIO.cleanup()
    print("GPIO cleaned up. Test complete.")
