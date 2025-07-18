<img width="400" height="200" alt="FotoPi_Logo" src="https://github.com/user-attachments/assets/d4edcda4-29ab-48d3-8b97-5cf923eac821" />  

I was looking for a photo-oriented GUI for the Raspberry Pi HQ Camera Module, like CinePi for example.
Sadly, i couldn't find anything that met my expectations.. so i started learning and made FotoPi! 

FotoPi uses picamera2 and is written in Python with PyQt5 libs.
The GUI is made for touchscreens, but can be controlled with a mouse as well.

I'm currently using the following hardware:
- Raspberry Pi 4 4GB
- Raspberry Pi HQ Camera Module
- C-Mount to EF/EF-S-Mount adapter (with Canon EF-S 18-55mm lens)
- Waveshare 5.5" AMOLED 1080x1920px capacitive touch display

The C-mount to EF-mount adapter is self-designed in CAD and 3D-printed, allowing pretty much all kinds of lenses!

# Current state of FotoPi's GUI:
Main Window:
<img width="1920" height="1080" alt="v0 5 3-screenshot1" src="https://github.com/user-attachments/assets/42e01951-5cb9-439b-92a1-3f909c3bf3c2" />

All camera settings:
<img width="1920" height="1080" alt="v0 5 3-screenshot2" src="https://github.com/user-attachments/assets/a72b020f-0b70-404d-9eea-5c4d1c28fb68" />

Built-in mini image gallery for the last 9 photos:
<img width="1920" height="1080" alt="v0 5 3-screenshot3" src="https://github.com/user-attachments/assets/d1c7c0e5-7aa0-4681-8f85-da58080ce44a" />

# Other
FotoPi features:
- Control ISO (100-6400)
- Control Shutter Speed (1/1000s - 1s or custom input option)
- Camera settings menu with 5 additional settings (see screenshot #2)
- Built-in mini-gallery for the last 9 photos
- Change image folder
- Enable grid overlay (for easy alignment)

The whole GUI is currently only made for a display resolution of 1920x1080px.
If anyone is even interested in this whole project and needs the option for lower resolution displays, i will make some changes.

Planned:
- Adding licenses and links before releasing any code.
- Adding a continuous shooting / burst mode option, maybe interesting for astrophotography or IR photography
- Adding AEC (Auto Exposure Compensation), essentially an auto mode for the shutter speed
- Designing a 3D-Printed Case for the whole assembly
- Designing other lens adapters for more support
- Adding hardware buttons & rotary encoder support for ISO & shutter adjust and the capture button.
