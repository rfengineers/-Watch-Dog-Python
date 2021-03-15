# A small Python program to monitor Watch Dog receiver instrument readings
# and record audio activity and instrument readings in nearby channels
# when SNR drops below a specified threshold

# Example usage:
#   python SignalMonitor.py

import sys
import serial
import time
from time import strftime
import pyaudio
import wave

# FM Broadcast frequency to monitor in MHz
FREQ = 89.1

# Minimum acceptable SNR
MIN_SNR = 10

# How often to poll for readings
POLL_SECS = 2

# Watch Dog USB serial port
WATCH_DOG_PORT = "/dev/ttyACM0"

# USB audio device index
USB_AUDIO_DEVICE_INDEX = -1

# How many seconds of audio to record for each audio sample
AUDIO_SECONDS = 3

def tuneToFreq(freq):
    x = s.write("FREQ " + str(freq * 100) + "\r\n")
    x = s.readline() # Discard this line
    x = s.readline() # Discard this line
    x = s.readline() # Discard this line
    time.sleep(1) # Short pause after re-tuning receiver

def setVolume():
    x = s.write("VOLPHONES 1\r\n")
    x = s.readline() # Discard this line
    x = s.readline() # Discard this line
    x = s.readline() # Discard this line

def getInstrumentReadings():
    # Send "RT" command, parse output
    x = s.write("RT\r\n") # Get real-time instrument readings
    x = s.readline() # Discard this line
    rt = s.readline().strip().split("|")
    x = s.readline() # Discard this line
    return { "snr": int(rt[0]), "rss": int(rt[1]), "multipath": int(rt[2]) }

AUDIO_SAMPLE_RATE = 44100
AUDIO_NUM_CHANNELS = 1
AUDIO_CHUNK_SIZE = 4096

def recordAudio(freq):
    stream = audio.open(format = pyaudio.paInt16, rate = AUDIO_SAMPLE_RATE, channels = AUDIO_NUM_CHANNELS, input_device_index = USB_AUDIO_DEVICE_INDEX, input = True, frames_per_buffer = AUDIO_CHUNK_SIZE)
    frames = []

    for i in range(0, int((AUDIO_SAMPLE_RATE / AUDIO_CHUNK_SIZE) * AUDIO_SECONDS)):
        data = stream.read(AUDIO_CHUNK_SIZE)
        frames.append(data)

    stream.stop_stream()
    stream.close()

    timestamp = strftime("%Y-%m-%d %H:%M:%S")

    wavefile = wave.open(str(freq) + " MHz " + timestamp + ".wav", "wb")
    wavefile.setnchannels(AUDIO_NUM_CHANNELS)
    wavefile.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    wavefile.setframerate(AUDIO_SAMPLE_RATE)
    wavefile.writeframes(b"".join(frames))
    wavefile.close()

def analyzeBadSNR():
    # While SNR on primary channel is below threshold,
    # record instrument readings and audio samples on primary channel
    # and four adjacent channels

    # Don't re-tune receiver on "first pass"
    firstPass = True

    # Continually analyze until SNR is back at threshold
    while True:
        # Analyze primary channel and four adjacent channels
        for freqOffset in [ 0, -0.2, 0.2, -0.4, 0.4 ]:
            freq = FREQ + freqOffset

            # Tune to frequency
            if not firstPass:
                tuneToFreq(freq)
            else:
                firstPass = False
        
            # Get real-time instrument readings
            rt = getInstrumentReadings()

            # If this is the primary channel and the SNR is no longer below threshold then stop analysis
            if freq == FREQ and rt["snr"] >= MIN_SNR:
                print("SNR is no longer below threshold")
                return

            # Output instrument readings
            logMessage = strftime("%Y-%m-%d %H:%M:%S") + "," + str(freq) + "," + str(rt["snr"]) + "," + str(rt["rss"]) + "," + str(rt["multipath"])
            print(logMessage)
            logFile.write(logMessage + "\r\n")

            # Record audio sample
            recordAudio(freq)

            time.sleep(1)

print("Detecting available audio devices")

# Initialize PyAudio
print("*** NOTE: Various audio-related error messages below are normal")
print("")
audio = pyaudio.PyAudio()
print("")
print("*** NOTE: Various audio-related error messages above are normal")
print("")

# List available audio devices
print("Available audio devices:")
print("")
for i in range(audio.get_device_count()):
    print("Index " + str(i) + ": " + audio.get_device_info_by_index(i).get('name'))
print("")

if USB_AUDIO_DEVICE_INDEX == -1:
    print("Please set USB_AUDIO_DEVICE_INDEX to an appropriate index from the above list and re-run this program")
    exit()

print("Starting RFEngineers, Inc. Watch Dog Signal Analyzer for " + str(FREQ) + " MHz")

# Open Watch Dog serial port
s = serial.Serial(port = WATCH_DOG_PORT, baudrate = 115200)

# Set headphones volume to minimum
setVolume()

# Tune to desired frequency
tuneToFreq(FREQ)

# Open log file
logFile = open(strftime("%Y-%m-%d %H:%M:%S") + ".csv", "w")

# Keep polling for readings
while True:
    # Get real-time instrument readings
    rt = getInstrumentReadings()

    if rt["snr"] >= MIN_SNR:
        print("SNR at or above threshold: " + str(rt["snr"]) + "/" + str(MIN_SNR))
        time.sleep(POLL_SECS)
    else:
        print("SNR below threshold: " + str(rt["snr"]) + "/" + str(MIN_SNR))
        analyzeBadSNR()

