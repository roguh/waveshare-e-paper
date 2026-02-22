## 3-Color E-Ink Clock, Picture Slideshow, and Event Calendar

#### by Felina Rivera Calzadillas (ROGUH)

![Buffalo Soldiers](./roguh_pics/generated/three_color_two_buffalo_104.resized104.png)
![Rose](./roguh_pics/test.png)

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

### Dependency Install                                                         
                                                                               
You might need to enable SPI for your board and install python-dev development dependencies `apt instal
l python3-dev`.
                                                                               
You might also need a larger swap file if any of these steps run out of memory.
                                                                               
```                                                                            
python3 -m venv venv                                                           
# or other file depending on shell, e.g. activate.fish                         
. venv/bin/activate                                                            
pip install -r requirements.txt                                                
``` 

### Credits

BTW FYI: some of the SPI firmware code is originally from an old waveshare git repo.

```bash
$ git diff 833d3a86be8c8e0463838574fdbece36b1487fa8 --stat
```

