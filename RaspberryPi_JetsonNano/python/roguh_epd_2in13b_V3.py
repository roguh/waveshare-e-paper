#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import datetime
import logging
import os
import re
import signal
import subprocess
import sys
import time
import zoneinfo
from argparse import ArgumentParser

from PIL import Image, ImageChops, ImageDraw, ImageFont

from lib.waveshare_epd import epd2in13b_V3

root = os.path.dirname(os.path.realpath(__file__))
picdir = os.path.join(root, "pic")
rpicdir = os.path.join(root, "roguh_pics")

LOG_FILE = os.path.expanduser(os.path.join("~/", os.path.basename(__file__) + ".log"))
FORMAT = "[%(levelname)s] %(module)s:%(funcName)s %(asctime)s: %(message)s"

logging.basicConfig(level=logging.DEBUG, format=FORMAT)

fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter(FORMAT))
logging.getLogger().addHandler(fh)

parser = ArgumentParser()
parser.add_argument("--white-background", "-w", action="store_true")
parser.add_argument("--max-iterations", "-m", type=int, default=float("inf"))
argp = parser.parse_args()
white_background = argp.white_background
max_iterations = argp.max_iterations

logging.info(
    "%s background, will iterate %s times",
    "white" if white_background else "black",
    max_iterations,
)
logging.info("log file %s", LOG_FILE)

TIME_FORMAT = "%H:%M:%S"
SUB_TIME_FORMAT = "%H"

# Ping google's rock-solid DNS server
PING_IP = "8.8.8.8"
PING_CMD = "ping -W 0.5 -t 250 -i 0.05 -c 20 " + PING_IP


def handler_stop_signals(signum, frame):
    logging.critical("SHUTTING DOWN DUE TO SIGNAL %s", signum)
    epd2in13b_V3.epdconfig.module_exit()
    sys.exit()


signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)

try:
    logging.info("roguh's epd2in13b_V3 clock and art")

    epd = epd2in13b_V3.EPD()

    # Drawing on the image
    logging.info("Loading files")
    font40 = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), 40)
    font27 = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), 27)
    font16 = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), 16)
    font12 = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), 12)
    entire_rose = Image.open(os.path.join(rpicdir, "test.png"))
    no_petals = Image.open(os.path.join(rpicdir, "black.png"))
    rose_petals = Image.open(os.path.join(rpicdir, "red.png"))

    # Drawing on the Vertical image
    refresh_time = 15
    iteration = 0
    while iteration < max_iterations:
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
        ping_output = subprocess.check_output(PING_CMD.split())

        packet_loss = re.match(
            ".*, (.*% packet loss)", ping_output.decode("utf-8"), re.DOTALL
        )
        if packet_loss is not None and len(packet_loss.groups()):
            packet_loss = packet_loss.groups()[0]

        ping = re.match(".*mdev = (.*)ms", ping_output.decode("utf-8"), re.DOTALL)
        if ping is not None and len(ping.groups()):
            ping = ping.groups()[0]
            ping = re.sub("\\.\\d+", "", ping, count=4).strip() + " ms"

        logging.info(
            "Drawing the current time (%s) + refresh time (%s), packet_loss=%s",
            datetime.datetime.now(),
            refresh_time,
            packet_loss,
        )
        drawing_start_time = time.time()

        LBlackimage = Image.new("1", (epd.width, epd.height), 255)  # 126*298
        LRYimage = Image.new("1", (epd.width, epd.height), 255)  # 126*298
        drawblack = ImageDraw.Draw(LBlackimage)
        drawry = ImageDraw.Draw(LRYimage)

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
                (i * 104 // 3, 38),
                msgs[i + 1].strftime(SUB_TIME_FORMAT),
                font=font27,
                fill=0,
            )

        drawblack.text((0, 70), f"{packet_loss}", font=font12, fill=0)
        drawblack.text((0, 82), f"{ping}", font=font12, fill=0)

        logging.info("Drawing rose")
        if white_background:
            rose = ImageChops.invert(no_petals.convert("1"))
        else:
            rose = entire_rose.convert("1")
        drawblack.bitmap((0, 90), rose)

        rose = ImageChops.invert(rose_petals.convert("1"))
        drawry.bitmap((0, 90), rose)

        logging.info("Initializing screen and sending drawing")
        epd.init()
        epd.display(epd.getbuffer(LBlackimage), epd.getbuffer(LRYimage))

        logging.info("Putting screen to low power mode")
        epd.sleep()

        refresh_time = time.time() - drawing_start_time
        iteration += 1

        if iteration < max_iterations:
            sleep_time = 60 - refresh_time
            logging.info("Sleeping %s seconds", sleep_time)
            time.sleep(sleep_time)

    logging.info("Done")

except IOError as e:
    logging.exception("uwu")

except KeyboardInterrupt:
    logging.critical("Shutting down. Bye!")
    epd2in13b_V3.epdconfig.module_exit()
