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

        // Text-to-Speech options
        this.enableTTS = options.enableTTS || false;
        this.ttsVoice = null;
        this.ttsRate = options.ttsRate || 1.0; // Speech rate (0.1 - 10)
        this.ttsPitch = options.ttsPitch || 1.0; // Voice pitch (0 - 2)
        this.ttsVolume = options.ttsVolume || 1.0; // Volume (0 - 1)

        this.init();
    }

    init() {
        // Create announcement overlay element
        this.createOverlay();

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

    createOverlay() {
        // Create overlay container
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
            const response = await fetch(`/api/encounter/${this.encounterId}/combat-log?limit=1`);
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
            let url = `/api/encounter/${this.encounterId}/combat-log?limit=10`;
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

            // Hide after duration
            setTimeout(() => {
                this.hideAnnouncement();
                resolve();
            }, this.displayDuration);
        });
    }

    hideAnnouncement() {
        this.overlay.classList.remove('show');

        // Wait for animation to complete before hiding
        setTimeout(() => {
            this.overlay.style.display = 'none';
        }, 300);
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
    }
}

// Export for use in templates
window.CombatAnnouncements = CombatAnnouncements;
