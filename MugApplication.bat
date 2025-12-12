@echo off
start photoshop C:\Users\DTFPrintBar\AppData\Local\MugApplication\MugPrintout_Template.psd
start explorer "C:\Users\DTFPrintBar\AppData\Local\MugApplication\FileDump\"
start explorer "C:\Users\DTFPrintBar\AppData\Local\MugApplication\HotFolder\"
python C:\Users\DTFPrintBar\AppData\Local\MugApplication\MugApplication.py
pause