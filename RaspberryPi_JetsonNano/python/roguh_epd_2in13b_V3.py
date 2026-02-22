#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import datetime
import json
import logging
import os
import re
import signal
import subprocess
import sys
import threading
import time
import zoneinfo
from argparse import ArgumentParser

from PIL import Image, ImageChops, ImageDraw, ImageFont


DESCRIPTION = "roguh's epd2in13b_V3 e-paper clock and art"

root = os.path.dirname(os.path.realpath(__file__))
picdir = os.path.join(root, "pic")
rpicdir = os.path.join(root, "roguh_pics")

LOG_FILE = os.path.expanduser(os.path.join("~/", os.path.basename(__file__) + ".log"))
FORMAT = "[%(levelname)s] %(module)s:%(funcName)s %(asctime)s: %(message)s"

logging.basicConfig(level=logging.DEBUG, format=FORMAT)

fh = logging.FileHandler(LOG_FILE, "a+")
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter(FORMAT))
logging.getLogger().addHandler(fh)

class DryRunEPD:
    @property
    def width(self):
        return 126
    @property
    def height(self):
        return 298
    def __getattr__(self, name):
        def anything(*args, **kwargs):
            logging.info("DryRunEPD.%s(%s, %s)", name, ", ".join(map(str, args)), kwargs)
        return anything
    @classmethod
    def EPD(cls):
        return cls()

try:
    from lib.waveshare_epd import epd2in13b_V3
except Exception:
    logging.error("Unable to load e-ink module, assuming dry-run mode.")
    epd2in13b_V3 = DryRunEPD

parser = ArgumentParser(description=DESCRIPTION)
parser.add_argument(
    "--cycle", "--period", "-c", type=float, default=1, help="Run every X minutes"
)
parser.add_argument("--black-background", "-b", action="store_true")
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--max-iterations", "-m", type=int, default=float("inf"))
parser.add_argument("--pictures", "-p", type=str, default="buffalo,rose")
argp = parser.parse_args()
black_background = argp.black_background
max_iterations = argp.max_iterations
target_cycle = argp.cycle
pictures = str(argp.pictures).split(",")

logging.warning(
    """
@@@@@@@    @@@@@@    @@@@@@@@  @@@  @@@  @@@  @@@        @@@@@@@   @@@@@@   @@@@@@@@@@
@@@@@@@@  @@@@@@@@  @@@@@@@@@  @@@  @@@  @@@  @@@       @@@@@@@@  @@@@@@@@  @@@@@@@@@@@
@@!  @@@  @@!  @@@  !@@        @@!  @@@  @@!  @@@       !@@       @@!  @@@  @@! @@! @@!
!@!  @!@  !@!  @!@  !@!        !@!  @!@  !@!  @!@       !@!       !@!  @!@  !@! !@! !@!
@!@!!@!   @!@  !@!  !@! @!@!@  @!@  !@!  @!@!@!@!       !@!       @!@  !@!  @!! !!@ @!@
!!@!@!    !@!  !!!  !!! !!@!!  !@!  !!!  !!!@!!!!       !!!       !@!  !!!  !@!   ! !@!
!!: :!!   !!:  !!!  :!!   !!:  !!:  !!!  !!:  !!!       :!!       !!:  !!!  !!:     !!:
:!:  !:!  :!:  !:!  :!:   !::  :!:  !:!  :!:  !:!  :!:  :!:       :!:  !:!  :!:     :!:
::   :::  ::::: ::   ::: ::::  ::::: ::  ::   :::  :::   ::: :::  ::::: ::  :::     ::
 :   : :   : :  :    :: :: :    : :  :    :   : :  :::   :: :: :   : :  :    :      :
"""
)
logging.info(DESCRIPTION)

logging.info(
    "Will draw %s background (%s), will iterate %s times approx. every %s minutes",
    "white" if not black_background else "black",
    ", ".join(pictures),
    max_iterations,
    target_cycle,
)
logging.info("Log file %s", LOG_FILE)

TIME_FORMAT = "%H:%M:%S"
SUB_TIME_FORMAT = "%H"

# Ping google's rock-solid DNS server
PING_IP = "8.8.8.8"
PING_CMD = "ping -W 0.5 -t 250 -i 0.05 -c 10".split() + [PING_IP]
PING_CMD_TIMEOUT_SECS = 5

SPEEDTEST_CMD = "speedtest-cli --json".split()
SPEEDTEST_CMD_TIMEOUT_SECS = 35


def handler_stop_signals(signum, frame):
    logging.critical("SHUTTING DOWN DUE TO SIGNAL %s frame=%s", signum, frame)
    epd2in13b_V3.epdconfig.module_exit()
    sys.exit()


signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)


def run(cmd, timeout):
    process = None
    process_output = ""

    def target():
        nonlocal process, process_output
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate()
        logging.info("Command output %s:\n%s", cmd, stdout)
        if stderr:
            logging.warning("Command %s printed to stderr! %s", cmd, stderr)
        process_output = stdout

    thread = threading.Thread(target=target)
    thread.start()

    thread.join(timeout)
    if thread.is_alive() and process is not None:
        process.terminate()
        thread.join()
    return process_output


def get_internet_speed():
    try:
        logging.info("Running SPEEDTEST_CMD command %s", SPEEDTEST_CMD)
        output = run(SPEEDTEST_CMD, SPEEDTEST_CMD_TIMEOUT_SECS)
        blob = json.loads(output)
        fmt = lambda num: f"{num / 1e6:0.3} Mb"
        return f"{fmt(blob['download'])}\u2193 {fmt(blob['upload'])}\u2191"
    except:
        logging.exception("Exception when running %s", SPEEDTEST_CMD)
    return ""


try:
    if argp.dry_run:
        epd = DryRunEPD.EPD()
    else:
        epd = epd2in13b_V3.EPD()

    # Drawing on the image
    logging.info("Loading files")
    fontpath = os.path.join(picdir, "Font.ttc")
    font40 = ImageFont.truetype(fontpath, 40)
    font27 = ImageFont.truetype(fontpath, 27)
    font16 = ImageFont.truetype(fontpath, 16)
    font12 = ImageFont.truetype(fontpath, 12)
    font10 = ImageFont.truetype(fontpath, 10)
    entire_rose = Image.open(os.path.join(rpicdir, "test.png"))
    no_petals = Image.open(os.path.join(rpicdir, "black.png"))
    rose_petals = Image.open(os.path.join(rpicdir, "red.png"))

    buffalo_black = Image.open(
        os.path.join(rpicdir, "generated/three_color_two_buffalo_104.black.png")
    )
    buffalo_red = Image.open(
        os.path.join(rpicdir, "generated/three_color_two_buffalo_104.red.png")
    )
    try:
        robot_black = Image.open(
            os.path.join(rpicdir, "generated/red_robot_3color.black.png")
        )
        robot_red = Image.open(os.path.join(rpicdir, "generated/red_robot_3color.red.png"))
    except Exception:
        logging.warning("Unable to find dumb robot from union-buster-inc")
        robot_red, robot_black = None, None

    # Drawing on the Vertical image
    refresh_time = 15
    iteration = 0
    internet_speed = ""
    while iteration < max_iterations:
        picture = pictures[iteration % len(pictures)]

        msgs = [
            (
                datetime.datetime.now(tz=zoneinfo.ZoneInfo(tz))
                + datetime.timedelta(seconds=refresh_time)
            )
            for tz in [
                "America/Denver",
                "America/Los_Angeles",
                "America/New_York",
                "Europe/Paris",
            ]
        ]

        logging.info("Running PING command %s", PING_CMD)
        ping_output = run(PING_CMD, PING_CMD_TIMEOUT_SECS)

        packet_loss = re.match(".*, (.*% packet loss)", ping_output, re.DOTALL)
        if packet_loss is not None and len(packet_loss.groups()):
            packet_loss = packet_loss.groups()[0]
        else:
            packet_loss = "naurrr"

        ping = re.match(".*mdev = (.*)ms", ping_output, re.DOTALL)
        if ping is not None and len(ping.groups()):
            ping = ping.groups()[0]
            ping = re.sub("\\.\\d+", "", ping, count=4).strip() + " ms"
        else:
            ping = ""

        # Don't run this too often
        if iteration % 5 == 1:
            new_internet_speed = get_internet_speed()
            if new_internet_speed != "":
                internet_speed = new_internet_speed

        jpath = os.path.join(root, "./upcoming.json")
        logging.info("Running CALENDAR command %s", PING_CMD)
        upcoming_output = run(
            [os.path.join(root, "./upcoming_ical_events.py"), "--output-file", jpath],
            60,
        )
        upcoming_event = {"summary": "", "delta": ""}
        if os.path.exists(jpath):
            with open(jpath) as upcoming_file:
                upcoming_event = json.load(upcoming_file)

        logging.info(
            "Drawing the current time=%s + refresh time=%s, packet_loss=%s, ping=%s, internet_speed=%s, upcoming event=%s",
            datetime.datetime.now(),
            refresh_time,
            packet_loss,
            ping,
            internet_speed,
            upcoming_event,
        )
        drawing_start_time = time.time()

        LBlackimage = Image.new("1", (epd.width, epd.height), 255)  # 126*298
        LRYimage = Image.new("1", (epd.width, epd.height), 255)  # 126*298
        drawblack = ImageDraw.Draw(LBlackimage)
        drawry = ImageDraw.Draw(LRYimage)

        logging.info("Drawing %s", picture)
        if picture == "rose":
            if black_background:
                rose = entire_rose.convert("1")
            else:
                rose = ImageChops.invert(no_petals.convert("1"))
            drawblack.bitmap((0, 90), rose)

            rose = ImageChops.invert(rose_petals.convert("1"))
            drawry.bitmap((0, 90), rose)
        elif picture == "buffalo":
            drawblack.bitmap((0, 90), buffalo_black)
            drawry.bitmap((0, 90), buffalo_red)

        elif picture == "robot":
            y = epd.height - robot_black.height
            drawblack.bitmap((0, y), robot_black)
            drawry.bitmap((0, y), robot_red)

        # greeting = "howdy!"
        # drawblack.text((2, 0), greeting, font=font16, fill=0)
        # greeting_w = 104 // 2 + 5
        # msg2 = "how you"
        # drawblack.text((greeting_w, 0), msg2, font=font10, fill=0)
        # _, h = font10.getsize(msg2)
        # drawblack.text((greeting_w, h - 3), "doin", font=font10, fill=0)

        # drawblack.text((10, 45), "roguh.com", font=font16, fill=0)
        # drawblack.text((20, 65), "微雪电子", font=font16, fill=0)

        drawblack.text((2, 0), msgs[0].strftime(TIME_FORMAT), font=font40, fill=0)
        for i in range(3):
            drawry.text(
                (i * 104 // 3, 35),
                msgs[i + 1].strftime(SUB_TIME_FORMAT),
                font=font27,
                fill=0,
            )

        info_y = 60
        drawblack.text((0, info_y), f"{packet_loss}", font=font12, fill=0)
        drawblack.text(
            (0, info_y + 12),
            f"{upcoming_event['summary']}",
            font=font10,
            fill=0,
        )
        drawblack.text(
            (0, info_y + 22),
            f"{upcoming_event['delta']}",
            font=font10,
            fill=0,
        )
        drawblack.text(
            (0, info_y + 2 + 10 * 3), f"{internet_speed}", font=font10, fill=0
        )

        logging.info("Initializing screen and sending drawing")
        epd.init()
        epd.display(epd.getbuffer(LBlackimage), epd.getbuffer(LRYimage))

        logging.info("Putting screen to low power mode")
        epd.sleep()

        refresh_time = time.time() - drawing_start_time
        iteration += 1

        if iteration < max_iterations:
            extra_quickness = 10
            sleep_time = max(10, target_cycle * 60 - refresh_time - extra_quickness)
            logging.info("Sleeping %s seconds", sleep_time)
            time.sleep(sleep_time)

    logging.info("Done")

except IOError as e:
    logging.exception("uwu")

except KeyboardInterrupt:
    logging.critical("Shutting down. Bye!")
    epd2in13b_V3.epdconfig.module_exit()
