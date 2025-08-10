<p align="center">
<img width="300" height="300" alt="FotoPi_render2b-trans2_1024" src="https://github.com/user-attachments/assets/e8aa3ddd-4811-4104-9862-f31117a7cf5d" />

<img width="400" height="200" alt="FotoPi_Logo" src="https://github.com/user-attachments/assets/d4edcda4-29ab-48d3-8b97-5cf923eac821" />  
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
<img width="480" height="270" alt="main" src="https://github.com/user-attachments/assets/dc14a789-206d-4da8-a910-d3ed13d6b136" />
<img width="480" height="270" alt="iso" src="https://github.com/user-attachments/assets/4258a578-bbe0-427e-9489-082e65f0913c" /> <br />

<img width="480" height="270" alt="shutter" src="https://github.com/user-attachments/assets/92682a52-e1d3-46f6-8a66-0df80c82877c" />
<img width="480" height="270" alt="custom_shutter" src="https://github.com/user-attachments/assets/cc46d65e-5433-465d-aa26-28e26fae1c44" /> <br />

<img width="480" height="270" alt="gallery" src="https://github.com/user-attachments/assets/c196ca2a-eeca-45d6-b4d3-0af816dbcfc8" />
<img width="480" height="270" alt="gallery_full" src="https://github.com/user-attachments/assets/8b8d9330-a552-4214-bdea-78f03cd92f5a" /> <br />

<img width="480" height="270" alt="app_settings" src="https://github.com/user-attachments/assets/ea625006-9527-463c-baa5-063b40f5308a" />
<img width="480" height="270" alt="camera_settings" src="https://github.com/user-attachments/assets/80c9c86c-9fea-4022-aaa8-18617cdc2b05" /> <br />









Built-in mini image gallery for the last 9 photos: <br />

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
sudo apt updatesudo apt install picamera2 python3-pyqt5 python3-pidng
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
