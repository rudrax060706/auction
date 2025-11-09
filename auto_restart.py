import subprocess
import time
import os
import signal

BOT_FILE = "main.py"  # your main bot file
RESTART_INTERVAL = 300  # 5 minutes in seconds

def restart_bot():
    print("Starting bot process...")
    process = subprocess.Popen(["python", BOT_FILE])

    try:
        while True:
            time.sleep(RESTART_INTERVAL)
            print("\n⏳ Restarting bot...")
            os.kill(process.pid, signal.SIGTERM)
            time.sleep(2)
            process = subprocess.Popen(["python", BOT_FILE])
            print("✅ Bot restarted successfully.")
    except KeyboardInterrupt:
        print("Stopping auto-restart system...")
        os.kill(process.pid, signal.SIGTERM)

if __name__ == "__main__":
    restart_bot()
