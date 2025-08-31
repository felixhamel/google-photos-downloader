#!/usr/bin/env python3
"""
Version simplifiée du Google Photos Downloader pour identifier les problèmes GUI
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from pathlib import Path

# Import calendar widget
try:
    from tkcalendar import DateEntry
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False
    print("Note: Install 'tkcalendar' for enhanced date pickers: pip install tkcalendar")

class GooglePhotosGUISimplified:
    """Version simplifiée de l'interface GUI."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Google Photos Downloader v2.0 - Simplified")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        
        print("Initialisation de l'interface...")
        self.setup_ui()
        print("Interface configurée!")
        
    def setup_ui(self):
        """Create the user interface elements."""
        
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="25")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for responsive design
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Header with title
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=3, pady=(0, 25))
        header_frame.columnconfigure(0, weight=1)
        
        # Application title
        title_label = ttk.Label(header_frame, text="Google Photos Downloader", 
                               font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Source selection section
        source_frame = ttk.LabelFrame(main_frame, text="Download Source", padding="15")
        source_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        source_frame.columnconfigure(1, weight=1)
        
        # Source type selection
        self.source_type_var = tk.StringVar(value="date_range")
        date_radio = ttk.Radiobutton(source_frame, text="📅 Date Range", 
                                   variable=self.source_type_var, value="date_range",
                                   command=self.on_source_type_changed)
        date_radio.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        album_radio = ttk.Radiobutton(source_frame, text="📚 Album", 
                                    variable=self.source_type_var, value="album",
                                    command=self.on_source_type_changed)
        album_radio.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Date selection section
        self.date_frame = ttk.LabelFrame(main_frame, text="Date Range", padding="15")
        self.date_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        self.date_frame.columnconfigure(1, weight=1)
        
        # Start date
        ttk.Label(self.date_frame, text="From:").grid(row=0, column=0, sticky=tk.W, pady=5)
        if CALENDAR_AVAILABLE:
            self.start_date_picker = DateEntry(self.date_frame, width=12, background='darkblue',
                                             foreground='white', borderwidth=2, 
                                             date_pattern='yyyy-mm-dd')
            self.start_date_picker.set_date(datetime.now().replace(year=datetime.now().year-1))
        else:
            self.start_date_var = tk.StringVar(value="2024-01-01")
            self.start_date_picker = ttk.Entry(self.date_frame, textvariable=self.start_date_var, width=15)
        self.start_date_picker.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        
        # End date
        ttk.Label(self.date_frame, text="To:").grid(row=1, column=0, sticky=tk.W, pady=5)
        if CALENDAR_AVAILABLE:
            self.end_date_picker = DateEntry(self.date_frame, width=12, background='darkblue',
                                           foreground='white', borderwidth=2,
                                           date_pattern='yyyy-mm-dd')
            self.end_date_picker.set_date(datetime.now())
        else:
            self.end_date_var = tk.StringVar(value="2024-12-31")
            self.end_date_picker = ttk.Entry(self.date_frame, textvariable=self.end_date_var, width=15)
        self.end_date_picker.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        
        # Album selection section
        self.album_frame = ttk.LabelFrame(main_frame, text="Album Selection", padding="15")
        self.album_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        self.album_frame.columnconfigure(1, weight=1)
        
        ttk.Label(self.album_frame, text="Album:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.album_var = tk.StringVar()
        self.album_combobox = ttk.Combobox(self.album_frame, textvariable=self.album_var, 
                                          state="readonly", width=40)
        self.album_combobox.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        
        refresh_albums_button = ttk.Button(self.album_frame, text="🔄 Refresh", 
                                         command=self.refresh_albums)
        refresh_albums_button.grid(row=0, column=2, padx=(5, 0), pady=5)
        
        # Media type filter section
        filter_frame = ttk.LabelFrame(main_frame, text="Media Type Filter", padding="15")
        filter_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.photos_var = tk.BooleanVar(value=True)
        self.videos_var = tk.BooleanVar(value=True)
        
        photos_cb = ttk.Checkbutton(filter_frame, text="📷 Photos", variable=self.photos_var)
        photos_cb.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        videos_cb = ttk.Checkbutton(filter_frame, text="🎥 Videos", variable=self.videos_var)
        videos_cb.grid(row=0, column=1, sticky=tk.W)
        
        # Destination folder section
        dest_frame = ttk.LabelFrame(main_frame, text="Destination", padding="15")
        dest_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        dest_frame.columnconfigure(1, weight=1)
        
        ttk.Label(dest_frame, text="Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.folder_var = tk.StringVar(value=str(Path.home() / "GooglePhotos"))
        self.folder_entry = ttk.Entry(dest_frame, textvariable=self.folder_var, font=('Consolas', 9))
        self.folder_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        
        folder_button = ttk.Button(dest_frame, text="📁 Browse", command=self.browse_folder)
        folder_button.grid(row=0, column=2, padx=(5, 0), pady=5)
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status Log", padding="15")
        status_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        
        # Status text with scrollbar
        text_frame = ttk.Frame(status_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.status_text = tk.Text(text_frame, height=6, wrap=tk.WORD, 
                                  font=('Consolas', 9), bg='#f8f9fa', fg='#333')
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=(15, 0))
        
        self.download_button = ttk.Button(button_frame, text="🚀 Start Download", 
                                        command=self.start_download)
        self.download_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.cancel_button = ttk.Button(button_frame, text="⏹️ Cancel", 
                                      command=self.cancel_download, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT)
        
        # Configure main_frame row weights for proper resizing
        main_frame.rowconfigure(6, weight=1)
        
        # Add initial status message
        self.add_status_message("🎯 Interface simplifiée chargée avec succès!")
        self.add_status_message("📝 Cette version permet de tester l'interface GUI.")
        
        # Initialize UI state AFTER all widgets are created
        self.albums = []
        self.on_source_type_changed()  # Set initial state
        
    def on_source_type_changed(self):
        """Handle source type radio button changes."""
        try:
            if hasattr(self, 'album_frame'):  # Check if album_frame exists
                if self.source_type_var.get() == "date_range":
                    # Show date frame, disable album frame
                    for child in self.album_frame.winfo_children():
                        if hasattr(child, 'configure'):
                            child.configure(state="disabled")
                else:
                    # Show album frame, enable album controls
                    for child in self.album_frame.winfo_children():
                        if hasattr(child, 'configure'):
                            try:
                                child.configure(state="normal")
                            except:
                                pass  # Some widgets don't support state
        except Exception as e:
            print(f"Erreur dans on_source_type_changed: {e}")
    
    def refresh_albums(self):
        """Mock refresh albums function."""
        self.add_status_message("🔄 Mock: Refreshing albums...")
        # Mock albums
        mock_albums = ["Album 1 (25 items)", "Album 2 (50 items)", "Album 3 (12 items)"]
        self.album_combobox['values'] = mock_albums
        if mock_albums:
            self.album_combobox.current(0)
        self.add_status_message(f"✅ Mock: Loaded {len(mock_albums)} albums")
    
    def browse_folder(self):
        """Mock browse folder."""
        from tkinter import filedialog
        folder = filedialog.askdirectory(
            title="Select Destination Folder",
            initialdir=self.folder_var.get()
        )
        if folder:
            self.folder_var.set(folder)
            self.add_status_message(f"📁 Folder selected: {folder}")
    
    def start_download(self):
        """Mock start download."""
        self.add_status_message("🚀 Mock: Download started (this is just a test)")
        messagebox.showinfo("Test Mode", "Ceci est juste un test de l'interface!\nLe téléchargement réel n'est pas implémenté ici.")
    
    def cancel_download(self):
        """Mock cancel download."""
        self.add_status_message("⏹️ Mock: Download cancelled")
    
    def add_status_message(self, message: str):
        """Add a timestamped status message to the log."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\\n")
        self.status_text.see(tk.END)
        print(f"Status: {message}")  # Also print to console
    
    def run(self):
        """Start the GUI application."""
        print("Démarrage de l'interface simplifiée...")
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Start the GUI event loop
        self.root.mainloop()

def main():
    """Main application entry point."""
    print("Google Photos Downloader v2.0 - Version Simplifiée")
    print("=" * 50)
    
    try:
        app = GooglePhotosGUISimplified()
        app.run()
    except Exception as e:
        print(f"❌ Failed to start GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()