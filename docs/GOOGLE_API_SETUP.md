# Google Photos API Setup Guide

This guide will walk you through setting up Google Photos API access for the Google Photos Downloader application.

## Prerequisites

- A Google account
- Access to Google Cloud Console

## Step-by-Step Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click "New Project"
4. Enter a project name (e.g., "Google Photos Downloader")
5. Click "Create"

### 2. Enable Google Photos Library API

1. In the Google Cloud Console, select your project
2. Navigate to **APIs & Services** > **Library**
3. Search for "Photos Library API"
4. Click on **Photos Library API**
5. Click the **Enable** button

### 3. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **+ CREATE CREDENTIALS** > **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - Choose "External" for user type
   - Fill in the required fields:
     - App name: "Google Photos Downloader"
     - User support email: Your email
     - Developer contact: Your email
   - Add scopes: `../auth/photoslibrary.readonly`
   - Add test users (your email)
   - Click "Save and Continue"

4. Back in Create OAuth client ID:
   - Application type: **Desktop app**
   - Name: "Google Photos Downloader Client"
   - Click **Create**

### 4. Download Credentials

1. After creating the OAuth client, you'll see a dialog with your credentials
2. Click **Download JSON**
3. Save the file as `credentials.json` in the same directory as the application

## Important Notes

### Security
- **Never share your `credentials.json` file** - it contains sensitive information
- The file is automatically excluded from version control via `.gitignore`
- Keep your credentials secure and don't commit them to any repository

### Token Storage
- After first authentication, a `token.json` file will be created
- This stores your access token for future use
- You can delete this file to force re-authentication

### API Quotas
- The Photos Library API has usage quotas
- Default quota: 10,000 requests per day
- If you exceed quotas, wait until the next day or request a quota increase

### Permissions
The application only requests read-only access to your photos:
- `https://www.googleapis.com/auth/photoslibrary.readonly`
- The app cannot modify, delete, or share your photos

## Troubleshooting

### "credentials.json not found"
- Ensure you've downloaded the OAuth credentials JSON file
- Rename it to exactly `credentials.json`
- Place it in the same directory as the application

### "Authentication failed"
- Delete `token.json` if it exists
- Ensure your Google Cloud project has the Photos Library API enabled
- Check that your OAuth consent screen is configured

### "Quota exceeded"
- Wait 24 hours for quota reset
- Or request a quota increase in Google Cloud Console

### Browser doesn't open for authentication
- The application will provide a URL
- Copy and paste it into your browser manually
- After authorizing, copy the code back to the application

## Using the Template

A template file is provided in `config/credentials_template.json`. To use it:

1. Copy `config/credentials_template.json` to `credentials.json`
2. Replace the placeholder values with your actual credentials:
   - `YOUR_CLIENT_ID` - Your OAuth 2.0 client ID
   - `your-project-id` - Your Google Cloud project ID
   - `YOUR_CLIENT_SECRET` - Your OAuth 2.0 client secret

## Support

For issues related to:
- **Google Cloud setup**: Check [Google Cloud documentation](https://cloud.google.com/docs)
- **Photos Library API**: See [Photos Library API documentation](https://developers.google.com/photos)
- **Application issues**: Create an issue on the project repository