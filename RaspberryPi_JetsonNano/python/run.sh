#!/bin/sh
set -x
scp -r roguh_pics roguh_epd_2in13b_V3.py roguh@roguh-eyeball-2.local:src/waveshare_epaper/e-Paper/RaspberryPi_JetsonNano/python
ssh roguh@roguh-eyeball-2.local killall python3
ssh roguh@roguh-eyeball-2.local src/waveshare_epaper/e-Paper/RaspberryPi_JetsonNano/python/roguh_epd_2in13b_V3.py "$@"
