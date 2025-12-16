/**
 * USS Cobia (SS-245) - Gulf of Thailand Submarine Battle
 * May 14, 1945
 * 
 * A historically-accurate recreation of the fateful attack
 */

// ==================== SOUND MANAGER ====================

const SoundManager = {
    audioCtx: null,
    enabled: true,
    masterVolume: 0.5,
    
    init() {
        try {
            this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.log('Web Audio API not supported');
            this.enabled = false;
        }
    },
    
    resume() {
        if (this.audioCtx && this.audioCtx.state === 'suspended') {
            this.audioCtx.resume();
        }
    },
    
    // Sonar ping - classic submarine sound
    playSonarPing() {
        if (!this.enabled || !this.audioCtx) return;
        this.resume();
        
        const ctx = this.audioCtx;
        const now = ctx.currentTime;
        
        // Main ping oscillator
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        
        osc.type = 'sine';
        osc.frequency.setValueAtTime(1500, now);
        osc.frequency.exponentialRampToValueAtTime(800, now + 0.15);
        
        gain.gain.setValueAtTime(0.3 * this.masterVolume, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.8);
        
        osc.connect(gain);
        gain.connect(ctx.destination);
        
        osc.start(now);
        osc.stop(now + 0.8);
    },
    
    // Depth charge explosion - deep boom
    playDepthCharge() {
        if (!this.enabled || !this.audioCtx) return;
        this.resume();
        
        const ctx = this.audioCtx;
        const now = ctx.currentTime;
        
        // Low frequency boom
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        const filter = ctx.createBiquadFilter();
        
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(80, now);
        osc.frequency.exponentialRampToValueAtTime(30, now + 0.5);
        
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(200, now);
        filter.frequency.exponentialRampToValueAtTime(50, now + 0.5);
        
        gain.gain.setValueAtTime(0.8 * this.masterVolume, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.8);
        
        osc.connect(filter);
        filter.connect(gain);
        gain.connect(ctx.destination);
        
        osc.start(now);
        osc.stop(now + 0.8);
        
        // Add noise burst for explosion
        const bufferSize = ctx.sampleRate * 0.5;
        const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const output = noiseBuffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            output[i] = Math.random() * 2 - 1;
        }
        
        const noise = ctx.createBufferSource();
        const noiseGain = ctx.createGain();
        const noiseFilter = ctx.createBiquadFilter();
        
        noise.buffer = noiseBuffer;
        noiseFilter.type = 'lowpass';
        noiseFilter.frequency.setValueAtTime(300, now);
        noiseFilter.frequency.exponentialRampToValueAtTime(80, now + 0.4);
        
        noiseGain.gain.setValueAtTime(0.5 * this.masterVolume, now);
        noiseGain.gain.exponentialRampToValueAtTime(0.01, now + 0.5);
        
        noise.connect(noiseFilter);
        noiseFilter.connect(noiseGain);
        noiseGain.connect(ctx.destination);
        
        noise.start(now);
        noise.stop(now + 0.5);
    },
    
    // Close depth charge - louder, more intense
    playCloseDepthCharge() {
        if (!this.enabled || !this.audioCtx) return;
        this.resume();
        
        const ctx = this.audioCtx;
        const now = ctx.currentTime;
        
        // Very low frequency impact
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        
        osc.type = 'sine';
        osc.frequency.setValueAtTime(60, now);
        osc.frequency.exponentialRampToValueAtTime(20, now + 0.8);
        
        gain.gain.setValueAtTime(1.0 * this.masterVolume, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 1.0);
        
        osc.connect(gain);
        gain.connect(ctx.destination);
        
        osc.start(now);
        osc.stop(now + 1.0);
        
        // Loud noise burst
        const bufferSize = ctx.sampleRate * 0.8;
        const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const output = noiseBuffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            output[i] = Math.random() * 2 - 1;
        }
        
        const noise = ctx.createBufferSource();
        const noiseGain = ctx.createGain();
        const noiseFilter = ctx.createBiquadFilter();
        
        noise.buffer = noiseBuffer;
        noiseFilter.type = 'lowpass';
        noiseFilter.frequency.setValueAtTime(400, now);
        noiseFilter.frequency.exponentialRampToValueAtTime(60, now + 0.6);
        
        noiseGain.gain.setValueAtTime(0.7 * this.masterVolume, now);
        noiseGain.gain.exponentialRampToValueAtTime(0.01, now + 0.7);
        
        noise.connect(noiseFilter);
        noiseFilter.connect(noiseGain);
        noiseGain.connect(ctx.destination);
        
        noise.start(now);
        noise.stop(now + 0.8);
    },
    
    // Torpedo launch - whoosh
    playTorpedoLaunch() {
        if (!this.enabled || !this.audioCtx) return;
        this.resume();
        
        const ctx = this.audioCtx;
        const now = ctx.currentTime;
        
        // Compressed air whoosh
        const bufferSize = ctx.sampleRate * 0.6;
        const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const output = noiseBuffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            output[i] = Math.random() * 2 - 1;
        }
        
        const noise = ctx.createBufferSource();
        const noiseGain = ctx.createGain();
        const filter = ctx.createBiquadFilter();
        
        noise.buffer = noiseBuffer;
        filter.type = 'bandpass';
        filter.frequency.setValueAtTime(2000, now);
        filter.frequency.exponentialRampToValueAtTime(500, now + 0.4);
        filter.Q.value = 2;
        
        noiseGain.gain.setValueAtTime(0.4 * this.masterVolume, now);
        noiseGain.gain.exponentialRampToValueAtTime(0.01, now + 0.5);
        
        noise.connect(filter);
        filter.connect(noiseGain);
        noiseGain.connect(ctx.destination);
        
        noise.start(now);
        noise.stop(now + 0.6);
    },
    
    // Hull creak - stress sound
    playHullCreak() {
        if (!this.enabled || !this.audioCtx) return;
        this.resume();
        
        const ctx = this.audioCtx;
        const now = ctx.currentTime;
        
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        
        osc.type = 'sine';
        // Random low frequency groan
        const baseFreq = 80 + Math.random() * 40;
        osc.frequency.setValueAtTime(baseFreq, now);
        osc.frequency.linearRampToValueAtTime(baseFreq * 0.8, now + 0.3);
        
        gain.gain.setValueAtTime(0.15 * this.masterVolume, now);
        gain.gain.linearRampToValueAtTime(0.2 * this.masterVolume, now + 0.1);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.4);
        
        osc.connect(gain);
        gain.connect(ctx.destination);
        
        osc.start(now);
        osc.stop(now + 0.4);
    },
    
    // Propeller/screws passing overhead
    playPropellerPass() {
        if (!this.enabled || !this.audioCtx) return;
        this.resume();
        
        const ctx = this.audioCtx;
        const now = ctx.currentTime;
        
        // Rhythmic prop noise
        const bufferSize = ctx.sampleRate * 2;
        const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const output = noiseBuffer.getChannelData(0);
        
        // Create pulsing prop sound
        for (let i = 0; i < bufferSize; i++) {
            const t = i / ctx.sampleRate;
            const pulse = Math.sin(t * 15 * Math.PI * 2) * 0.5 + 0.5; // ~15 Hz pulsing
            output[i] = (Math.random() * 2 - 1) * pulse;
        }
        
        const noise = ctx.createBufferSource();
        const noiseGain = ctx.createGain();
        const filter = ctx.createBiquadFilter();
        
        noise.buffer = noiseBuffer;
        filter.type = 'lowpass';
        filter.frequency.value = 400;
        
        noiseGain.gain.setValueAtTime(0.01, now);
        noiseGain.gain.linearRampToValueAtTime(0.25 * this.masterVolume, now + 0.5);
        noiseGain.gain.linearRampToValueAtTime(0.25 * this.masterVolume, now + 1.5);
        noiseGain.gain.exponentialRampToValueAtTime(0.01, now + 2.0);
        
        noise.connect(filter);
        filter.connect(noiseGain);
        noiseGain.connect(ctx.destination);
        
        noise.start(now);
        noise.stop(now + 2.0);
    },
    
    // Ambient submarine hum
    ambientSource: null,
    ambientGain: null,
    
    startAmbient() {
        if (!this.enabled || !this.audioCtx || this.ambientSource) return;
        this.resume();
        
        const ctx = this.audioCtx;
        
        // Low frequency hum
        this.ambientSource = ctx.createOscillator();
        this.ambientGain = ctx.createGain();
        const filter = ctx.createBiquadFilter();
        
        this.ambientSource.type = 'sine';
        this.ambientSource.frequency.value = 60;
        
        filter.type = 'lowpass';
        filter.frequency.value = 100;
        
        this.ambientGain.gain.value = 0.08 * this.masterVolume;
        
        this.ambientSource.connect(filter);
        filter.connect(this.ambientGain);
        this.ambientGain.connect(ctx.destination);
        
        this.ambientSource.start();
    },
    
    stopAmbient() {
        if (this.ambientSource) {
            this.ambientSource.stop();
            this.ambientSource = null;
        }
    },
    
    setAmbientVolume(vol) {
        if (this.ambientGain) {
            this.ambientGain.gain.value = vol * 0.08 * this.masterVolume;
        }
    }
};

// ==================== GAME STATE ====================

const GameState = {
    phase: 'title',
    time: 638, // Military time, starts at 0638
    
    // Cobia state
    cobia: {
        x: 0,
        y: 0,
        course: 120,    // Heading directly toward target (target at bearing 120°)
        speed: 8,       // knots (FULL speed for visible movement)
        depth: 60,      // feet
        targetDepth: 60
    },
    
    // Convoy state
    convoy: {
        baseCourse: 250,
        currentCourse: 250,
        speed: 9.5,
        zigzagTimer: 0,
        zigzagDirection: 1,
        zigzagAngle: 30
    },
    
    // Target ships (relative to convoy center)
    tottoriMaru: {
        x: 0,
        y: 0,
        type: 'freighter',
        sunk: false,
        health: 100
    },
    yaeyama: {
        x: 0,
        y: 0,
        patrolAngle: 0,
        type: 'escort',
        distracted: false,  // True when chasing Cobia
        distractedTime: 0   // How long distracted
    },
    
    // Allied submarine - USS Hammerhead (SS-364)
    hammerhead: {
        x: 0,
        y: 0,
        course: 0,
        speed: 0,
        state: 'waiting',  // waiting, approaching, attacking, withdrawing
        attackReady: false,
        torpedoesFired: false
    },
    
    // Torpedo state
    torpedoes: {
        tubes: [true, true, true, true, true, true], // 6 forward tubes
        fired: [],
        gyroError: 0
    },
    
    // Depth charge state
    depthCharging: {
        totalCharges: 0,
        attackRuns: 0,
        maxRuns: 8,
        nextAttackTime: 0,
        chargesInWater: []
    },
    
    // Damage state
    damage: {
        forward: 0,
        control: 0,
        engine: 0,
        aft: 0,
        hull: 100,
        tdcOperational: true,
        tubesOperational: true,
        motorsOperational: true,
        sternGlandsOperational: true
    },
    
    // Resources
    resources: {
        battery: 100,
        oxygen: 100,
        timeSubmerged: 0
    },
    
    // Detection
    detected: false,
    silentRunning: false,
    
    // Attack phase
    periscopeBearing: 120,
    miscommunicationTriggered: false,
    attackTarget: 'escort',
    
    // Tactical tracking
    initialRange: 8000,
    currentRange: 8000,
    bearing: 120,
    
    // Game over
    gameOver: false,
    survived: false
};

// ==================== CONSTANTS ====================

const SCALE = 0.015; // yards to pixels
const YARD_PER_KNOT_PER_SECOND = 0.5; // Simplified movement rate
const WATER_DEPTH = 145;
const THERMOCLINE_DEPTH = 60;

// ==================== CANVAS CONTEXTS ====================

let radarCtx, tacticalCtx, periscopeCtx, depthChargeCtx;
let gameLoop;
let lastTime = 0;

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    initializeCanvases();
    initializeControls();
    setupEventListeners();
    SoundManager.init();
});

function initializeCanvases() {
    const radarCanvas = document.getElementById('radar-canvas');
    const tacticalCanvas = document.getElementById('tactical-canvas');
    const periscopeCanvas = document.getElementById('periscope-canvas');
    const depthChargeCanvas = document.getElementById('depth-charge-canvas');
    
    if (radarCanvas) radarCtx = radarCanvas.getContext('2d');
    if (tacticalCanvas) tacticalCtx = tacticalCanvas.getContext('2d');
    if (periscopeCanvas) periscopeCtx = periscopeCanvas.getContext('2d');
    if (depthChargeCanvas) depthChargeCtx = depthChargeCanvas.getContext('2d');
}

function initializeControls() {
    // Course dial controls
    document.querySelectorAll('.dial-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const control = e.target.dataset.control;
            const dir = parseInt(e.target.dataset.dir);
            if (control === 'course') {
                GameState.cobia.course = (GameState.cobia.course + dir + 360) % 360;
                document.getElementById('course-display').textContent = 
                    GameState.cobia.course.toString().padStart(3, '0');
            }
        });
    });
    
    // Speed buttons
    document.querySelectorAll('.speed-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            GameState.cobia.speed = parseInt(e.target.dataset.speed);
        });
    });
    
    // Depth buttons
    document.querySelectorAll('.depth-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.depth-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            GameState.cobia.targetDepth = parseInt(e.target.dataset.depth);
        });
    });
    
    // Periscope controls
    const scopeLeft = document.getElementById('scope-left');
    const scopeRight = document.getElementById('scope-right');
    if (scopeLeft) {
        scopeLeft.addEventListener('click', () => {
            GameState.periscopeBearing = (GameState.periscopeBearing - 5 + 360) % 360;
            updatePeriscopeBearing();
        });
    }
    if (scopeRight) {
        scopeRight.addEventListener('click', () => {
            GameState.periscopeBearing = (GameState.periscopeBearing + 5) % 360;
            updatePeriscopeBearing();
        });
    }
    
    // Evasion controls
    document.querySelectorAll('.evasion-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.target.dataset.action || e.target.closest('.evasion-btn').dataset.action;
            handleEvasionAction(action);
        });
    });
}

function setupEventListeners() {
    document.getElementById('start-btn')?.addEventListener('click', startGame);
    document.getElementById('attack-btn')?.addEventListener('click', transitionToPhase2);
    document.getElementById('fire-btn')?.addEventListener('click', fireTorpedoes);
    document.getElementById('replay-btn')?.addEventListener('click', resetGame);
    
    // Sound toggle
    document.getElementById('sound-toggle')?.addEventListener('click', (e) => {
        SoundManager.enabled = !SoundManager.enabled;
        const btn = e.target;
        if (SoundManager.enabled) {
            btn.textContent = '🔊 SOUND ON';
            btn.classList.remove('muted');
        } else {
            btn.textContent = '🔇 SOUND OFF';
            btn.classList.add('muted');
            SoundManager.stopAmbient();
        }
    });
    
    // Target selection
    document.getElementById('attack-target')?.addEventListener('change', (e) => {
        GameState.attackTarget = e.target.value;
    });
}

// ==================== SCREEN MANAGEMENT ====================

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId)?.classList.add('active');
}

function startGame() {
    resetGameState();
    GameState.phase = 'approach';
    showScreen('phase1-screen');
    
    // Initialize positions
    initializePositions();
    
    // Initialize UI displays
    document.getElementById('course-display').textContent = 
        GameState.cobia.course.toString().padStart(3, '0');
    
    // Set correct speed button as active
    document.querySelectorAll('.speed-btn').forEach(btn => {
        btn.classList.remove('active');
        if (parseInt(btn.dataset.speed) === GameState.cobia.speed) {
            btn.classList.add('active');
        }
    });
    
    // Start game loop
    lastTime = performance.now();
    gameLoop = requestAnimationFrame(update);
    
    addLogEntry('phase1-log', '0638 - Submerging to periscope depth. Beginning approach.');
}

function initializePositions() {
    // Cobia starts at origin
    GameState.cobia.x = 0;
    GameState.cobia.y = 0;
    
    // Convoy is 8,000 yards away at bearing 120
    const bearingRad = (GameState.bearing - 90) * Math.PI / 180;
    const convoyDist = GameState.initialRange;
    
    // Convoy center position
    GameState.tottoriMaru.x = Math.cos(bearingRad) * convoyDist;
    GameState.tottoriMaru.y = Math.sin(bearingRad) * convoyDist;
    GameState.tottoriMaru.sunk = false;
    GameState.tottoriMaru.health = 100;
    
    // Yaeyama patrols on starboard bow of freighter
    GameState.yaeyama.patrolAngle = 0;
    GameState.yaeyama.distracted = false;
    GameState.yaeyama.distractedTime = 0;
    updateEscortPosition();
    
    // Hammerhead starts on opposite side of convoy (bearing ~240° from convoy)
    // She's about 6,000 yards from the convoy, waiting
    const hhBearing = (240 - 90) * Math.PI / 180;
    const hhDist = 6000;
    GameState.hammerhead.x = GameState.tottoriMaru.x + Math.cos(hhBearing) * hhDist;
    GameState.hammerhead.y = GameState.tottoriMaru.y + Math.sin(hhBearing) * hhDist;
    GameState.hammerhead.course = 60; // Pointing toward convoy
    GameState.hammerhead.speed = 0;
    GameState.hammerhead.state = 'waiting';
    GameState.hammerhead.attackReady = false;
    GameState.hammerhead.torpedoesFired = false;
}

function updateEscortPosition() {
    // Escort patrols 1000 yards ahead and to starboard of freighter
    const patrolRadius = 1500;
    const baseAngle = (GameState.convoy.currentCourse - 90) * Math.PI / 180;
    const patrolOffset = GameState.yaeyama.patrolAngle * Math.PI / 180;
    
    GameState.yaeyama.x = GameState.tottoriMaru.x + Math.cos(baseAngle + patrolOffset) * patrolRadius;
    GameState.yaeyama.y = GameState.tottoriMaru.y + Math.sin(baseAngle + patrolOffset) * patrolRadius;
}

// ==================== MAIN GAME LOOP ====================

function update(timestamp) {
    const deltaTime = (timestamp - lastTime) / 1000;
    lastTime = timestamp;
    
    if (GameState.gameOver) return;
    
    switch (GameState.phase) {
        case 'approach':
            updateApproach(deltaTime);
            renderRadar();
            renderTactical();
            break;
        case 'attack':
            updateAttack(deltaTime);
            renderPeriscope();
            break;
        case 'depthcharge':
            updateDepthCharge(deltaTime);
            renderDepthCharge();
            break;
    }
    
    updateDepthGauge();
    
    gameLoop = requestAnimationFrame(update);
}

// ==================== PHASE 1: APPROACH ====================

function updateApproach(deltaTime) {
    // Update game time
    GameState.time += deltaTime * 10; // Accelerated time
    updateGameTime('phase1-time');
    
    // Move Cobia (speed multiplied for gameplay pacing)
    const cobiaRad = (GameState.cobia.course - 90) * Math.PI / 180;
    const cobiaSpeed = GameState.cobia.speed * YARD_PER_KNOT_PER_SECOND * deltaTime * 200;
    GameState.cobia.x += Math.cos(cobiaRad) * cobiaSpeed;
    GameState.cobia.y += Math.sin(cobiaRad) * cobiaSpeed;
    
    // Move convoy
    updateConvoy(deltaTime);
    
    // Adjust depth
    if (GameState.cobia.depth !== GameState.cobia.targetDepth) {
        const depthChange = Math.sign(GameState.cobia.targetDepth - GameState.cobia.depth) * 10 * deltaTime;
        GameState.cobia.depth += depthChange;
        if (Math.abs(GameState.cobia.depth - GameState.cobia.targetDepth) < 1) {
            GameState.cobia.depth = GameState.cobia.targetDepth;
        }
    }
    
    // Calculate range and bearing to target
    const dx = GameState.tottoriMaru.x - GameState.cobia.x;
    const dy = GameState.tottoriMaru.y - GameState.cobia.y;
    GameState.currentRange = Math.sqrt(dx * dx + dy * dy);
    GameState.bearing = (Math.atan2(dy, dx) * 180 / Math.PI + 90 + 360) % 360;
    
    // Update displays
    updateTargetData();
    
    // Check if in attack position (historical attack was at 2,700 yards)
    const attackBtn = document.getElementById('attack-btn');
    if (GameState.currentRange < 10000 && GameState.currentRange > 1500) {
        attackBtn.disabled = false;
        if (!GameState.attackPositionReached) {
            GameState.attackPositionReached = true;
            addLogEntry('phase1-log', `${formatTime(GameState.time)} - Attack position reached. Range ${Math.round(GameState.currentRange)} yards.`);
        }
    } else if (GameState.currentRange >= 10000) {
        attackBtn.disabled = true;
    }
    
    // Escort patrol angle
    GameState.yaeyama.patrolAngle = Math.sin(performance.now() / 5000) * 45;
    updateEscortPosition();
    
    // Update Hammerhead AI
    updateHammerhead(deltaTime);
}

function updateHammerhead(deltaTime) {
    const hh = GameState.hammerhead;
    const escort = GameState.yaeyama;
    const target = GameState.tottoriMaru;
    
    if (target.sunk) return; // Mission complete
    
    // Calculate distances
    const dxToTarget = target.x - hh.x;
    const dyToTarget = target.y - hh.y;
    const rangeToTarget = Math.sqrt(dxToTarget * dxToTarget + dyToTarget * dyToTarget);
    
    const dxToEscort = escort.x - hh.x;
    const dyToEscort = escort.y - hh.y;
    const rangeToEscort = Math.sqrt(dxToEscort * dxToEscort + dyToEscort * dyToEscort);
    
    // Calculate escort's distance to Cobia (is escort distracted?)
    const dxEscortCobia = GameState.cobia.x - escort.x;
    const dyEscortCobia = GameState.cobia.y - escort.y;
    const escortToCobiaRange = Math.sqrt(dxEscortCobia * dxEscortCobia + dyEscortCobia * dyEscortCobia);
    
    // Escort is distracted if it's chasing Cobia (close and Cobia detected)
    const escortDistracted = escortToCobiaRange < 5000 && GameState.detected;
    GameState.yaeyama.distracted = escortDistracted;
    
    if (escortDistracted) {
        GameState.yaeyama.distractedTime += deltaTime;
    } else {
        GameState.yaeyama.distractedTime = Math.max(0, GameState.yaeyama.distractedTime - deltaTime * 0.5);
    }
    
    // Hammerhead state machine
    switch (hh.state) {
        case 'waiting':
            hh.speed = 0;
            // If escort is distracted for at least 30 seconds, start approach
            if (GameState.yaeyama.distractedTime > 30 && rangeToEscort > 4000) {
                hh.state = 'approaching';
                addLogEntry('phase1-log', `${formatTime(GameState.time)} - HAMMERHEAD reports: "Escort distracted. Beginning approach."`, 'warning');
            }
            break;
            
        case 'approaching':
            // Move toward target
            hh.course = (Math.atan2(dyToTarget, dxToTarget) * 180 / Math.PI + 90 + 360) % 360;
            hh.speed = 6; // Slow approach
            
            // Move Hammerhead
            const hhRad = (hh.course - 90) * Math.PI / 180;
            const hhSpeed = hh.speed * 0.5 * deltaTime * 200;
            hh.x += Math.cos(hhRad) * hhSpeed;
            hh.y += Math.sin(hhRad) * hhSpeed;
            
            // If escort returns, withdraw
            if (!escortDistracted && rangeToEscort < 5000) {
                hh.state = 'withdrawing';
                addLogEntry('phase1-log', `${formatTime(GameState.time)} - HAMMERHEAD: "Escort returning! Withdrawing."`, 'warning');
            }
            
            // If in attack range, attack!
            if (rangeToTarget < 3000 && rangeToEscort > 4000) {
                hh.state = 'attacking';
                addLogEntry('phase1-log', `${formatTime(GameState.time)} - HAMMERHEAD: "In position! Firing torpedoes!"`, 'warning');
            }
            break;
            
        case 'attacking':
            if (!hh.torpedoesFired) {
                hh.torpedoesFired = true;
                // Play torpedo sounds
                SoundManager.playTorpedoLaunch();
                setTimeout(() => SoundManager.playTorpedoLaunch(), 400);
                
                // Determine if torpedo is a dud (historically ~30% dud rate for US torpedoes)
                const isDud = Math.random() < 0.4; // 40% chance of dud
                
                // Torpedoes hit after delay
                setTimeout(() => {
                    if (isDud) {
                        // DUD! Torpedo hits but doesn't explode
                        GameState.hammerhead.torpedoDud = true;
                        
                        const logId = GameState.phase === 'depthcharge' ? 'phase3-log' : 'phase1-log';
                        addLogEntry(logId, `${formatTime(GameState.time)} - HAMMERHEAD: "Torpedo impact... NO DETONATION! It's a dud!"`, 'danger');
                        
                        // Alert the convoy - Yaeyama breaks off attack on Cobia
                        setTimeout(() => {
                            addLogEntry(logId, `${formatTime(GameState.time)} - Sound reports: Escort screws increasing speed, moving away!`, 'warning');
                            
                            if (GameState.phase === 'depthcharge') {
                                // Yaeyama returns to protect the freighter
                                addLogEntry(logId, `${formatTime(GameState.time)} - YAEYAMA BREAKING OFF ATTACK! Returning to convoy!`, 'warning');
                                GameState.yaeyama.distracted = false;
                                GameState.depthCharging.escortDeparted = true;
                                
                                // End depth charging - Cobia survives!
                                setTimeout(() => {
                                    endGameDudSurvival();
                                }, 3000);
                            }
                        }, 2000);
                    } else {
                        // DIRECT HIT! Freighter sinking
                        if (!target.sunk) {
                            target.sunk = true;
                            target.health = 0;
                            
                            const logId = GameState.phase === 'depthcharge' ? 'phase3-log' : 'phase1-log';
                            addLogEntry(logId, `${formatTime(GameState.time)} - HAMMERHEAD: "TORPEDO HIT! TOTTORI MARU IS SINKING!"`, 'danger');
                            
                            // Play explosion sound
                            SoundManager.playDepthCharge();
                            
                            // Check for victory
                            setTimeout(() => {
                                if (GameState.phase !== 'end') {
                                    checkVictoryCondition();
                                }
                            }, 2000);
                        }
                    }
                }, 3000);
                
                hh.state = 'withdrawing';
            }
            break;
            
        case 'withdrawing':
            // Move away from convoy
            hh.course = (Math.atan2(-dyToTarget, -dxToTarget) * 180 / Math.PI + 90 + 360) % 360;
            hh.speed = 8;
            
            const hhRad2 = (hh.course - 90) * Math.PI / 180;
            const hhSpeed2 = hh.speed * 0.5 * deltaTime * 200;
            hh.x += Math.cos(hhRad2) * hhSpeed2;
            hh.y += Math.sin(hhRad2) * hhSpeed2;
            
            // If far enough and escort distracted again, can re-approach
            if (rangeToTarget > 8000 && !hh.torpedoesFired) {
                hh.state = 'waiting';
            }
            break;
    }
}

function checkVictoryCondition() {
    if (GameState.tottoriMaru.sunk) {
        // Freighter sunk - victory!
        GameState.gameOver = true;
        GameState.survived = true;
        GameState.freighterSunk = true;
        cancelAnimationFrame(gameLoop);
        SoundManager.stopAmbient();
        showEndScreen(true, 'freighter_sunk');
    }
}

function updateConvoy(deltaTime) {
    // Zigzag timer
    GameState.convoy.zigzagTimer += deltaTime;
    if (GameState.convoy.zigzagTimer > 10) { // Zig every 10 seconds (representing 10 minutes)
        GameState.convoy.zigzagTimer = 0;
        GameState.convoy.zigzagDirection *= -1;
        const newCourse = GameState.convoy.baseCourse + (GameState.convoy.zigzagAngle * GameState.convoy.zigzagDirection);
        GameState.convoy.currentCourse = newCourse;
        addLogEntry('phase1-log', `${formatTime(GameState.time)} - Convoy zigzagging. New course ${Math.round(newCourse)}°T.`, 'warning');
    }
    
    // Move convoy (speed multiplied for gameplay pacing)
    const convoyRad = (GameState.convoy.currentCourse - 90) * Math.PI / 180;
    const convoySpeed = GameState.convoy.speed * YARD_PER_KNOT_PER_SECOND * deltaTime * 200;
    
    GameState.tottoriMaru.x += Math.cos(convoyRad) * convoySpeed;
    GameState.tottoriMaru.y += Math.sin(convoyRad) * convoySpeed;
    
    updateEscortPosition();
}

function updateTargetData() {
    document.getElementById('target-range').textContent = Math.round(GameState.currentRange).toLocaleString();
    document.getElementById('target-bearing').textContent = Math.round(GameState.bearing);
    document.getElementById('target-course').textContent = Math.round(GameState.convoy.currentCourse);
    document.getElementById('target-speed').textContent = GameState.convoy.speed;
    
    // Calculate angle on bow
    const relBearing = (GameState.bearing - GameState.convoy.currentCourse + 360) % 360;
    const aob = relBearing > 180 ? 360 - relBearing : relBearing;
    document.getElementById('target-aob').textContent = Math.round(aob);
    
    document.getElementById('radar-range').textContent = Math.round(GameState.currentRange).toLocaleString();
    document.getElementById('radar-bearing').textContent = Math.round(GameState.bearing);
    document.getElementById('current-depth').textContent = Math.round(GameState.cobia.depth);
    
    // Update Hammerhead status
    const hhStateEl = document.getElementById('hammerhead-state');
    if (hhStateEl) {
        const stateDisplay = {
            'waiting': 'STANDING BY',
            'approaching': 'APPROACHING TARGET',
            'attacking': 'FIRING TORPEDOES!',
            'withdrawing': 'WITHDRAWING'
        };
        hhStateEl.textContent = stateDisplay[GameState.hammerhead.state] || GameState.hammerhead.state.toUpperCase();
        
        // Color the status indicator based on state
        const indicator = document.querySelector('#status-hammerhead .status-indicator');
        if (indicator) {
            if (GameState.hammerhead.state === 'attacking') {
                indicator.style.background = '#d9d94a';
            } else if (GameState.hammerhead.state === 'approaching') {
                indicator.style.background = '#90d94a';
            } else {
                indicator.style.background = '#4a90d9';
            }
        }
    }
}

// ==================== PHASE 2: ATTACK ====================

function transitionToPhase2() {
    GameState.phase = 'attack';
    GameState.time = 735; // 0735
    GameState.cobia.depth = 45; // Periscope depth
    GameState.cobia.targetDepth = 45;
    GameState.periscopeBearing = Math.round(GameState.bearing);
    
    showScreen('phase2-screen');
    updatePeriscopeBearing();
    updateTDC();
    
    addLogEntry('phase2-log', '0735 - Battle stations torpedo. All hands man your stations.');
    
    // Start communications chatter
    setTimeout(() => addCommMessage('Conning tower: "Escort bearing mark!"'), 1000);
    setTimeout(() => addCommMessage('Plot: "Range 2,700 yards, tracking steady."'), 2500);
}

function updateAttack(deltaTime) {
    GameState.time += deltaTime * 5;
    updateGameTime('phase2-time');
    
    // Continue convoy movement
    updateConvoy(deltaTime);
    
    // Recalculate bearing to targets
    const dx = GameState.tottoriMaru.x - GameState.cobia.x;
    const dy = GameState.tottoriMaru.y - GameState.cobia.y;
    GameState.currentRange = Math.sqrt(dx * dx + dy * dy);
    GameState.bearing = (Math.atan2(dy, dx) * 180 / Math.PI + 90 + 360) % 360;
    
    // Check for escort zig
    if (!GameState.escortZigTriggered && GameState.time > 738) {
        GameState.escortZigTriggered = true;
        addCommMessage('Exec: "Escort is zigging! She\'s crossing our bow!"', 'captain');
        addLogEntry('phase2-log', '0738 - Escort Yaeyama zigs across, presenting ideal firing solution.', 'warning');
    }
    
    // Adjust depth
    if (GameState.cobia.depth !== GameState.cobia.targetDepth) {
        const depthChange = Math.sign(GameState.cobia.targetDepth - GameState.cobia.depth) * 15 * deltaTime;
        GameState.cobia.depth += depthChange;
        if (Math.abs(GameState.cobia.depth - GameState.cobia.targetDepth) < 1) {
            GameState.cobia.depth = GameState.cobia.targetDepth;
        }
    }
    
    updateTDC();
    document.getElementById('current-depth-2').textContent = Math.round(GameState.cobia.depth);
    updateDepthMarker('depth-marker-2', GameState.cobia.depth);
}

function updateTDC() {
    const target = GameState.attackTarget === 'escort' ? GameState.yaeyama : GameState.tottoriMaru;
    
    const dx = target.x - GameState.cobia.x;
    const dy = target.y - GameState.cobia.y;
    const range = Math.sqrt(dx * dx + dy * dy);
    const bearing = (Math.atan2(dy, dx) * 180 / Math.PI + 90 + 360) % 360;
    
    // Calculate gyro angle (simplified)
    const trackAngle = (bearing - GameState.convoy.currentCourse + 540) % 360 - 180;
    const gyroAngle = bearing - GameState.cobia.course;
    
    document.getElementById('tdc-bearing').textContent = Math.round(bearing);
    document.getElementById('tdc-range').textContent = Math.round(range).toLocaleString();
    document.getElementById('tdc-course').textContent = Math.round(GameState.convoy.currentCourse);
    document.getElementById('tdc-speed').textContent = GameState.convoy.speed;
    document.getElementById('tdc-gyro').textContent = Math.round(gyroAngle);
    document.getElementById('tdc-track').textContent = Math.round(trackAngle);
    
    // Solution quality
    const solutionEl = document.getElementById('tdc-solution');
    const absGyro = Math.abs(gyroAngle);
    
    if (absGyro < 30 && range < 3000) {
        solutionEl.textContent = 'SOLUTION READY';
        solutionEl.className = 'tdc-solution ready';
    } else if (absGyro > 90) {
        solutionEl.textContent = 'POOR GYRO ANGLE';
        solutionEl.className = 'tdc-solution bad';
    } else {
        solutionEl.textContent = 'CALCULATING...';
        solutionEl.className = 'tdc-solution';
    }
}

function updatePeriscopeBearing() {
    document.getElementById('scope-current-bearing').textContent = 
        GameState.periscopeBearing.toString().padStart(3, '0') + '°';
    document.getElementById('scope-bearing').textContent = 
        'BRG: ' + GameState.periscopeBearing.toString().padStart(3, '0') + '°';
}

function fireTorpedoes() {
    const spread = parseInt(document.getElementById('torpedo-spread').value);
    
    addLogEntry('phase2-log', `${formatTime(GameState.time)} - FIRE! ${spread} torpedoes away!`, 'warning');
    addCommMessage('Captain: "Fire one! Fire two! Fire three!"', 'captain');
    
    // Play torpedo launch sounds (staggered)
    for (let i = 0; i < spread; i++) {
        setTimeout(() => SoundManager.playTorpedoLaunch(), i * 400);
    }
    
    // Mark tubes as fired
    for (let i = 0; i < spread && i < 6; i++) {
        GameState.torpedoes.tubes[i] = false;
        document.querySelectorAll('.tube')[i].classList.remove('ready');
        document.querySelectorAll('.tube')[i].classList.add('fired');
    }
    
    // THE CRITICAL MISCOMMUNICATION
    // Historical: Conning tower talker heard "70 feet" (masthead height) and told diving officer to go to 70 feet depth
    setTimeout(() => {
        addCommMessage('Talker: "Seventy feet!"', 'error');
        addCommMessage('Diving Officer: "Make your depth seven-zero feet!"', 'error');
        GameState.cobia.targetDepth = 70;
        GameState.miscommunicationTriggered = true;
        
        addLogEntry('phase2-log', `${formatTime(GameState.time)} - MISCOMMUNICATION! Diving officer takes boat to 70 feet!`, 'danger');
    }, 1500);
    
    // Periscope dunks at critical moment
    setTimeout(() => {
        addCommMessage('Captain: "What the hell?! I\'ve lost the scope!"', 'captain');
        addLogEntry('phase2-log', `${formatTime(GameState.time)} - Periscope underwater! Lost visual on target!`, 'danger');
    }, 3000);
    
    // Torpedoes broach and are spotted
    setTimeout(() => {
        addCommMessage('Sound: "Torpedoes running hot, straight and normal--"');
        addCommMessage('Sound: "Two fish broaching! They\'ve been spotted!"', 'error');
        addLogEntry('phase2-log', `${formatTime(GameState.time)} - Two torpedoes broach! Escort alerted!`, 'danger');
    }, 4500);
    
    // Escort evades and begins attack
    setTimeout(() => {
        addCommMessage('Sound: "High speed screws! Escort turning toward us!"', 'error');
        addCommMessage('Captain: "All ahead flank! Take her deep! Rig for depth charge!"', 'captain');
        addLogEntry('phase2-log', '0745 - YAEYAMA COMBS TRACKS AND TURNS TO ATTACK!', 'danger');
        
        // Transition to Phase 3
        transitionToPhase3();
    }, 6000);
    
    document.getElementById('fire-btn').disabled = true;
}

function addCommMessage(msg, type = '') {
    const chatter = document.getElementById('comm-chatter');
    const div = document.createElement('div');
    div.className = 'comm-msg ' + type;
    div.textContent = msg;
    chatter.appendChild(div);
    chatter.scrollTop = chatter.scrollHeight;
}

// ==================== PHASE 3: DEPTH CHARGE EVASION ====================

function transitionToPhase3() {
    GameState.phase = 'depthcharge';
    GameState.time = 745;
    GameState.cobia.targetDepth = 148; // Go to bottom
    GameState.detected = true;
    GameState.lastSonarPing = 0; // Track last sonar ping time
    
    showScreen('phase3-screen');
    
    // Start ambient submarine sound
    SoundManager.startAmbient();
    
    addLogEntry('phase3-log', '0745 - Diving to bottom! Depth 145 feet - NO ROOM TO MANEUVER!', 'danger');
    addLogEntry('phase3-log', '0745 - Rigging for depth charge. Rigging for silent running.');
    
    // Schedule first depth charge attack
    GameState.depthCharging.nextAttackTime = GameState.time + 2;
}

function updateDepthCharge(deltaTime) {
    GameState.time += deltaTime * 3; // Slower time progression
    GameState.resources.timeSubmerged += deltaTime;
    updateGameTime('phase3-time');
    
    // Periodic sonar pings (every 4-6 seconds)
    if (!GameState.lastSonarPing) GameState.lastSonarPing = 0;
    GameState.lastSonarPing += deltaTime;
    if (GameState.lastSonarPing > 4 + Math.random() * 2) {
        GameState.lastSonarPing = 0;
        SoundManager.playSonarPing();
    }
    
    // Resource depletion
    GameState.resources.battery -= deltaTime * 0.5;
    GameState.resources.oxygen -= deltaTime * 0.3;
    
    if (GameState.silentRunning) {
        GameState.resources.battery -= deltaTime * 0.1; // Less drain when silent
    }
    
    updateResourceDisplays();
    
    // Depth adjustment
    if (GameState.cobia.depth !== GameState.cobia.targetDepth) {
        const depthChange = Math.sign(GameState.cobia.targetDepth - GameState.cobia.depth) * 20 * deltaTime;
        GameState.cobia.depth += depthChange;
        if (Math.abs(GameState.cobia.depth - GameState.cobia.targetDepth) < 1) {
            GameState.cobia.depth = GameState.cobia.targetDepth;
        }
    }
    
    // Clamp to bottom
    if (GameState.cobia.depth > 148) GameState.cobia.depth = 148;
    
    document.getElementById('current-depth-3').textContent = Math.round(GameState.cobia.depth);
    updateDepthMarker('depth-marker-3', GameState.cobia.depth);
    
    // Depth charge attacks
    if (GameState.time >= GameState.depthCharging.nextAttackTime && 
        GameState.depthCharging.attackRuns < GameState.depthCharging.maxRuns) {
        launchDepthChargeAttack();
    }
    
    // Update depth charges in water
    updateDepthCharges(deltaTime);
    
    // Check for game end
    if (GameState.depthCharging.attackRuns >= GameState.depthCharging.maxRuns && 
        GameState.depthCharging.chargesInWater.length === 0) {
        endGameSurvived();
    }
    
    if (GameState.damage.hull <= 0) {
        endGameSunk();
    }
    
    if (GameState.resources.battery <= 0 || GameState.resources.oxygen <= 0) {
        endGameSunk();
    }
}

function launchDepthChargeAttack() {
    GameState.depthCharging.attackRuns++;
    const runNumber = GameState.depthCharging.attackRuns;
    
    addLogEntry('phase3-log', 
        `${formatTime(GameState.time)} - ATTACK RUN ${runNumber}! Screws passing overhead!`, 'danger');
    
    // Play propeller pass sound
    SoundManager.playPropellerPass();
    
    // Play sonar ping
    setTimeout(() => SoundManager.playSonarPing(), 500);
    
    // Drop 2-3 depth charges per run
    const chargeCount = 2 + Math.floor(Math.random() * 2);
    
    for (let i = 0; i < chargeCount; i++) {
        setTimeout(() => {
            dropDepthCharge();
        }, i * 800);
    }
    
    // Schedule next attack
    const interval = 30 + Math.random() * 30; // 30-60 seconds between runs
    GameState.depthCharging.nextAttackTime = GameState.time + interval;
    
    document.getElementById('attack-count').textContent = runNumber;
}

function dropDepthCharge() {
    GameState.depthCharging.totalCharges++;
    document.getElementById('dc-count').textContent = GameState.depthCharging.totalCharges;
    
    // Calculate escort position (same formula as in render)
    const width = 600; // Canvas width
    const escortPhase = (performance.now() / 3000) % 1;
    const escortDirection = Math.floor(performance.now() / 3000) % 2 === 0 ? 1 : -1;
    const escortX = escortDirection === 1 
        ? width * 0.2 + escortPhase * width * 0.6 
        : width * 0.8 - escortPhase * width * 0.6;
    
    // Depth charge falls from escort position with some spread
    const charge = {
        y: 0, // Start at surface
        targetDepth: 130 + Math.random() * 20, // Set deep "in the mud"
        x: escortX + (Math.random() - 0.5) * 60, // Drop near escort with small spread
        falling: true
    };
    
    GameState.depthCharging.chargesInWater.push(charge);
}

function updateDepthCharges(deltaTime) {
    const toRemove = [];
    
    GameState.depthCharging.chargesInWater.forEach((charge, index) => {
        if (charge.falling) {
            charge.y += deltaTime * 80; // Sinking speed
            
            if (charge.y >= charge.targetDepth) {
                charge.falling = false;
                explodeDepthCharge(charge);
                toRemove.push(index);
            }
        }
    });
    
    // Remove exploded charges
    toRemove.reverse().forEach(i => {
        GameState.depthCharging.chargesInWater.splice(i, 1);
    });
}

function explodeDepthCharge(charge) {
    // Screen shake
    document.getElementById('phase3-screen').classList.add('shake');
    document.getElementById('game-container').classList.add('flash');
    
    setTimeout(() => {
        document.getElementById('phase3-screen').classList.remove('shake');
        document.getElementById('game-container').classList.remove('flash');
    }, 500);
    
    // Calculate damage based on proximity
    const depthDiff = Math.abs(charge.targetDepth - GameState.cobia.depth);
    const proximity = 1 - (depthDiff / 50); // Closer = more damage
    
    if (proximity > 0) {
        const baseDamage = proximity * (10 + Math.random() * 15);
        applyDamage(baseDamage);
    }
    
    // Play explosion sound based on proximity
    if (proximity > 0.7) {
        SoundManager.playCloseDepthCharge();
        addLogEntry('phase3-log', `${formatTime(GameState.time)} - CLOSE! Depth charge exploding nearby!`, 'danger');
        // Hull creak from close explosion
        setTimeout(() => SoundManager.playHullCreak(), 600);
    } else if (proximity > 0.3) {
        SoundManager.playDepthCharge();
        addLogEntry('phase3-log', `${formatTime(GameState.time)} - Depth charge detonation. Checking for damage...`, 'warning');
    } else {
        SoundManager.playDepthCharge();
    }
}

function applyDamage(amount) {
    // Distribute damage across compartments
    const compartments = ['forward', 'control', 'engine', 'aft'];
    const target = compartments[Math.floor(Math.random() * compartments.length)];
    
    GameState.damage[target] += amount * 0.7;
    GameState.damage.hull -= amount * 0.3;
    
    // Cap damage values
    compartments.forEach(c => {
        GameState.damage[c] = Math.min(100, GameState.damage[c]);
    });
    GameState.damage.hull = Math.max(0, GameState.damage.hull);
    
    updateDamageDisplays();
    
    // System failures based on damage
    if (GameState.damage.forward > 60 && GameState.damage.tubesOperational) {
        GameState.damage.tubesOperational = false;
        updateSystemStatus('sys-tubes', 'destroyed');
        addLogEntry('phase3-log', `${formatTime(GameState.time)} - Forward torpedo tubes DISABLED!`, 'danger');
    }
    
    if (GameState.damage.control > 50 && GameState.damage.tdcOperational) {
        GameState.damage.tdcOperational = false;
        updateSystemStatus('sys-tdc', 'destroyed');
        addLogEntry('phase3-log', `${formatTime(GameState.time)} - TDC knocked out!`, 'danger');
    }
    
    if (GameState.damage.aft > 40 && GameState.damage.sternGlandsOperational) {
        GameState.damage.sternGlandsOperational = false;
        updateSystemStatus('sys-stern', 'damaged');
        addLogEntry('phase3-log', `${formatTime(GameState.time)} - Flooding through stern packing glands!`, 'danger');
        // Accelerate hull damage when flooded
        GameState.damage.hull -= 0.5;
    }
}

function handleEvasionAction(action) {
    document.querySelectorAll('.evasion-btn').forEach(b => b.classList.remove('active'));
    
    switch(action) {
        case 'silent':
            GameState.silentRunning = true;
            GameState.cobia.speed = 0;
            document.querySelector('[data-action="silent"]').classList.add('active');
            addLogEntry('phase3-log', `${formatTime(GameState.time)} - Rigged for silent running. All unnecessary equipment secured.`);
            break;
            
        case 'creep':
            GameState.silentRunning = false;
            GameState.cobia.speed = 2;
            document.querySelector('[data-action="creep"]').classList.add('active');
            addLogEntry('phase3-log', `${formatTime(GameState.time)} - Creeping ahead. Attempting to clear datum.`, 'warning');
            // Slight chance of detection
            if (Math.random() < 0.3) {
                addLogEntry('phase3-log', `${formatTime(GameState.time)} - Escort sonar pinging! We may be detected!`, 'danger');
            }
            break;
            
        case 'blow':
            // Emergency surface - desperate move
            GameState.cobia.targetDepth = 0;
            addLogEntry('phase3-log', `${formatTime(GameState.time)} - EMERGENCY BLOW! All ballast tanks!`, 'danger');
            // This would likely result in being sunk by gunfire, but we'll be generous
            endGameSurfaced();
            break;
    }
}

function updateDamageDisplays() {
    document.getElementById('dmg-fwd').style.width = GameState.damage.forward + '%';
    document.getElementById('dmg-ctrl').style.width = GameState.damage.control + '%';
    document.getElementById('dmg-eng').style.width = GameState.damage.engine + '%';
    document.getElementById('dmg-aft').style.width = GameState.damage.aft + '%';
    document.getElementById('dmg-hull').style.width = GameState.damage.hull + '%';
    
    // Color the hull bar based on integrity
    const hullFill = document.getElementById('dmg-hull');
    if (GameState.damage.hull < 30) {
        hullFill.style.background = 'var(--danger-red)';
    } else if (GameState.damage.hull < 60) {
        hullFill.style.background = 'var(--warning-amber)';
    }
}

function updateSystemStatus(elementId, status) {
    const el = document.getElementById(elementId);
    if (el) {
        const indicator = el.querySelector('.system-indicator');
        indicator.className = 'system-indicator ' + status;
    }
}

function updateResourceDisplays() {
    const batteryFill = document.getElementById('battery-fill');
    const o2Fill = document.getElementById('o2-fill');
    
    batteryFill.style.width = GameState.resources.battery + '%';
    o2Fill.style.width = GameState.resources.oxygen + '%';
    
    // Add warning classes
    if (GameState.resources.battery < 30) batteryFill.classList.add('critical');
    else if (GameState.resources.battery < 50) batteryFill.classList.add('low');
    
    if (GameState.resources.oxygen < 30) o2Fill.classList.add('critical');
    else if (GameState.resources.oxygen < 50) o2Fill.classList.add('low');
    
    // Time submerged
    const minutes = Math.floor(GameState.resources.timeSubmerged / 60);
    const seconds = Math.floor(GameState.resources.timeSubmerged % 60);
    document.getElementById('time-submerged').textContent = 
        `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

// ==================== RENDERING ====================

function renderRadar() {
    if (!radarCtx) return;
    
    const canvas = radarCtx.canvas;
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const radius = cx - 10;
    
    // Clear
    radarCtx.fillStyle = '#0a1a0a';
    radarCtx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Range rings
    radarCtx.strokeStyle = 'rgba(57, 255, 20, 0.3)';
    radarCtx.lineWidth = 1;
    for (let i = 1; i <= 4; i++) {
        radarCtx.beginPath();
        radarCtx.arc(cx, cy, (radius / 4) * i, 0, Math.PI * 2);
        radarCtx.stroke();
    }
    
    // Bearing lines
    for (let i = 0; i < 12; i++) {
        const angle = (i * 30 - 90) * Math.PI / 180;
        radarCtx.beginPath();
        radarCtx.moveTo(cx, cy);
        radarCtx.lineTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius);
        radarCtx.stroke();
    }
    
    // Sweep line
    const sweepAngle = (performance.now() / 20) % 360;
    const sweepRad = (sweepAngle - 90) * Math.PI / 180;
    
    const gradient = radarCtx.createLinearGradient(cx, cy, 
        cx + Math.cos(sweepRad) * radius, cy + Math.sin(sweepRad) * radius);
    gradient.addColorStop(0, 'rgba(57, 255, 20, 0.8)');
    gradient.addColorStop(1, 'rgba(57, 255, 20, 0)');
    
    radarCtx.strokeStyle = gradient;
    radarCtx.lineWidth = 2;
    radarCtx.beginPath();
    radarCtx.moveTo(cx, cy);
    radarCtx.lineTo(cx + Math.cos(sweepRad) * radius, cy + Math.sin(sweepRad) * radius);
    radarCtx.stroke();
    
    // Plot contacts
    const maxRange = 25000; // Display range
    const scale = radius / maxRange;
    
    // Tottori Maru
    const dx1 = (GameState.tottoriMaru.x - GameState.cobia.x) * scale;
    const dy1 = (GameState.tottoriMaru.y - GameState.cobia.y) * scale;
    if (Math.sqrt(dx1*dx1 + dy1*dy1) < radius) {
        radarCtx.fillStyle = '#ff3131';
        radarCtx.beginPath();
        radarCtx.arc(cx + dx1, cy + dy1, 4, 0, Math.PI * 2);
        radarCtx.fill();
    }
    
    // Yaeyama
    const dx2 = (GameState.yaeyama.x - GameState.cobia.x) * scale;
    const dy2 = (GameState.yaeyama.y - GameState.cobia.y) * scale;
    if (Math.sqrt(dx2*dx2 + dy2*dy2) < radius) {
        radarCtx.fillStyle = '#ffbf00';
        radarCtx.beginPath();
        radarCtx.arc(cx + dx2, cy + dy2, 3, 0, Math.PI * 2);
        radarCtx.fill();
    }
    
    // Own ship (center)
    radarCtx.fillStyle = '#00ff41';
    radarCtx.beginPath();
    radarCtx.arc(cx, cy, 3, 0, Math.PI * 2);
    radarCtx.fill();
}

function renderTactical() {
    if (!tacticalCtx) return;
    
    const canvas = tacticalCtx.canvas;
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear with ocean color
    tacticalCtx.fillStyle = '#0d2a3d';
    tacticalCtx.fillRect(0, 0, width, height);
    
    // Grid lines (nautical chart style)
    tacticalCtx.strokeStyle = 'rgba(100, 150, 200, 0.2)';
    tacticalCtx.lineWidth = 1;
    
    for (let x = 0; x < width; x += 50) {
        tacticalCtx.beginPath();
        tacticalCtx.moveTo(x, 0);
        tacticalCtx.lineTo(x, height);
        tacticalCtx.stroke();
    }
    for (let y = 0; y < height; y += 50) {
        tacticalCtx.beginPath();
        tacticalCtx.moveTo(0, y);
        tacticalCtx.lineTo(width, y);
        tacticalCtx.stroke();
    }
    
    // Calculate view - center on Cobia so player can see their movement
    const scale = 0.015; // Slightly zoomed out to see more area
    const offsetX = width / 2 - GameState.cobia.x * scale;
    const offsetY = height / 2 - GameState.cobia.y * scale;
    
    // Draw Cobia
    drawShip(tacticalCtx, 
        GameState.cobia.x * scale + offsetX, 
        GameState.cobia.y * scale + offsetY,
        GameState.cobia.course, '#00ff41', 'submarine');
    
    // Draw Tottori Maru
    drawShip(tacticalCtx,
        GameState.tottoriMaru.x * scale + offsetX,
        GameState.tottoriMaru.y * scale + offsetY,
        GameState.convoy.currentCourse, '#ff3131', 'freighter');
    
    // Draw Yaeyama
    drawShip(tacticalCtx,
        GameState.yaeyama.x * scale + offsetX,
        GameState.yaeyama.y * scale + offsetY,
        GameState.convoy.currentCourse, '#ffbf00', 'escort');
    
    // Draw Hammerhead (allied submarine)
    if (!GameState.tottoriMaru.sunk) {
        const hhX = GameState.hammerhead.x * scale + offsetX;
        const hhY = GameState.hammerhead.y * scale + offsetY;
        
        // Different color based on state
        let hhColor = '#4a90d9'; // Blue for waiting
        if (GameState.hammerhead.state === 'approaching') hhColor = '#90d94a'; // Green for approaching
        if (GameState.hammerhead.state === 'attacking') hhColor = '#d9d94a'; // Yellow for attacking
        if (GameState.hammerhead.state === 'withdrawing') hhColor = '#d9904a'; // Orange for withdrawing
        
        drawShip(tacticalCtx, hhX, hhY, GameState.hammerhead.course, hhColor, 'submarine');
        
        // Label
        tacticalCtx.fillStyle = hhColor;
        tacticalCtx.font = '10px VT323, monospace';
        tacticalCtx.textAlign = 'center';
        tacticalCtx.fillText('HAMMERHEAD', hhX, hhY + 20);
        tacticalCtx.fillText(`[${GameState.hammerhead.state.toUpperCase()}]`, hhX, hhY + 30);
        tacticalCtx.textAlign = 'left';
    }
    
    // Draw track history / intended track
    tacticalCtx.setLineDash([5, 5]);
    tacticalCtx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
    tacticalCtx.beginPath();
    const convoyRad = (GameState.convoy.currentCourse - 90) * Math.PI / 180;
    tacticalCtx.moveTo(
        GameState.tottoriMaru.x * scale + offsetX - Math.cos(convoyRad) * 100,
        GameState.tottoriMaru.y * scale + offsetY - Math.sin(convoyRad) * 100
    );
    tacticalCtx.lineTo(
        GameState.tottoriMaru.x * scale + offsetX + Math.cos(convoyRad) * 200,
        GameState.tottoriMaru.y * scale + offsetY + Math.sin(convoyRad) * 200
    );
    tacticalCtx.stroke();
    tacticalCtx.setLineDash([]);
    
    // Range circle around Cobia
    tacticalCtx.strokeStyle = 'rgba(0, 255, 65, 0.3)';
    tacticalCtx.beginPath();
    tacticalCtx.arc(
        GameState.cobia.x * scale + offsetX,
        GameState.cobia.y * scale + offsetY,
        3000 * scale, 0, Math.PI * 2);
    tacticalCtx.stroke();
    
    // Compass rose
    drawCompassRose(tacticalCtx, 50, 50, 30);
    
    // Speed/Course indicator for Cobia
    tacticalCtx.fillStyle = 'rgba(0, 255, 65, 0.9)';
    tacticalCtx.font = '12px Orbitron, monospace';
    tacticalCtx.textAlign = 'right';
    tacticalCtx.fillText(`COBIA: ${GameState.cobia.speed} KTS / HDG ${GameState.cobia.course.toString().padStart(3, '0')}°`, width - 10, 20);
}

function drawShip(ctx, x, y, heading, color, type) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate((heading - 90) * Math.PI / 180);
    
    ctx.fillStyle = color;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    
    if (type === 'submarine') {
        // Heading indicator line (shows direction of travel)
        ctx.strokeStyle = 'rgba(0, 255, 65, 0.5)';
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(60, 0);
        ctx.stroke();
        ctx.setLineDash([]);
        
        // Submarine shape
        ctx.fillStyle = color;
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.ellipse(0, 0, 15, 5, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Bow indicator
        ctx.beginPath();
        ctx.moveTo(15, 0);
        ctx.lineTo(22, 0);
        ctx.stroke();
    } else if (type === 'freighter') {
        // Cargo ship shape
        ctx.beginPath();
        ctx.moveTo(20, 0);
        ctx.lineTo(10, 6);
        ctx.lineTo(-15, 6);
        ctx.lineTo(-20, 0);
        ctx.lineTo(-15, -6);
        ctx.lineTo(10, -6);
        ctx.closePath();
        ctx.fill();
    } else {
        // Escort shape
        ctx.beginPath();
        ctx.moveTo(15, 0);
        ctx.lineTo(5, 4);
        ctx.lineTo(-12, 4);
        ctx.lineTo(-15, 0);
        ctx.lineTo(-12, -4);
        ctx.lineTo(5, -4);
        ctx.closePath();
        ctx.fill();
    }
    
    ctx.restore();
}

function drawCompassRose(ctx, x, y, radius) {
    ctx.save();
    ctx.translate(x, y);
    
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
    ctx.lineWidth = 1;
    
    // Circle
    ctx.beginPath();
    ctx.arc(0, 0, radius, 0, Math.PI * 2);
    ctx.stroke();
    
    // Cardinal points
    ctx.font = '10px Orbitron, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('N', 0, -radius - 8);
    ctx.fillText('S', 0, radius + 8);
    ctx.fillText('E', radius + 8, 0);
    ctx.fillText('W', -radius - 8, 0);
    
    // Lines
    for (let i = 0; i < 8; i++) {
        const angle = (i * 45 - 90) * Math.PI / 180;
        const inner = i % 2 === 0 ? radius * 0.5 : radius * 0.7;
        ctx.beginPath();
        ctx.moveTo(Math.cos(angle) * inner, Math.sin(angle) * inner);
        ctx.lineTo(Math.cos(angle) * radius, Math.sin(angle) * radius);
        ctx.stroke();
    }
    
    ctx.restore();
}

function renderPeriscope() {
    if (!periscopeCtx) return;
    
    const canvas = periscopeCtx.canvas;
    const width = canvas.width;
    const height = canvas.height;
    const horizonY = height * 0.6;
    
    // Sky gradient
    const skyGrad = periscopeCtx.createLinearGradient(0, 0, 0, horizonY);
    skyGrad.addColorStop(0, '#1a3a5c');
    skyGrad.addColorStop(1, '#4a7a9c');
    periscopeCtx.fillStyle = skyGrad;
    periscopeCtx.fillRect(0, 0, width, horizonY);
    
    // Sea gradient
    const seaGrad = periscopeCtx.createLinearGradient(0, horizonY, 0, height);
    seaGrad.addColorStop(0, '#2a5a7a');
    seaGrad.addColorStop(1, '#1a3a5a');
    periscopeCtx.fillStyle = seaGrad;
    periscopeCtx.fillRect(0, horizonY, width, height - horizonY);
    
    // Periscope depth check - if too deep, show water
    if (GameState.cobia.depth > 50) {
        periscopeCtx.fillStyle = 'rgba(0, 40, 60, 0.9)';
        periscopeCtx.fillRect(0, 0, width, height);
        periscopeCtx.fillStyle = '#00ff41';
        periscopeCtx.font = '24px VT323, monospace';
        periscopeCtx.textAlign = 'center';
        periscopeCtx.fillText('PERISCOPE SUBMERGED', width/2, height/2);
        return;
    }
    
    // Waves on horizon
    periscopeCtx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
    periscopeCtx.lineWidth = 1;
    for (let x = 0; x < width; x += 20) {
        const waveOffset = Math.sin((x + performance.now()/50) * 0.05) * 3;
        periscopeCtx.beginPath();
        periscopeCtx.moveTo(x, horizonY + waveOffset);
        periscopeCtx.lineTo(x + 10, horizonY + waveOffset - 2);
        periscopeCtx.stroke();
    }
    
    // Calculate where targets appear in periscope view
    const viewAngle = 40; // Degrees of view
    
    // Draw Tottori Maru
    drawTargetInScope(periscopeCtx, GameState.tottoriMaru, '#555555', width, horizonY, viewAngle, 'freighter');
    
    // Draw Yaeyama
    drawTargetInScope(periscopeCtx, GameState.yaeyama, '#666666', width, horizonY, viewAngle, 'escort');
    
    // Periscope vignette
    const vignetteGrad = periscopeCtx.createRadialGradient(width/2, height/2, height*0.3, width/2, height/2, height*0.7);
    vignetteGrad.addColorStop(0, 'rgba(0,0,0,0)');
    vignetteGrad.addColorStop(1, 'rgba(0,0,0,0.8)');
    periscopeCtx.fillStyle = vignetteGrad;
    periscopeCtx.fillRect(0, 0, width, height);
    
    // Periscope frame (circular mask effect)
    periscopeCtx.strokeStyle = '#000';
    periscopeCtx.lineWidth = 80;
    periscopeCtx.beginPath();
    periscopeCtx.arc(width/2, height/2 - 30, height*0.55, 0, Math.PI * 2);
    periscopeCtx.stroke();
}

function drawTargetInScope(ctx, target, color, width, horizonY, viewAngle, type) {
    const dx = target.x - GameState.cobia.x;
    const dy = target.y - GameState.cobia.y;
    const range = Math.sqrt(dx * dx + dy * dy);
    const bearing = (Math.atan2(dy, dx) * 180 / Math.PI + 90 + 360) % 360;
    
    // Calculate position in view based on bearing relative to periscope bearing
    let relativeBearing = bearing - GameState.periscopeBearing;
    if (relativeBearing > 180) relativeBearing -= 360;
    if (relativeBearing < -180) relativeBearing += 360;
    
    // Only draw if in view
    if (Math.abs(relativeBearing) > viewAngle/2) return;
    
    const xPos = width/2 + (relativeBearing / viewAngle) * width;
    
    // Size based on range
    const size = Math.max(10, 80 - (range / 500));
    
    // Draw ship silhouette
    ctx.fillStyle = color;
    
    if (type === 'freighter') {
        // Cargo ship silhouette
        ctx.beginPath();
        ctx.moveTo(xPos - size, horizonY);
        ctx.lineTo(xPos - size * 0.8, horizonY - size * 0.3);
        ctx.lineTo(xPos - size * 0.3, horizonY - size * 0.3);
        ctx.lineTo(xPos - size * 0.2, horizonY - size * 0.6);
        ctx.lineTo(xPos + size * 0.1, horizonY - size * 0.6);
        ctx.lineTo(xPos + size * 0.2, horizonY - size * 0.3);
        ctx.lineTo(xPos + size * 0.7, horizonY - size * 0.3);
        ctx.lineTo(xPos + size, horizonY);
        ctx.closePath();
        ctx.fill();
    } else {
        // Escort silhouette
        ctx.beginPath();
        ctx.moveTo(xPos - size * 0.8, horizonY);
        ctx.lineTo(xPos - size * 0.6, horizonY - size * 0.25);
        ctx.lineTo(xPos, horizonY - size * 0.25);
        ctx.lineTo(xPos + size * 0.1, horizonY - size * 0.5);
        ctx.lineTo(xPos + size * 0.2, horizonY - size * 0.25);
        ctx.lineTo(xPos + size * 0.6, horizonY - size * 0.2);
        ctx.lineTo(xPos + size * 0.8, horizonY);
        ctx.closePath();
        ctx.fill();
    }
    
    // Update scope data
    if (Math.abs(relativeBearing) < 5) {
        document.getElementById('scope-range').textContent = `RNG: ${Math.round(range)} YDS`;
    }
}

function renderDepthCharge() {
    if (!depthChargeCtx) return;
    
    const canvas = depthChargeCtx.canvas;
    const width = canvas.width;
    const height = canvas.height;
    const surfaceY = 35; // Air/water boundary
    
    // Sky gradient (above water)
    const skyGrad = depthChargeCtx.createLinearGradient(0, 0, 0, surfaceY);
    skyGrad.addColorStop(0, '#2a4a6a');
    skyGrad.addColorStop(1, '#4a7a9a');
    depthChargeCtx.fillStyle = skyGrad;
    depthChargeCtx.fillRect(0, 0, width, surfaceY);
    
    // Ocean gradient (side view - below surface)
    const oceanGrad = depthChargeCtx.createLinearGradient(0, surfaceY, 0, height);
    oceanGrad.addColorStop(0, '#1a5a7e');
    oceanGrad.addColorStop(0.3, '#0a3a5e');
    oceanGrad.addColorStop(1, '#0a1a2e');
    depthChargeCtx.fillStyle = oceanGrad;
    depthChargeCtx.fillRect(0, surfaceY, width, height - surfaceY);
    
    // Water surface line with waves
    depthChargeCtx.strokeStyle = '#6ab4d4';
    depthChargeCtx.lineWidth = 3;
    depthChargeCtx.beginPath();
    depthChargeCtx.moveTo(0, surfaceY);
    for (let x = 0; x < width; x += 10) {
        const waveY = surfaceY + Math.sin((x + performance.now() / 200) * 0.1) * 2;
        depthChargeCtx.lineTo(x, waveY);
    }
    depthChargeCtx.stroke();
    
    // Surface label
    depthChargeCtx.fillStyle = '#6ab4d4';
    depthChargeCtx.font = '10px VT323, monospace';
    depthChargeCtx.fillText('SURFACE', 10, surfaceY - 5);
    
    // Thermocline layer
    const thermoY = surfaceY + (60 / WATER_DEPTH) * (height - surfaceY - 20);
    depthChargeCtx.fillStyle = 'rgba(42, 90, 142, 0.4)';
    depthChargeCtx.fillRect(0, thermoY - 3, width, 6);
    depthChargeCtx.fillStyle = '#2a5a8e';
    depthChargeCtx.font = '10px VT323, monospace';
    depthChargeCtx.fillText('THERMOCLINE 60\'', 10, thermoY - 8);
    
    // Sea floor
    const floorY = height - 25;
    depthChargeCtx.fillStyle = '#3a2a1a';
    depthChargeCtx.fillRect(0, floorY, width, 25);
    depthChargeCtx.fillStyle = '#5a4a3a';
    depthChargeCtx.font = '10px VT323, monospace';
    depthChargeCtx.fillText('BOTTOM 145\'', 10, floorY + 15);
    
    // Mud pattern
    depthChargeCtx.fillStyle = '#2a1a0a';
    for (let x = 0; x < width; x += 40) {
        depthChargeCtx.beginPath();
        depthChargeCtx.arc(x + 20, floorY + 12, 6, 0, Math.PI * 2);
        depthChargeCtx.fill();
    }
    
    // Calculate depth positions (relative to water column, not including sky)
    const waterColumnHeight = floorY - surfaceY;
    const getDepthY = (depth) => surfaceY + (depth / WATER_DEPTH) * waterColumnHeight;
    
    // Draw Yaeyama on surface - moving back and forth during attack
    const escortPhase = (performance.now() / 3000) % 1; // 3 second cycle
    const escortDirection = Math.floor(performance.now() / 3000) % 2 === 0 ? 1 : -1;
    const escortX = escortDirection === 1 
        ? width * 0.2 + escortPhase * width * 0.6 
        : width * 0.8 - escortPhase * width * 0.6;
    
    // Escort hull (side view on surface)
    depthChargeCtx.fillStyle = '#ffbf00';
    depthChargeCtx.beginPath();
    // Hull shape
    depthChargeCtx.moveTo(escortX - 35, surfaceY);
    depthChargeCtx.lineTo(escortX - 30, surfaceY - 8);
    depthChargeCtx.lineTo(escortX + 25, surfaceY - 8);
    depthChargeCtx.lineTo(escortX + 35, surfaceY);
    depthChargeCtx.lineTo(escortX + 30, surfaceY + 5);
    depthChargeCtx.lineTo(escortX - 30, surfaceY + 5);
    depthChargeCtx.closePath();
    depthChargeCtx.fill();
    
    // Superstructure
    depthChargeCtx.fillRect(escortX - 10, surfaceY - 18, 15, 10);
    depthChargeCtx.fillRect(escortX + 5, surfaceY - 14, 5, 6);
    
    // Mast
    depthChargeCtx.strokeStyle = '#ffbf00';
    depthChargeCtx.lineWidth = 2;
    depthChargeCtx.beginPath();
    depthChargeCtx.moveTo(escortX, surfaceY - 18);
    depthChargeCtx.lineTo(escortX, surfaceY - 28);
    depthChargeCtx.stroke();
    
    // Wake behind escort
    depthChargeCtx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
    depthChargeCtx.lineWidth = 1;
    const wakeStartX = escortDirection === 1 ? escortX - 35 : escortX + 35;
    for (let i = 0; i < 3; i++) {
        depthChargeCtx.beginPath();
        depthChargeCtx.moveTo(wakeStartX, surfaceY + 2);
        depthChargeCtx.lineTo(wakeStartX - escortDirection * (30 + i * 20), surfaceY + 5 + i * 3);
        depthChargeCtx.stroke();
    }
    
    // Label
    depthChargeCtx.fillStyle = '#ffbf00';
    depthChargeCtx.font = '11px VT323, monospace';
    depthChargeCtx.textAlign = 'center';
    depthChargeCtx.fillText('YAEYAMA', escortX, surfaceY - 32);
    depthChargeCtx.textAlign = 'left';
    
    // Draw Cobia (side view)
    const subY = getDepthY(GameState.cobia.depth);
    const subX = width / 2;
    
    // Submarine hull
    depthChargeCtx.fillStyle = '#00ff41';
    depthChargeCtx.beginPath();
    depthChargeCtx.ellipse(subX, subY, 50, 12, 0, 0, Math.PI * 2);
    depthChargeCtx.fill();
    
    // Conning tower
    depthChargeCtx.fillRect(subX - 8, subY - 20, 16, 12);
    
    // Bow
    depthChargeCtx.beginPath();
    depthChargeCtx.moveTo(subX + 50, subY);
    depthChargeCtx.lineTo(subX + 60, subY);
    depthChargeCtx.lineWidth = 3;
    depthChargeCtx.strokeStyle = '#00ff41';
    depthChargeCtx.stroke();
    
    // Label
    depthChargeCtx.fillStyle = '#00ff41';
    depthChargeCtx.font = '11px VT323, monospace';
    depthChargeCtx.textAlign = 'center';
    depthChargeCtx.fillText('COBIA', subX, subY + 25);
    depthChargeCtx.textAlign = 'left';
    
    // Draw depth charges falling
    GameState.depthCharging.chargesInWater.forEach(charge => {
        const chargeY = getDepthY(charge.y);
        
        // Depth charge canister
        depthChargeCtx.fillStyle = '#444';
        depthChargeCtx.beginPath();
        depthChargeCtx.ellipse(charge.x, chargeY, 6, 10, 0, 0, Math.PI * 2);
        depthChargeCtx.fill();
        depthChargeCtx.strokeStyle = '#666';
        depthChargeCtx.lineWidth = 1;
        depthChargeCtx.stroke();
        
        // Bubble trail
        depthChargeCtx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        for (let i = 0; i < 6; i++) {
            const bubbleY = chargeY - 12 - i * 8;
            if (bubbleY > surfaceY) {
                depthChargeCtx.beginPath();
                depthChargeCtx.arc(
                    charge.x + (Math.random() - 0.5) * 8, 
                    bubbleY, 
                    1.5 + Math.random() * 2, 
                    0, Math.PI * 2
                );
                depthChargeCtx.fill();
            }
        }
    });
    
    // Sonar pings emanating from escort (visual representation)
    const pingRadius = (performance.now() % 1500) / 8;
    if (pingRadius < 150) {
        depthChargeCtx.strokeStyle = `rgba(255, 191, 0, ${0.6 - pingRadius/250})`;
        depthChargeCtx.lineWidth = 2;
        depthChargeCtx.beginPath();
        depthChargeCtx.arc(escortX, surfaceY + 5, pingRadius, 0.2, Math.PI - 0.2);
        depthChargeCtx.stroke();
    }
    
    // Depth scale on the right
    depthChargeCtx.fillStyle = 'rgba(255, 255, 255, 0.5)';
    depthChargeCtx.font = '10px VT323, monospace';
    depthChargeCtx.textAlign = 'right';
    for (let d = 0; d <= 140; d += 20) {
        const y = getDepthY(d);
        depthChargeCtx.fillText(`${d}'`, width - 5, y + 3);
        depthChargeCtx.fillRect(width - 25, y, 15, 1);
    }
    depthChargeCtx.textAlign = 'left';
}

// ==================== UTILITIES ====================

function updateDepthGauge() {
    // Update all depth markers based on current phase
    const depth = GameState.cobia.depth;
    const percentage = (depth / WATER_DEPTH) * 100;
    
    updateDepthMarker('depth-marker', depth);
    updateDepthMarker('depth-marker-2', depth);
    updateDepthMarker('depth-marker-3', depth);
}

function updateDepthMarker(markerId, depth) {
    const marker = document.getElementById(markerId);
    if (marker) {
        const percentage = (depth / WATER_DEPTH) * 100;
        marker.style.top = Math.min(percentage, 100) + '%';
    }
}

function updateGameTime(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = formatTime(GameState.time);
    }
}

function formatTime(militaryTime) {
    // Convert raw time value to proper military time
    // Time is stored as HHMM but minutes can exceed 59
    let hours = Math.floor(militaryTime / 100);
    let mins = Math.floor(militaryTime % 100);
    
    // Handle minute overflow
    while (mins >= 60) {
        mins -= 60;
        hours += 1;
    }
    
    // Handle hour overflow (24-hour wrap)
    hours = hours % 24;
    
    return hours.toString().padStart(2, '0') + mins.toString().padStart(2, '0');
}

function addLogEntry(logId, message, type = '') {
    const log = document.getElementById(logId);
    if (log) {
        const entry = document.createElement('div');
        entry.className = 'log-entry ' + type;
        entry.textContent = message;
        log.appendChild(entry);
        log.scrollTop = log.scrollHeight;
    }
}

// ==================== GAME END ====================

function endGameSurvived() {
    GameState.gameOver = true;
    GameState.survived = true;
    cancelAnimationFrame(gameLoop);
    SoundManager.stopAmbient();
    
    addLogEntry('phase3-log', '1320 - Escort screws fading. She\'s departing!');
    addLogEntry('phase3-log', '1320 - YAEYAMA HAS BROKEN OFF THE ATTACK.');
    
    setTimeout(() => {
        showEndScreen(true);
    }, 2000);
}

function endGameSunk() {
    GameState.gameOver = true;
    GameState.survived = false;
    cancelAnimationFrame(gameLoop);
    SoundManager.stopAmbient();
    
    addLogEntry('phase3-log', `${formatTime(GameState.time)} - HULL BREACH! FLOODING UNCONTROLLABLE!`, 'danger');
    
    setTimeout(() => {
        showEndScreen(false);
    }, 2000);
}

function endGameSurfaced() {
    GameState.gameOver = true;
    GameState.survived = false;
    cancelAnimationFrame(gameLoop);
    SoundManager.stopAmbient();
    
    addLogEntry('phase3-log', `${formatTime(GameState.time)} - Emergency surface! We're sitting ducks!`, 'danger');
    
    setTimeout(() => {
        showEndScreen(false, 'surfaced');
    }, 2000);
}

function endGameDudSurvival() {
    GameState.gameOver = true;
    GameState.survived = true;
    GameState.dudSurvival = true;
    cancelAnimationFrame(gameLoop);
    SoundManager.stopAmbient();
    
    addLogEntry('phase3-log', `${formatTime(GameState.time)} - Escort departing to rejoin convoy. We're safe!`);
    addLogEntry('phase3-log', `${formatTime(GameState.time)} - TOTTORI MARU escapes, but COBIA survives to fight another day.`);
    
    setTimeout(() => {
        showEndScreen(true, 'dud_survival');
    }, 2000);
}

function showEndScreen(survived, reason = '') {
    showScreen('end-screen');
    
    const statusEl = document.getElementById('end-status');
    const titleEl = document.getElementById('end-title');
    const reportEl = document.getElementById('end-report');
    
    if (survived) {
        if (reason === 'freighter_sunk') {
            statusEl.textContent = 'VICTORY';
            statusEl.className = 'end-status survived';
            if (GameState.hammerhead.torpedoesFired) {
                titleEl.textContent = 'Mission Success - Hammerhead Sinks Tottori Maru!';
            } else {
                titleEl.textContent = 'Mission Success - Tottori Maru Destroyed!';
            }
        } else if (reason === 'dud_survival') {
            statusEl.textContent = 'SURVIVED';
            statusEl.className = 'end-status survived';
            titleEl.textContent = 'Cobia Survives - Hammerhead\'s Dud Saves the Day!';
        } else {
            statusEl.textContent = 'SURVIVED';
            statusEl.className = 'end-status survived';
            titleEl.textContent = 'USS Cobia Survives the Ordeal';
        }
    } else {
        statusEl.textContent = 'LOST';
        statusEl.className = 'end-status sunk';
        titleEl.textContent = reason === 'surfaced' ? 
            'USS Cobia Destroyed on Surface' : 
            'USS Cobia Lost with All Hands';
    }
    
    // Generate report
    let missionResult;
    if (GameState.tottoriMaru.sunk) {
        missionResult = GameState.hammerhead.torpedoesFired ? 'TOTTORI MARU SUNK BY HAMMERHEAD' : 'TOTTORI MARU SUNK BY COBIA';
    } else if (GameState.hammerhead.torpedoDud) {
        missionResult = 'DUD TORPEDO - TARGET ESCAPED (BUT ESCORT RECALLED)';
    } else {
        missionResult = 'TARGET ESCAPED';
    }
    
    reportEl.innerHTML = `
        <div class="report-line" style="border-bottom: 2px solid var(--scope-green); margin-bottom: 10px; padding-bottom: 10px;">
            <span class="report-label">Mission Result:</span>
            <span class="report-value" style="color: ${GameState.tottoriMaru.sunk ? 'var(--scope-green)' : 'var(--warning-amber)'}">${missionResult}</span>
        </div>
        <div class="report-line">
            <span class="report-label">Depth Charges Endured:</span>
            <span class="report-value">${GameState.depthCharging.totalCharges}</span>
        </div>
        <div class="report-line">
            <span class="report-label">Attack Runs Survived:</span>
            <span class="report-value">${GameState.depthCharging.attackRuns}</span>
        </div>
        <div class="report-line">
            <span class="report-label">Hull Integrity:</span>
            <span class="report-value">${Math.max(0, Math.round(GameState.damage.hull))}%</span>
        </div>
        <div class="report-line">
            <span class="report-label">Time Submerged:</span>
            <span class="report-value">${Math.floor(GameState.resources.timeSubmerged / 60)} minutes</span>
        </div>
        <div class="report-line">
            <span class="report-label">Systems Damaged:</span>
            <span class="report-value">${countDamagedSystems()}</span>
        </div>
        <div class="report-line">
            <span class="report-label">Hammerhead Status:</span>
            <span class="report-value">${GameState.hammerhead.torpedoesFired ? 'Torpedoes Expended' : 'Standing By'}</span>
        </div>
    `;
}

function countDamagedSystems() {
    let count = 0;
    if (!GameState.damage.tdcOperational) count++;
    if (!GameState.damage.tubesOperational) count++;
    if (!GameState.damage.motorsOperational) count++;
    if (!GameState.damage.sternGlandsOperational) count++;
    return count;
}

function resetGameState() {
    // Reset all game state to initial values
    GameState.phase = 'title';
    GameState.time = 638;
    GameState.gameOver = false;
    GameState.survived = false;
    GameState.detected = false;
    GameState.silentRunning = false;
    GameState.miscommunicationTriggered = false;
    GameState.attackPositionReached = false;
    GameState.escortZigTriggered = false;
    
    GameState.cobia = {
        x: 0, y: 0,
        course: 120,
        speed: 8,
        depth: 60,
        targetDepth: 60
    };
    
    GameState.convoy = {
        baseCourse: 250,
        currentCourse: 250,
        speed: 9.5,
        zigzagTimer: 0,
        zigzagDirection: 1,
        zigzagAngle: 30
    };
    
    GameState.torpedoes = {
        tubes: [true, true, true, true, true, true],
        fired: [],
        gyroError: 0
    };
    
    GameState.depthCharging = {
        totalCharges: 0,
        attackRuns: 0,
        maxRuns: 8,
        nextAttackTime: 0,
        chargesInWater: []
    };
    
    GameState.damage = {
        forward: 0, control: 0, engine: 0, aft: 0,
        hull: 100,
        tdcOperational: true,
        tubesOperational: true,
        motorsOperational: true,
        sternGlandsOperational: true
    };
    
    GameState.resources = {
        battery: 100,
        oxygen: 100,
        timeSubmerged: 0
    };
    
    GameState.currentRange = 8000;
    GameState.bearing = 120;
    GameState.periscopeBearing = 120;
    
    // Reset Hammerhead
    GameState.hammerhead = {
        x: 0, y: 0,
        course: 60,
        speed: 0,
        state: 'waiting',
        attackReady: false,
        torpedoesFired: false,
        torpedoDud: false
    };
    
    // Reset target status
    GameState.tottoriMaru.sunk = false;
    GameState.tottoriMaru.health = 100;
    GameState.yaeyama.distracted = false;
    GameState.yaeyama.distractedTime = 0;
    GameState.freighterSunk = false;
    GameState.dudSurvival = false;
    GameState.depthCharging.escortDeparted = false;
    
    // Reset UI elements
    document.querySelectorAll('.tube').forEach((tube, i) => {
        tube.classList.remove('fired', 'disabled');
        tube.classList.add('ready');
    });
    
    document.querySelectorAll('.system-indicator').forEach(ind => {
        ind.className = 'system-indicator operational';
    });
    
    document.getElementById('fire-btn').disabled = false;
    
    // Clear logs
    ['phase1-log', 'phase2-log', 'phase3-log'].forEach(logId => {
        const log = document.getElementById(logId);
        if (log) log.innerHTML = '';
    });
    
    const commChatter = document.getElementById('comm-chatter');
    if (commChatter) commChatter.innerHTML = '<div class="comm-msg">Standing by for attack...</div>';
}

function resetGame() {
    resetGameState();
    showScreen('title-screen');
}

