# Setting up Google API access

You need to get credentials from Google before you can download your photos.

## What files you'll see

**credentials.json** - This identifies the app to Google. I've already set this up, you just need to download it from Google Cloud Console.

**token.json** - This gets created automatically the first time you run the app and log in. It's tied to your Google account, so keep it private.

## Getting your credentials

1. Go to https://console.cloud.google.com/
2. Create a new project (or use an existing one)
3. Enable the "Google Photos Library API" 
4. Go to "Credentials" and create new OAuth 2.0 Client IDs
5. Choose "Desktop application" as the type
6. Download the JSON file and rename it to `credentials.json`
7. Put it in the same folder as the app

## How it works

First time you run the app:
- It opens your web browser to Google's login page
- You sign in with your Google account
- Google asks if you want to allow the app to access your photos
- If you click "Allow", Google creates the token.json file
- The app can now download your photos

Later runs:
- The app uses the saved token.json
- If it expires, Google automatically refreshes it
- If something goes wrong, you just need to delete token.json and log in again

## Multiple users on same computer

If different people want to use the app on the same computer, you can:
- Rename token.json to something like token_mom.json before the second person runs it
- Or just delete token.json between users
- Each person will go through the Google login flow for their own account

## Security notes

The app only asks for read-only access to your Google Photos. It can't delete or modify anything.

If you want to revoke access later, go to your Google Account settings > Security > Third-party apps and remove this app.

The credentials.json file is safe to share (it just identifies the app), but never share your token.json file - that's tied to your personal Google account.