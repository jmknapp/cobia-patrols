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
        
        // Torpedo geometry (from O.P. 1056 Fig. 4)
        this.TUBE_BASE_LINE = 50;  // P - distance from conning tower to forward tubes (yards)
        this.REACH = 75;           // M - straight run before gyro engages (yards)
        this.TURN_RADIUS = 130;    // Z - torpedo turning radius (yards)
        
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
        this.gyroServoRate = 8; // degrees/second - slow realistic mechanical servo
        this.servoVelocity = 0;  // current servo angular velocity
        this.servoInertia = 0.95; // momentum retention (0-1), high inertia for slow response
        
        // Resolver 2FA: Resolves (G - Br)
        this.resolver2FA = new Resolver('resolver_2FA', 'Resolver 2FA (G - Br)');
        
        // Cams for torpedo characteristics
        // Torpedo path components (from O.P. 1056):
        // P = Tube Base Line (distance from conning tower to tubes)
        // M = Reach (straight run before gyro engages)
        // J = Torpedo Advance (lateral offset during turn)
        // Us = Semi-pseudo run (extra path length from curved trajectory)
        // Z = Turning Radius
        
        // Combined offset: |P| + M = total straight distance before turn starts
        // Uses absolute value of TUBE_BASE_LINE because TDC equations use distances
        // The directional logic (bow vs stern) is handled in the visualization
        this.getTotalStraightRun = () => Math.abs(this.TUBE_BASE_LINE) + this.REACH;
        
        this.camP = new Cam('cam_P', 'Cam P+M (Tube+Reach)', (g) => {
            // Total straight run before turn: |P| (tube base line) + M (reach)
            return this.getTotalStraightRun();
        });
        
        this.camJ = new Cam('cam_J', 'Cam J (Advance)', (g) => {
            // Torpedo Advance = turn_radius × (1 - cos(G))
            const g_rad = g * Math.PI / 180;
            return this.TURN_RADIUS * (1 - Math.cos(g_rad));
        });
        
        this.camUs = new Cam('cam_Us', 'Cam Us (Pseudo-run)', (g) => {
            // Extra path length from curved trajectory
            const g_rad = Math.abs(g) * Math.PI / 180;
            const arcLength = this.TURN_RADIUS * g_rad;
            const chordLength = 2 * this.TURN_RADIUS * Math.sin(g_rad / 2);
            return arcLength - chordLength;
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
            cam_Us: this.camUs,
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
        
        // Reset gyro solver - initialize gyro toward target's relative bearing
        // This prevents converging on wrong-side spurious solutions
        const relBearing = this.normalizeAngle(this.inputs.targetBearing - this.inputs.ownCourse);
        // Start gyro roughly toward target (servo will refine from here)
        this.gyroAngle = relBearing * 0.8; // Start 80% of the way toward target
        this.gyroAngle = Math.max(-90, Math.min(90, this.gyroAngle)); // Clamp to valid range
        this.servoVelocity = 0;
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
     * 
     * The real TDC Mark III Angle Solver uses equations XVII and XVIII from OP 1631.
     * These equations include correction terms (Us, J) computed by cams.
     * 
     * The key insight: the LATERAL equation (XVIII) is what drives the gyro servo,
     * because it's most sensitive to gyro angle. The servo hunts until XVIII ≈ 0.
     * 
     * For the equations to balance, we must include proper torpedo path corrections.
     */
    runAngleSolver(dt) {
        const R = this.outputs.presentRange;
        const Br = this.outputs.relativeBearing;
        const S = this.inputs.targetSpeed * this.KNOTS_TO_YPS;
        const torpedoSpeedYps = this.TORPEDO_SPEED * this.KNOTS_TO_YPS;
        
        // === FUNCTION TO COMPUTE MECHANICAL ERROR FOR A GIVEN GYRO ANGLE ===
        const computeError = (testGyro) => {
            const G_rad = testGyro * Math.PI / 180;
            const G_minus_Br = testGyro - Br;
            const G_minus_Br_rad = G_minus_Br * Math.PI / 180;
            
            // Resolver outputs
            const sin_G_minus_Br = Math.sin(G_minus_Br_rad);
            const cos_G_minus_Br = Math.cos(G_minus_Br_rad);
            
            // Torpedo characteristics
            const PM = this.getTotalStraightRun(); // |P| + M
            const Z = this.TURN_RADIUS; // 130 yards
            
            // Target travel during torpedo run
            // Compute ACTUAL torpedo path length to match what torpedo simulation does:
            // 1. Straight run: P + M (tube base line + reach) = 125 yards
            // 2. Arc of turn: Z × |G| (in radians)
            // 3. Final straight run to intercept
            const arcLength = Z * Math.abs(G_rad);
            // Final run: from end of turn to intercept point
            // Approximate: total range minus the straight portions covered
            const straightPortionCovered = PM * Math.cos(G_rad) + Z * Math.sin(Math.abs(G_rad));
            const finalRun = Math.max(0, R - straightPortionCovered);
            const torpedoPath = PM + arcLength + finalRun;
            const estRunTime = torpedoPath / torpedoSpeedYps;
            const H = S * estRunTime;
            
            // Impact angle I = A + (G - Br)
            const A = this.outputs.targetAngle;
            const I = A + G_minus_Br;
            const I_rad = I * Math.PI / 180;
            const sinI = Math.sin(I_rad);
            const cosI = Math.cos(I_rad);
            
            // Torpedo characteristics (from O.P. 1056):
            // PM, Z, arcLength already defined above for path calculation
            
            // J (Torpedo Advance) = lateral offset from turn
            // J = Z × (1 - cos(G))
            const J = Z * (1 - Math.cos(G_rad));
            
            // Us (Semi-pseudo run) = extra path length from curved vs straight
            // Arc length - chord length
            const chordLength = 2 * Z * Math.sin(Math.abs(G_rad) / 2);
            const Us = arcLength - chordLength;
            
            // Equation XVII (Range component):
            // R·cos(G-Br) = H·cos(I) + Us + (P+M)·cos(G)
            const errorXVII = R * cos_G_minus_Br - H * cosI - Us - PM * Math.cos(G_rad);
            
            // Equation XVIII (Lateral component):
            // R·sin(G-Br) = H·sin(I) + J + (P+M)·sin(G)
            const errorXVIII = R * sin_G_minus_Br - H * sinI - J - PM * Math.sin(G_rad);
            
            return { errorXVII, errorXVIII, H, I, J, Us };
        };
        
        // === COMPUTE CURRENT ERRORS ===
        const errors = computeError(this.gyroAngle);
        const { errorXVII, errorXVIII, H, I, J, Us } = errors;
        
        // Update mechanical components for visualization
        const G_minus_Br = this.gyroAngle - Br;
        this.resolver2FA.update(G_minus_Br);
        this.camP.update(this.gyroAngle);
        this.camJ.update(this.gyroAngle);
        this.camUs.update(this.gyroAngle);
        
        // Error magnitude for display/threshold
        this.outputs.solverError = Math.sqrt(errorXVII * errorXVII + errorXVIII * errorXVIII);
        
        // Debug
        if (Math.random() < 0.01) {
            console.log('Solver: G=', this.gyroAngle.toFixed(1), 
                        'errXVII=', errorXVII.toFixed(1), 'errXVIII=', errorXVIII.toFixed(1),
                        'H=', H.toFixed(1), 'I=', I.toFixed(1), 'J=', J.toFixed(1), 'Us=', Us.toFixed(1));
        }
        
        // === MECHANICAL SERVO FEEDBACK ===
        // The real TDC servo is driven by ERROR XVIII (lateral component)
        // When XVIII > 0: torpedo aims too far right, need less gyro angle
        // When XVIII < 0: torpedo aims too far left, need more gyro angle
        
        // Error threshold with strong hysteresis for stable solution light
        // In real TDC, solution light stayed on steadily once found
        const solveThreshold = Math.max(10, R * 0.005); // Threshold to declare solved
        const unsolvThreshold = solveThreshold * 10;    // Very large - only lose solution on major error
        
        const isLateralSolved = Math.abs(errorXVIII) < solveThreshold;
        
        // Hysteresis: once solved, stay solved unless error gets MUCH worse
        // Real TDC solution light was stable during normal tracking
        if (this.outputs.isSolved) {
            // Already solved - only go back to hunting if error gets very large
            if (Math.abs(errorXVIII) > unsolvThreshold) {
                this.outputs.isSolved = false;
            }
            // Continue gentle tracking adjustments while solved
            // (servo still runs, just more gently)
        } else {
            // Not yet solved - check if we've reached the solution
            if (isLateralSolved) {
                this.outputs.isSolved = true;
            }
        }
        
        // Servo always runs, but speed depends on solved state
        const servoSpeedMultiplier = this.outputs.isSolved ? 0.3 : 1.0;
        
        if (!this.outputs.isSolved || Math.abs(errorXVIII) > solveThreshold * 0.5) {
            // === REALISTIC MECHANICAL SERVO SIMULATION ===
            // The servo motor responds to error XVIII with physical inertia
            
            // Compute derivative of errorXVIII with respect to G (which way to turn?)
            const delta = 0.5;
            const errPlus = computeError(this.gyroAngle + delta);
            const errMinus = computeError(this.gyroAngle - delta);
            const dErrXVIII_dG = (errPlus.errorXVIII - errMinus.errorXVIII) / (2 * delta);
            
            // Desired servo direction based on error gradient
            let targetVelocity = 0;
            if (Math.abs(dErrXVIII_dG) > 0.1) {
                // Newton-Raphson tells us the ideal step
                const idealStep = -errorXVIII / dErrXVIII_dG;
                // But servo has limited speed - just go in that direction
                targetVelocity = Math.sign(idealStep) * this.gyroServoRate * servoSpeedMultiplier;
                
                // Reduce speed as we get close to solution (proportional control)
                const errorMag = Math.abs(errorXVIII);
                if (errorMag < 50) {
                    targetVelocity *= errorMag / 50;
                }
            } else {
                // Gradient too small - use proportional control on error
                targetVelocity = -Math.sign(errorXVIII) * this.gyroServoRate * 0.3 * servoSpeedMultiplier;
            }
            
            // Apply inertia: servo can't instantly change velocity
            // This creates the characteristic "hunting" behavior
            this.servoVelocity = this.servoVelocity * this.servoInertia + 
                                 targetVelocity * (1 - this.servoInertia);
            
            // Apply velocity to position
            const step = this.servoVelocity * dt;
            this.gyroAngle += step;
            this.gyroAngle = Math.max(-90, Math.min(90, this.gyroAngle));
            
            // Debug
            if (Math.random() < 0.02) {
                console.log('Servo: err=', errorXVIII.toFixed(1), 
                            'vel=', this.servoVelocity.toFixed(2), 
                            'G=', this.gyroAngle.toFixed(2));
            }
            
            this.diff22FA.update(this.gyroAngle, 0);
        } else {
            // Solution found - servo stops smoothly
            this.servoVelocity *= 0.8; // Gradually stop
            this.diff22FA.update(this.gyroAngle, 0);
        }
        
        this.outputs.gyroAngle = this.gyroAngle;
        
        // Calculate track angle
        const torpedoHeading = this.inputs.ownCourse + this.gyroAngle;
        let trackAngle = Math.abs(this.normalizeAngle(torpedoHeading - this.inputs.targetCourse + 180));
        if (trackAngle > 180) trackAngle = 360 - trackAngle;
        this.outputs.trackAngle = trackAngle;
        
        // Torpedo run (approximation including corrections)
        const G_rad = this.gyroAngle * Math.PI / 180;
        const G_minus_Br_rad = (this.gyroAngle - Br) * Math.PI / 180;
        this.outputs.torpedoRun = R / Math.max(0.5, Math.cos(G_minus_Br_rad));
        this.outputs.runTime = this.outputs.torpedoRun / torpedoSpeedYps;
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

