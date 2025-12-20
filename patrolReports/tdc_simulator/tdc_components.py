"""
TDC Mark III Component Models and Topology

This module defines the mechanical components of the Torpedo Data Computer
and their interconnections, enabling simulation of the analog computer's operation.

Based on Bureau of Ordnance OP 1631 (Torpedo Data Computer Mark III Manual)
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum


class ComponentType(Enum):
    DIFFERENTIAL = "differential"
    INTEGRATOR = "integrator"
    RESOLVER = "resolver"
    CAM = "cam"
    SYNCHRO = "synchro"
    FOLLOWUP_HEAD = "followup_head"
    FOLLOWUP_MOTOR = "followup_motor"
    TIME_MOTOR = "time_motor"
    DIVIDER = "divider"
    INPUT = "input"
    OUTPUT = "output"


@dataclass
class Component:
    """Base class for TDC mechanical components"""
    id: str
    name: str
    component_type: ComponentType
    inputs: List[str] = field(default_factory=list)
    output_value: float = 0.0
    rotation_angle: float = 0.0  # For visualization (degrees)
    rotation_speed: float = 0.0  # For animation (deg/sec)
    
    def update(self, dt: float, input_values: Dict[str, float]) -> float:
        """Update component state and return output value"""
        raise NotImplementedError


@dataclass
class Differential(Component):
    """
    Bevel gear differential - adds or subtracts two rotational inputs.
    
    Output = (Input1 + Input2) / 2, then doubled by 2:1 gears
    Net effect: Output = Input1 + Input2 (or Input1 - Input2 if one is negative)
    """
    component_type: ComponentType = ComponentType.DIFFERENTIAL
    operation: str = "add"  # "add" or "subtract"
    
    def update(self, dt: float, input_values: Dict[str, float]) -> float:
        if len(self.inputs) >= 2:
            val1 = input_values.get(self.inputs[0], 0.0)
            val2 = input_values.get(self.inputs[1], 0.0)
            if self.operation == "add":
                self.output_value = val1 + val2
            else:
                self.output_value = val1 - val2
        elif len(self.inputs) == 1:
            self.output_value = input_values.get(self.inputs[0], 0.0)
        
        # Animation: rotation proportional to output
        self.rotation_angle = (self.rotation_angle + self.output_value * dt * 10) % 360
        return self.output_value


@dataclass
class Integrator(Component):
    """
    Mechanical integrator - multiplies and accumulates.
    
    Uses a disc and roller mechanism:
    - Disc rotates at rate proportional to one input (e.g., time)
    - Roller position set by another input (e.g., speed)
    - Output = integral of (roller_position × disc_rotation)
    
    Mechanically: output_rotation = ∫(roller_offset × disc_angular_velocity) dt
    """
    component_type: ComponentType = ComponentType.INTEGRATOR
    roller_position: float = 0.0  # Offset from center (-1 to +1 normalized)
    disc_rotation: float = 0.0
    accumulated: float = 0.0
    
    def update(self, dt: float, input_values: Dict[str, float]) -> float:
        # Input 0: roller position (multiplicand)
        # Input 1: disc rotation rate (time derivative)
        if len(self.inputs) >= 2:
            self.roller_position = input_values.get(self.inputs[0], 0.0)
            disc_rate = input_values.get(self.inputs[1], 0.0)
            
            # Integrate: output += roller_position × disc_rate × dt
            self.accumulated += self.roller_position * disc_rate * dt
            self.output_value = self.accumulated
            
            # Animation
            self.disc_rotation = (self.disc_rotation + disc_rate * dt * 10) % 360
            self.rotation_angle = self.disc_rotation
        
        return self.output_value


@dataclass  
class Resolver(Component):
    """
    Mechanical resolver - converts polar to rectangular coordinates.
    
    Given an angle θ, produces sin(θ) and cos(θ) outputs.
    Uses specially-shaped cams or gear mechanisms.
    """
    component_type: ComponentType = ComponentType.RESOLVER
    sin_output: float = 0.0
    cos_output: float = 0.0
    
    def update(self, dt: float, input_values: Dict[str, float]) -> float:
        if len(self.inputs) >= 1:
            angle_deg = input_values.get(self.inputs[0], 0.0)
            angle_rad = math.radians(angle_deg)
            self.sin_output = math.sin(angle_rad)
            self.cos_output = math.cos(angle_rad)
            self.output_value = angle_deg  # Pass through angle
            self.rotation_angle = angle_deg % 360
        
        return self.output_value
    
    def get_sin(self) -> float:
        return self.sin_output
    
    def get_cos(self) -> float:
        return self.cos_output


@dataclass
class Cam(Component):
    """
    Cam mechanism - implements arbitrary functions via shaped profile.
    
    Common TDC cams:
    - Reach cam: torpedo initial straight run distance
    - Transfer cam: lateral displacement during turn
    - Speed cams: various speed-dependent corrections
    """
    component_type: ComponentType = ComponentType.CAM
    cam_function: Optional[Callable[[float], float]] = None
    cam_type: str = "linear"  # "linear", "sin", "cos", "reach", "transfer"
    
    def __post_init__(self):
        if self.cam_function is None:
            self.cam_function = self._get_default_function()
    
    def _get_default_function(self) -> Callable[[float], float]:
        if self.cam_type == "sin":
            return lambda x: math.sin(math.radians(x))
        elif self.cam_type == "cos":
            return lambda x: math.cos(math.radians(x))
        elif self.cam_type == "reach":
            # Torpedo reach (P) as function of gyro angle
            # Simplified model
            return lambda g: 75 + abs(g) * 0.5  # yards
        elif self.cam_type == "transfer":
            # Torpedo lateral transfer (J) as function of gyro angle
            return lambda g: abs(g) * 2  # simplified
        else:
            return lambda x: x
    
    def update(self, dt: float, input_values: Dict[str, float]) -> float:
        if len(self.inputs) >= 1:
            input_val = input_values.get(self.inputs[0], 0.0)
            self.output_value = self.cam_function(input_val)
            self.rotation_angle = (input_val * 2) % 360  # Animation
        
        return self.output_value


@dataclass
class Synchro(Component):
    """
    Synchro transmitter/receiver - electrical angle transmission.
    
    Converts mechanical rotation to electrical signals and back.
    Used to transmit values between TDC sections.
    """
    component_type: ComponentType = ComponentType.SYNCHRO
    transmitted_angle: float = 0.0
    
    def update(self, dt: float, input_values: Dict[str, float]) -> float:
        if len(self.inputs) >= 1:
            self.transmitted_angle = input_values.get(self.inputs[0], 0.0)
            self.output_value = self.transmitted_angle
            self.rotation_angle = self.transmitted_angle % 360
        
        return self.output_value


# =============================================================================
# TDC TOPOLOGY DEFINITION
# Based on OP 1631 Position Keeper and Angle Solver schematics
# =============================================================================

def create_position_keeper() -> Dict[str, Component]:
    """
    Create the Position Keeper section of the TDC.
    
    Inputs: So (Own Speed), Co (Own Course), S (Target Speed), C (Target Course),
            B (True Target Bearing), R (Range)
    
    Outputs: Br (Relative Target Bearing), A (Target Angle), 
             ΔR (Change in Range), ΔB (Change in Bearing)
    """
    components = {}
    
    # Input components
    components['So'] = Component(id='So', name='Own Speed', 
                                  component_type=ComponentType.INPUT, inputs=[])
    components['Co'] = Component(id='Co', name='Own Course',
                                  component_type=ComponentType.INPUT, inputs=[])
    components['S'] = Component(id='S', name='Target Speed',
                                 component_type=ComponentType.INPUT, inputs=[])
    components['C'] = Component(id='C', name='Target Course',
                                 component_type=ComponentType.INPUT, inputs=[])
    components['B'] = Component(id='B', name='True Target Bearing',
                                 component_type=ComponentType.INPUT, inputs=[])
    components['R'] = Component(id='R', name='Range',
                                 component_type=ComponentType.INPUT, inputs=[])
    
    # Differential 7: Br = B - Co (Relative Target Bearing)
    components['diff_7'] = Differential(
        id='diff_7', name='Differential 7 (B - Co)',
        inputs=['B', 'Co'], operation='subtract'
    )
    
    # Differential 33: A = B + 180 - C (Target Angle)
    components['diff_33'] = Differential(
        id='diff_33', name='Differential 33 (A = B + 180 - C)',
        inputs=['B_plus_180', 'C'], operation='subtract'
    )
    
    # Resolver 13: Resolve Br into sin(Br) and cos(Br)
    components['resolver_13'] = Resolver(
        id='resolver_13', name='Resolver 13 (sin/cos Br)',
        inputs=['diff_7']  # Br
    )
    
    # Resolver 34: Resolve A into sin(A) and cos(A)  
    components['resolver_34'] = Resolver(
        id='resolver_34', name='Resolver 34 (sin/cos A)',
        inputs=['diff_33']  # A
    )
    
    # Integrator 20: ∫So·dT (Own Ship travel)
    components['int_20'] = Integrator(
        id='int_20', name='Integrator 20 (∫So·dT)',
        inputs=['So', 'dT']
    )
    
    # Integrator 25: ∫S·dT (Target travel)
    components['int_25'] = Integrator(
        id='int_25', name='Integrator 25 (∫S·dT)',
        inputs=['S', 'dT']
    )
    
    # Integrator 14: ∫So·sin(Br)·dT
    components['int_14'] = Integrator(
        id='int_14', name='Integrator 14 (∫So·sinBr·dT)',
        inputs=['resolver_13_sin', 'int_20']
    )
    
    # Integrator 15: ∫So·cos(Br)·dT
    components['int_15'] = Integrator(
        id='int_15', name='Integrator 15 (∫So·cosBr·dT)',
        inputs=['resolver_13_cos', 'int_20']
    )
    
    # Integrator 35: ∫S·sin(A)·dT
    components['int_35'] = Integrator(
        id='int_35', name='Integrator 35 (∫S·sinA·dT)',
        inputs=['resolver_34_sin', 'int_25']
    )
    
    # Integrator 36: ∫S·cos(A)·dT
    components['int_36'] = Integrator(
        id='int_36', name='Integrator 36 (∫S·cosA·dT)',
        inputs=['resolver_34_cos', 'int_25']
    )
    
    # Differential 28: RdB = ∫So·sinBr·dT + ∫S·sinA·dT
    components['diff_28'] = Differential(
        id='diff_28', name='Differential 28 (R·dB)',
        inputs=['int_14', 'int_35'], operation='add'
    )
    
    # Differential 29: dR = ∫So·cosBr·dT + ∫S·cosA·dT
    components['diff_29'] = Differential(
        id='diff_29', name='Differential 29 (dR)',
        inputs=['int_15', 'int_36'], operation='add'
    )
    
    # Output components
    components['Br'] = Component(id='Br', name='Relative Target Bearing',
                                  component_type=ComponentType.OUTPUT, inputs=['diff_7'])
    components['A'] = Component(id='A', name='Target Angle',
                                 component_type=ComponentType.OUTPUT, inputs=['diff_33'])
    components['dR'] = Component(id='dR', name='Change in Range',
                                  component_type=ComponentType.OUTPUT, inputs=['diff_29'])
    components['RdB'] = Component(id='RdB', name='R × Change in Bearing',
                                   component_type=ComponentType.OUTPUT, inputs=['diff_28'])
    
    return components


def create_angle_solver() -> Dict[str, Component]:
    """
    Create the Angle Solver section of the TDC.
    
    Inputs: R, Br, A, S (from Position Keeper), torpedo characteristics
    
    Outputs: G (Gyro Angle), I (Impact Angle), U (Torpedo Run)
    """
    components = {}
    
    # Inputs from Position Keeper
    components['R_in'] = Component(id='R_in', name='Range (from PK)',
                                    component_type=ComponentType.INPUT, inputs=[])
    components['Br_in'] = Component(id='Br_in', name='Rel Bearing (from PK)',
                                     component_type=ComponentType.INPUT, inputs=[])
    components['A_in'] = Component(id='A_in', name='Target Angle (from PK)',
                                    component_type=ComponentType.INPUT, inputs=[])
    components['S_in'] = Component(id='S_in', name='Target Speed (from PK)',
                                    component_type=ComponentType.INPUT, inputs=[])
    
    # Torpedo characteristics (manual inputs)
    components['Sz'] = Component(id='Sz', name='Torpedo Speed',
                                  component_type=ComponentType.INPUT, inputs=[])
    
    # Resolver 2FA: R·sin(G-Br), R·cos(G-Br)
    components['resolver_2FA'] = Resolver(
        id='resolver_2FA', name='Resolver 2FA (G-Br)',
        inputs=['G_minus_Br']
    )
    
    # Resolver 16FA: H·sin(I), H·cos(I)
    components['resolver_16FA'] = Resolver(
        id='resolver_16FA', name='Resolver 16FA (I)',
        inputs=['I']
    )
    
    # Resolver 58FA: P·sin(G), P·cos(G)
    components['resolver_58FA'] = Resolver(
        id='resolver_58FA', name='Resolver 58FA (G)',
        inputs=['G']
    )
    
    # Cam 48FA: M·cos(G)
    components['cam_48FA'] = Cam(
        id='cam_48FA', name='Cam 48FA (M·cosG)',
        inputs=['G'], cam_type='cos'
    )
    
    # Cam 49FA: M·sin(G)
    components['cam_49FA'] = Cam(
        id='cam_49FA', name='Cam 49FA (M·sinG)',
        inputs=['G'], cam_type='sin'
    )
    
    # Differential 3FA: R·cos(G-Br) - H·cos(I)
    components['diff_3FA'] = Differential(
        id='diff_3FA', name='Diff 3FA (Eq XVII left)',
        inputs=['R_cos_G_Br', 'H_cos_I'], operation='subtract'
    )
    
    # Differential 18FA: R·sin(G-Br) - H·sin(I)
    components['diff_18FA'] = Differential(
        id='diff_18FA', name='Diff 18FA (Eq XVIII left)',
        inputs=['R_sin_G_Br', 'H_sin_I'], operation='subtract'
    )
    
    # Differential 22FA: Gyro Angle output
    components['diff_22FA'] = Differential(
        id='diff_22FA', name='Diff 22FA (Gyro Angle)',
        inputs=['G_minus_Br', 'Br_in'], operation='add'
    )
    
    # Differential 23FA: G + L (Gyro + Offset)
    components['diff_23FA'] = Differential(
        id='diff_23FA', name='Diff 23FA (G + Offset)',
        inputs=['diff_22FA', 'L'], operation='add'
    )
    
    # Outputs
    components['G'] = Component(id='G', name='Gyro Angle',
                                 component_type=ComponentType.OUTPUT, inputs=['diff_22FA'])
    components['I'] = Component(id='I', name='Impact Angle',
                                 component_type=ComponentType.OUTPUT, inputs=['I_calc'])
    components['U'] = Component(id='U', name='Torpedo Run',
                                 component_type=ComponentType.OUTPUT, inputs=['U_calc'])
    
    return components


# =============================================================================
# COMPLETE TDC MODEL
# =============================================================================

@dataclass
class TDCMark3:
    """
    Complete TDC Mark III Simulator
    
    Combines Position Keeper and Angle Solver into a unified model
    that can be stepped through time for visualization.
    """
    position_keeper: Dict[str, Component] = field(default_factory=dict)
    angle_solver: Dict[str, Component] = field(default_factory=dict)
    time: float = 0.0
    dt: float = 0.1  # Time step in seconds
    
    # Current input values
    own_speed: float = 0.0
    own_course: float = 0.0
    target_speed: float = 0.0
    target_course: float = 0.0
    target_bearing: float = 0.0
    target_range: float = 0.0
    
    # Computed outputs
    gyro_angle: float = 0.0
    relative_bearing: float = 0.0
    target_angle: float = 0.0
    
    def __post_init__(self):
        self.position_keeper = create_position_keeper()
        self.angle_solver = create_angle_solver()
    
    def set_inputs(self, own_speed: float, own_course: float,
                   target_speed: float, target_course: float,
                   target_bearing: float, target_range: float):
        """Set the input values for the TDC"""
        self.own_speed = own_speed
        self.own_course = own_course
        self.target_speed = target_speed
        self.target_course = target_course
        self.target_bearing = target_bearing
        self.target_range = target_range
    
    def step(self, dt: float = None) -> Dict[str, float]:
        """
        Advance the simulation by one time step.
        
        Returns dict of all component output values for visualization.
        """
        if dt is None:
            dt = self.dt
        
        self.time += dt
        
        # Build input values dict
        values = {
            'So': self.own_speed,
            'Co': self.own_course,
            'S': self.target_speed,
            'C': self.target_course,
            'B': self.target_bearing,
            'R': self.target_range,
            'dT': dt,
            'B_plus_180': (self.target_bearing + 180) % 360,
        }
        
        # Update Position Keeper components
        # Differential 7: Br = B - Co
        br = self.target_bearing - self.own_course
        while br < -180: br += 360
        while br > 180: br -= 360
        values['diff_7'] = br
        self.relative_bearing = br
        
        # Differential 33: A = B + 180 - C
        a = (self.target_bearing + 180 - self.target_course) % 360
        if a > 180: a -= 360
        values['diff_33'] = a
        self.target_angle = a
        
        # Resolver outputs
        values['resolver_13_sin'] = math.sin(math.radians(br))
        values['resolver_13_cos'] = math.cos(math.radians(br))
        values['resolver_34_sin'] = math.sin(math.radians(a))
        values['resolver_34_cos'] = math.cos(math.radians(a))
        
        # Simplified gyro angle calculation (full iterative solution in tdc_mk3.py)
        # For visualization, use approximate solution
        torpedo_speed = 46.0  # knots
        
        # Estimate intercept bearing
        torpedo_speed_yps = torpedo_speed * 2025.4 / 3600
        target_speed_yps = self.target_speed * 2025.4 / 3600
        
        run_time = self.target_range / torpedo_speed_yps
        target_advance = target_speed_yps * run_time
        
        target_rad = math.radians(self.target_course)
        bearing_rad = math.radians(self.target_bearing)
        
        target_x = self.target_range * math.sin(bearing_rad)
        target_y = self.target_range * math.cos(bearing_rad)
        
        future_x = target_x + target_advance * math.sin(target_rad)
        future_y = target_y + target_advance * math.cos(target_rad)
        
        intercept_bearing = math.degrees(math.atan2(future_x, future_y))
        
        self.gyro_angle = intercept_bearing - self.own_course
        while self.gyro_angle < -180: self.gyro_angle += 360
        while self.gyro_angle > 180: self.gyro_angle -= 360
        
        values['G'] = self.gyro_angle
        values['Br'] = self.relative_bearing
        values['A'] = self.target_angle
        
        # Update component rotation angles for visualization
        for comp_id, comp in self.position_keeper.items():
            if hasattr(comp, 'rotation_angle'):
                comp.rotation_angle = (comp.rotation_angle + values.get(comp_id, 0) * dt) % 360
        
        return values
    
    def get_component_states(self) -> List[Dict]:
        """Get all component states for visualization"""
        states = []
        
        for comp_id, comp in self.position_keeper.items():
            states.append({
                'id': comp_id,
                'name': comp.name,
                'type': comp.component_type.value,
                'rotation': comp.rotation_angle,
                'value': comp.output_value
            })
        
        for comp_id, comp in self.angle_solver.items():
            states.append({
                'id': comp_id,
                'name': comp.name,
                'type': comp.component_type.value,
                'rotation': comp.rotation_angle,
                'value': comp.output_value
            })
        
        return states


if __name__ == '__main__':
    # Test the TDC model
    tdc = TDCMark3()
    tdc.set_inputs(
        own_speed=3.0,
        own_course=281.0,
        target_speed=8.0,
        target_course=115.0,
        target_bearing=291.0,
        target_range=900.0
    )
    
    print("TDC Mark III Component Test")
    print("=" * 50)
    
    # Run a few time steps
    for i in range(5):
        values = tdc.step(0.1)
        print(f"\nTime: {tdc.time:.1f}s")
        print(f"  Relative Bearing (Br): {values['Br']:.1f}°")
        print(f"  Target Angle (A): {values['A']:.1f}°")
        print(f"  Gyro Angle (G): {values['G']:.1f}°")

