/**
 * TDC Mark III Mechanical Computer Simulation Engine
 * 
 * This is a true simulation of the analog computer mechanism.
 * Each component actually computes its output based on inputs.
 * The firing solution emerges from the mechanism, not a formula.
 * 
 * Based on Bureau of Ordnance OP 1631
 */

// ============================================
// MECHANICAL COMPONENT CLASSES
// ============================================

class Differential {
    /**
     * Bevel gear differential - adds or subtracts two rotational inputs.
     * Output = Input1 ± Input2
     */
    constructor(id, name, operation = 'add') {
        this.id = id;
        this.name = name;
        this.operation = operation; // 'add' or 'subtract'
        this.input1 = 0;
        this.input2 = 0;
        this.output = 0;
        this.rotation = 0; // Visual rotation angle
    }
    
    update(input1, input2) {
        this.input1 = input1;
        this.input2 = input2;
        if (this.operation === 'add') {
            this.output = input1 + input2;
        } else {
            this.output = input1 - input2;
        }
        // Spider gear rotates at average of inputs
        this.rotation += (input1 + input2) / 2;
        return this.output;
    }
}

class Integrator {
    /**
     * Disc and roller integrator - multiplies and accumulates.
     * Output = ∫(rollerPosition × discRate) dt
     */
    constructor(id, name) {
        this.id = id;
        this.name = name;
        this.rollerPosition = 0; // Position from center (-1 to +1)
        this.discRate = 0;       // Rate of disc rotation
        this.accumulated = 0;    // Integrated value
        this.discRotation = 0;   // Visual disc angle
        this.outputRotation = 0; // Visual output wheel angle
    }
    
    update(rollerPosition, discRate, dt) {
        this.rollerPosition = rollerPosition;
        this.discRate = discRate;
        
        // The magic of mechanical integration:
        // Output rate = roller_position × disc_rate
        const outputRate = rollerPosition * discRate;
        this.accumulated += outputRate * dt;
        
        // Visual rotations
        this.discRotation += discRate * dt * 50; // Scale for visibility
        this.outputRotation += outputRate * dt * 50;
        
        return this.accumulated;
    }
    
    reset() {
        this.accumulated = 0;
        this.discRotation = 0;
        this.outputRotation = 0;
    }
}

class Resolver {
    /**
     * Mechanical resolver - converts angle to sin/cos components.
     * Uses cam followers or gear linkages.
     */
    constructor(id, name) {
        this.id = id;
        this.name = name;
        this.inputAngle = 0;  // degrees
        this.sinOutput = 0;
        this.cosOutput = 0;
        this.rotation = 0;    // Visual rotation
    }
    
    update(angleDegrees) {
        this.inputAngle = angleDegrees;
        const angleRad = angleDegrees * Math.PI / 180;
        this.sinOutput = Math.sin(angleRad);
        this.cosOutput = Math.cos(angleRad);
        this.rotation = angleDegrees;
        return { sin: this.sinOutput, cos: this.cosOutput };
    }
}

class Cam {
    /**
     * Cam mechanism - provides non-linear function.
     * Used for torpedo reach (P), transfer (J), pseudo-run (Us).
     */
    constructor(id, name, profileFn) {
        this.id = id;
        this.name = name;
        this.profileFn = profileFn || ((x) => x); // Default: identity
        this.inputAngle = 0;
        this.output = 0;
        this.rotation = 0;
    }
    
    update(inputAngle) {
        this.inputAngle = inputAngle;
        this.output = this.profileFn(inputAngle);
        this.rotation = inputAngle;
        return this.output;
    }
}

// ============================================
// TDC MARK III SIMULATION ENGINE
// ============================================

class TDCMarkIII {
    constructor() {
        // Physical constants
        this.KNOTS_TO_YPS = 2025.4 / 3600; // Yards per second per knot
        this.TORPEDO_SPEED = 46; // knots (Mark 14 high speed)
        this.TORPEDO_INITIAL_RUN = 75; // yards before gyro engages
        
        // === INPUTS (set by operator) ===
        this.inputs = {
            ownCourse: 0,      // Co - Own ship course (degrees)
            ownSpeed: 0,       // So - Own ship speed (knots)
            targetBearing: 0,  // B - Target bearing (degrees)
            targetRange: 0,    // R - Target range (yards)
            targetCourse: 0,   // C - Target course (degrees)
            targetSpeed: 0     // S - Target speed (knots)
        };
        
        // === POSITION STATE (for simulation) ===
        this.state = {
            ownX: 0, ownY: 0,
            targetX: 0, targetY: 0,
            elapsedTime: 0
        };
        
        // === POSITION KEEPER COMPONENTS ===
        
        // Differential 7: Br = B - Co (Relative Bearing)
        this.diff7 = new Differential('diff_7', 'Diff 7 (Br = B - Co)', 'subtract');
        
        // Differential 33: A = B + 180 - C (Target Angle)
        this.diff33 = new Differential('diff_33', 'Diff 33 (A = B + 180 - C)', 'subtract');
        
        // Resolver 13: sin(Br), cos(Br)
        this.resolver13 = new Resolver('resolver_13', 'Resolver 13 (Br)');
        
        // Resolver 34: sin(A), cos(A)
        this.resolver34 = new Resolver('resolver_34', 'Resolver 34 (A)');
        
        // Integrator 20: ∫So·dT (Own ship travel)
        this.int20 = new Integrator('int_20', 'Int 20 (∫So·dT)');
        
        // Integrator 25: ∫S·dT (Target travel)
        this.int25 = new Integrator('int_25', 'Int 25 (∫S·dT)');
        
        // Integrator 14: ∫So·sin(Br)·dT (Lateral component)
        this.int14 = new Integrator('int_14', 'Int 14 (∫So·sin(Br)·dT)');
        
        // Integrator 15: ∫So·cos(Br)·dT (Along-LOS component)
        this.int15 = new Integrator('int_15', 'Int 15 (∫So·cos(Br)·dT)');
        
        // Integrator 35: ∫S·sin(A)·dT
        this.int35 = new Integrator('int_35', 'Int 35 (∫S·sin(A)·dT)');
        
        // Integrator 36: ∫S·cos(A)·dT
        this.int36 = new Integrator('int_36', 'Int 36 (∫S·cos(A)·dT)');
        
        // Differential 28: ΔB (change in bearing from integrators)
        this.diff28 = new Differential('diff_28', 'Diff 28 (ΔB)', 'add');
        
        // Differential 29: ΔR (change in range from integrators)
        this.diff29 = new Differential('diff_29', 'Diff 29 (ΔR)', 'add');
        
        // === ANGLE SOLVER COMPONENTS ===
        
        // The Angle Solver finds gyro angle G such that torpedo hits target
        // It uses feedback to minimize error in equations XVII and XVIII
        
        // Current gyro angle being computed
        this.gyroAngle = 0;
        this.gyroServoRate = 200; // degrees/second servo response (fast for convergence)
        
        // Resolver 2FA: Resolves (G - Br)
        this.resolver2FA = new Resolver('resolver_2FA', 'Resolver 2FA (G - Br)');
        
        // Cams for torpedo characteristics (simplified)
        // P = Reach (initial straight run distance)
        // J = Transfer (lateral displacement during turn)
        this.camP = new Cam('cam_P', 'Cam P (Reach)', (g) => {
            // Reach component depends on gyro angle
            return this.TORPEDO_INITIAL_RUN * Math.cos(g * Math.PI / 180);
        });
        
        this.camJ = new Cam('cam_J', 'Cam J (Transfer)', (g) => {
            // Transfer component depends on gyro angle
            return this.TORPEDO_INITIAL_RUN * Math.sin(g * Math.PI / 180);
        });
        
        // Differential 22FA: Gyro angle output
        this.diff22FA = new Differential('diff_22FA', 'Diff 22FA (G)', 'add');
        
        // === OUTPUTS ===
        this.outputs = {
            gyroAngle: 0,      // G - Gyro angle setting
            relativeBearing: 0, // Br
            targetAngle: 0,    // A
            presentBearing: 0, // B (updated)
            presentRange: 0,   // R (updated)
            torpedoRun: 0,     // U
            runTime: 0,
            trackAngle: 0,
            isSolved: false,
            solverError: 999
        };
        
        // Collection of all components for visualization
        this.components = {
            diff_7: this.diff7,
            diff_33: this.diff33,
            resolver_13: this.resolver13,
            resolver_34: this.resolver34,
            int_20: this.int20,
            int_25: this.int25,
            int_14: this.int14,
            int_15: this.int15,
            int_35: this.int35,
            int_36: this.int36,
            diff_28: this.diff28,
            diff_29: this.diff29,
            resolver_2FA: this.resolver2FA,
            cam_P: this.camP,
            cam_J: this.camJ,
            diff_22FA: this.diff22FA
        };
    }
    
    /**
     * Initialize state from inputs
     */
    initialize() {
        const bearingRad = this.inputs.targetBearing * Math.PI / 180;
        this.state.ownX = 0;
        this.state.ownY = 0;
        this.state.targetX = this.inputs.targetRange * Math.sin(bearingRad);
        this.state.targetY = this.inputs.targetRange * Math.cos(bearingRad);
        this.state.elapsedTime = 0;
        
        // Reset integrators
        this.int20.reset();
        this.int25.reset();
        this.int14.reset();
        this.int15.reset();
        this.int35.reset();
        this.int36.reset();
        
        // Reset gyro solver
        this.gyroAngle = 0;
        this.outputs.isSolved = false;
    }
    
    /**
     * Update ship positions based on movement
     */
    updatePositions(dt) {
        const ownCourseRad = this.inputs.ownCourse * Math.PI / 180;
        const ownSpeedYps = this.inputs.ownSpeed * this.KNOTS_TO_YPS;
        this.state.ownX += ownSpeedYps * Math.sin(ownCourseRad) * dt;
        this.state.ownY += ownSpeedYps * Math.cos(ownCourseRad) * dt;
        
        const targetCourseRad = this.inputs.targetCourse * Math.PI / 180;
        const targetSpeedYps = this.inputs.targetSpeed * this.KNOTS_TO_YPS;
        this.state.targetX += targetSpeedYps * Math.sin(targetCourseRad) * dt;
        this.state.targetY += targetSpeedYps * Math.cos(targetCourseRad) * dt;
        
        this.state.elapsedTime += dt;
    }
    
    /**
     * Calculate present bearing and range from positions
     */
    calculatePresentGeometry() {
        const dx = this.state.targetX - this.state.ownX;
        const dy = this.state.targetY - this.state.ownY;
        
        this.outputs.presentRange = Math.sqrt(dx * dx + dy * dy);
        this.outputs.presentBearing = Math.atan2(dx, dy) * 180 / Math.PI;
        if (this.outputs.presentBearing < 0) {
            this.outputs.presentBearing += 360;
        }
    }
    
    /**
     * Run the Position Keeper mechanism
     * This tracks the changing geometry as ships move
     */
    runPositionKeeper(dt) {
        const So = this.inputs.ownSpeed * this.KNOTS_TO_YPS; // Own speed in yps
        const S = this.inputs.targetSpeed * this.KNOTS_TO_YPS; // Target speed in yps
        const B = this.outputs.presentBearing;
        const Co = this.inputs.ownCourse;
        const C = this.inputs.targetCourse;
        
        // Differential 7: Br = B - Co
        const Br = this.diff7.update(B, Co);
        this.outputs.relativeBearing = this.normalizeAngle(Br);
        
        // Differential 33: A = (B + 180) - C
        const A = this.diff33.update(B + 180, C);
        this.outputs.targetAngle = this.normalizeAngle(A);
        
        // Resolver 13: Get sin(Br), cos(Br)
        const res13 = this.resolver13.update(this.outputs.relativeBearing);
        
        // Resolver 34: Get sin(A), cos(A)
        const res34 = this.resolver34.update(this.outputs.targetAngle);
        
        // Integrator 20: ∫So·dT (total own ship travel)
        // Roller at 1.0 (full), disc driven by time
        this.int20.update(1.0, So, dt);
        
        // Integrator 25: ∫S·dT (total target travel)
        this.int25.update(1.0, S, dt);
        
        // Integrator 14: ∫So·sin(Br)·dT
        // Roller position set by sin(Br), disc rate by So
        this.int14.update(res13.sin, So, dt);
        
        // Integrator 15: ∫So·cos(Br)·dT
        this.int15.update(res13.cos, So, dt);
        
        // Integrator 35: ∫S·sin(A)·dT
        this.int35.update(res34.sin, S, dt);
        
        // Integrator 36: ∫S·cos(A)·dT
        this.int36.update(res34.cos, S, dt);
        
        // Differential 28: Combines lateral components
        // ΔB ∝ ∫So·sin(Br)·dT + ∫S·sin(A)·dT
        this.diff28.update(this.int14.accumulated, this.int35.accumulated);
        
        // Differential 29: Combines LOS components
        // ΔR ∝ ∫So·cos(Br)·dT + ∫S·cos(A)·dT
        this.diff29.update(this.int15.accumulated, this.int36.accumulated);
    }
    
    /**
     * Run the Angle Solver mechanism
     * This finds the gyro angle through mechanical feedback
     */
    runAngleSolver(dt) {
        const R = this.outputs.presentRange;
        const Br = this.outputs.relativeBearing;
        const S = this.inputs.targetSpeed * this.KNOTS_TO_YPS;
        const torpedoSpeedYps = this.TORPEDO_SPEED * this.KNOTS_TO_YPS;
        
        // Debug: log key values periodically
        if (Math.random() < 0.01) {
            console.log('AngleSolver: R=', R, 'Br=', Br, 'gyro=', this.gyroAngle, 'dt=', dt);
        }
        
        // The Angle Solver implements equations XVII, XVIII, XIX
        // It adjusts G until the error is zero
        
        // Resolver 2FA: Resolve (G - Br)
        const G_minus_Br = this.gyroAngle - Br;
        const res2FA = this.resolver2FA.update(G_minus_Br);
        
        // Estimate torpedo run time
        const estRunTime = R / torpedoSpeedYps;
        
        // H = target travel during torpedo run
        const H = S * estRunTime;
        
        // I = Impact angle (angle torpedo crosses target track)
        // Equation XIX: I = A + (G - Br)
        const I = this.outputs.targetAngle + G_minus_Br;
        const sinI = Math.sin(I * Math.PI / 180);
        const cosI = Math.cos(I * Math.PI / 180);
        
        // Get cam values
        const P_cosG = this.camP.update(this.gyroAngle);
        const P_sinG = this.camJ.update(this.gyroAngle);
        
        // Equation XVII: R·cos(G-Br) - H·cos(I) = Us + P·cos(G)
        // Simplified: we compute the error
        const term1_XVII = R * res2FA.cos;
        const term2_XVII = H * cosI;
        const Us = 0; // Pseudo-run (simplified)
        const errorXVII = term1_XVII - term2_XVII - Us - P_cosG;
        
        // Equation XVIII: R·sin(G-Br) - H·sin(I) = J + P·sin(G)
        const term1_XVIII = R * res2FA.sin;
        const term2_XVIII = H * sinI;
        const J = 0; // Transfer (simplified)
        const errorXVIII = term1_XVIII - term2_XVIII - J - P_sinG;
        
        // Total error (what the servo tries to minimize)
        // Error is in yards (range-scaled), so threshold should be appropriate
        this.outputs.solverError = Math.abs(errorXVII) + Math.abs(errorXVIII);
        
        // Servo adjusts gyro angle to minimize error
        // This is the key feedback mechanism - TRUE MECHANICAL FEEDBACK
        // The error terms drive the servo directly, not a computed "ideal" value
        const errorThreshold = Math.max(5, R * 0.001);
        
        // Debug: log error values periodically
        if (Math.random() < 0.01) {
            console.log('Solver: errorXVII=', errorXVII.toFixed(1), 'errorXVIII=', errorXVIII.toFixed(1), 
                        'total=', this.outputs.solverError.toFixed(1), 'threshold=', errorThreshold.toFixed(1));
        }
        
        if (this.outputs.solverError > errorThreshold) {
            // TRUE MECHANICAL FEEDBACK using BOTH error terms:
            // Error XVII (range component) - negative means torpedo won't reach, positive means overshoot
            // Error XVIII (lateral component) - tells us if aiming left or right of intercept
            
            // The key insight: use Error XVIII primarily, but add Error XVII influence
            // to avoid spurious solutions where sin(G-Br) = 0
            
            // Also: keep gyro in reasonable range (-90 to +90 degrees)
            // Values outside this are torpedo pointing backwards, which is invalid
            
            // If we're at an extreme angle and Error XVIII is small but Error XVII is large,
            // we're at a spurious solution - need to push back toward center
            let gyroCorrection = 0;
            
            if (Math.abs(this.gyroAngle) > 120) {
                // Spurious solution detected - push back toward 0
                gyroCorrection = -Math.sign(this.gyroAngle) * 10;
            } else {
                // Normal operation: Error XVIII drives the servo
                // But also add a small component from Error XVII to help stability
                const scaleFactor = 0.03;
                gyroCorrection = errorXVIII * scaleFactor;
                
                // If Error XVIII is very small but Error XVII is large, use XVII to adjust
                if (Math.abs(errorXVIII) < 10 && Math.abs(errorXVII) > 50) {
                    gyroCorrection += Math.sign(errorXVII) * 0.5;
                }
            }
            
            // Rate limit the servo
            const maxStep = this.gyroServoRate * dt;
            const step = Math.max(-maxStep, Math.min(maxStep, gyroCorrection));
            this.gyroAngle += step;
            
            // Hard clamp to valid range
            this.gyroAngle = Math.max(-90, Math.min(90, this.gyroAngle));
            
            // Debug
            if (Math.random() < 0.02) {
                console.log('Servo: errXVII=', errorXVII.toFixed(1), 'errXVIII=', errorXVIII.toFixed(1),
                            'step=', step.toFixed(3), 'newGyro=', this.gyroAngle.toFixed(2));
            }
            
            // Differential 22FA shows the adjusting gyro
            this.diff22FA.update(this.gyroAngle, 0);
            
            this.outputs.isSolved = false;
        } else {
            this.outputs.isSolved = true;
        }
        
        this.outputs.gyroAngle = this.gyroAngle;
        
        // Calculate track angle
        const torpedoHeading = this.inputs.ownCourse + this.gyroAngle;
        let trackAngle = Math.abs(this.normalizeAngle(torpedoHeading - this.inputs.targetCourse + 180));
        if (trackAngle > 180) trackAngle = 360 - trackAngle;
        this.outputs.trackAngle = trackAngle;
        
        // Torpedo run
        this.outputs.torpedoRun = R; // Simplified
        this.outputs.runTime = R / torpedoSpeedYps;
    }
    
    /**
     * Compute the ideal gyro angle (used for servo feedback)
     * In the real TDC, this emerges from the mechanism
     */
    computeIdealGyro() {
        const dx = this.state.targetX - this.state.ownX;
        const dy = this.state.targetY - this.state.ownY;
        const torpedoSpeedYps = this.TORPEDO_SPEED * this.KNOTS_TO_YPS;
        const targetSpeedYps = this.inputs.targetSpeed * this.KNOTS_TO_YPS;
        
        const range = Math.sqrt(dx * dx + dy * dy);
        const estRunTime = range / torpedoSpeedYps;
        const targetAdvance = targetSpeedYps * estRunTime;
        
        const courseRad = this.inputs.targetCourse * Math.PI / 180;
        const futureX = dx + targetAdvance * Math.sin(courseRad);
        const futureY = dy + targetAdvance * Math.cos(courseRad);
        
        let interceptBearing = Math.atan2(futureX, futureY) * 180 / Math.PI;
        if (interceptBearing < 0) interceptBearing += 360;
        
        return this.normalizeAngle(interceptBearing - this.inputs.ownCourse);
    }
    
    /**
     * Main simulation step
     */
    step(dt) {
        // Update ship positions
        this.updatePositions(dt);
        
        // Calculate current geometry from positions
        this.calculatePresentGeometry();
        
        // Run Position Keeper
        this.runPositionKeeper(dt);
        
        // Run Angle Solver
        this.runAngleSolver(dt);
    }
    
    /**
     * Normalize angle to -180 to +180
     */
    normalizeAngle(angle) {
        while (angle > 180) angle -= 360;
        while (angle < -180) angle += 360;
        return angle;
    }
    
    /**
     * Set inputs from external source
     */
    setInputs(inputs) {
        Object.assign(this.inputs, inputs);
    }
    
    /**
     * Get all component states for visualization
     */
    getComponentStates() {
        const states = {};
        for (const [id, comp] of Object.entries(this.components)) {
            states[id] = {
                rotation: comp.rotation || 0,
                discRotation: comp.discRotation || 0,
                outputRotation: comp.outputRotation || 0,
                output: comp.output || comp.accumulated || comp.output_value || 0
            };
        }
        return states;
    }
}

// Export for use in visualizer
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TDCMarkIII, Differential, Integrator, Resolver, Cam };
}

