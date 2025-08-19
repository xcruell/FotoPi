<p align="center">
<img width="2048" height="1024" alt="FotoPi-trans" src="https://github.com/user-attachments/assets/d51795ef-8d2b-48e6-aff9-84d260be7681" />
</p>
<h1 align="center">

</h1>   
<br />


I was looking for a photo-oriented GUI for the Raspberry Pi HQ Camera Module, like CinePi for example.
Sadly, i couldn't find anything that met my expectations.. so i started learning and made FotoPi!

FotoPi uses picamera2 and PyQt5 libs.<br />
The GUI is made for touchscreens, but can be controlled with a mouse as well.

I'm currently using the following hardware:
- Raspberry Pi 4 4GB
- Raspberry Pi HQ Camera Module
- C-Mount to EF/EF-S-Mount adapter (with a Canon lens)
- Waveshare 5.5" AMOLED 1080x1920px capacitive touch display

The C-mount to EF-mount adapter is self-designed in CAD and 3D-printed, allowing pretty much all kinds of lenses!

# Screenshots:
<img width="1920" height="1080" alt="screenshot_block1" src="https://github.com/user-attachments/assets/e361bd01-6a42-473f-be4e-374b3c5bfe66" />
<img width="1920" height="1080" alt="screenshot_block2" src="https://github.com/user-attachments/assets/109b4394-1af6-4463-a9c9-167eb113c499" />


<br />

# FotoPi features
- Control ISO (100-6400)
- Control Shutter Speed (1/1000s - 1s or custom value)
- Camera settings menu with 5 additional settings (see screenshot #2)
- Built-in simple mini-gallery
- Change output folder & format (.jpg, .png, .dng [raw])
- Enable grid overlay (for easy alignment)

The whole GUI is currently only made for a display resolution of 480x270px.
If anyone is even interested in this whole project and needs the option for lower resolution displays, i will make some changes.

# Planned features
- Adding a continuous shooting / burst mode option, maybe interesting for astrophotography or IR photography
- Adding AEC (Auto Exposure Compensation)
- Design other lens adapters for more support
- Adding hardware button & rotary encoder support for ISO, shutter and the capture button.

# Installation
First of all, make sure that you have picamera2 and PyQt5 installed with:

```
sudo apt update 
sudo apt install picamera2 python3-pyqt5 python3-pidng
``` 
<br />
FotoPi currently only comes as a python3 script. Download latest from here or with git clone:

```
wget git clone https://github.com/xcruell/FotoPi
```
<br />

<details>
<summary>soon™</summary>
If you want to always boot into FotoPi, launch FotoPi_startup.sh with:

```
sudo chmod +x /FotoPi_startup.shsudo ./FotoPi_startup.sh
```

This will copy a systemctl service, which starts FotoPi when the Raspberry Pi has successfully booted.<br />
It also adds a "Start FotoPi" shortcut to your desktop, perfect for touchscreen use.
</details>
<br />

If you don't use the startup script, you have to make the script executable with:
```
sudo chmod +x /FotoPi.py
```
Manually start FotoPi with:
```
cd /FotoPipython3 FotoPi.py
```

# License
FotoPi is licensed under BSD 2-Clause.<br />
Copyright © 2025 by xcruell
<br />
<br />
<br />
