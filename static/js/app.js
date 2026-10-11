/**
 * TactileTrail - Client Application Logic
 * Zero-Screen Audio Naturalist for the DEV Hacktoberfest "Touch Grass" Challenge
 *
 * Implements:
 * 1. Procedural Web Audio API Nature Soundscape (wind, leaf rustle, birdsong)
 * 2. Multi-tier Audio Narration Player (ElevenLabs -> gTTS -> Web SpeechSynthesis)
 * 3. Mobile MediaSession API (earbuds/lockscreen playback controls in-pocket)
 * 4. Haptic vibration feedback for screenless checkpoint transitions
 * 5. Pocket-Lock protection mode & sunlight high-contrast toggle
 * 6. Field Journal record with specimen photo attachment and export
 */

// ==============================================================================
// 1. PROCEDURAL WEB AUDIO NATURE SOUNDSCAPE ENGINE
// ==============================================================================
class ProceduralNatureSoundscape {
  constructor() {
    this.ctx = null;
    this.isMuted = false;
    this.isPlaying = false;
    this.masterGain = null;
    this.windGain = null;
    this.birdTimer = null;
  }

  init() {
    if (this.ctx) return;
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioCtx();
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(0.35, this.ctx.currentTime);
      this.masterGain.connect(this.ctx.destination);
    } catch (e) {
      console.warn("Web Audio API not supported:", e);
    }
  }

  start(environment = "forest") {
    this.init();
    if (!this.ctx || this.isPlaying) return;
    if (this.ctx.state === "suspended") {
      this.ctx.resume();
    }

    this.isPlaying = true;
    this.createWindAmbience(environment);
    this.scheduleProceduralBirds();
  }

  stop() {
    if (!this.ctx || !this.isPlaying) return;
    this.isPlaying = false;
    if (this.birdTimer) {
      clearTimeout(this.birdTimer);
      this.birdTimer = null;
    }
    if (this.windGain) {
      try {
        this.windGain.gain.setTargetAtTime(0.001, this.ctx.currentTime, 0.5);
      } catch (e) {}
    }
  }

  toggle() {
    if (this.isMuted) {
      this.unmute();
      return true;
    } else {
      this.mute();
      return false;
    }
  }

  mute() {
    this.isMuted = true;
    if (this.masterGain && this.ctx) {
      this.masterGain.gain.setTargetAtTime(0.001, this.ctx.currentTime, 0.2);
    }
  }

  unmute() {
    this.isMuted = false;
    if (this.masterGain && this.ctx) {
      this.masterGain.gain.setTargetAtTime(0.35, this.ctx.currentTime, 0.3);
    }
  }

  createWindAmbience(environment) {
    if (!this.ctx) return;
    // Generate 3 seconds of pink/brownian noise in a loop buffer
    const bufferSize = this.ctx.sampleRate * 3;
    const noiseBuffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const output = noiseBuffer.getChannelData(0);
    let b0 = 0, b1 = 0, b2 = 0;

    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      b0 = 0.99886 * b0 + white * 0.0555179;
      b1 = 0.99332 * b1 + white * 0.0750759;
      b2 = 0.96900 * b2 + white * 0.1538520;
      output[i] = (b0 + b1 + b2) * 0.18;
    }

    const whiteNoise = this.ctx.createBufferSource();
    whiteNoise.buffer = noiseBuffer;
    whiteNoise.loop = true;

    // Resonant Biquad Filter for wind whisper through branches
    const filter = this.ctx.createBiquadFilter();
    filter.type = "lowpass";
    const cutoffFreq = environment === "water" ? 750 : (environment === "meadow" ? 650 : 450);
    filter.frequency.setValueAtTime(cutoffFreq, this.ctx.currentTime);
    filter.Q.setValueAtTime(2.5, this.ctx.currentTime);

    // LFO to simulate gentle gusts of wind
    const lfo = this.ctx.createOscillator();
    lfo.frequency.setValueAtTime(0.12, this.ctx.currentTime); // 8-second swell
    const lfoGain = this.ctx.createGain();
    lfoGain.gain.setValueAtTime(180, this.ctx.currentTime);
    lfo.connect(lfoGain);
    lfoGain.connect(filter.frequency);

    this.windGain = this.ctx.createGain();
    this.windGain.gain.setValueAtTime(0.2, this.ctx.currentTime);

    whiteNoise.connect(filter);
    filter.connect(this.windGain);
    this.windGain.connect(this.masterGain);

    whiteNoise.start();
    lfo.start();
  }

  scheduleProceduralBirds() {
    if (!this.isPlaying || this.isMuted) return;
    const nextInMs = 6000 + Math.random() * 8000;
    this.birdTimer = setTimeout(() => {
      this.playChirp();
      this.scheduleProceduralBirds();
    }, nextInMs);
  }

  playChirp() {
    if (!this.ctx || !this.isPlaying || this.isMuted) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      const now = this.ctx.currentTime;

      // Realistic avian frequency modulation
      const baseFreq = 2600 + Math.random() * 800;
      osc.type = "sine";
      osc.frequency.setValueAtTime(baseFreq, now);
      osc.frequency.exponentialRampToValueAtTime(baseFreq + 700, now + 0.08);
      osc.frequency.exponentialRampToValueAtTime(baseFreq - 300, now + 0.16);

      gain.gain.setValueAtTime(0.001, now);
      gain.gain.linearRampToValueAtTime(0.04, now + 0.04);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start(now);
      osc.stop(now + 0.22);
    } catch (e) {}
  }
}

// ==============================================================================
// 2. MAIN APPLICATION CONTROLLER
// ==============================================================================
class TactileTrailApp {
  constructor() {
    // State
    this.currentView = "view-setup";
    this.selectedEnv = "forest";
    this.selectedLength = "standard";
    this.isOfflineMode = true;
    this.ambientSoundEnabled = true;
    this.currentVoiceId = "JBFqnCBsd6RMkjVDRZzb";

    // Active walk state
    this.walkData = null;
    this.currentStepIndex = 0;
    this.isPlaying = false;
    this.walkStartTime = null;
    this.walkElapsedTimer = null;
    this.audioBlobUrl = null;
    this.specimenPhotoDataUrl = null;

    // Components
    this.soundscape = new ProceduralNatureSoundscape();
    this.audioEl = document.getElementById("narration-audio");

    this.initDOMElements();
    this.attachEventListeners();
    this.checkRuntimeConfig();
  }

  initDOMElements() {
    // Views
    this.viewSetup = document.getElementById("view-setup");
    this.viewActive = document.getElementById("view-active-walk");
    this.viewReflection = document.getElementById("view-reflection");

    // Controls
    this.offlineToggle = document.getElementById("offline-mode-toggle");
    this.edgeModeLabel = document.getElementById("edge-mode-label");
    this.edgeModeDesc = document.getElementById("edge-mode-desc");
    this.edgeModeIcon = document.getElementById("edge-mode-icon");
    this.ambientToggle = document.getElementById("ambient-audio-toggle");
    this.voiceSelect = document.getElementById("voice-select");
    this.startWalkBtn = document.getElementById("start-walk-btn");

    // Active walk elements
    this.activeEnvBadge = document.getElementById("active-env-badge");
    this.activeAiBadge = document.getElementById("active-ai-badge");
    this.stepperDots = document.getElementById("stepper-dots");
    this.checkpointSenseBadge = document.getElementById("checkpoint-sense-badge");
    this.senseEmoji = document.getElementById("sense-emoji");
    this.senseLabel = document.getElementById("sense-label");
    this.stepNumberText = document.getElementById("step-number-text");
    this.checkpointTitle = document.getElementById("checkpoint-title");
    this.checkpointInvitation = document.getElementById("checkpoint-invitation");
    this.checkpointNarration = document.getElementById("checkpoint-narration");
    this.scientificNoteText = document.getElementById("scientific-note-text");
    this.audioVisualizer = document.getElementById("audio-visualizer");
    this.currentTimeEl = document.getElementById("current-time");
    this.totalTimeEl = document.getElementById("total-time");
    this.scrubberFill = document.getElementById("scrubber-fill");

    // Tactile Controls
    this.playPauseBtn = document.getElementById("play-pause-btn");
    this.playPauseIcon = document.getElementById("play-pause-icon");
    this.prevStepBtn = document.getElementById("prev-step-btn");
    this.nextStepBtn = document.getElementById("next-step-btn");
    this.ambientMuteBtn = document.getElementById("ambient-mute-btn");
    this.vibrateTestBtn = document.getElementById("vibrate-test-btn");
    this.pocketModeBtn = document.getElementById("pocket-mode-btn");
    this.endWalkEarlyBtn = document.getElementById("end-walk-early-btn");

    // Pocket Overlay
    this.pocketOverlay = document.getElementById("pocket-overlay");
    this.pocketStepName = document.getElementById("pocket-step-name");
    this.exitPocketModeBtn = document.getElementById("exit-pocket-mode-btn");

    // Reflection Card Elements
    this.statSenses = document.getElementById("stat-senses");
    this.statMinutes = document.getElementById("stat-minutes");
    this.statAiModel = document.getElementById("stat-ai-model");
    this.recapList = document.getElementById("recap-list");
    this.photoInput = document.getElementById("photo-input");
    this.photoUploadZone = document.getElementById("photo-upload-zone");
    this.photoPlaceholder = document.getElementById("photo-placeholder");
    this.photoPreviewContainer = document.getElementById("photo-preview-container");
    this.photoPreviewImg = document.getElementById("photo-preview-img");
    this.removePhotoBtn = document.getElementById("remove-photo-btn");
    this.reflectionText = document.getElementById("reflection-text");
    this.natureQuoteText = document.getElementById("nature-quote-text");
    this.saveJournalBtn = document.getElementById("save-journal-btn");
    this.shareWalkBtn = document.getElementById("share-walk-btn");
    this.newWalkBtn = document.getElementById("new-walk-btn");

    // Top Bar Actions
    this.contrastToggleBtn = document.getElementById("contrast-toggle-btn");
    this.infoModalBtn = document.getElementById("info-modal-btn");
    this.infoModal = document.getElementById("info-modal");
    this.closeModalBtn = document.getElementById("close-modal-btn");
  }

  attachEventListeners() {
    // 1. Environment selector cards
    document.querySelectorAll(".env-card").forEach((card) => {
      card.addEventListener("click", () => {
        document.querySelectorAll(".env-card").forEach((c) => c.classList.remove("active"));
        card.classList.add("active");
        this.selectedEnv = card.getAttribute("data-env");
      });
    });

    // 2. Length segmented buttons
    document.querySelectorAll(".seg-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".seg-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        this.selectedLength = btn.getAttribute("data-length");
      });
    });

    // 3. Offline / Edge Toggle
    this.offlineToggle.addEventListener("change", (e) => {
      this.isOfflineMode = e.target.checked;
      this.updateEdgeBannerDisplay();
    });

    // 4. Ambient sound toggle
    this.ambientToggle.addEventListener("change", (e) => {
      this.ambientSoundEnabled = e.target.checked;
    });

    // 5. Narrator voice selection
    this.voiceSelect.addEventListener("change", (e) => {
      this.currentVoiceId = e.target.value;
    });

    // 6. Begin Walk button
    this.startWalkBtn.addEventListener("click", () => this.handleBeginWalk());

    // 7. Audio narration element events
    this.audioEl.addEventListener("timeupdate", () => this.updateAudioProgress());
    this.audioEl.addEventListener("ended", () => this.handleNarrationEnded());
    this.audioEl.addEventListener("play", () => this.setAudioPlayingState(true));
    this.audioEl.addEventListener("pause", () => this.setAudioPlayingState(false));

    // 8. Active Walk Tactile Buttons
    this.playPauseBtn.addEventListener("click", () => this.togglePlayPause());
    this.prevStepBtn.addEventListener("click", () => this.goToPreviousCheckpoint());
    this.nextStepBtn.addEventListener("click", () => this.goToNextCheckpoint());
    this.endWalkEarlyBtn.addEventListener("click", () => this.finishWalk());

    // 9. Ambient Nature Sound toggle chip
    this.ambientMuteBtn.addEventListener("click", () => {
      const active = this.soundscape.toggle();
      this.ambientMuteBtn.classList.toggle("active", active);
    });

    // 10. Haptic pulse test button
    this.vibrateTestBtn.addEventListener("click", () => {
      this.triggerHaptic("double");
    });

    // 11. Pocket Mode
    this.pocketModeBtn.addEventListener("click", () => this.enterPocketMode());
    this.exitPocketModeBtn.addEventListener("click", () => this.exitPocketMode());

    // 12. Sunlight High Contrast Toggle
    this.contrastToggleBtn.addEventListener("click", () => {
      const isSun = document.body.classList.toggle("theme-sunlight");
      document.getElementById("contrast-icon").textContent = isSun ? "🌲" : "☀️";
    });

    // 13. Info Modal
    this.infoModalBtn.addEventListener("click", () => this.infoModal.classList.remove("hidden"));
    this.closeModalBtn.addEventListener("click", () => this.infoModal.classList.add("hidden"));
    this.infoModal.addEventListener("click", (e) => {
      if (e.target === this.infoModal) this.infoModal.classList.add("hidden");
    });

    // 14. Specimen Photo Capture
    this.photoUploadZone.addEventListener("click", (e) => {
      if (e.target !== this.removePhotoBtn && !this.removePhotoBtn.contains(e.target)) {
        this.photoInput.click();
      }
    });

    this.photoInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (evt) => {
          this.specimenPhotoDataUrl = evt.target.result;
          this.photoPreviewImg.src = this.specimenPhotoDataUrl;
          this.photoPreviewContainer.classList.remove("hidden");
          this.photoPlaceholder.classList.add("hidden");
        };
        reader.readAsDataURL(file);
      }
    });

    this.removePhotoBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      this.specimenPhotoDataUrl = null;
      this.photoPreviewImg.src = "";
      this.photoPreviewContainer.classList.add("hidden");
      this.photoPlaceholder.classList.remove("hidden");
      this.photoInput.value = "";
    });

    // 15. Reflection save & share
    this.saveJournalBtn.addEventListener("click", () => this.saveJournalEntry());
    this.shareWalkBtn.addEventListener("click", () => this.shareWalkSummary());
    this.newWalkBtn.addEventListener("click", () => this.resetToSetup());

    // 16. Setup MediaSession API handlers
    this.setupMediaSession();
  }

  async checkRuntimeConfig() {
    try {
      const res = await fetch("/api/config");
      if (res.ok) {
        const data = await res.json();
        // If user has Gemma or ElevenLabs API keys configured in environment, update toggle default
        if (data.ai_engine.google_ai_studio_active || data.ai_engine.huggingface_active) {
          this.offlineToggle.checked = false;
          this.isOfflineMode = false;
          this.updateEdgeBannerDisplay();
        }
      }
    } catch (e) {
      console.log("Using default offline edge mode.");
    }
  }

  updateEdgeBannerDisplay() {
    if (this.isOfflineMode) {
      this.edgeModeIcon.textContent = "⚡";
      this.edgeModeLabel.textContent = "Gemma Edge (Offline Mode)";
      this.edgeModeDesc.textContent = "Running on-device edge weights. Zero cell reception required on deep wilderness trails.";
    } else {
      this.edgeModeIcon.textContent = "📶";
      this.edgeModeLabel.textContent = "Live Cloud AI (Gemma 2 + ElevenLabs)";
      this.edgeModeDesc.textContent = "Invoking Google AI Studio & ElevenLabs Neural TTS for dynamic trails.";
    }
  }

  switchView(viewId) {
    [this.viewSetup, this.viewActive, this.viewReflection].forEach((v) => {
      v.classList.remove("active");
    });
    document.getElementById(viewId).classList.add("active");
    this.currentView = viewId;
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // ============================================================================
  // WALK GENERATION & TRANSITION
  // ============================================================================
  async handleBeginWalk() {
    // Show quick loading state on button
    this.startWalkBtn.disabled = true;
    const originalText = this.startWalkBtn.innerHTML;
    this.startWalkBtn.innerHTML = `
      <span class="btn-icon">🌿</span>
      <span class="btn-text">
        <strong>Tuning Senses...</strong>
        <small>Generating naturalist checkpoints</small>
      </span>
    `;

    try {
      const payload = {
        environment: this.selectedEnv,
        walk_length: this.selectedLength,
        mode: this.isOfflineMode ? "offline" : "auto",
        sensory_focus: "all"
      };

      const response = await fetch("/api/generate-walk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error("Unable to fetch walk");
      }

      this.walkData = await response.json();
      this.currentStepIndex = 0;
      this.walkStartTime = new Date();

      // Launch Ambient Soundscape
      if (this.ambientSoundEnabled) {
        this.soundscape.start(this.selectedEnv);
      }

      // Switch to active walk view
      this.renderActiveWalkHUD();
      this.switchView("view-active-walk");
      this.loadCheckpoint(0, true);

    } catch (err) {
      console.error("Walk generation error:", err);
      alert("Unable to generate walk. Please try again.");
    } finally {
      this.startWalkBtn.disabled = false;
      this.startWalkBtn.innerHTML = originalText;
    }
  }

  renderActiveWalkHUD() {
    const envNames = {
      forest: "🌲 Forest Trail",
      park: "🌿 Park & Botanical",
      neighborhood: "🏘️ Neighborhood",
      water: "🌊 Lake & River",
      meadow: "🌾 Open Meadow"
    };
    this.activeEnvBadge.textContent = envNames[this.walkData.environment] || "🌲 Trail";

    if (this.walkData.is_offline) {
      this.activeAiBadge.className = "hud-badge badge-edge";
      this.activeAiBadge.textContent = "⚡ Gemma Edge (Off-Grid)";
    } else {
      this.activeAiBadge.className = "hud-badge";
      this.activeAiBadge.textContent = `📶 ${this.walkData.model_name}`;
    }

    // Render stepper dots
    this.stepperDots.innerHTML = "";
    this.walkData.checkpoints.forEach((_, idx) => {
      const dot = document.createElement("div");
      dot.className = `step-dot ${idx === 0 ? "active" : ""}`;
      dot.id = `step-dot-${idx}`;
      this.stepperDots.appendChild(dot);
    });
  }

  async loadCheckpoint(index, autoPlay = true) {
    if (!this.walkData || !this.walkData.checkpoints[index]) return;

    this.currentStepIndex = index;
    const cp = this.walkData.checkpoints[index];
    const total = this.walkData.checkpoints.length;

    // Trigger haptic vibration for pocket notification
    this.triggerHaptic(cp.haptic_cue || "pulse");

    // Update UI elements
    const senseIcons = {
      touch: "🖐️",
      sound: "👂",
      observation: "👁️",
      reflection: "🧘"
    };

    this.senseEmoji.textContent = senseIcons[cp.sense] || "🌿";
    this.senseLabel.textContent = `${cp.sense.toUpperCase()} QUEST`;
    this.stepNumberText.textContent = `${index + 1} of ${total}`;
    this.checkpointTitle.textContent = cp.title;
    this.checkpointInvitation.textContent = cp.invitation;
    this.checkpointNarration.textContent = `"${cp.narration}"`;
    this.scientificNoteText.innerHTML = `🔬 <em>${cp.scientific_note || "Natural sensory alignment"}</em>`;
    this.pocketStepName.textContent = `Checkpoint ${index + 1}: ${cp.title}`;

    // Update stepper dots
    for (let i = 0; i < total; i++) {
      const dot = document.getElementById(`step-dot-${i}`);
      if (dot) {
        dot.className = "step-dot";
        if (i < index) dot.classList.add("completed");
        if (i === index) dot.classList.add("active");
      }
    }

    // Update Next button text
    if (index === total - 1) {
      this.nextStepBtn.innerHTML = "<span>✨ Finish Walk</span>";
    } else {
      this.nextStepBtn.innerHTML = "<span>⏭️ Next Sense</span>";
    }

    // Update MediaSession lockscreen metadata
    this.updateMediaSessionMetadata(cp);

    // Stop current speech or audio
    this.stopAudioPlayback();

    // Reset scrubber
    this.scrubberFill.style.width = "0%";
    this.currentTimeEl.textContent = "0:00";
    this.totalTimeEl.textContent = this.formatTime(cp.duration_seconds || 50);

    if (autoPlay) {
      await this.synthesizeAndPlayNarration(cp);
    }
  }

  // ============================================================================
  // AUDIO SYNTHESIS & PLAYBACK ENGINE
  // ============================================================================
  async synthesizeAndPlayNarration(checkpoint) {
    this.setAudioPlayingState(true);

    try {
      // 1. Request audio from backend (ElevenLabs with gTTS fallback)
      const res = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: checkpoint.narration,
          voice_id: this.currentVoiceId,
          checkpoint_id: checkpoint.id
        })
      });

      const contentType = res.headers.get("Content-Type") || "";

      // Case A: Audio stream (MP3 from ElevenLabs or gTTS)
      if (contentType.includes("audio/mpeg")) {
        const blob = await res.blob();
        if (this.audioBlobUrl) {
          URL.revokeObjectURL(this.audioBlobUrl);
        }
        this.audioBlobUrl = URL.createObjectURL(blob);
        this.audioEl.src = this.audioBlobUrl;
        await this.audioEl.play();
        return;
      }

      // Case B: Client-side Web SpeechSynthesis Fallback
      const json = await res.json();
      if (json.fallback_to_browser_tts) {
        this.speakWithBrowserWebSpeech(checkpoint.narration);
        return;
      }

    } catch (e) {
      console.warn("Backend audio synthesis failed. Falling back to browser SpeechSynthesis:", e);
      this.speakWithBrowserWebSpeech(checkpoint.narration);
    }
  }

  speakWithBrowserWebSpeech(text) {
    if (!('speechSynthesis' in window)) {
      console.error("Speech Synthesis not available.");
      this.setAudioPlayingState(false);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Choose British or deep resonant natural voice if available
    const voices = window.speechSynthesis.getVoices();
    const naturalistVoice = voices.find(v => 
      v.lang.includes("en-GB") || v.name.includes("Natural") || v.name.includes("Daniel") || v.name.includes("George")
    );
    if (naturalistVoice) utterance.voice = naturalistVoice;

    // Slow, meditative cadence
    utterance.rate = 0.88;
    utterance.pitch = 0.94;

    const estDuration = Math.max(15, Math.round(text.split(" ").length * 0.5));
    let elapsed = 0;
    const progressInterval = setInterval(() => {
      if (!window.speechSynthesis.speaking) {
        clearInterval(progressInterval);
        return;
      }
      elapsed += 0.5;
      const pct = Math.min(100, (elapsed / estDuration) * 100);
      this.scrubberFill.style.width = `${pct}%`;
      this.currentTimeEl.textContent = this.formatTime(Math.round(elapsed));
    }, 500);

    utterance.onstart = () => {
      this.setAudioPlayingState(true);
    };

    utterance.onend = () => {
      clearInterval(progressInterval);
      this.setAudioPlayingState(false);
      this.scrubberFill.style.width = "100%";
      this.handleNarrationEnded();
    };

    utterance.onerror = () => {
      clearInterval(progressInterval);
      this.setAudioPlayingState(false);
    };

    window.speechSynthesis.speak(utterance);
  }

  togglePlayPause() {
    if (this.isPlaying) {
      this.pauseAudioPlayback();
    } else {
      this.resumeAudioPlayback();
    }
  }

  pauseAudioPlayback() {
    if (this.audioEl.src && !this.audioEl.paused) {
      this.audioEl.pause();
    }
    if ('speechSynthesis' in window && window.speechSynthesis.speaking) {
      window.speechSynthesis.pause();
    }
    this.setAudioPlayingState(false);
  }

  resumeAudioPlayback() {
    if (this.audioEl.src && this.audioEl.paused && this.audioEl.currentTime > 0) {
      this.audioEl.play();
      this.setAudioPlayingState(true);
    } else if ('speechSynthesis' in window && window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
      this.setAudioPlayingState(true);
    } else {
      const cp = this.walkData.checkpoints[this.currentStepIndex];
      this.synthesizeAndPlayNarration(cp);
    }
  }

  stopAudioPlayback() {
    if (this.audioEl) {
      this.audioEl.pause();
      this.audioEl.currentTime = 0;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    this.setAudioPlayingState(false);
  }

  setAudioPlayingState(playing) {
    this.isPlaying = playing;
    if (playing) {
      this.playPauseIcon.textContent = "⏸️";
      this.audioVisualizer.classList.add("playing");
    } else {
      this.playPauseIcon.textContent = "▶️";
      this.audioVisualizer.classList.remove("playing");
    }
  }

  updateAudioProgress() {
    if (!this.audioEl.duration) return;
    const cur = this.audioEl.currentTime;
    const dur = this.audioEl.duration;
    const pct = (cur / dur) * 100;
    this.scrubberFill.style.width = `${pct}%`;
    this.currentTimeEl.textContent = this.formatTime(cur);
    this.totalTimeEl.textContent = this.formatTime(dur);
  }

  handleNarrationEnded() {
    this.setAudioPlayingState(false);
    // After narration, give a soft haptic pulse signaling that reflection time begins
    this.triggerHaptic("gentle");
  }

  goToPreviousCheckpoint() {
    if (this.currentStepIndex > 0) {
      this.loadCheckpoint(this.currentStepIndex - 1, true);
    }
  }

  goToNextCheckpoint() {
    if (!this.walkData) return;
    if (this.currentStepIndex < this.walkData.checkpoints.length - 1) {
      this.loadCheckpoint(this.currentStepIndex + 1, true);
    } else {
      this.finishWalk();
    }
  }

  // ============================================================================
  // HAPTIC FEEDBACK & POCKET MODE
  // ============================================================================
  triggerHaptic(type = "pulse") {
    if (!("vibrate" in navigator)) return;
    try {
      if (type === "double") {
        navigator.vibrate([100, 75, 100]);
      } else if (type === "gentle") {
        navigator.vibrate([60]);
      } else {
        navigator.vibrate([150]);
      }
    } catch (e) {}
  }

  enterPocketMode() {
    this.pocketOverlay.classList.remove("hidden");
  }

  exitPocketMode() {
    this.pocketOverlay.classList.add("hidden");
  }

  // ============================================================================
  // MEDIASESSION (EARBUDS & LOCK-SCREEN CONTROLS)
  // ============================================================================
  setupMediaSession() {
    if (!("mediaSession" in navigator)) return;

    try {
      navigator.mediaSession.setActionHandler("play", () => this.resumeAudioPlayback());
      navigator.mediaSession.setActionHandler("pause", () => this.pauseAudioPlayback());
      navigator.mediaSession.setActionHandler("previoustrack", () => this.goToPreviousCheckpoint());
      navigator.mediaSession.setActionHandler("nexttrack", () => this.goToNextCheckpoint());
    } catch (e) {
      console.warn("MediaSession handler setup failed:", e);
    }
  }

  updateMediaSessionMetadata(checkpoint) {
    if (!("mediaSession" in navigator)) return;
    try {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: `${checkpoint.title}`,
        artist: `TactileTrail • ${checkpoint.sense.toUpperCase()}`,
        album: `Zero-Screen Audio Naturalist`,
        artwork: [
          { src: "https://images.unsplash.com/photo-1448375240586-882707db888b?w=512&q=80", sizes: "512x512", type: "image/jpeg" }
        ]
      });
    } catch (e) {}
  }

  // ============================================================================
  // POST-WALK REFLECTION & FIELD JOURNAL
  // ============================================================================
  finishWalk() {
    this.stopAudioPlayback();
    this.soundscape.stop();
    this.exitPocketMode();

    const elapsedMinutes = this.walkStartTime 
      ? Math.max(1, Math.round((new Date() - this.walkStartTime) / 60000))
      : 8;

    this.statSenses.textContent = this.walkData.checkpoints.length;
    this.statMinutes.textContent = `${elapsedMinutes}m`;
    this.statAiModel.textContent = this.walkData.is_offline ? "Gemma Edge" : "Gemma 2";

    // Populate Recap
    this.recapList.innerHTML = "";
    const senseIcons = { touch: "🖐️", sound: "👂", observation: "👁️", reflection: "🧘" };
    this.walkData.checkpoints.forEach((cp) => {
      const row = document.createElement("div");
      row.className = "recap-row";
      row.innerHTML = `
        <span class="recap-row-emoji">${senseIcons[cp.sense] || "🌿"}</span>
        <div>
          <strong>${cp.title}</strong>
          <small style="display:block; opacity:0.8;">${cp.invitation}</small>
        </div>
      `;
      this.recapList.appendChild(row);
    });

    if (this.walkData.quote) {
      this.natureQuoteText.textContent = `"${this.walkData.quote}"`;
    }

    this.switchView("view-reflection");
    this.triggerHaptic("double");
  }

  async saveJournalEntry() {
    const notes = this.reflectionText.value.trim();
    const entry = {
      walk_id: `walk_${Date.now()}`,
      environment: this.walkData.environment,
      date: new Date().toLocaleDateString(),
      duration_minutes: parseInt(this.statMinutes.textContent) || 8,
      reflection_notes: notes,
      checkpoints_completed: this.walkData.checkpoints.length,
      photo_data_url: this.specimenPhotoDataUrl
    };

    // Save to browser LocalStorage for offline resilience
    const existing = JSON.parse(localStorage.getItem("tactile_trail_journal") || "[]");
    existing.unshift(entry);
    localStorage.setItem("tactile_trail_journal", JSON.stringify(existing));

    // Also attempt backend backup
    try {
      await fetch("/api/journal/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(entry)
      });
    } catch (e) {}

    alert("🌿 Field Journal saved! Your observation is preserved in your offline notebook.");
  }

  shareWalkSummary() {
    const env = this.walkData.environment.toUpperCase();
    const count = this.walkData.checkpoints.length;
    const text = `🌿 Just completed a Zero-Screen Sensory Walk on TactileTrail!
Biome: ${env}
Checkpoints: ${count} sensory micro-quests (Touch, Sound, Observation)
Mindful Time: ${this.statMinutes.textContent}
AI Naturalist: ${this.walkData.model_name}
#TouchGrass #Hacktoberfest #Gemma #TactileTrail`;

    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => {
        alert("📋 Walk summary copied to clipboard! Share your outdoor journey with your community.");
      });
    } else {
      alert(text);
    }
  }

  resetToSetup() {
    this.stopAudioPlayback();
    this.soundscape.stop();
    this.walkData = null;
    this.specimenPhotoDataUrl = null;
    this.photoPreviewImg.src = "";
    this.photoPreviewContainer.classList.add("hidden");
    this.photoPlaceholder.classList.remove("hidden");
    this.reflectionText.value = "";
    this.switchView("view-setup");
  }

  formatTime(seconds) {
    const s = Math.floor(seconds || 0);
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return `${m}:${rem < 10 ? "0" : ""}${rem}`;
  }
}

// Instantiate on DOMContentLoaded
window.addEventListener("DOMContentLoaded", () => {
  window.app = new TactileTrailApp();
});
