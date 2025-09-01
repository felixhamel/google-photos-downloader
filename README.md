# GPhotos Downloader (Desktop App)

This is a simple, rewritten desktop application to download your photos and videos from Google Photos to your computer. It provides a graphical user interface to select a date range and a destination folder.

This version is a complete rewrite of the original web-based application, now using Python and the Flet GUI framework to create a standalone desktop experience.

## Features

- **Simple Graphical User Interface (GUI)**
- **Secure Google Authentication**: Logs in using Google's official OAuth flow.
- **Date Range Selection**: Download photos and videos between specific start and end dates.
- **Folder Selection**: Choose exactly where to save your files.
- **Real-time Progress**: A progress bar and status messages keep you updated.
- **Cross-Platform Source**: The code works on Windows, macOS, and Linux.

---

## How to Get Your Copy

Because this application requires being built on a Windows machine to be a native Windows `.exe`, you will build it yourself from the source code. This ensures it's perfectly tailored to your system and avoids the "weird issues" that can happen with pre-packaged software.

Follow the **"How to Build for Windows"** instructions below.

---

## Part 1: Getting Your Google API Credentials

Before you can use the app, you need to tell Google you've authorized it to access your photos. This is a one-time setup.

### 1. Go to Google Cloud Console
Open [https://console.cloud.google.com/](https://console.cloud.google.com/) and log in with the Google account whose photos you want to download.

### 2. Create a project
- Click the project dropdown at the top of the page and click **New Project**.
- Give it any name you want (e.g., "My Photos Downloader").
- Click **Create**.

### 3. Enable the Google Photos API
- Make sure your new project is selected in the dropdown at the top.
- In the search bar, type "Photos Library API".
- Click on it in the search results and then click the **Enable** button.

### 4. Create Credentials
- From the navigation menu (☰), go to **APIs & Services > Credentials**.
- Click **+ Create Credentials** and select **OAuth 2.0 Client ID**.
- If it's your first time, you might be asked to configure an "OAuth consent screen".
  - Choose **External** for the User Type and click **Create**.
  - On the next page, just fill in the required fields:
    - **App name**: "Photos Downloader" (or any name you like).
    - **User support email**: Your email address.
    - **Developer contact information**: Your email address.
  - Click **Save and Continue** through the rest of the steps. You don't need to add scopes or test users.
- Now, back on the Credentials page, create the OAuth client:
  - For **Application type**, select **Desktop application**.
  - Give it any name you want.
  - Click **Create**.

### 5. Download the Credentials File
- A popup will show your Client ID and Secret. Just click **OK**.
- In your list of "OAuth 2.0 Client IDs", find the one you just created and click the **download icon** (↓) on the right.
- This will save a JSON file to your computer. **Rename this file to `credentials.json`**.

**You will need this `credentials.json` file later.**

---

## Part 2: How to Build the Application for Windows

Follow these steps on your Windows machine.

### 1. Install Python
- If you don't have Python, download and install it from the official website: [python.org](https://www.python.org/downloads/).
- During installation, make sure to check the box that says **"Add Python to PATH"**.

### 2. Download the Application Source Code
- Download the source code of this project as a ZIP file and extract it to a folder on your computer (e.g., `C:\GPhotos-Downloader`).

### 3. Place Your Credentials File
- Take the `credentials.json` file you downloaded in Part 1 and place it in the root of the project folder you just extracted (e.g., inside `C:\GPhotos-Downloader`).

### 4. Build the Executable (`.exe`)
- Open the **Command Prompt** or **PowerShell** on Windows.
- Navigate to the project folder using the `cd` command. Example: `cd C:\GPhotos-Downloader`
- Run the following commands one by one:

```shell
# 1. Create a virtual environment to keep dependencies clean
python -m venv venv

# 2. Activate the virtual environment
venv\Scripts\activate

# 3. Install all the necessary libraries
pip install -r requirements.txt

# 4. Run the PyInstaller build command
pyinstaller --onefile --windowed --name GPhotos-Downloader gui.py
```

### 5. Run Your Application!
- After the build command finishes, you will find a new `dist` folder.
- Inside the `dist` folder is your application: **`GPhotos-Downloader.exe`**.
- You can now run this file. You can also copy it to your Desktop or anywhere else you'd like.

---

## Part 3: Using the Application

1.  **Run `GPhotos-Downloader.exe`**.
2.  **Login**: Click the "Login to Google" button. Your web browser will open, asking you to sign in and grant permission.
3.  **Select Dates**: Use the date pickers to choose your desired start and end dates.
4.  **Choose Folder**: Click "Choose Folder" and select a destination on your computer for the downloaded photos.
5.  **Download**: Once you've logged in and selected dates and a folder, the "Download Photos" button will become active. Click it to start the process.
6.  **Monitor Progress**: The status text and progress bar will show you the current progress of the download.

If something goes wrong with your login token, just delete the `token.json` file that appears in the same directory as the executable and log in again.
