/**
 * Combat Announcements System
 *
 * Displays action announcements across player stations, GM view, and viewscreen.
 * Polls the combat log API and shows new actions in a prominent overlay.
 */

class CombatAnnouncements {
    constructor(encounterId, options = {}) {
        this.encounterId = encounterId;
        this.lastLogId = null;
        this.pollInterval = options.pollInterval || 2000; // Poll every 2 seconds
        this.displayDuration = options.displayDuration || 6000; // Show for 6 seconds
        this.isDisplaying = false;
        this.announcementQueue = [];
        this.pollingTimer = null;

        // Display mode: 'modal' (old fullscreen), 'banner' (persistent top bar), 'tts-only' (no visual)
        this.displayMode = options.displayMode || 'banner';

        // Role for visibility filtering: 'player', 'viewscreen', or 'gm'
        // Player/viewscreen roles filter out actions from hidden enemies
        this.role = options.role || 'player';

        // Text-to-Speech options
        this.enableTTS = options.enableTTS || false;
        this.ttsVoice = null;
        this.ttsRate = options.ttsRate || 1.0; // Speech rate (0.1 - 10)
        this.ttsPitch = options.ttsPitch || 1.0; // Voice pitch (0 - 2)
        this.ttsVolume = options.ttsVolume || 1.0; // Volume (0 - 1)

        this.init();
    }

    init() {
        // Create announcement element (unless TTS-only mode)
        if (this.displayMode !== 'tts-only') {
            this.createDisplay();
        }

        // Initialize text-to-speech if enabled
        if (this.enableTTS) {
            this.initTTS();
        }

        // Start polling for new actions
        this.startPolling();
    }

    initTTS() {
        // Check if speech synthesis is supported
        if (!('speechSynthesis' in window)) {
            console.warn('Text-to-speech not supported in this browser');
            this.enableTTS = false;
            return;
        }

        // Load voices (voices may load asynchronously)
        const loadVoices = () => {
            const voices = window.speechSynthesis.getVoices();
            if (voices.length > 0) {
                // Try to find a good "computer" voice
                // Prefer Google UK English Female, Microsoft Zira, or similar
                this.ttsVoice = voices.find(v =>
                    v.name.includes('Google UK') ||
                    v.name.includes('Zira') ||
                    v.name.includes('Samantha')
                ) || voices[0]; // Fallback to first available voice

                console.log('TTS initialized with voice:', this.ttsVoice.name);
            }
        };

        // Load voices immediately
        loadVoices();

        // Also listen for voiceschanged event (Chrome needs this)
        if (window.speechSynthesis.onvoiceschanged !== undefined) {
            window.speechSynthesis.onvoiceschanged = loadVoices;
        }
    }

    speak(text) {
        if (!this.enableTTS || !('speechSynthesis' in window)) {
            return;
        }

        // Cancel any ongoing speech
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);

        if (this.ttsVoice) {
            utterance.voice = this.ttsVoice;
        }

        utterance.rate = this.ttsRate;
        utterance.pitch = this.ttsPitch;
        utterance.volume = this.ttsVolume;

        window.speechSynthesis.speak(utterance);
    }

    generateAnnouncementText(logEntry) {
        let text = '';

        // Start with actor and action
        const actor = logEntry.actor_name || 'Unknown';
        const action = logEntry.action_name;

        text += `${actor}: ${action}. `;

        // Add task result if present
        if (logEntry.task_result) {
            const tr = logEntry.task_result;
            if (tr.succeeded) {
                text += `Success! ${tr.successes} successes. `;
                if (tr.momentum_generated > 0) {
                    text += `${tr.momentum_generated} momentum generated. `;
                }
            } else {
                text += `Failed. ${tr.successes} out of ${tr.difficulty} successes needed. `;
            }

            if (tr.complications > 0) {
                text += `${tr.complications} complication${tr.complications > 1 ? 's' : ''}. `;
            }
        }

        // Add damage if dealt
        if (logEntry.damage_dealt > 0) {
            text += `${logEntry.damage_dealt} damage dealt. `;
        }

        return text;
    }

    createDisplay() {
        if (this.displayMode === 'banner') {
            this.createBanner();
        } else if (this.displayMode === 'modal') {
            this.createModal();
        }
    }

    createBanner() {
        // Create persistent banner at top of page
        const banner = document.createElement('div');
        banner.id = 'announcement-banner';
        banner.className = 'announcement-banner';

        // Banner content
        banner.innerHTML = `
            <div class="banner-left">
                <div class="banner-current-turn">
                    <span class="banner-current-actor">Waiting for action...</span>
                    <span class="banner-current-action"></span>
                </div>
            </div>
            <div class="banner-center">
                <div class="banner-round">Round <span class="banner-round-num">1</span></div>
            </div>
            <div class="banner-right">
                <div class="banner-next-turn">
                    <span class="banner-label">Now:</span>
                    <span class="banner-next-actor">—</span>
                </div>
            </div>
            <div class="banner-hailing" style="display: none;">
                <div class="banner-hailing-content">
                    <span class="banner-hailing-icon">📡</span>
                    <span class="banner-hailing-status">INCOMING HAIL</span>
                    <span class="banner-hailing-from">—</span>
                    <div class="banner-hailing-actions"></div>
                </div>
            </div>
        `;

        document.body.insertBefore(banner, document.body.firstChild);

        this.banner = banner;
        this.bannerElements = {
            currentActor: banner.querySelector('.banner-current-actor'),
            currentAction: banner.querySelector('.banner-current-action'),
            roundNum: banner.querySelector('.banner-round-num'),
            nextActor: banner.querySelector('.banner-next-actor'),
            hailingContainer: banner.querySelector('.banner-hailing'),
            hailingStatus: banner.querySelector('.banner-hailing-status'),
            hailingFrom: banner.querySelector('.banner-hailing-from'),
            hailingActions: banner.querySelector('.banner-hailing-actions')
        };

        // Add class to body for flexbox layout
        document.body.classList.add('has-announcement-banner');
    }

    createModal() {
        // Create overlay container (old fullscreen modal style)
        const overlay = document.createElement('div');
        overlay.id = 'announcement-overlay';
        overlay.className = 'announcement-overlay';
        overlay.style.display = 'none';

        // Create content container
        const content = document.createElement('div');
        content.className = 'announcement-content';

        // Create elements for announcement data
        content.innerHTML = `
            <div class="announcement-header">
                <div class="announcement-ship"></div>
                <div class="announcement-round"></div>
            </div>
            <div class="announcement-actor"></div>
            <div class="announcement-action"></div>
            <div class="announcement-description"></div>
            <div class="announcement-result"></div>
        `;

        overlay.appendChild(content);
        document.body.appendChild(overlay);

        this.overlay = overlay;
        this.contentElements = {
            ship: content.querySelector('.announcement-ship'),
            round: content.querySelector('.announcement-round'),
            actor: content.querySelector('.announcement-actor'),
            action: content.querySelector('.announcement-action'),
            description: content.querySelector('.announcement-description'),
            result: content.querySelector('.announcement-result')
        };
    }

    async startPolling() {
        // Initial fetch to get latest ID (don't display)
        await this.fetchInitialLog();

        // Poll for new entries
        this.pollingTimer = setInterval(() => this.pollForNewActions(), this.pollInterval);
    }

    stopPolling() {
        if (this.pollingTimer) {
            clearInterval(this.pollingTimer);
            this.pollingTimer = null;
        }
    }

    async fetchInitialLog() {
        try {
            const response = await fetch(`/api/encounter/${this.encounterId}/combat-log?limit=1&role=${this.role}`);
            if (!response.ok) return;

            const data = await response.json();
            if (data.latest_id) {
                this.lastLogId = data.latest_id;
            }
        } catch (error) {
            console.error('Error fetching initial combat log:', error);
        }
    }

    async pollForNewActions() {
        try {
            let url = `/api/encounter/${this.encounterId}/combat-log?limit=10&role=${this.role}`;
            if (this.lastLogId) {
                url += `&since_id=${this.lastLogId}`;
            }

            const response = await fetch(url);
            if (!response.ok) return;

            const data = await response.json();

            // Update last log ID
            if (data.latest_id && data.latest_id > this.lastLogId) {
                this.lastLogId = data.latest_id;
            }

            // Queue new announcements (they come in order)
            if (data.log && data.log.length > 0) {
                for (const logEntry of data.log) {
                    this.queueAnnouncement(logEntry);
                }
            }
        } catch (error) {
            console.error('Error polling for new actions:', error);
        }
    }

    queueAnnouncement(logEntry) {
        this.announcementQueue.push(logEntry);

        // If not currently displaying, start processing queue
        if (!this.isDisplaying) {
            this.processQueue();
        }
    }

    async processQueue() {
        if (this.announcementQueue.length === 0) {
            this.isDisplaying = false;
            return;
        }

        this.isDisplaying = true;
        const announcement = this.announcementQueue.shift();

        // Display the announcement
        await this.showAnnouncement(announcement);

        // Process next in queue after delay
        setTimeout(() => this.processQueue(), 500); // Small gap between announcements
    }

    async showAnnouncement(logEntry) {
        return new Promise((resolve) => {
            // Generate and speak announcement text if TTS is enabled
            if (this.enableTTS) {
                const announcementText = this.generateAnnouncementText(logEntry);
                this.speak(announcementText);
            }

            // Banner mode - update persistent banner
            if (this.displayMode === 'banner') {
                this.updateBanner(logEntry);
                resolve();
                return;
            }

            // TTS-only mode - no visual update needed
            if (this.displayMode === 'tts-only') {
                resolve();
                return;
            }

            // Modal mode - show fullscreen overlay
            this.showModal(logEntry);
            setTimeout(() => {
                this.hideAnnouncement();
                resolve();
            }, this.displayDuration);
        });
    }

    updateBanner(logEntry) {
        // Build verbose action description
        const actor = logEntry.actor_name || 'Unknown';
        const action = logEntry.action_name || 'acts';

        // Format: "Actor Action!" with results
        let actionText = `${actor} ${this.formatActionVerb(action)}!`;

        // Add result details
        let resultParts = [];

        if (logEntry.task_result) {
            const tr = logEntry.task_result;
            if (tr.succeeded) {
                if (tr.momentum_generated > 0) {
                    resultParts.push(`+${tr.momentum_generated} Momentum`);
                }
            } else {
                resultParts.push('Failed');
            }
            if (tr.complications > 0) {
                resultParts.push(`${tr.complications} complication${tr.complications > 1 ? 's' : ''}`);
            }
        }

        if (logEntry.damage_dealt > 0) {
            resultParts.push(`${logEntry.damage_dealt} damage`);
        }

        // Combine action text with results
        if (resultParts.length > 0) {
            actionText += ' ' + resultParts.join(', ') + '.';
        }

        this.bannerElements.currentActor.textContent = actionText;
        this.bannerElements.currentAction.textContent = '';
        this.bannerElements.roundNum.textContent = logEntry.round || '1';

        // Fetch and update who's turn it is NOW
        this.updateNextPlayer();

        // Add brief highlight animation
        this.banner.classList.add('banner-pulse');
        setTimeout(() => this.banner.classList.remove('banner-pulse'), 1000);
    }

    formatActionVerb(actionName) {
        // Convert action names to past tense verbs
        const verbMap = {
            'Rally': 'Rallies',
            'Scan': 'Scans',
            'Attack': 'Attacks',
            'Fire Weapons': 'Fires Weapons',
            'Maneuver': 'Maneuvers',
            'Evasive Action': 'Takes Evasive Action',
            'Lock On': 'Locks On',
            'Damage Control': 'Performs Damage Control',
            'Regenerate Shields': 'Regenerates Shields',
            'Calibrate Weapons': 'Calibrates Weapons',
            'Calibrate Sensors': 'Calibrates Sensors',
            'Sensor Sweep': 'Performs Sensor Sweep',
            'Scan For Weakness': 'Scans For Weakness',
            'Modulate Shields': 'Modulates Shields',
            'Targeting Solution': 'Calculates Targeting Solution',
            'Attack Pattern': 'Executes Attack Pattern',
            'Regain Power': 'Regains Power',
            'Pass': 'Passes',
            'Change Position': 'Changes Position',
        };

        return verbMap[actionName] || actionName;
    }

    async updateNextPlayer() {
        try {
            const response = await fetch(`/api/encounter/${this.encounterId}/turn-status`);
            if (!response.ok) return;

            const data = await response.json();
            if (data.next_participant && data.next_participant.name) {
                this.bannerElements.nextActor.textContent = data.next_participant.name;
            } else {
                this.bannerElements.nextActor.textContent = '—';
            }
        } catch (error) {
            console.error('Error fetching next player:', error);
        }
    }

    showModal(logEntry) {
        // Populate announcement content
        this.contentElements.ship.textContent = logEntry.ship_name || 'Unknown Ship';
        this.contentElements.round.textContent = `Round ${logEntry.round}`;
        this.contentElements.actor.textContent = logEntry.actor_name || 'Unknown Actor';
        this.contentElements.action.textContent = logEntry.action_name;
        this.contentElements.description.textContent = logEntry.description || '';

        // Build result text
        let resultHTML = '';

        if (logEntry.task_result) {
            const tr = logEntry.task_result;
            resultHTML += `<div class="announcement-roll">`;
            resultHTML += `<strong>Roll:</strong> ${tr.rolls ? tr.rolls.join(', ') : 'N/A'}`;
            resultHTML += ` (TN: ${tr.target_number})`;
            resultHTML += `</div>`;

            const resultClass = tr.succeeded ? 'success' : 'failure';
            resultHTML += `<div class="announcement-roll-result ${resultClass}">`;
            if (tr.succeeded) {
                resultHTML += `✓ SUCCESS - ${tr.successes} successes`;
                if (tr.momentum_generated > 0) {
                    resultHTML += ` (+${tr.momentum_generated} Momentum)`;
                }
            } else {
                resultHTML += `✗ FAILED - ${tr.successes}/${tr.difficulty} successes`;
            }
            if (tr.complications > 0) {
                resultHTML += ` <span class="complication">(${tr.complications} complication${tr.complications > 1 ? 's' : ''})</span>`;
            }
            resultHTML += `</div>`;
        }

        if (logEntry.damage_dealt > 0) {
            resultHTML += `<div class="announcement-damage">💥 <strong>${logEntry.damage_dealt}</strong> damage dealt</div>`;
        }

        if (logEntry.momentum_spent > 0) {
            resultHTML += `<div class="announcement-resource">Momentum spent: ${logEntry.momentum_spent}</div>`;
        }

        if (logEntry.threat_spent > 0) {
            resultHTML += `<div class="announcement-resource">Threat spent: ${logEntry.threat_spent}</div>`;
        }

        this.contentElements.result.innerHTML = resultHTML;

        // Show overlay with animation
        this.overlay.style.display = 'flex';
        // Force reflow
        this.overlay.offsetHeight;
        this.overlay.classList.add('show');
    }

    hideAnnouncement() {
        if (this.displayMode === 'modal' && this.overlay) {
            this.overlay.classList.remove('show');

            // Wait for animation to complete before hiding
            setTimeout(() => {
                this.overlay.style.display = 'none';
            }, 300);
        }
        // Banner mode doesn't hide - it's persistent
    }

    updateHailingState(hailingState) {
        // Only update banner mode
        if (this.displayMode !== 'banner' || !this.bannerElements.hailingContainer) {
            return;
        }

        if (!hailingState) {
            // Hide hailing section
            this.bannerElements.hailingContainer.style.display = 'none';
            return;
        }

        // Show hailing section
        this.bannerElements.hailingContainer.style.display = 'flex';

        // Update based on hailing state
        if (hailingState.active && hailingState.initiator === 'gm') {
            // Incoming hail from GM
            this.bannerElements.hailingStatus.textContent = '📡 INCOMING HAIL';
            this.bannerElements.hailingFrom.textContent = `from ${hailingState.from_ship}`;

            // Show accept/reject buttons (if they exist on page)
            this.bannerElements.hailingActions.innerHTML = `
                <button onclick="respondToHail(true)" class="banner-hail-btn banner-hail-accept">ACCEPT</button>
                <button onclick="respondToHail(false)" class="banner-hail-btn banner-hail-reject">REJECT</button>
            `;
        } else if (hailingState.channel_open) {
            // Channel is open
            this.bannerElements.hailingStatus.textContent = '✓ CHANNEL OPEN';
            this.bannerElements.hailingFrom.textContent = `with ${hailingState.from_ship}`;

            // Show close button
            this.bannerElements.hailingActions.innerHTML = `
                <button onclick="closeChannel()" class="banner-hail-btn banner-hail-close">CLOSE</button>
            `;
        } else {
            // Hail initiated by player, waiting for response
            this.bannerElements.hailingStatus.textContent = '📡 HAILING...';
            this.bannerElements.hailingFrom.textContent = hailingState.to_ship;
            this.bannerElements.hailingActions.innerHTML = '';
        }

        // Add pulse animation
        this.banner.classList.add('banner-pulse');
        setTimeout(() => this.banner.classList.remove('banner-pulse'), 1000);
    }

    destroy() {
        this.stopPolling();

        // Cancel any ongoing speech
        if (this.enableTTS && 'speechSynthesis' in window) {
            window.speechSynthesis.cancel();
        }

        if (this.overlay) {
            this.overlay.remove();
        }

        if (this.banner) {
            this.banner.remove();
            document.body.classList.remove('has-announcement-banner');
        }
    }
}

// Export for use in templates
window.CombatAnnouncements = CombatAnnouncements;
