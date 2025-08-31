/**
 * Alpine.js application for Google Photos Downloader
 */
function googlePhotosApp() {
    return {
        // Core state
        darkMode: false,
        websocket: null,
        currentSessionId: null,
        
        // Authentication
        authStatus: {
            authenticated: false,
            message: ''
        },
        
        // Loading states
        loading: {
            albums: false,
            sessions: false,
            download: false
        },
        
        // Download configuration
        downloadConfig: {
            sourceType: 'date_range',
            startDate: '',
            endDate: '',
            albumId: '',
            includePhotos: true,
            includeVideos: true,
            outputDir: ''
        },
        
        // Data
        albums: [],
        sessions: [],
        
        // Progress tracking
        progress: {
            current: 0,
            total: 0,
            percentage: 0,
            speed: 0,
            eta: null,
            status: 'idle'
        },
        
        // UI state
        isDownloading: false,
        showSessions: false,
        statusMessages: [],
        
        // Notifications
        notification: {
            show: false,
            message: '',
            type: 'info'
        },
        
        // Computed properties
        get canStartDownload() {
            if (!this.authStatus.authenticated) return false;
            if (!this.downloadConfig.outputDir.trim()) return false;
            if (!this.downloadConfig.includePhotos && !this.downloadConfig.includeVideos) return false;
            
            if (this.downloadConfig.sourceType === 'date_range') {
                return this.downloadConfig.startDate && this.downloadConfig.endDate;
            } else {
                return this.downloadConfig.albumId;
            }
        },
        
        // Initialization
        async init() {
            console.log('🚀 Initializing Google Photos Downloader Web App');
            
            // Initialize default dates
            this.downloadConfig.startDate = this.getDefaultStartDate();
            this.downloadConfig.endDate = this.getDefaultEndDate();
            this.downloadConfig.outputDir = this.getDefaultOutputDir();
            
            // Check authentication status
            await this.checkAuthStatus();
            
            // Load saved sessions
            await this.loadSessions();
            
            // Add welcome message
            this.addStatusMessage('Bienvenue dans le Téléchargeur Google Photos v2.0 ! 🎉', 'success');
            this.addStatusMessage('Configurez vos paramètres de téléchargement ci-dessus et cliquez sur "Commencer le Téléchargement" pour débuter.', 'info');
        },
        
        // Helper methods
        getDefaultStartDate() {
            const date = new Date();
            date.setFullYear(date.getFullYear() - 1);
            return date.toISOString().split('T')[0];
        },
        
        getDefaultEndDate() {
            return new Date().toISOString().split('T')[0];
        },
        
        getDefaultOutputDir() {
            // Simple default path that works cross-platform
            return '/Users/user/GooglePhotos';
        },
        
        formatTime(timestamp) {
            return new Date(timestamp).toLocaleTimeString();
        },
        
        formatETA(seconds) {
            if (!seconds) return '--';
            
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;
            
            if (hours > 0) {
                return `${hours}h ${minutes}m`;
            } else if (minutes > 0) {
                return `${minutes}m ${secs}s`;
            } else {
                return `${secs}s`;
            }
        },
        
        // API methods
        async apiRequest(endpoint, options = {}) {
            try {
                const response = await fetch(`/api${endpoint}`, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    ...options
                });
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                    throw new Error(errorData.detail || `HTTP ${response.status}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error(`API Error (${endpoint}):`, error);
                throw error;
            }
        },
        
        // Authentication methods
        async checkAuthStatus() {
            try {
                const response = await this.apiRequest('/auth/status');
                this.authStatus = response;
                
                if (response.authenticated) {
                    this.addStatusMessage('✅ Authentification réussie avec l\'API Google Photos', 'success');
                } else {
                    this.addStatusMessage('⚠️ Authentification requise - Veuillez vérifier votre fichier credentials.json', 'warning');
                }
            } catch (error) {
                this.addStatusMessage(`❌ Échec de vérification du statut d'authentification : ${error.message}`, 'error');
                this.authStatus = { authenticated: false, message: error.message };
            }
        },
        
        async authenticate() {
            try {
                this.addStatusMessage('🔄 Tentative d\'authentification en cours...', 'info');
                const response = await this.apiRequest('/auth/authenticate', { method: 'POST' });
                
                if (response.success) {
                    await this.checkAuthStatus();
                    this.showNotification('Authentification réussie !', 'success');
                }
            } catch (error) {
                this.addStatusMessage(`❌ Échec de l'authentification : ${error.message}`, 'error');
                this.showNotification('Échec de l\'authentification', 'error');
            }
        },
        
        // Albums methods
        async loadAlbums() {
            if (!this.authStatus.authenticated) {
                this.showNotification('Veuillez d\'abord vous authentifier', 'error');
                return;
            }
            
            this.loading.albums = true;
            try {
                this.addStatusMessage('🔄 Chargement des albums...', 'info');
                this.albums = await this.apiRequest('/albums');
                this.addStatusMessage(`✅ ${this.albums.length} albums chargés`, 'success');
            } catch (error) {
                this.addStatusMessage(`❌ Échec du chargement des albums : ${error.message}`, 'error');
                this.showNotification('Échec du chargement des albums', 'error');
            } finally {
                this.loading.albums = false;
            }
        },
        
        // Sessions methods
        async loadSessions() {
            this.loading.sessions = true;
            try {
                this.sessions = await this.apiRequest('/sessions');
            } catch (error) {
                console.error('Échec du chargement des sessions :', error);
            } finally {
                this.loading.sessions = false;
            }
        },
        
        async deleteSession(sessionId) {
            try {
                await this.apiRequest(`/sessions/${sessionId}`, { method: 'DELETE' });
                this.sessions = this.sessions.filter(s => s.session_id !== sessionId);
                this.addStatusMessage(`🗑️ Session ${sessionId.substring(0, 8)}... supprimée`, 'info');
            } catch (error) {
                this.addStatusMessage(`❌ Échec de la suppression de session : ${error.message}`, 'error');
            }
        },
        
        async resumeSession(sessionId) {
            try {
                this.addStatusMessage(`🔄 Reprise de la session ${sessionId.substring(0, 8)}...`, 'info');
                
                const response = await this.apiRequest('/download/resume', {
                    method: 'POST',
                    body: JSON.stringify({ session_id: sessionId })
                });
                
                if (response.success) {
                    this.currentSessionId = sessionId;
                    this.isDownloading = true;
                    this.showSessions = false;
                    this.connectWebSocket(sessionId);
                    this.addStatusMessage('✅ Session de téléchargement reprise', 'success');
                }
            } catch (error) {
                this.addStatusMessage(`❌ Échec de reprise de session : ${error.message}`, 'error');
                this.showNotification('Échec de reprise de session', 'error');
            }
        },
        
        // Download methods
        async startDownload() {
            if (!this.canStartDownload) return;
            
            try {
                this.isDownloading = true;
                this.addStatusMessage('🚀 Démarrage du téléchargement...', 'info');
                
                // Prepare media types
                const mediaTypes = [];
                if (this.downloadConfig.includePhotos) mediaTypes.push('PHOTO');
                if (this.downloadConfig.includeVideos) mediaTypes.push('VIDEO');
                
                // Prepare request
                const request = {
                    source_type: this.downloadConfig.sourceType,
                    media_types: mediaTypes,
                    output_dir: this.downloadConfig.outputDir
                };
                
                if (this.downloadConfig.sourceType === 'date_range') {
                    request.start_date = this.downloadConfig.startDate + 'T00:00:00Z';
                    request.end_date = this.downloadConfig.endDate + 'T23:59:59Z';
                } else {
                    request.album_id = this.downloadConfig.albumId;
                }
                
                const response = await this.apiRequest('/download/start', {
                    method: 'POST',
                    body: JSON.stringify(request)
                });
                
                if (response.success) {
                    this.currentSessionId = response.session_id;
                    this.connectWebSocket(response.session_id);
                    this.addStatusMessage('✅ Téléchargement démarré avec succès', 'success');
                }
            } catch (error) {
                this.isDownloading = false;
                this.addStatusMessage(`❌ Échec du démarrage du téléchargement : ${error.message}`, 'error');
                this.showNotification('Échec du démarrage du téléchargement', 'error');
            }
        },
        
        async cancelDownload() {
            if (!this.isDownloading || !this.currentSessionId) return;
            
            try {
                await this.apiRequest(`/download/cancel/${this.currentSessionId}`, { method: 'POST' });
                this.addStatusMessage('🛑 Téléchargement annulé', 'warning');
                this.showNotification('Téléchargement annulé', 'info');
            } catch (error) {
                this.addStatusMessage(`❌ Échec d'annulation du téléchargement : ${error.message}`, 'error');
            }
            
            this.isDownloading = false;
            this.disconnectWebSocket();
        },
        
        // WebSocket methods
        connectWebSocket(sessionId) {
            if (this.websocket) {
                this.websocket.close();
            }
            
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.addStatusMessage('🔗 Connecté aux mises à jour en temps réel', 'info');
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleWebSocketMessage(message);
                } catch (error) {
                    console.error('WebSocket message parse error:', error);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.websocket = null;
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.addStatusMessage('❌ Erreur de connexion WebSocket', 'error');
            };
        },
        
        disconnectWebSocket() {
            if (this.websocket) {
                this.websocket.close();
                this.websocket = null;
            }
            this.currentSessionId = null;
        },
        
        handleWebSocketMessage(message) {
            if (message.type === 'progress') {
                this.progress = {
                    current: message.data.current,
                    total: message.data.total,
                    percentage: message.data.percentage,
                    speed: message.data.speed_mbps,
                    eta: message.data.eta_seconds,
                    status: message.data.status
                };
                
                // Check if download is complete
                if (message.data.current === message.data.total && message.data.total > 0) {
                    this.isDownloading = false;
                    this.disconnectWebSocket();
                    this.loadSessions(); // Refresh sessions
                }
            } else if (message.type === 'status') {
                this.addStatusMessage(message.data.message, message.data.level);
                
                // Handle completion messages
                if (message.data.message.includes('complete') && message.data.level === 'success') {
                    this.isDownloading = false;
                    this.showNotification('Téléchargement terminé avec succès !', 'success');
                    this.disconnectWebSocket();
                }
            }
        },
        
        // UI methods
        toggleTheme() {
            this.darkMode = !this.darkMode;
            document.documentElement.classList.toggle('dark', this.darkMode);
        },
        
        selectFolder() {
            // Note: File system access is limited in browsers
            // This would need to be implemented with a file input or backend endpoint
            this.showNotification('Veuillez entrer le chemin du dossier manuellement', 'info');
        },
        
        addStatusMessage(message, level = 'info') {
            this.statusMessages.push({
                message,
                level,
                timestamp: new Date().toISOString()
            });
            
            // Keep only last 100 messages
            if (this.statusMessages.length > 100) {
                this.statusMessages = this.statusMessages.slice(-100);
            }
            
            // Auto-scroll to bottom (using setTimeout to ensure DOM is updated)
            setTimeout(() => {
                const logContainer = document.querySelector('.bg-gray-900');
                if (logContainer) {
                    logContainer.scrollTop = logContainer.scrollHeight;
                }
            }, 50);
        },
        
        clearLog() {
            this.statusMessages = [];
            this.addStatusMessage('Journal d\'état vidé', 'info');
        },
        
        showNotification(message, type = 'info') {
            this.notification = {
                show: true,
                message,
                type
            };
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                this.notification.show = false;
            }, 5000);
        }
    };
}