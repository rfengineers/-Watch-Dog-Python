# A small Python program to record Watch Dog receiver instrument readings
# to a spreadsheet (.CSV file) for further analysis

# Example usage:
#   python InstrumentReadings.py | tee InstrumentReadings.csv

import sys
import serial
import time
from time import strftime

# How often to poll for readings
POLL_SECS = 2

# Watch Dog USB serial port
WATCH_DOG_PORT = "/dev/ttyACM0"

# Open Watch Dog serial port
s = serial.Serial(port = WATCH_DOG_PORT, baudrate = 115200)

# Keep polling for readings
while True:
    # Send "RT" command, parse output, process alarm states
    x = s.write("RT\r\n") # Get real-time instrument values
    x = s.readline() # Discard this line
    rt = s.readline().strip().split("|")
    x = s.readline() # Discard this line
    
    # Extract readings from pipe-delimited output
    snr        = rt[0]
    rss        = rt[1]
    multipath  = rt[2]
    audioLeft  = rt[4]
    audioRight = rt[5]

    # Output readings    
    sys.stdout.write(strftime("%Y-%m-%d %H:%M:%S") + "," + snr + "," + rss + "," + multipath + "," + audioLeft + "," + audioRight + "\n")
    sys.stdout.flush()
    
    time.sleep(POLL_SECS)

