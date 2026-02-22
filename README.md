My files are in `RaspberryPi_JetsonNano/python/`.

**Usage**: install all dependencies and run the main script:

```
cd RaspberryPi_JetsonNano/python/
./roguh_epd_2in13b_V3.py
./roguh_epd_2in13b_V3.py --dry-run  # if you're uncool and dont have a ROC with SPI libraries installed
```

To use the calendar features, get a public ical link and add it as a JSON list to `calendar_links.json`:

```
# EXAMPLE ONLY!
$ cd RaspberryPi_JetsonNano/python/
$ cat ./calendar_links.json
["https://outlook.office365.com/owa/calendar/..../reachcalendar.ics"]
```

BTW FYI:
```bash
$ git diff 833d3a86be8c8e0463838574fdbece36b1487fa8 --stat
```
 
 
#### e-Paper  
waveshare electronics
![waveshare_logo.png](waveshare_logo.png)

##### 中文:  
Jetson Nano、Raspberry Pi、Arduino、STM32例程
* RaspberryPi_JetsonNano  
    > C
    > Python 
* Arduino:  
    > Arduino UNO  
* STM32:  
    > STM32F103ZET6 
    
更多资料请在官网上搜索:  
http://www.waveshare.net


## English:  
Jetson Nano、Raspberry Pi、Arduino、STM32 Demo:  
* RaspberryPi_JetsonNano:  
    > C
    > Python
* Arduino:  
    > Arduino UNO  
* STM32:  
    > STM32F103ZET6 
    
For more information, please search on the official website:   
https://www.waveshare.com



