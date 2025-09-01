# What's changed

## v2.0.0 - August 2025

Completely rewrote this thing as a web app because the GUI was broken.

New stuff:
- Web interface that actually works (runs on http://127.0.0.1:8000)
- Command line version for scripting
- Works on Windows without needing to compile anything
- French interface 
- Real-time progress bars
- Can resume interrupted downloads
- Executable versions so you don't need Python

Fixed:
- The empty window bug that made the original GUI unusable
- Windows compatibility issues with Rust dependencies
- Better error messages when things go wrong

Technical changes:
- FastAPI instead of tkinter
- WebSocket for live updates
- Better OAuth flow
- Modular code structure

## v1.0.0 - August 2025

Initial version with tkinter GUI. Had some issues but the core Google Photos API integration worked.

Features:
- Basic GUI for downloading photos
- Date range selection
- OAuth authentication
- Progress tracking

Known issues:
- GUI would sometimes show empty window
- Windows users had trouble with dependencies