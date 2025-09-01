# Setting up Google API access

You need to get credentials from Google before you can download your photos. This is a one-time setup.

## Step-by-step instructions

### 1. Go to Google Cloud Console
Open https://console.cloud.google.com/ and log in with your Google account.

### 2. Create a project
- Click the project dropdown at the top
- Click "New Project" 
- Give it any name you want (like "Photos Downloader")
- Click "Create"

### 3. Enable the Google Photos API
- Make sure your new project is selected
- Search for "Photos Library API" in the search bar
- Click on it and press "Enable"

### 4. Create credentials
- Go to "APIs & Services" > "Credentials" (left sidebar)
- Click "Create Credentials" > "OAuth 2.0 Client IDs"
- If it asks, set up the OAuth consent screen first:
  - Choose "External" user type
  - Fill in just the required fields (app name, your email)
  - Skip everything else, just save
- Now create the OAuth client:
  - Choose "Desktop application" as the type
  - Give it any name you want
  - Click "Create"

### 5. Download the file
- Click the download button next to your new credential
- Save the JSON file and rename it to `credentials.json`
- Put it in the same folder as the executable (or project root if running from source)

## How it works

**First time:**
When you run the app, it opens your browser to Google's login page. You sign in and click "Allow" to let the app access your photos. Google creates a `token.json` file that lets the app access your photos.

**Later:**
The app uses the saved `token.json`. If it expires, Google automatically refreshes it. If something breaks, just delete `token.json` and log in again.

## Multiple users

If different people want to use the app on the same computer:
- Each person needs to delete `token.json` before their first use
- Or rename it to something like `token_mom.json` to keep it
- Each person goes through the Google login for their own account

## Security

- The app only asks for **read-only** access - it can't delete or modify your photos
- `credentials.json` is safe to share (just identifies the app)
- `token.json` is private to your Google account - don't share it
- You can revoke access anytime in your Google Account settings > Security > Third-party apps