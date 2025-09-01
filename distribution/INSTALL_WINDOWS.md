# Windows Installation Guide

## Fixing "Rust/Cargo compilation required" errors

If you see errors about **Rust**, **Cargo**, or **compilation required**, it's because some newer Python packages need to be compiled from source. Here's how to fix it:

## Quick fix (recommended)

Just double-click on `run_web_windows_fixed.bat` - it handles everything automatically.

Or run these commands:

```cmd
# Use pre-compiled packages only
pip install --only-binary=all -r requirements-web-windows.txt

# Start the app
python start_server.py
```

## Manual installation

If the automatic script doesn't work:

```cmd
pip install --only-binary=all fastapi==0.100.1
pip install --only-binary=all uvicorn==0.23.2  
pip install --only-binary=all pydantic==1.10.13
pip install --only-binary=all python-multipart==0.0.6
pip install --only-binary=all websockets==11.0.3
pip install --only-binary=all google-auth-oauthlib==0.7.1
pip install --only-binary=all requests==2.31.0
```

The `--only-binary=all` flag tells pip to only use pre-compiled packages, avoiding any compilation that would need Rust or other build tools.

## 🚀 Modes d'Utilisation

### 1. Mode Web (Interface Graphique)
```cmd
# Lancement web avec interface browser
run_web_windows_fixed.bat
# OU
python start_server.py
```
- Interface web moderne à http://127.0.0.1:8000
- Traduction française complète
- Suivi temps réel des téléchargements
- Gestion des sessions

### 2. Mode CLI (Ligne de Commande)
```cmd
# Mode commande complète
python cli_mode.py --help

# Exemples:
python cli_mode.py --list-albums
python cli_mode.py --start-date 2023-01-01 --end-date 2023-12-31 --output downloads/2023
python cli_mode.py --last-30-days --output downloads/recent
python cli_mode.py --album-id ABC123XYZ --output downloads/album
```

### 3. Mode GUI (Original)
```cmd
# Interface graphique originale (si réparée)
python src/google_photos_downloader.py
```

## 🛠️ En Cas de Problème

### Python pas trouvé:
```cmd
# Installe Python depuis python.org
# Coche "Add to PATH" pendant l'installation
```

### Erreur PowerShell "Execution Policy":
```powershell
# Lance en tant qu'administrateur:
powershell -ExecutionPolicy Bypass -File run_web_macos.sh
```

### Rust/Cargo encore demandé:
```cmd
# Force l'installation de versions plus anciennes:
pip install --force-reinstall --only-binary=all fastapi==0.100.1 uvicorn==0.23.2
```

## 📋 Versions Testées Windows

- **Windows 10/11** ✅
- **Python 3.8+** ✅  
- **Pas besoin de Visual Studio** ✅
- **Pas besoin de Rust** ✅
- **Pas besoin de compilateur** ✅

## 🎯 Que Faire Maintenant

1. Supprime les anciens packages qui causent problème:
   ```cmd
   pip uninstall fastapi uvicorn pydantic
   ```

2. Lance le script Windows:
   ```cmd
   run_web_windows_fixed.bat
   ```

3. L'app s'ouvre automatiquement dans Chrome!

**C'est tout!** Plus besoin de Rust/Cargo/compilation. 🎉

## 📁 Structure du Projet

```
google-photos-downloader/
├── credentials.json              # ⚠️  REQUIS - À ajouter
├── run_web_windows_fixed.bat     # Windows launcher
├── run_web_macos.sh             # macOS/Linux launcher  
├── start_server.py              # Cross-platform launcher
├── cli_mode.py                  # Mode CLI complet
├── run_cli.py                   # Wrapper CLI simple
├── src/google_photos_downloader.py # GUI original
├── app/                         # Web application
├── static/                      # Interface web
├── requirements-web-windows.txt # Windows dependencies
├── OAUTH_GUIDE.md              # Setup OAuth2
└── DEPLOYMENT_GUIDE.md         # Guide complet
```