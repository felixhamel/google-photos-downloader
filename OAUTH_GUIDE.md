# Google OAuth2 Setup Guide

## How OAuth2 works for this app

### Understanding the files

**credentials.json** (from the developer)
- Contains app identification info (`client_id`, `client_secret`)
- Tells Google which application is requesting access
- Safe to distribute with the app
- Stays the same for all users

**token.json** (created for each user)  
- Contains your personal access tokens
- Created when you log in and authorize the app
- Private to your Google account - never share this
- Automatically refreshes when needed

## How the OAuth flow works

### Step 1: Developer setup (done once)
1. Create project in Google Cloud Console
2. Enable Google Photos Library API  
3. Create OAuth2 credentials (Desktop Application type)
4. Download credentials.json
5. Include it with the app

### Step 2: User authentication (each user does this)
1. User runs the app for first time
2. App opens browser to Google login page
3. User logs in with their Google account
4. Google asks: "Allow this app to access your photos?"
5. If user clicks "Allow", Google creates a token.json file
6. App can now access that user's photos

### Step 3: Ongoing use
1. App loads existing token.json
2. If token expired, automatically refreshes it
3. If refresh fails, user needs to re-authorize
4. App accesses the authenticated user's photos

## 🚀 Scénarios d'Usage

### **Scénario A : Utilisateur Unique**
```
Computer/
├── google-photos-downloader/
│   ├── credentials.json        # Tes credentials (app)
│   ├── token.json             # Token de Jean
│   └── app/
```
Jean utilise l'app → Accès à SES photos seulement.

### **Scénario B : Utilisateurs Multiples (Même Ordinateur)**
```
Computer/
├── google-photos-downloader/
│   ├── credentials.json        # Tes credentials (app)
│   ├── token_jean.json        # Token de Jean
│   ├── token_marie.json       # Token de Marie
│   └── app/
```

Pour changer d'utilisateur :
1. Renommer/supprimer token.json actuel
2. Relancer l'app
3. Nouveau flow OAuth pour le nouvel utilisateur

### **Scénario C : Distribution Publique**
Chaque utilisateur télécharge l'app avec :
- ✅ `credentials.json` (tes credentials d'app)
- ❌ SANS `token.json` (sera créé lors de leur première connexion)

## 🛡️ Sécurité et Permissions

### **Permissions Demandées**
```python
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
```
- **Lecture seule** des photos Google Photos
- **Aucune permission d'écriture** ou modification
- **Aucun accès** aux autres services Google (Gmail, Drive, etc.)

### **Révocation des Permissions**
L'utilisateur peut révoquer l'accès à tout moment :
1. **Google Account Settings** → Security → Third-party apps
2. Trouver "[Nom de ton app]" → Remove access
3. L'app ne pourra plus accéder aux photos jusqu'au prochain OAuth

### **Limites et Quotas**
- **Quota API** : Partagé entre tous les utilisateurs de ton `credentials.json`
- **Limite Google** : 10,000 requêtes/jour par projet (par défaut)
- **Gestion** : Si dépassé, demander augmentation de quota à Google

## 🔧 Implémentation Technique

### **Code d'Authentification**
```python
def authenticate(self) -> bool:
    # 1. Chercher token existant de l'utilisateur
    if os.path.exists(self.token_file):
        self.creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
    
    # 2. Vérifier validité du token
    if not self.creds or not self.creds.valid:
        if self.creds and self.creds.expired and self.creds.refresh_token:
            # 3. Refresh automatique si possible
            self.creds.refresh(Request())
        else:
            # 4. Nouveau flow OAuth avec TES credentials mais compte UTILISATEUR
            flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
            self.creds = flow.run_local_server(port=0)
        
        # 5. Sauver le nouveau token pour cet utilisateur
        with open(self.token_file, 'w') as token:
            token.write(self.creds.to_json())
    
    return True
```

### **Gestion Multi-Utilisateurs** (Optionnel)
Pour supporter plusieurs utilisateurs sur le même ordinateur :

```python
# Modifier le nom du fichier token par utilisateur
def __init__(self, user_profile='default'):
    self.token_file = f'token_{user_profile}.json'
    # ... reste du code
```

## 🚨 Points Importants

### **À Faire**
- ✅ Inclure `credentials.json` dans l'app distribuée
- ✅ Ajouter `.gitignore` pour `token*.json`
- ✅ Documentation claire pour l'utilisateur final
- ✅ Gestion d'erreur si `credentials.json` manquant

### **À NE PAS Faire**
- ❌ Committer `token.json` dans Git
- ❌ Partager le `token.json` d'un utilisateur
- ❌ Hardcoder des tokens dans le code
- ❌ Stocker les tokens en plain text en production (OK pour usage local)

## 📋 Checklist de Sécurité

### **Avant Distribution**
- [ ] `credentials.json` présent
- [ ] `token*.json` dans `.gitignore`
- [ ] Permissions minimales (readonly)
- [ ] Documentation utilisateur claire
- [ ] Gestion d'erreur authentification

### **Pour l'Utilisateur Final**
- [ ] Instructions claires pour l'OAuth
- [ ] Explication des permissions demandées
- [ ] Procédure de révocation d'accès
- [ ] Contact support en cas de problème

## 🔗 Ressources

- [Google Photos API Documentation](https://developers.google.com/photos/library/guides/overview)
- [OAuth2 Best Practices](https://developers.google.com/identity/protocols/oauth2/security-best-practices)
- [Google Cloud Console](https://console.cloud.google.com/)

---

**Note** : Cette architecture OAuth2 est identique à celle utilisée par des applications populaires comme Google Drive Desktop, Dropbox, Spotify Desktop, etc. L'utilisateur final authentifie TOUJOURS avec son propre compte, même si l'app utilise les credentials du développeur.