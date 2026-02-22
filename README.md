## E-Ink Clock, Picture Slideshow, and Event Calendar by Felina Rivera Calzadillas (ROGUH)

### **Usage**

Install all dependencies and run the main script:

```
cd RaspberryPi_JetsonNano/python/
./main.py
./main.py --dry-run  # if you're uncool and dont have a ROC with SPI libraries installed
```

### Calendar Setup

To use the calendar features, get a public ical link and add it as a JSON list to `calendar_links.json`:

```
# EXAMPLE ONLY!
$ cd RaspberryPi_JetsonNano/python/
$ cat ./calendar_links.json
["https://outlook.office365.com/owa/calendar/..../reachcalendar.ics"]
```

### Hardware: 2.13 e-Paper HAT by Waveshare

https://www.waveshare.com/2.13inch-e-paper-hat.htm

### Credits

BTW FYI: some of the SPI firmware code is originally from an old waveshare git repo.

```bash
$ git diff 833d3a86be8c8e0463838574fdbece36b1487fa8 --stat
```

