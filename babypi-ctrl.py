import time
import RPi.GPIO as GPIO
import datetime
import signal
from sun import sun
from config import *
import os, subprocess, re

bLedStatus = False

dtLastStatusUpdate = datetime.datetime.min
oSunrise = datetime.time()
oSunset = datetime.time()

oSun = sun(lat=LATITUDE,long=LONGITUDE)

bRedLedEnabled = True
bGreenLedEnabled = False

bServiceRunning = False

def dprint(sMessage, iLogLevel):
    if DEBUG_ENABLED:
        if LOG_LEVEL >= iLogLevel:
            print(f"[DEBUG] {sMessage}")


def toggle_ir_led(bEnable):
    if bEnable:
        print("[INFO] Enabling IR-LED")
        GPIO.output(IR_LED_PIN, True)
    else:
        print("[INFO] Disabling IR-LED")
        GPIO.output(IR_LED_PIN, False)


def toggle_status_led(bEnableGreen, bEnableRed):
    global bGreenLedEnabled
    global bRedLedEnabled

    if bGreenLedEnabled != bEnableGreen:
        bGreenLedEnabled = bEnableGreen
        if bEnableGreen:
            dprint("Enabling Green LED",  4)
            GPIO.output(GREEN_STATUS_PIN, True)
        else:
            dprint("Disabling Green LED", 4)
            GPIO.output(GREEN_STATUS_PIN, False)

    if bRedLedEnabled != bEnableRed:
        bRedLedEnabled = bEnableRed
        if bEnableRed:
            dprint("Enabling Red LED", 4)
            GPIO.output(RED_STATUS_PIN, True)
        else:
            dprint("Disabling Red LED", 4)
            GPIO.output(RED_STATUS_PIN, False)


def setup_ports():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SHUTDOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(IR_LED_PIN, GPIO.OUT)
    GPIO.output(IR_LED_PIN, False)
    GPIO.setup(RED_STATUS_PIN, GPIO.OUT)
    GPIO.output(RED_STATUS_PIN, True)
    GPIO.setup(GREEN_STATUS_PIN, GPIO.OUT)
    GPIO.output(GREEN_STATUS_PIN, False)


def ir_led_routine():
    global bLedStatus
    global oSunrise
    global oSunset
    global oSun

    dtNow = datetime.datetime.now()

    oSunrise = oSun.sunrise(dtNow)
    oSunrise = datetime.datetime(dtNow.year, dtNow.month, dtNow.day, oSunrise.hour + 1, oSunrise.minute, oSunrise.second)
    oSunset = oSun.sunset(dtNow)
    oSunset = datetime.datetime(dtNow.year, dtNow.month, dtNow.day, oSunset.hour - 1, oSunset.minute, oSunset.second)

    if (dtNow >= oSunset or dtNow <= oSunrise):
        # Nighttime
        if not bLedStatus:
            toggle_ir_led(True)
            bLedStatus = True
    else:
        # Daytime
        if bLedStatus:
            toggle_ir_led(False)
            bLedStatus = False


# Prepare Shutdown-Handler function
def shutdown_handler(signum, frame):
    print("[INFO] Shutting down BabyPi-Controller")
    toggle_ir_led(False)
    toggle_status_led(False, True)
    exit(0)

# Register Shutdown-Handler function to SIGINT
signal.signal(signal.SIGINT, shutdown_handler)


# Shutdown-Function for powerbutton
def shut_down():
    print("[WARNING] Shutting down")
    toggle_ir_led(False)
    toggle_status_led(False, True)
    sCommand = "/usr/bin/sudo /sbin/shutdown -h now"
    oProcess = subprocess.Popen(sCommand.split(), stdout=subprocess.PIPE)
    sOutput = oProcess.communicate()[0]
    dprint(sOutput)


def check_service_routine():
    dprint("Checking Service-Status", 9)
    oCheckProcess = subprocess.Popen('ps -eaf|grep "picam"', shell=True, stdout=subprocess.PIPE)
    sOutput = oCheckProcess.stdout.read().decode("utf-8")
    oCheckProcess.stdout.close()
    oCheckProcess.wait()

    if sOutput.count('\n') == 3:
        dprint("picam service is running.", 9)
        bServiceRunning = True
        toggle_status_led(True, False)
    elif sOutput.count('\n') == 2:
        dprint(sOutput, 9)
        print("[WARNING] picam service seems to be restarting.")
        bServiceRunning = True
        toggle_status_led(True, True)
    else:
        dprint(sOutput, 9)
        print("[ERROR] picam service not running!")
        bServiceRunning = False
        toggle_status_led(False, True)


def check_powerbutton():
    if GPIO.input(SHUTDOWN_PIN) == False:
            shut_down()


# Run Main-Function
if __name__ == "__main__":
    setup_ports()

    while True:
        time.sleep(0.5)
        
        ir_led_routine()
        check_service_routine()
        check_powerbutton()

        time.sleep(0.5)

        oStatusDelay = datetime.datetime.now() - dtLastStatusUpdate
        if (oStatusDelay.total_seconds() > UPDATE_STATUS_INTERVAL * 60):
            sStatusMessage = ""
            if bLedStatus:
                sStatusMessage += "IR LED ON - "
            else:
                sStatusMessage += "IR LED OFF - "

            sStatusMessage += f"Sunrise: {str(oSun.sunrise())} - "
            sStatusMessage += f"Sunset: {str(oSun.sunset())}"
            print(f"[INFO] {sStatusMessage}")

            dtLastStatusUpdate = datetime.datetime.now()