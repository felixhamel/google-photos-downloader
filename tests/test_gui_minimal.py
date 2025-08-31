#!/usr/bin/env python3
"""
Test minimal de l'interface GUI pour identifier le problème
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path

class TestGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Test GUI - Google Photos Downloader")
        self.root.geometry("600x400")
        
        # Test basique
        self.setup_ui()
    
    def setup_ui(self):
        # Main container avec padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Test simple - titre
        title_label = ttk.Label(main_frame, text="Google Photos Downloader - TEST", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=10)
        
        # Test section dates
        date_frame = ttk.LabelFrame(main_frame, text="Test Date Range", padding="15")
        date_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        date_frame.columnconfigure(1, weight=1)
        
        ttk.Label(date_frame, text="From:").grid(row=0, column=0, sticky=tk.W, pady=5)
        start_entry = ttk.Entry(date_frame, width=15)
        start_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        start_entry.insert(0, "2024-01-01")
        
        ttk.Label(date_frame, text="To:").grid(row=1, column=0, sticky=tk.W, pady=5)
        end_entry = ttk.Entry(date_frame, width=15)
        end_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        end_entry.insert(0, "2024-12-31")
        
        # Test folder
        dest_frame = ttk.LabelFrame(main_frame, text="Test Destination", padding="15")
        dest_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        dest_frame.columnconfigure(1, weight=1)
        
        ttk.Label(dest_frame, text="Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        folder_entry = ttk.Entry(dest_frame)
        folder_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        folder_entry.insert(0, str(Path.home() / "GooglePhotos"))
        
        browse_button = ttk.Button(dest_frame, text="📁 Browse")
        browse_button.grid(row=0, column=2, padx=(5, 0), pady=5)
        
        # Test buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=20)
        
        test_button = ttk.Button(button_frame, text="🚀 Test Download")
        test_button.pack(side=tk.LEFT, padx=10)
        
        close_button = ttk.Button(button_frame, text="❌ Close", command=self.root.destroy)
        close_button.pack(side=tk.LEFT, padx=10)
        
        # Status text
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=10)
        status_frame.columnconfigure(0, weight=1)
        
        status_text = tk.Text(status_frame, height=6, wrap=tk.WORD)
        status_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        status_text.insert(tk.END, "Interface de test chargée avec succès!\n")
        status_text.insert(tk.END, "Si tu vois ce message, l'interface fonctionne.\n")
        
        print("Interface de test configurée!")
    
    def run(self):
        print("Lancement de l'interface de test...")
        self.root.mainloop()

if __name__ == "__main__":
    print("=== TEST GUI MINIMAL ===")
    try:
        app = TestGUI()
        app.run()
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()