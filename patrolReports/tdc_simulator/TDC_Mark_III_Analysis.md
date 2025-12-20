# TDC Mark III Torpedo Data Computer
## Technical Analysis and Simulation Documentation

---

## Overview

The Torpedo Data Computer (TDC) Mark III was an electromechanical analog computer used aboard US Navy submarines during World War II. It continuously computed the firing solution for torpedoes by tracking the relative motion of the submarine and target, then calculating the gyro angle setting required for the torpedo to intercept the target.

This document describes the mathematical foundations, mechanical components, and simulation implementation of the TDC Mark III.

---

## 1. Coordinate System and Conventions

### Angles
- **True Bearing (B)**: Direction from own ship to target, measured clockwise from true north (0°-360°)
- **Own Course (Co)**: Submarine's heading, measured clockwise from true north
- **Target Course (C)**: Target ship's heading, measured clockwise from true north
- **Relative Bearing (Br)**: Direction to target relative to own ship's bow: `Br = B - Co`
- **Gyro Angle (G)**: Angle the torpedo turns after launch, relative to own ship's heading (positive = starboard, negative = port)
- **Target Angle (A)**: Angle from target's bow to the line of sight: `A = B + 180° - C`
- **Impact Angle (I)**: Angle at which torpedo crosses target's track: `I = A + (G - Br)`

### Distances and Speeds
- **Range (R)**: Distance from own ship to target (yards)
- **Own Speed (So)**: Submarine's speed (knots)
- **Target Speed (S)**: Target ship's speed (knots)
- **Torpedo Speed (Vt)**: Typically 46 knots for Mark 14/18 torpedoes
- **H**: Target travel during torpedo run = S × (torpedo run time)

### Torpedo Characteristics
- **P (Reach)**: Initial straight run distance before gyro engages (~75 yards)
- **J (Transfer)**: Lateral displacement during the turn
- **Us (Pseudo-run)**: Effective additional run due to turn geometry

---

## 2. The Fire Control Problem

The fundamental problem is: **Given the current positions and velocities of submarine and target, at what angle should the torpedo be fired to intercept the target?**

### Geometry of Intercept

```
                    Target at T₁ (future)
                         ●
                        /|
                       / |
            H (target / |
              travel)/  |
                    /   |
                   /    | Torpedo
        Target at ●     | Run
        T₀ (now)   \    |
                    \   |
                  R  \  |
              (range) \ |
                       \|
                        ● Own Ship
```

The torpedo must be aimed at where the target **will be**, not where it **is now**.

---

## 3. TDC Mechanical Sections

### 3.1 Position Keeper

The Position Keeper continuously tracks the changing geometry as both ships move. It uses mechanical integrators to accumulate the effects of motion over time.

**Key Components:**
- **Differential 7**: Computes Relative Bearing: `Br = B - Co`
- **Differential 33**: Computes Target Angle: `A = (B + 180°) - C`
- **Resolver 13**: Converts Br to sin(Br) and cos(Br)
- **Resolver 34**: Converts A to sin(A) and cos(A)
- **Integrators 14, 15**: Accumulate own ship motion components:
  - `∫ So·sin(Br)·dt` (lateral component)
  - `∫ So·cos(Br)·dt` (line-of-sight component)
- **Integrators 35, 36**: Accumulate target motion components:
  - `∫ S·sin(A)·dt`
  - `∫ S·cos(A)·dt`
- **Differentials 28, 29**: Combine motion components to update bearing and range

### 3.2 Angle Solver

The Angle Solver finds the gyro angle G that produces a valid intercept solution. It implements two fundamental equations that must simultaneously equal zero.

---

## 4. The Fundamental Equations

### Equation XVII (Range/Line-of-Sight Balance)

```
R·cos(G - Br) = H·cos(I) + Us + P·cos(G)
```

**Physical Meaning**: The projection of range along the torpedo's path must equal the sum of:
- Target's travel projected along the impact direction
- Pseudo-run distance
- Reach projected along gyro direction

### Equation XVIII (Lateral Balance)

```
R·sin(G - Br) = H·sin(I) + J + P·sin(G)
```

**Physical Meaning**: The lateral offset from own ship to target must equal:
- Target's travel projected perpendicular to impact
- Transfer distance
- Reach projected perpendicular to gyro direction

### Error Form

The TDC computes errors from these equations:

```
Error XVII  = R·cos(G - Br) - H·cos(I) - Us - P·cos(G)
Error XVIII = R·sin(G - Br) - H·sin(I) - J - P·sin(G)
```

When both errors are zero, the gyro angle G is correct.

---

## 5. Servo Feedback Mechanism

The TDC uses mechanical feedback to find the solution:

1. **Error Computation**: The mechanism continuously computes Error XVII and Error XVIII
2. **Servo Response**: A servo motor adjusts the gyro angle based on the errors
3. **Feedback Loop**: The adjusted gyro angle feeds back into the computation
4. **Convergence**: The loop continues until both errors approach zero

### Feedback Direction

```
ΔG ∝ -Error XVIII
```

- **Positive Error XVIII**: Torpedo is leading too much → Decrease G
- **Negative Error XVIII**: Torpedo is trailing → Increase G

---

## 6. Mechanical Components

### 6.1 Differential

A bevel gear differential adds or subtracts two rotational inputs.

```
Output = Input₁ ± Input₂
```

Used for computing Br = B - Co, A = B + 180 - C, etc.

### 6.2 Integrator (Disc and Roller)

Performs mechanical integration by multiplying and accumulating.

```
Output = ∫ (roller_position × disc_rate) dt
```

- The disc rotates at a rate proportional to speed
- The roller position (from center) is set by sin/cos of angles
- The output wheel accumulates the product over time

### 6.3 Resolver

Converts an angle input to sin and cos outputs using cam followers or gear linkages.

```
Input: θ (degrees)
Outputs: sin(θ), cos(θ)
```

### 6.4 Cam

Provides non-linear function outputs based on the gyro angle. Used for torpedo reach (P), transfer (J), and pseudo-run (Us) which vary with gyro setting.

---

## 7. Simulation Inputs

| Input | Symbol | Units | Typical Range | Source |
|-------|--------|-------|---------------|--------|
| Own Course | Co | degrees | 0-360 | Ship's gyrocompass |
| Own Speed | So | knots | 2-10 | Pit log |
| Target Bearing | B | degrees | 0-360 | Periscope/TBT |
| Target Range | R | yards | 500-10,000 | Stadimeter/Radar |
| Target Course | C | degrees | 0-360 | Estimated from observations |
| Target Speed | S | knots | 5-20 | Estimated from observations |

---

## 8. Simulation Outputs

| Output | Symbol | Units | Description |
|--------|--------|-------|-------------|
| Gyro Angle | G | degrees | Torpedo steering angle (±90°) |
| Relative Bearing | Br | degrees | B - Co |
| Target Angle | A | degrees | Angle on bow from target's perspective |
| Track Angle | - | degrees | Angle torpedo crosses target's track |
| Torpedo Run | - | yards | Distance torpedo travels to intercept |
| Run Time | - | seconds | Time for torpedo to reach intercept |
| Solution Status | - | boolean | Whether valid solution exists |

---

## 9. Solution Validity

A valid solution requires:

1. **Torpedo faster than target**: Vt > S (otherwise torpedo can never catch up)
2. **Geometry allows intercept**: Target not moving directly away faster than torpedo closing rate
3. **Gyro angle within limits**: Typically -90° to +90°
4. **Range within torpedo endurance**: Run distance < maximum torpedo range

---

## 10. Simplified vs Full Implementation

### Current Simulation Simplifications

1. **Torpedo characteristics**: P, J, Us are simplified
   - P (Reach) = 75 yards (fixed)
   - J (Transfer) = 0 (ignored)
   - Us (Pseudo-run) = 0 (ignored)

2. **Straight-line torpedo run**: Actual torpedo follows curved path during gyro turn

3. **Instantaneous updates**: Real TDC has mechanical time delays

### Full Implementation Would Include

1. Cam curves for P, J, Us as functions of gyro angle
2. Speed ring corrections for torpedo speed variations
3. Parallax corrections for periscope offset
4. Own ship acceleration effects
5. Torpedo ballistic variations

---

## 11. Historical Context

The TDC Mark III was a remarkable engineering achievement. It:

- Weighed approximately 700 pounds
- Contained over 1,500 precision parts
- Used no electronic computation (purely mechanical)
- Could track targets and maintain solutions continuously
- Transmitted gyro angle settings directly to torpedoes in tubes

The TDC gave US submarines a significant advantage in WWII, enabling accurate torpedo attacks from various approach angles and speeds.

---

## 12. References

1. **OP 1631**: Torpedo Data Computer Mark III, Bureau of Ordnance, US Navy
2. **OP 1665**: Fire Control Fundamentals, Bureau of Ordnance
3. **NavPers 16166**: Submarine Torpedo Fire Control Manual

---

## Appendix A: Conversion Factors

| Conversion | Value |
|------------|-------|
| Yards per Nautical Mile | 2,025.4 |
| Knots to Yards/Second | 0.5626 (2025.4 / 3600) |
| Degrees to Radians | π / 180 |

---

## Appendix B: Equation Derivation

Starting from the intercept geometry:

**At intercept time T:**
- Torpedo position = Own Ship position + Torpedo velocity × T
- Target position = Initial Target position + Target velocity × T

**These must be equal:**

Let the torpedo heading be (Co + G), then:
- Torpedo travels: Vt × T at heading (Co + G)
- Target travels: S × T at heading C

Projecting onto the line-of-sight (Br direction) and perpendicular gives Equations XVII and XVIII.

---

*Document generated from USS Cobia Patrol Reports TDC Simulation*
*https://cobiapatrols.com/tdc*

