# Guide OAuth2 - Google Photos Downloader

## 🔐 Architecture de Sécurité OAuth2

### Comprendre les Credentials vs Tokens

#### **credentials.json (Développeur)**
- **Propriétaire** : Le développeur de l'application (toi)
- **Contenu** : `client_id`, `client_secret`, configuration de l'app
- **Usage** : Identifier l'application auprès de Google
- **Sécurité** : Peut être distribué avec l'app (non-sensible)
- **Durée** : Permanent jusqu'à révocation manuelle

#### **token.json (Utilisateur Final)**
- **Propriétaire** : L'utilisateur spécifique qui se connecte
- **Contenu** : `access_token`, `refresh_token` pour cet utilisateur
- **Usage** : Accéder aux données Google Photos de CET utilisateur
- **Sécurité** : PRIVÉ - ne jamais partager
- **Durée** : Expire et se renouvelle automatiquement

## 🎯 Flow OAuth2 Complet

### Phase 1 : Configuration Développeur (Une seule fois)
```bash
1. Créer projet Google Cloud Console
2. Activer Google Photos Library API
3. Créer credentials OAuth2 (Desktop Application)
4. Télécharger credentials.json
5. Distribuer l'app avec credentials.json
```

### Phase 2 : Authentification Utilisateur (À chaque utilisateur)
```bash
1. Utilisateur lance l'app
2. App utilise credentials.json pour initier OAuth
3. Navigateur s'ouvre → Page de connexion Google
4. Utilisateur se connecte avec SON compte Google
5. Google demande : "Autoriser [Nom App] à accéder à vos photos ?"
6. Si accepté → Google génère token.json spécifique à cet utilisateur
7. App peut maintenant accéder aux photos de CET utilisateur
```

### Phase 3 : Utilisation Continue
```bash
1. App charge token.json existant
2. Si token expiré → Refresh automatique via refresh_token
3. Si refresh_token expiré → Refaire le flow OAuth complet
4. Accès aux photos de l'utilisateur authentifié
```

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