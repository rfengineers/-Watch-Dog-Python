# A small Python program to monitor a Watch Dog receiver for alarm conditions
# and send alert emails when active alarms are found

import serial
import time
import smtplib

# Minimum amount of time between alarm emails
ALARM_LIMIT_SECS = 900

# How often to poll for alarms
ALARM_POLL_SECS = 15

# Watch Dog USB serial port
WATCH_DOG_PORT = "/dev/ttyACM0"

# Email settings
EMAIL_SUBJECT = "Watch Dog alarms active!"
EMAIL_FROM = "<Your email address>"
EMAIL_PASSWORD = "<Your password>"
EMAIL_TO = "<Recipient email address>"
EMAIL_SERVER_HOSTNAME = "<Your SMTP server address>" # e.g. smtp.gmail.com, etc
EMAIL_SERVER_PORT = 587

def sendEmail(emailBody):
    print("Sending email")
    server = smtplib.SMTP(EMAIL_SERVER_HOSTNAME, EMAIL_SERVER_PORT)
    server.starttls()
    server.login(EMAIL_FROM, EMAIL_PASSWORD)
    server.sendmail(EMAIL_FROM, EMAIL_TO, emailBody)
    server.quit()

def processAlarms(snrAlarm, audioAlarm, rdsAlarm, rssAlarm, pilotAlarm, noaaAlarm, lastAlarm):
    if (snrAlarm or audioAlarm or rdsAlarm or rssAlarm or pilotAlarm or noaaAlarm) and (time.time() - lastAlarm > ALARM_LIMIT_SECS):
        print("ALARM")
        emailBody = "From: " + EMAIL_FROM + "\nTo: " + EMAIL_TO + "\nSubject: " + EMAIL_SUBJECT + "\n\nThe following alarms are active on your Watch Dog receiver:\n\n"
        if snrAlarm:
            emailBody += "SNR alarm\n"
        if audioAlarm:
            emailBody += "Audio alarm\n"
        if rdsAlarm:
            emailBody += "RDS alarm\n"
        if rssAlarm:
            emailBody += "RSS alarm\n"
        if pilotAlarm:
            emailBody += "Pilot alarm\n"
        if noaaAlarm:
            emailBody += "NOAA 1,050 Hz alert tone detected\n"
        sendEmail(emailBody)
        return True
    else:
        return False

# Open Watch Dog serial port
s = serial.Serial(port = WATCH_DOG_PORT, baudrate = 115200)

# Initialize "lastAlarm"
lastAlarm = time.time() - ALARM_LIMIT_SECS

# Keep polling for alarms
while True:
    # Send "RT" command, parse output, process alarm states
    x = s.write("RT\r\n") # Get real-time instrument values
    x = s.readline() # Discard this line
    rt = s.readline().strip().split("|")
    snrAlarm = int(rt[6]) == 1
    audioAlarm = int(rt[7]) == 1
    rdsAlarm = int(rt[8]) == 1
    rssAlarm = int(rt[13]) == 1
    pilotAlarm = int(rt[14]) == 1
    noaaAlarm = int(rt[15]) == 1
    print("Alarm states [RSS: " + str(rssAlarm) + "] [SNR: " + str(snrAlarm) + "] [Audio: " + str(audioAlarm) + "] [RDS: " + str(rdsAlarm) + "] [Pilot: " + str(pilotAlarm) + "] [NOAA: " + str(noaaAlarm) + "]")
    if processAlarms(snrAlarm, audioAlarm, rdsAlarm, rssAlarm, pilotAlarm, noaaAlarm, lastAlarm):
        lastAlarm = time.time()
    x = s.readline() # Discard this line
    time.sleep(ALARM_POLL_SECS)

