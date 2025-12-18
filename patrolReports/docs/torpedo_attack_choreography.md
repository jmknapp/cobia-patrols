# Torpedo Attack Choreography System

## Overview

This document describes the architecture needed to create historically accurate, fully animated torpedo attack visualizations based on USS Cobia's patrol reports.

## Current System Limitations

The existing visualization system has these constraints:

1. **Static Cobia Position**: Cobia doesn't maneuver during the attack (can't show turning between salvos)
2. **Linear Convoy Movement**: All convoy ships move in straight lines on their initial course
3. **No Reactive Behavior**: Escorts don't counterattack, ships don't scatter
4. **Single Geometry Snapshot**: Attack parameters represent one moment in time, not the evolving battle

## Real-World Complexity

Patrol reports describe dynamic multi-phase engagements:

```
0700 I  Fired six tubes forward... Turned left to shoot aft.
0704 I  Fired four tubes aft with a large track, short run.
        Two hits in his screws... These blew depth charges over
        his stern and the escorts headed in.
```

This 4-minute engagement involves:
- Cobia firing forward tubes
- Cobia turning ~180° 
- Cobia firing aft tubes from new heading
- Target being hit multiple times
- Escorts turning to counterattack
- Depth charge attack beginning

---

## Proposed Database Schema

### 1. Attack Events Table

Core table for time-sequenced events during an attack:

```sql
CREATE TABLE attack_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attack_id INT NOT NULL,
    event_time TIME NOT NULL,           -- Absolute time (07:00:00)
    event_sequence INT NOT NULL,        -- Order within attack (1, 2, 3...)
    event_type ENUM(
        'attack_start',
        'fire_salvo',
        'start_maneuver',
        'end_maneuver', 
        'torpedo_hit',
        'torpedo_miss',
        'target_sinks',
        'depth_charge',
        'attack_end'
    ) NOT NULL,
    
    -- Actor (who is doing this)
    actor ENUM('cobia', 'target', 'convoy_ship') NOT NULL,
    actor_ship_id INT NULL,             -- FK to convoy_ships if actor='convoy_ship'
    
    -- State at this moment (for positioning actors)
    course INT,
    speed DECIMAL(4,1),
    latitude DECIMAL(10,6),
    longitude DECIMAL(10,6),
    depth INT,                          -- For Cobia (periscope depth, deep, etc.)
    
    -- For fire_salvo events
    tubes_fired VARCHAR(50),            -- "1,2,3,4,5,6" or "7,8,9,10"
    
    -- For maneuver events
    turn_direction ENUM('left', 'right'),
    turn_degrees INT,
    
    remarks TEXT,
    
    FOREIGN KEY (attack_id) REFERENCES torpedo_attacks(id) ON DELETE CASCADE,
    FOREIGN KEY (actor_ship_id) REFERENCES convoy_ships(id) ON DELETE SET NULL,
    INDEX idx_attack_sequence (attack_id, event_sequence)
);
```

### 2. Ship Behaviors Table

Define reactive behaviors for convoy ships:

```sql
CREATE TABLE ship_behaviors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attack_id INT NOT NULL,
    ship_id INT NOT NULL,               -- FK to convoy_ships
    trigger_event_id INT,               -- What triggers this behavior
    trigger_delay_seconds INT DEFAULT 0, -- Delay after trigger
    
    behavior_type ENUM(
        'continue',                     -- Keep current course/speed
        'turn_toward_cobia',            -- Counterattack
        'turn_away',                    -- Flee
        'scatter',                      -- Random evasion
        'stop',                         -- Dead in water
        'circle',                       -- Search pattern
        'drop_depth_charges'            -- Attack run
    ) NOT NULL,
    
    new_course INT,                     -- Target course (or NULL for calculated)
    new_speed DECIMAL(4,1),
    duration_seconds INT,               -- How long behavior lasts
    
    remarks TEXT,
    
    FOREIGN KEY (attack_id) REFERENCES torpedo_attacks(id) ON DELETE CASCADE,
    FOREIGN KEY (ship_id) REFERENCES convoy_ships(id) ON DELETE CASCADE,
    FOREIGN KEY (trigger_event_id) REFERENCES attack_events(id) ON DELETE SET NULL
);
```

### 3. Enhanced Torpedoes Table

Link torpedoes to specific fire events:

```sql
ALTER TABLE torpedoes_fired 
ADD COLUMN fire_event_id INT,
ADD COLUMN launch_time TIME,
ADD COLUMN impact_time TIME,
ADD FOREIGN KEY (fire_event_id) REFERENCES attack_events(id);
```

---

## Animation Engine Design

### Phase-Based Playback

```javascript
class AttackAnimation {
    constructor(attackData, events, behaviors) {
        this.events = events.sort((a, b) => a.event_sequence - b.event_sequence);
        this.behaviors = behaviors;
        this.actors = new Map();  // ship_id -> current state
        this.currentTime = events[0].event_time;
        this.startTime = events[0].event_time;
    }
    
    // Convert event time to milliseconds from start
    timeToMs(eventTime) {
        return (eventTime - this.startTime) * 1000;
    }
    
    // Get interpolated state for any actor at any time
    getActorState(actorId, currentTime) {
        // Find bracketing events for this actor
        const prevEvent = this.findPreviousEvent(actorId, currentTime);
        const nextEvent = this.findNextEvent(actorId, currentTime);
        
        if (!nextEvent) return prevEvent.state;
        
        // Interpolate position, course, speed
        const progress = (currentTime - prevEvent.time) / (nextEvent.time - prevEvent.time);
        return this.interpolateState(prevEvent.state, nextEvent.state, progress);
    }
    
    // Handle maneuvers (turning)
    interpolateTurn(startCourse, endCourse, direction, progress) {
        // Smooth easing for realistic turn
        const eased = progress * progress * (3 - 2 * progress);
        
        let courseDiff = endCourse - startCourse;
        if (direction === 'left' && courseDiff > 0) courseDiff -= 360;
        if (direction === 'right' && courseDiff < 0) courseDiff += 360;
        
        return (startCourse + courseDiff * eased + 360) % 360;
    }
    
    // Check and trigger reactive behaviors
    checkBehaviorTriggers(currentTime) {
        this.behaviors.forEach(behavior => {
            const triggerEvent = this.events.find(e => e.id === behavior.trigger_event_id);
            if (!triggerEvent) return;
            
            const triggerTime = this.timeToMs(triggerEvent.event_time) + behavior.trigger_delay_seconds * 1000;
            
            if (currentTime >= triggerTime && !behavior.triggered) {
                this.activateBehavior(behavior);
                behavior.triggered = true;
            }
        });
    }
    
    // Main animation loop
    animate(timestamp) {
        const elapsed = timestamp - this.animationStart;
        const simTime = elapsed * this.speedMultiplier;
        
        // Update all actors
        this.checkBehaviorTriggers(simTime);
        
        this.actors.forEach((state, actorId) => {
            const newState = this.getActorState(actorId, simTime);
            this.updateActorPosition(actorId, newState);
        });
        
        // Fire torpedoes at appropriate times
        this.checkTorpedoLaunches(simTime);
        
        // Update torpedo positions
        this.updateTorpedoes(simTime);
        
        this.draw();
        
        if (!this.isComplete(simTime)) {
            requestAnimationFrame(this.animate.bind(this));
        }
    }
}
```

### Torpedo Launch from Events

```javascript
checkTorpedoLaunches(currentTime) {
    this.events
        .filter(e => e.event_type === 'fire_salvo')
        .forEach(event => {
            const fireTime = this.timeToMs(event.event_time);
            
            if (currentTime >= fireTime && !event.fired) {
                const tubes = event.tubes_fired.split(',').map(Number);
                const cobiaState = this.getActorState('cobia', fireTime);
                
                tubes.forEach((tubeNum, index) => {
                    // Stagger launches by firing interval
                    setTimeout(() => {
                        this.launchTorpedo(tubeNum, cobiaState);
                    }, index * this.firingInterval);
                });
                
                event.fired = true;
            }
        });
}
```

---

## Data Entry Example: Attack #4

### Attack Events

| Seq | Time | Type | Actor | Course | Speed | Details |
|-----|------|------|-------|--------|-------|---------|
| 1 | 07:00:00 | attack_start | cobia | 281 | 2.8 | Begin approach |
| 2 | 07:00:00 | fire_salvo | cobia | 281 | 2.8 | tubes: 1,2,3,4,5,6 |
| 3 | 07:00:30 | start_maneuver | cobia | 281 | 5.0 | turn_left, 180° |
| 4 | 07:00:35 | torpedo_hit | target | 115 | 8.0 | Tube 1 hits port amidships |
| 5 | 07:00:38 | torpedo_hit | target | 115 | 4.0 | Tube 2 hits port amidships |
| 6 | 07:02:30 | end_maneuver | cobia | 101 | 5.0 | Turn complete |
| 7 | 07:04:00 | fire_salvo | cobia | 101 | 3.0 | tubes: 7,8,9,10 |
| 8 | 07:04:20 | torpedo_hit | target | 115 | 0 | Tube 8 hits screws |
| 9 | 07:04:25 | torpedo_hit | target | 115 | 0 | Tube 10 hits screws |
| 10 | 07:05:00 | depth_charge | convoy_ship | - | - | CHIDORI attacks |
| 11 | 07:15:00 | target_sinks | target | - | 0 | Arizona Maru sinks |
| 12 | 07:20:00 | attack_end | cobia | 101 | 2.0 | Rigged for depth charge |

### Ship Behaviors

| Ship | Trigger Event | Delay | Behavior | New Course | New Speed |
|------|---------------|-------|----------|------------|-----------|
| CHIDORI | #4 (first hit) | 30s | turn_toward_cobia | (calculated) | 20 |
| Sampan | #4 (first hit) | 60s | turn_away | 295 | 10 |
| Large AK | #4 (first hit) | 45s | scatter | 180 | 12 |
| Small AK | #4 (first hit) | 45s | scatter | 90 | 10 |

---

## Visual Enhancements

### 1. Depth Charge Animation
```javascript
function drawDepthCharge(x, y, depth, detonated) {
    if (detonated) {
        // Underwater explosion effect
        drawUnderwaterExplosion(x, y, depth);
    } else {
        // Sinking depth charge
        ctx.fillStyle = '#333';
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fill();
    }
}
```

### 2. Ship Damage States
```javascript
function drawShip(ship) {
    // Base ship
    drawShipHull(ship.x, ship.y, ship.course, ship.type);
    
    // Damage effects
    if (ship.hits > 0) {
        drawFire(ship.x, ship.y, ship.hits);
    }
    if (ship.listing) {
        drawListingShip(ship.x, ship.y, ship.listAngle);
    }
    if (ship.sinking) {
        drawSinkingShip(ship.x, ship.y, ship.sinkProgress);
    }
}
```

### 3. Wake and Trail Effects
```javascript
function drawWake(ship, history) {
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.beginPath();
    history.forEach((pos, i) => {
        const alpha = 1 - (i / history.length);
        ctx.globalAlpha = alpha * 0.3;
        if (i === 0) ctx.moveTo(pos.x, pos.y);
        else ctx.lineTo(pos.x, pos.y);
    });
    ctx.stroke();
    ctx.globalAlpha = 1;
}
```

---

## Implementation Phases

### Phase 1: Schema & Basic Events (1-2 days)
- Create new database tables
- Migrate existing attack data to event format
- Basic event playback without interpolation

### Phase 2: Cobia Maneuvers (2-3 days)
- Implement turn interpolation
- Fire salvos from dynamic positions
- Handle course changes between salvos

### Phase 3: Convoy Reactions (2-3 days)
- Implement behavior triggers
- Escort counterattack logic
- Ship scatter/flee behaviors

### Phase 4: Visual Polish (1-2 days)
- Damage states and sinking animations
- Depth charge effects
- Wake trails
- Enhanced explosion effects

### Phase 5: Data Entry Tools (2-3 days)
- Admin interface for creating events
- Timeline editor
- Behavior configuration UI
- Preview/test mode

**Total Estimated Effort: 8-13 days**

---

## Alternative: Simplified Choreography

If full choreography is too complex, a middle-ground approach:

### Just Add Cobia Waypoints

```sql
CREATE TABLE cobia_waypoints (
    id INT PRIMARY KEY,
    attack_id INT,
    waypoint_time TIME,
    course INT,
    speed DECIMAL(4,1),
    action VARCHAR(50),  -- 'fire_forward', 'fire_aft', 'evade'
    FOREIGN KEY (attack_id) REFERENCES torpedo_attacks(id)
);
```

This enables multi-salvo attacks without full convoy choreography:

| Time | Course | Speed | Action |
|------|--------|-------|--------|
| 07:00:00 | 281 | 2.8 | fire_forward |
| 07:02:30 | 101 | 5.0 | (turning) |
| 07:04:00 | 101 | 3.0 | fire_aft |

Convoy ships would still move linearly, but Cobia's maneuvers would be accurate.

**Estimated Effort: 2-3 days**

---

## Conclusion

The full choreography system provides historically accurate battle recreations but requires significant development and data entry effort. The simplified waypoint system covers the most visible limitation (Cobia's maneuvers) with much less work.

Recommendation: Start with the simplified waypoint system for Cobia, then evaluate whether full convoy choreography is worth the investment based on user interest and available time.

