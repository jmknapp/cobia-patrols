#!/usr/bin/env python3
"""Generate PDF from TDC Analysis markdown using reportlab."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import re

def create_tdc_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.darkblue
    )
    
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontSize=13,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.darkblue
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        leading=14
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=9,
        fontName='Courier',
        backColor=colors.Color(0.95, 0.95, 0.95),
        borderPadding=5,
        spaceAfter=10
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=20,
        bulletIndent=10
    )
    
    story = []
    
    # Title
    story.append(Paragraph("TDC Mark III Torpedo Data Computer", title_style))
    story.append(Paragraph("Technical Analysis and Simulation Documentation", subtitle_style))
    story.append(Spacer(1, 20))
    
    # Overview
    story.append(Paragraph("1. Overview", h1_style))
    story.append(Paragraph(
        "The Torpedo Data Computer (TDC) Mark III was an electromechanical analog computer used aboard "
        "US Navy submarines during World War II. It continuously computed the firing solution for torpedoes "
        "by tracking the relative motion of the submarine and target, then calculating the gyro angle setting "
        "required for the torpedo to intercept the target.",
        body_style
    ))
    
    # Coordinate System
    story.append(Paragraph("2. Coordinate System and Conventions", h1_style))
    
    story.append(Paragraph("2.1 Angles", h2_style))
    angles_data = [
        ["Symbol", "Name", "Definition"],
        ["B", "True Bearing", "Direction from own ship to target (0°-360° from north)"],
        ["Co", "Own Course", "Submarine's heading (0°-360° from north)"],
        ["C", "Target Course", "Target ship's heading (0°-360° from north)"],
        ["Br", "Relative Bearing", "Br = B - Co"],
        ["G", "Gyro Angle", "Torpedo steering angle (+ = starboard, - = port)"],
        ["A", "Target Angle", "A = B + 180° - C"],
        ["I", "Impact Angle", "I = A + (G - Br)"],
    ]
    t = Table(angles_data, colWidths=[0.7*inch, 1.3*inch, 4*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("2.2 Distances and Speeds", h2_style))
    dist_data = [
        ["Symbol", "Name", "Units"],
        ["R", "Range (own ship to target)", "yards"],
        ["So", "Own Speed", "knots"],
        ["S", "Target Speed", "knots"],
        ["Vt", "Torpedo Speed", "knots (typically 46)"],
        ["H", "Target travel during torpedo run", "yards (= S × run time)"],
        ["P", "Reach (initial straight run)", "yards (~75)"],
        ["J", "Transfer (lateral displacement)", "yards"],
    ]
    t = Table(dist_data, colWidths=[0.7*inch, 2.8*inch, 2.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))
    
    # Fire Control Problem
    story.append(Paragraph("3. The Fire Control Problem", h1_style))
    story.append(Paragraph(
        "The fundamental problem is: <b>Given the current positions and velocities of submarine and target, "
        "at what angle should the torpedo be fired to intercept the target?</b>",
        body_style
    ))
    story.append(Paragraph(
        "The torpedo must be aimed at where the target <i>will be</i>, not where it <i>is now</i>. "
        "This requires predicting the target's future position based on its course and speed, and computing "
        "the torpedo trajectory that will intersect that position.",
        body_style
    ))
    
    # TDC Sections
    story.append(Paragraph("4. TDC Mechanical Sections", h1_style))
    
    story.append(Paragraph("4.1 Position Keeper", h2_style))
    story.append(Paragraph(
        "The Position Keeper continuously tracks the changing geometry as both ships move. "
        "It uses mechanical integrators to accumulate the effects of motion over time.",
        body_style
    ))
    story.append(Paragraph("<b>Key Components:</b>", body_style))
    story.append(Paragraph("• <b>Differential 7</b>: Computes Relative Bearing: Br = B - Co", bullet_style))
    story.append(Paragraph("• <b>Differential 33</b>: Computes Target Angle: A = (B + 180°) - C", bullet_style))
    story.append(Paragraph("• <b>Resolver 13</b>: Converts Br to sin(Br) and cos(Br)", bullet_style))
    story.append(Paragraph("• <b>Resolver 34</b>: Converts A to sin(A) and cos(A)", bullet_style))
    story.append(Paragraph("• <b>Integrators 14, 15</b>: Accumulate own ship motion components", bullet_style))
    story.append(Paragraph("• <b>Integrators 35, 36</b>: Accumulate target motion components", bullet_style))
    
    story.append(Paragraph("4.2 Angle Solver", h2_style))
    story.append(Paragraph(
        "The Angle Solver finds the gyro angle G that produces a valid intercept solution. "
        "It implements two fundamental equations that must simultaneously equal zero.",
        body_style
    ))
    
    # Fundamental Equations
    story.append(Paragraph("5. The Fundamental Equations", h1_style))
    
    story.append(Paragraph("<b>Equation XVII (Range/Line-of-Sight Balance):</b>", body_style))
    story.append(Paragraph("R·cos(G - Br) = H·cos(I) + Us + P·cos(G)", code_style))
    story.append(Paragraph(
        "Physical Meaning: The projection of range along the torpedo's path must equal the sum of "
        "target's travel projected along the impact direction, pseudo-run distance, and reach projected "
        "along gyro direction.",
        body_style
    ))
    
    story.append(Paragraph("<b>Equation XVIII (Lateral Balance):</b>", body_style))
    story.append(Paragraph("R·sin(G - Br) = H·sin(I) + J + P·sin(G)", code_style))
    story.append(Paragraph(
        "Physical Meaning: The lateral offset from own ship to target must equal target's travel "
        "projected perpendicular to impact, transfer distance, and reach projected perpendicular to gyro direction.",
        body_style
    ))
    
    story.append(Paragraph("<b>Error Form:</b>", body_style))
    story.append(Paragraph("Error XVII  = R·cos(G-Br) - H·cos(I) - Us - P·cos(G)", code_style))
    story.append(Paragraph("Error XVIII = R·sin(G-Br) - H·sin(I) - J - P·sin(G)", code_style))
    story.append(Paragraph("When both errors are zero, the gyro angle G is correct.", body_style))
    
    # Servo Feedback
    story.append(Paragraph("6. Servo Feedback Mechanism", h1_style))
    story.append(Paragraph(
        "The TDC uses mechanical feedback to find the solution:",
        body_style
    ))
    story.append(Paragraph("1. <b>Error Computation</b>: The mechanism continuously computes Error XVII and Error XVIII", bullet_style))
    story.append(Paragraph("2. <b>Servo Response</b>: A servo motor adjusts the gyro angle based on the errors", bullet_style))
    story.append(Paragraph("3. <b>Feedback Loop</b>: The adjusted gyro angle feeds back into the computation", bullet_style))
    story.append(Paragraph("4. <b>Convergence</b>: The loop continues until both errors approach zero", bullet_style))
    
    story.append(Paragraph("<b>Feedback Direction:</b>", body_style))
    story.append(Paragraph("ΔG ∝ -Error XVIII", code_style))
    story.append(Paragraph("• Positive Error XVIII: Torpedo leading too much → Decrease G", bullet_style))
    story.append(Paragraph("• Negative Error XVIII: Torpedo trailing → Increase G", bullet_style))
    
    story.append(PageBreak())
    
    # Mechanical Components
    story.append(Paragraph("7. Mechanical Components", h1_style))
    
    story.append(Paragraph("7.1 Differential", h2_style))
    story.append(Paragraph(
        "A bevel gear differential adds or subtracts two rotational inputs: Output = Input₁ ± Input₂. "
        "Used for computing Br = B - Co, A = B + 180 - C, etc.",
        body_style
    ))
    
    story.append(Paragraph("7.2 Integrator (Disc and Roller)", h2_style))
    story.append(Paragraph(
        "Performs mechanical integration: Output = ∫(roller_position × disc_rate)dt. "
        "The disc rotates at a rate proportional to speed, the roller position is set by sin/cos of angles, "
        "and the output wheel accumulates the product over time.",
        body_style
    ))
    
    story.append(Paragraph("7.3 Resolver", h2_style))
    story.append(Paragraph(
        "Converts an angle input to sin and cos outputs using cam followers or gear linkages. "
        "Input: θ (degrees) → Outputs: sin(θ), cos(θ)",
        body_style
    ))
    
    story.append(Paragraph("7.4 Cam", h2_style))
    story.append(Paragraph(
        "Provides non-linear function outputs based on the gyro angle. Used for torpedo reach (P), "
        "transfer (J), and pseudo-run (Us) which vary with gyro setting.",
        body_style
    ))
    
    # Inputs
    story.append(Paragraph("8. Simulation Inputs", h1_style))
    inputs_data = [
        ["Input", "Symbol", "Units", "Typical Range", "Source"],
        ["Own Course", "Co", "degrees", "0-360", "Ship's gyrocompass"],
        ["Own Speed", "So", "knots", "2-10", "Pit log"],
        ["Target Bearing", "B", "degrees", "0-360", "Periscope/TBT"],
        ["Target Range", "R", "yards", "500-10,000", "Stadimeter/Radar"],
        ["Target Course", "C", "degrees", "0-360", "Estimated"],
        ["Target Speed", "S", "knots", "5-20", "Estimated"],
    ]
    t = Table(inputs_data, colWidths=[1.1*inch, 0.6*inch, 0.6*inch, 0.9*inch, 1.4*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    
    # Outputs
    story.append(Paragraph("9. Simulation Outputs", h1_style))
    outputs_data = [
        ["Output", "Symbol", "Units", "Description"],
        ["Gyro Angle", "G", "degrees", "Torpedo steering angle (±90°)"],
        ["Relative Bearing", "Br", "degrees", "B - Co"],
        ["Target Angle", "A", "degrees", "Angle on bow from target's perspective"],
        ["Track Angle", "-", "degrees", "Angle torpedo crosses target's track"],
        ["Torpedo Run", "-", "yards", "Distance torpedo travels to intercept"],
        ["Run Time", "-", "seconds", "Time for torpedo to reach intercept"],
        ["Solution Status", "-", "boolean", "Whether valid solution exists"],
    ]
    t = Table(outputs_data, colWidths=[1.2*inch, 0.6*inch, 0.7*inch, 2.8*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    
    # Solution Validity
    story.append(Paragraph("10. Solution Validity", h1_style))
    story.append(Paragraph("A valid solution requires:", body_style))
    story.append(Paragraph("1. <b>Torpedo faster than target</b>: Vt > S", bullet_style))
    story.append(Paragraph("2. <b>Geometry allows intercept</b>: Target not moving directly away", bullet_style))
    story.append(Paragraph("3. <b>Gyro angle within limits</b>: Typically -90° to +90°", bullet_style))
    story.append(Paragraph("4. <b>Range within torpedo endurance</b>: Run distance < maximum range", bullet_style))
    
    # Historical Context
    story.append(Paragraph("11. Historical Context", h1_style))
    story.append(Paragraph(
        "The TDC Mark III was a remarkable engineering achievement:",
        body_style
    ))
    story.append(Paragraph("• Weighed approximately 700 pounds", bullet_style))
    story.append(Paragraph("• Contained over 1,500 precision parts", bullet_style))
    story.append(Paragraph("• Used no electronic computation (purely mechanical)", bullet_style))
    story.append(Paragraph("• Could track targets and maintain solutions continuously", bullet_style))
    story.append(Paragraph("• Transmitted gyro angle settings directly to torpedoes in tubes", bullet_style))
    story.append(Paragraph(
        "The TDC gave US submarines a significant advantage in WWII, enabling accurate torpedo attacks "
        "from various approach angles and speeds.",
        body_style
    ))
    
    # References
    story.append(Paragraph("12. References", h1_style))
    story.append(Paragraph("• <b>OP 1631</b>: Torpedo Data Computer Mark III, Bureau of Ordnance, US Navy", bullet_style))
    story.append(Paragraph("• <b>OP 1665</b>: Fire Control Fundamentals, Bureau of Ordnance", bullet_style))
    story.append(Paragraph("• <b>NavPers 16166</b>: Submarine Torpedo Fire Control Manual", bullet_style))
    
    # Conversion Factors
    story.append(Paragraph("Appendix A: Conversion Factors", h1_style))
    conv_data = [
        ["Conversion", "Value"],
        ["Yards per Nautical Mile", "2,025.4"],
        ["Knots to Yards/Second", "0.5626 (2025.4 / 3600)"],
        ["Degrees to Radians", "π / 180"],
    ]
    t = Table(conv_data, colWidths=[2.5*inch, 2.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        "<i>Document generated from USS Cobia Patrol Reports TDC Simulation</i><br/>"
        "<i>https://cobiapatrols.com/tdc</i>",
        ParagraphStyle('Footer', parent=body_style, alignment=TA_CENTER, textColor=colors.grey)
    ))
    
    doc.build(story)
    print(f"PDF created: {output_path}")

if __name__ == "__main__":
    create_tdc_pdf("TDC_Mark_III_Analysis.pdf")

