# FRAS-FACE-RECOGNITION-ATTENDANCE-SYSTEM-
FRAS (Face Recognition Attendance System) is a smart, secure solution for automated attendance tracking using facial recognition. It streamlines check-ins, reduces manual errors, and ensures real-time monitoring—ideal for schools, offices, and events. Powered by AI and OpenCV.
FRAS Build & Install

Quick steps to build a Windows EXE using PyInstaller (PowerShell):

1. Install build tools
   - pip install pyinstaller

2. Open PowerShell in this folder:
   Set-Location "D:\code\Upwork Project\FRAS"

3. Run the build script:
   .\build.ps1

Notes:
- The script includes the face_recognition_models .dat files detected on the development machine.
- If your Python installation is in a different location, edit `build.ps1` and update the paths in the `$models` array.
- For debugging, remove `--noconsole` in `build.ps1` and re-run.

Default admin credentials (created automatically on first run):
- UserID: admin
- Password: admin123

After building, distribute the `.exe` from the `dist` folder.
