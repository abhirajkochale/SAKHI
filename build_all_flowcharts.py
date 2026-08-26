# -*- coding: utf-8 -*-
import os
import subprocess

out_dir_docs = r"C:\GitHub\SAKHI\docs\flowcharts"
out_dir_artifacts = r"C:\Users\abhir\.gemini\antigravity\brain\0b23f962-4bf9-44d4-9fd5-caaeedac01c8\artifacts"
os.makedirs(out_dir_docs, exist_ok=True)
os.makedirs(out_dir_artifacts, exist_ok=True)

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def render_svg_to_png(svg_path, png_path, width, height):
    file_uri = f"file:///{svg_path.replace('\\', '/')}"
    cmd = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        f"--window-size={width},{height}",
        f"--screenshot={png_path}",
        file_uri
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def draw_box(x, y, w, h, title, subtitle="", fill="#FFF0F0", stroke="#800000", title_color="#1A1A1A", rx=6, stroke_dash=""):
    dash_attr = f'stroke-dasharray="{stroke_dash}"' if stroke_dash else ''
    res = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="2" {dash_attr}/>\n'
    if subtitle:
        ty = y + h/2 - 8
        sy = y + h/2 + 12
        res += f'<text x="{x + w/2}" y="{ty}" font-family="Arial" font-size="14" font-weight="bold" fill="{title_color}" text-anchor="middle">{title}</text>\n'
        res += f'<text x="{x + w/2}" y="{sy}" font-family="Arial" font-size="12" fill="#4B5563" text-anchor="middle">{subtitle}</text>\n'
    else:
        ty = y + h/2 + 5
        res += f'<text x="{x + w/2}" y="{ty}" font-family="Arial" font-size="14" font-weight="bold" fill="{title_color}" text-anchor="middle">{title}</text>\n'
    return res

def draw_arrow(x1, y1, x2, y2, color="#374151", stroke_width=2, dash="", marker="arrow"):
    dash_attr = f'stroke-dasharray="{dash}"' if dash else ''
    res = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{stroke_width}" {dash_attr} marker-end="url(#{marker})"/>\n'
    return res

def draw_arrow_label(x, y, text, color="#374151", bg="#FFFFFF"):
    w = len(text) * 7.5 + 12
    return f'<rect x="{x - w/2}" y="{y - 10}" width="{w}" height="20" rx="4" fill="{bg}" stroke="#D1D5DB" stroke-width="1"/>\n<text x="{x}" y="{y + 4}" font-family="Arial" font-size="11" font-weight="bold" fill="{color}" text-anchor="middle">{text}</text>\n'

def make_legend(y_pos, width=1120):
    return f'''
  <!-- Legend -->
  <g transform="translate(40, {y_pos})">
    <rect x="0" y="0" width="{width}" height="40" rx="6" fill="#FAFAFA" stroke="#E5E7EB" stroke-width="1"/>
    <text x="15" y="24" font-family="Arial" font-size="12" font-weight="bold" fill="#374151">LEGEND:</text>
    
    <rect x="85" y="12" width="16" height="16" rx="3" fill="#800000"/>
    <text x="106" y="24" font-family="Arial" font-size="11" fill="#374151">Main Flow / User</text>

    <rect x="220" y="12" width="16" height="16" rx="3" fill="#FFF0F0" stroke="#800000" stroke-width="1.5"/>
    <text x="241" y="24" font-family="Arial" font-size="11" fill="#374151">System Component</text>

    <rect x="380" y="12" width="16" height="16" rx="3" fill="#E6F2FF" stroke="#0066CC" stroke-width="1.5"/>
    <text x="401" y="24" font-family="Arial" font-size="11" fill="#374151">Data / Inputs</text>

    <rect x="500" y="12" width="16" height="16" rx="3" fill="#F2E6FF" stroke="#6600CC" stroke-width="1.5"/>
    <text x="521" y="24" font-family="Arial" font-size="11" fill="#374151">ML / Risk Engine</text>

    <rect x="640" y="12" width="16" height="16" rx="3" fill="#E6FFE6" stroke="#009933" stroke-width="1.5"/>
    <text x="661" y="24" font-family="Arial" font-size="11" fill="#374151">User Output / Success</text>

    <rect x="810" y="12" width="16" height="16" rx="3" fill="#FFF3E0" stroke="#E65100" stroke-width="1.5"/>
    <text x="831" y="24" font-family="Arial" font-size="11" fill="#374151">Feedback / Recalculation</text>

    <rect x="990" y="12" width="16" height="16" rx="3" fill="#F0F0F0" stroke="#666666" stroke-width="1.5"/>
    <text x="1011" y="24" font-family="Arial" font-size="11" fill="#374151">External Service</text>
  </g>
'''

# ==============================================================================
# FLOWCHART 1: OVERALL SAKHI SYSTEM FLOW
# ==============================================================================
def generate_flowchart_1():
    w, h = 1200, 1000
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#374151" />
    </marker>
    <marker id="arrow-orange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#E65100" />
    </marker>
  </defs>
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  <rect x="0" y="0" width="{w}" height="60" fill="#800000"/>
  <text x="{w/2}" y="38" font-family="Arial" font-size="20" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Flowchart 1 — Overall SAKHI System Flow</text>
'''
    nodes = [
        ("USER", "Initiates Safety Journey", "#800000", "#5A0000", "#FFFFFF"),
        ("MOBILE APP", "React Native + Expo", "#FFF0F0", "#800000", "#1A1A1A"),
        ("JOURNEY REQUEST", "Origin + Destination Input", "#E6F2FF", "#0066CC", "#1A1A1A"),
        ("JOURNEY ENGINE", "FastAPI Backend Service", "#FFF0F0", "#800000", "#1A1A1A"),
        ("ROUTE GENERATION", "OpenStreetMap + OSRM Engine", "#F0F0F0", "#666666", "#1A1A1A"),
        ("ROUTE SEGMENTATION", "Divided into Geographic Segments", "#FFF0F0", "#800000", "#1A1A1A"),
        ("CONTEXTUAL RISK ENGINE", "XGBoost Machine Learning Model", "#F2E6FF", "#6600CC", "#1A1A1A"),
        ("RISK + EXPLANATION", "Risk Score + SHAP Values + Confidence", "#F2E6FF", "#6600CC", "#1A1A1A"),
        ("ROUTE RANKING", "Safest / Balanced / Fastest Options", "#FFF0F0", "#800000", "#1A1A1A"),
        ("PREFERRED ROUTE", "Selected Optimal Safety Path", "#E6FFE6", "#009933", "#1A1A1A"),
        ("USER OUTPUT", "Interactive Route + Safety Analysis Report", "#E6FFE6", "#009933", "#1A1A1A")
    ]

    bx, bw, bh = 450, 300, 52
    sy = 85
    gap = 25
    centers = []

    for i, (t, sub, f, s, tc) in enumerate(nodes):
        cy = sy + i * (bh + gap)
        svg += draw_box(bx, cy, bw, bh, t, sub, fill=f, stroke=s, title_color=tc)
        centers.append((bx + bw/2, cy, cy + bh))
        if i > 0:
            svg += draw_arrow(bx + bw/2, centers[i-1][2], bx + bw/2, cy)

    # Supporting Risk Data Inputs (Left Group)
    svg += '<rect x="40" y="475" width="340" height="230" rx="8" fill="#F4F8FB" stroke="#0066CC" stroke-width="1.5" stroke-dasharray="4"/>\n'
    svg += '<text x="210" y="500" font-family="Arial" font-size="14" font-weight="bold" fill="#0066CC" text-anchor="middle">SUPPORTING RISK DATA INPUTS</text>\n'
    
    sub_inputs = [
        "NCRB / OGD Official Crime Statistics",
        "OpenStreetMap / GIS Physical Features",
        "Historical Incident Reports & Safety Logs",
        "Temporal Factors (Time of Day / Lighting)",
        "Infrastructure & Contextual Risk Data"
    ]
    for k, s_text in enumerate(sub_inputs):
        iy = 515 + k * 35
        svg += draw_box(55, iy, 310, 28, s_text, "", fill="#E6F2FF", stroke="#0066CC")

    svg += draw_arrow(380, 590, bx, 590, color="#0066CC", stroke_width=2)
    svg += draw_arrow_label(415, 580, "Feeds Features", color="#0066CC")

    # Feedback / Update Loop (Right Group)
    svg += '<rect x="820" y="540" width="340" height="200" rx="8" fill="#FFF8F0" stroke="#E65100" stroke-width="1.5" stroke-dasharray="4"/>\n'
    svg += '<text x="990" y="565" font-family="Arial" font-size="14" font-weight="bold" fill="#E65100" text-anchor="middle">DYNAMIC FEEDBACK / UPDATE LOOP</text>\n'

    loop_boxes = [
        ("CONTEXT UPDATE", "Real-time Incident / Environment Change"),
        ("RISK RECALCULATION", "Re-evaluating Segment Safety Scores"),
        ("RE-RANK / RE-ROUTE", "Dynamic Route Adaptation")
    ]
    for k, (lt, lsub) in enumerate(loop_boxes):
        ly = 580 + k * 50
        svg += draw_box(835, ly, 310, 40, lt, lsub, fill="#FFF3E0", stroke="#E65100")
        if k > 0:
            svg += draw_arrow(990, 580 + (k-1)*50 + 40, 990, ly, color="#E65100", stroke_width=1.5, dash="3", marker="arrow-orange")

    svg += draw_arrow(bx + bw, 876, 990, 876, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")
    svg += draw_arrow(990, 876, 990, 730, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")
    svg += draw_arrow(835, 600, bx + bw, 566, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")
    svg += draw_arrow_label(785, 575, "Recalculate", color="#E65100")

    svg += make_legend(940)
    svg += "</svg>"
    return svg

# ==============================================================================
# FLOWCHART 2: DATA -> ML -> RISK PIPELINE
# ==============================================================================
def generate_flowchart_2():
    w, h = 1300, 1000
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#374151" />
    </marker>
  </defs>
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  <rect x="0" y="0" width="{w}" height="60" fill="#800000"/>
  <text x="{w/2}" y="38" font-family="Arial" font-size="20" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Flowchart 2 — Data → ML → Risk Pipeline</text>
'''
    svg += draw_box(50, 90, 260, 52, "RAW DELHI DATA", "NCRB + OSM + Spatial Features", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_box(360, 90, 260, 52, "DATA CLEANING", "Null Handling & Format Standardizing", fill="#FFF0F0", stroke="#800000")
    svg += draw_box(670, 90, 260, 52, "DATA VALIDATION", "Coordinate & Range Checks", fill="#FFF0F0", stroke="#800000")
    svg += draw_box(980, 90, 270, 52, "FEATURE ENGINEERING", "Extract Spatial & Temporal Metrics", fill="#F2E6FF", stroke="#6600CC")

    svg += draw_arrow(310, 116, 360, 116)
    svg += draw_arrow(620, 116, 670, 116)
    svg += draw_arrow(930, 116, 980, 116)

    svg += draw_box(980, 185, 270, 52, "SPATIAL + TEMPORAL FEATURES", "Grid Density, Lighting, Time Slot", fill="#F2E6FF", stroke="#6600CC")
    svg += draw_box(670, 185, 260, 52, "TRAINING DATASET", "Structured Feature Matrix", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_box(360, 185, 260, 52, "TRAIN / VALID / TEST SPLIT", "Temporal & Spatial Stratified Split", fill="#F2E6FF", stroke="#6600CC")
    svg += draw_box(50, 185, 260, 52, "BASELINE MODELS", "Logistic Reg / Random Forest Benchmark", fill="#F2E6FF", stroke="#6600CC")

    svg += draw_arrow(1115, 142, 1115, 185)
    svg += draw_arrow(980, 211, 930, 211)
    svg += draw_arrow(670, 211, 620, 211)
    svg += draw_arrow(360, 211, 310, 211)

    svg += draw_box(50, 280, 260, 52, "XGBOOST TRAINING", "Gradient Boosted Decision Trees", fill="#F2E6FF", stroke="#6600CC")
    svg += draw_box(360, 280, 260, 52, "MODEL VALIDATION", "Hyperparameter Tuning & ROC-AUC", fill="#F2E6FF", stroke="#6600CC")
    svg += draw_box(670, 280, 260, 52, "FINAL MODEL", "Trained Risk Predictor", fill="#F2E6FF", stroke="#6600CC")
    svg += draw_box(980, 280, 270, 52, "SHAP EXPLANATION", "TreeSHAP Feature Attribution", fill="#F2E6FF", stroke="#6600CC")

    svg += draw_arrow(180, 237, 180, 280)
    svg += draw_arrow(310, 306, 360, 306)
    svg += draw_arrow(620, 306, 670, 306)
    svg += draw_arrow(930, 306, 980, 306)

    svg += draw_box(980, 375, 270, 52, "CONFIDENCE / DATA QUALITY", "Uncertainty & Sample Density Metric", fill="#F2E6FF", stroke="#6600CC")
    svg += draw_box(530, 375, 360, 52, "CONTEXTUAL SAFETY RISK ENGINE", "Segment-Level Risk Score Generation", fill="#FFF0F0", stroke="#800000")
    svg += draw_box(50, 375, 360, 52, "SAFETY-AWARE ROUTE RANKING", "Safest / Balanced / Fastest Evaluation", fill="#E6FFE6", stroke="#009933")

    svg += draw_arrow(1115, 332, 1115, 375)
    svg += draw_arrow(980, 401, 890, 401)
    svg += draw_arrow(530, 401, 410, 401)

    svg += '<rect x="50" y="470" width="1200" height="230" rx="8" fill="#FAFAFA" stroke="#D1D5DB" stroke-width="1.5"/>\n'
    svg += '<text x="650" y="495" font-family="Arial" font-size="15" font-weight="bold" fill="#1F2937" text-anchor="middle">DATA SOURCE CLASSIFICATION & INTEGRITY ARCHITECTURE</text>\n'

    svg += draw_box(80, 515, 540, 70, "REAL DATA SOURCES", "NCRB Statistics, OpenStreetMap GIS, Official Open Government Data", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_box(680, 515, 540, 70, "SYNTHETIC / PROXY DATA (Where Required)", "Simulated Context Features, Proxy Density Estimates", fill="#FFF3E0", stroke="#E65100")

    svg += '<rect x="80" y="605" width="1140" height="75" rx="6" fill="#FFFBEB" stroke="#D97706" stroke-width="2"/>\n'
    svg += '<text x="650" y="635" font-family="Arial" font-size="13" font-weight="bold" fill="#92400E" text-anchor="middle">⚠️ DATA INTEGRITY DIRECTIVE</text>\n'
    svg += '<text x="650" y="660" font-family="Arial" font-size="13" fill="#B45309" text-anchor="middle">"Replace or minimize synthetic / proxy inputs wherever reliable real data is available. Do not imply synthetic data represents real crime records."</text>\n'

    svg += make_legend(940)
    svg += "</svg>"
    return svg

# ==============================================================================
# FLOWCHART 3: SAFETY-AWARE ROUTE DECISION
# ==============================================================================
def generate_flowchart_3():
    w, h = 1200, 960
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#374151" />
    </marker>
  </defs>
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  <rect x="0" y="0" width="{w}" height="60" fill="#800000"/>
  <text x="{w/2}" y="38" font-family="Arial" font-size="20" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Flowchart 3 — Safety-Aware Route Decision</text>
'''
    svg += draw_box(450, 85, 300, 48, "USER ENTERS ORIGIN + DESTINATION", "Delhi Location Selection", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_box(450, 155, 300, 48, "ROUTE GENERATION (OSRM)", "Fetches Candidate Paths", fill="#FFF0F0", stroke="#800000")
    svg += draw_box(450, 225, 300, 48, "MULTIPLE CANDIDATE ROUTES", "Route A, Route B, Route C", fill="#FFF0F0", stroke="#800000")
    svg += draw_box(450, 295, 300, 48, "SEGMENT-LEVEL RISK EVALUATION", "XGBoost Predicts Segment Risk", fill="#F2E6FF", stroke="#6600CC")
    svg += draw_box(450, 365, 300, 48, "ROUTE RISK + DISTANCE + TIME", "Aggregated Route Metrics", fill="#FFF0F0", stroke="#800000")
    svg += draw_box(450, 435, 300, 48, "SAFETY / TIME TRADE-OFF ENGINE", "Evaluates Safety vs Travel Time", fill="#FFF0F0", stroke="#800000")

    svg += draw_arrow(600, 133, 600, 155)
    svg += draw_arrow(600, 203, 600, 225)
    svg += draw_arrow(600, 273, 600, 295)
    svg += draw_arrow(600, 343, 600, 365)
    svg += draw_arrow(600, 413, 600, 435)

    svg += '<rect x="40" y="320" width="340" height="150" rx="8" fill="#F8F5FF" stroke="#6600CC" stroke-width="1.5" stroke-dasharray="4"/>\n'
    svg += '<text x="210" y="345" font-family="Arial" font-size="14" font-weight="bold" fill="#6600CC" text-anchor="middle">EXPLANABILITY & CONFIDENCE</text>\n'
    svg += draw_box(60, 360, 300, 30, "RISK SCORE (0 - 100)", "", fill="#F2E6FF", stroke="#6600CC")
    svg += draw_box(60, 395, 300, 30, "SHAP EXPLANATION (Top Risk Drivers)", "", fill="#F2E6FF", stroke="#6600CC")
    svg += draw_box(60, 430, 300, 30, "CONFIDENCE SCORE (Data Density)", "", fill="#F2E6FF", stroke="#6600CC")

    svg += draw_arrow(380, 435, 450, 435, color="#6600CC", stroke_width=2)
    svg += draw_arrow_label(415, 425, "Feeds Evaluation", color="#6600CC")

    svg += draw_arrow(600, 483, 600, 520)
    svg += draw_arrow(600, 520, 200, 540)
    svg += draw_arrow(600, 520, 600, 540)
    svg += draw_arrow(600, 520, 1000, 540)

    svg += draw_box(60, 540, 280, 80, "🟢 SAFEST ROUTE", "Prioritizes Lowest Risk\nMinimal Exposure to Unsafe Segments", fill="#ECFDF5", stroke="#10B981")
    svg += draw_box(460, 540, 280, 80, "🟡 BALANCED ROUTE", "Optimal Compromise\nBalances Safety Score with Travel Duration", fill="#FEF3C7", stroke="#F59E0B")
    svg += draw_box(860, 540, 280, 80, "🔴 FASTEST ROUTE", "Prioritizes Minimum Time\nDirect Route with Standard Routing", fill="#FEF2F2", stroke="#EF4444")

    svg += draw_arrow(200, 620, 600, 670)
    svg += draw_arrow(600, 620, 600, 670)
    svg += draw_arrow(1000, 620, 600, 670)

    svg += draw_box(450, 670, 300, 50, "PREFERRED ROUTE SELECTION", "User Selects Preferred Mode", fill="#E6FFE6", stroke="#009933")
    svg += draw_arrow(600, 720, 600, 750)
    svg += draw_box(450, 750, 300, 50, "SAFETY ANALYSIS REPORT", "Full Route Map + SHAP Explanations", fill="#E6FFE6", stroke="#009933")

    svg += make_legend(900)
    svg += "</svg>"
    return svg

# ==============================================================================
# FLOWCHART 4: USER FEEDBACK / INCIDENT REPORTING LOOP
# ==============================================================================
def generate_flowchart_4():
    w, h = 1300, 1000
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#374151" />
    </marker>
    <marker id="arrow-orange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#E65100" />
    </marker>
  </defs>
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  <rect x="0" y="0" width="{w}" height="60" fill="#800000"/>
  <text x="{w/2}" y="38" font-family="Arial" font-size="20" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Flowchart 4 — User Feedback / Incident Reporting Loop</text>
'''
    nodes = [
        ("USER", "Identifies Safety Concern", "#800000", "#5A0000", "#FFFFFF"),
        ("REPORT SAFETY ISSUE", "Category + Location + Time + Description", "#E6F2FF", "#0066CC", "#1A1A1A"),
        ("IDENTITY / ACCOUNT CHECK", "Verifies Registered Account Status", "#FFF0F0", "#800000", "#1A1A1A"),
        ("REPORT VALIDATION", "Initial Format & Sanity Verification", "#FFF0F0", "#800000", "#1A1A1A"),
        ("DUPLICATE / SPAM CHECK", "Rate Limiting & Duplicate Detection", "#FFF0F0", "#800000", "#1A1A1A"),
        ("CORROBORATION ENGINE", "Spatial & Temporal Incident Clustering", "#FFF0F0", "#800000", "#1A1A1A"),
        ("REPORT CONFIDENCE SCORE", "Weights Trust, Proximity & Multi-user Consensus", "#F2E6FF", "#6600CC", "#1A1A1A"),
        ("VALIDATED SAFETY OBSERVATION", "Confirmed Context Observation", "#E6FFE6", "#009933", "#1A1A1A"),
        ("CONTEXT UPDATE", "Real-time Map Context Refresh", "#FFF3E0", "#E65100", "#1A1A1A"),
        ("RISK RECALCULATION & ROUTE RE-RANKING", "Updates Active Journey Safety & Routes", "#E6FFE6", "#009933", "#1A1A1A")
    ]

    bx, bw, bh = 450, 340, 48
    sy = 80
    gap = 20

    for i, (t, sub, f, s, tc) in enumerate(nodes):
        cy = sy + i * (bh + gap)
        svg += draw_box(bx, cy, bw, bh, t, sub, fill=f, stroke=s, title_color=tc)
        if i > 0:
            svg += draw_arrow(bx + bw/2, cy - gap, bx + bw/2, cy)

    svg += '<rect x="850" y="480" width="380" height="260" rx="8" fill="#FFF8F0" stroke="#E65100" stroke-width="1.5" stroke-dasharray="4"/>\n'
    svg += '<text x="1040" y="508" font-family="Arial" font-size="14" font-weight="bold" fill="#E65100" text-anchor="middle">LONG-TERM MODEL RETRAINING LOOP</text>\n'

    lt_steps = [
        ("VALIDATED REPORT DATABASE", "Persistent Incident Store"),
        ("FEATURE EXTRACTOR", "Updated Training Features"),
        ("PERIODIC MODEL RETRAINING", "XGBoost Retraining Cycle"),
        ("IMPROVED SAFETY INTELLIGENCE", "Upgraded Model Weights")
    ]
    for k, (ltt, ltsub) in enumerate(lt_steps):
        lty = 525 + k * 52
        svg += draw_box(870, lty, 340, 40, ltt, ltsub, fill="#FFF3E0", stroke="#E65100")
        if k > 0:
            svg += draw_arrow(1040, 525 + (k-1)*52 + 40, 1040, lty, color="#E65100", stroke_width=1.5, dash="3", marker="arrow-orange")

    svg += draw_arrow(bx + bw, 560, 870, 560, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")
    svg += draw_arrow(1040, 733, 1040, 770, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")
    svg += draw_arrow(1040, 770, 620, 770, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")
    svg += draw_arrow_label(800, 760, "Model Upgrade Loop", color="#E65100")

    svg += '<rect x="40" y="780" width="1220" height="85" rx="6" fill="#FFFBEB" stroke="#D97706" stroke-width="2"/>\n'
    svg += '<text x="650" y="805" font-family="Arial" font-size="13" font-weight="bold" fill="#92400E" text-anchor="middle">⚠️ IDENTITY TRUST vs INCIDENT VALIDATION SPECIFICATION</text>\n'
    svg += '<text x="650" y="830" font-family="Arial" font-size="12" fill="#B45309" text-anchor="middle">"Identity verification (demo code/account check) increases account trust ONLY. It does NOT prove an incident report is true."</text>\n'
    svg += '<text x="650" y="850" font-family="Arial" font-size="12" fill="#B45309" text-anchor="middle">"Incident validation strictly relies on corroboration, duplicate checks, spatial/temporal consistency, and multi-report confidence."</text>\n'

    svg += make_legend(940)
    svg += "</svg>"
    return svg

# ==============================================================================
# FLOWCHART 5: RIGHT TO PEE / AMENITIES
# ==============================================================================
def generate_flowchart_5():
    w, h = 1200, 960
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#374151" />
    </marker>
  </defs>
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  <rect x="0" y="0" width="{w}" height="60" fill="#800000"/>
  <text x="{w/2}" y="38" font-family="Arial" font-size="20" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Flowchart 5 — Right to Pee / Amenities Flow</text>
'''
    svg += '<rect x="40" y="85" width="1120" height="110" rx="8" fill="#F4F8FB" stroke="#0066CC" stroke-width="1.5"/>\n'
    svg += '<text x="600" y="110" font-family="Arial" font-size="14" font-weight="bold" fill="#0066CC" text-anchor="middle">USER SELECTS ORIGIN LOCATION (EXPLICIT USER CHOICE REQUIRED)</text>\n'

    svg += draw_box(60, 125, 340, 55, "OPTION A: MANUAL SEARCH", "Type Delhi Landmark / Address", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_box(430, 125, 340, 55, "OPTION B: MAP TAP", "Select Specific Location on Map", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_box(800, 125, 340, 55, "OPTION C: CURRENT LOCATION", "Explicitly Choose 'Use My GPS'", fill="#E6F2FF", stroke="#0066CC")

    svg += draw_arrow(600, 195, 600, 230)
    svg += draw_box(450, 230, 300, 48, "AMENITY SEARCH TRIGGER", "Query Nearby Safe Facilities", fill="#FFF0F0", stroke="#800000")

    svg += draw_arrow(600, 278, 600, 310)
    svg += draw_box(410, 310, 380, 48, "REAL DELHI AMENITY DATA RETRIEVAL", "Official Delhi Restroom Infrastructure Data", fill="#E6F2FF", stroke="#0066CC")

    svg += draw_arrow(600, 358, 320, 390)
    svg += draw_arrow(600, 358, 880, 390)

    svg += draw_box(160, 390, 320, 48, "OPENSTREETMAP / OVERPASS API", "Real-time Overpass Queries", fill="#F0F0F0", stroke="#666666")
    svg += draw_box(720, 390, 320, 48, "GOVERNMENT / OFFICIAL OPEN DATA", "Verified Municipal Washrooms", fill="#F0F0F0", stroke="#666666")

    svg += draw_arrow(320, 438, 600, 470)
    svg += draw_arrow(880, 438, 600, 470)

    svg += draw_box(410, 470, 380, 48, "NEARBY WASHROOMS & AMENITIES", "Filter Clean, Accessible & Safe Restrooms", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(600, 518, 600, 550)
    svg += draw_box(410, 550, 380, 48, "MAP MARKERS DISPLAY", "Interactive Washroom Pins on Map", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(600, 598, 600, 630)
    svg += draw_box(410, 630, 380, 48, "USER SELECTS A SPECIFIC WASHROOM", "Views Cleanliness & Safety Details", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_arrow(600, 678, 600, 710)
    svg += draw_box(410, 710, 380, 48, "DEDICATED NAVIGATE BUTTON", "One-Tap Direction Launch per Marker", fill="#E6FFE6", stroke="#009933")
    svg += draw_arrow(600, 758, 600, 790)
    svg += draw_box(380, 790, 440, 52, "GOOGLE MAPS NAVIGATION LAUNCH", "Navigates Selected Origin → Exact Amenity Coordinates", fill="#E6FFE6", stroke="#009933")

    svg += '<rect x="40" y="852" width="1120" height="35" rx="4" fill="#FFFBEB" stroke="#D97706" stroke-width="1.5"/>\n'
    svg += '<text x="600" y="874" font-family="Arial" font-size="12" font-weight="bold" fill="#92400E" text-anchor="middle">📌 Note: App does NOT automatically fetch live GPS without explicit choice. Destinations use exact selected amenity coordinates.</text>\n'

    svg += make_legend(900)
    svg += "</svg>"
    return svg

# ==============================================================================
# FLOWCHART 6: CALL A FRIEND (TWO-LAYER ARCHITECTURE)
# ==============================================================================
def generate_flowchart_6():
    w, h = 1300, 960
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#374151" />
    </marker>
  </defs>
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  <rect x="0" y="0" width="{w}" height="60" fill="#800000"/>
  <text x="{w/2}" y="38" font-family="Arial" font-size="20" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Flowchart 6 — Two-Layer Call a Friend Architecture</text>
'''
    svg += draw_box(500, 85, 300, 48, "CALL A FRIEND TRIGGER", "User Taps Emergency Safety Call", fill="#800000", stroke="#5A0000", title_color="#FFFFFF")
    svg += draw_arrow(650, 133, 650, 165)

    svg += draw_box(480, 165, 340, 52, "NETWORK CONNECTIVITY STATUS", "Detects Internet Availability (NetInfo)", fill="#FFF0F0", stroke="#800000")

    svg += draw_arrow(480, 191, 280, 240)
    svg += draw_arrow_label(360, 205, "YES (ONLINE)", color="#0066CC")

    svg += draw_box(100, 240, 360, 48, "ONLINE SARVAM AI TTS LAYER", "Live Custom Voice Generation", fill="#EFF6FF", stroke="#2563EB")
    svg += draw_arrow(280, 288, 280, 315)
    svg += draw_box(100, 315, 360, 48, "CUSTOM SCRIPT / SUGGESTED SCRIPT", "English, Hindi, or Marathi Script", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_arrow(280, 363, 280, 390)
    svg += draw_box(100, 390, 360, 48, "VOICE SELECTION", "Male (shubh) / Female (priya)", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(280, 438, 280, 465)
    svg += draw_box(100, 465, 360, 48, "FASTAPI BACKEND API", "/api/v1/call-friend/tts Endpoint", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(280, 513, 280, 540)
    svg += draw_box(100, 540, 360, 48, "SARVAM AI TTS ENGINE", "Bulbul V3 Model Synthesis", fill="#F2E6FF", stroke="#6600CC")
    svg += draw_arrow(280, 588, 280, 615)
    svg += draw_box(100, 615, 360, 48, "GENERATED BASE64 WAV AUDIO", "Returned High-Quality Audio Payload", fill="#F2E6FF", stroke="#6600CC")
    svg += draw_arrow(280, 663, 280, 690)
    svg += draw_box(100, 690, 360, 52, "SIMULATED CALL UI PLAYBACK", "expo-audio Player Active Call Screen", fill="#E6FFE6", stroke="#009933")

    svg += draw_arrow(820, 191, 1020, 240)
    svg += draw_arrow_label(940, 205, "NO (OFFLINE)", color="#DC2626")

    svg += draw_box(840, 240, 360, 48, "OFFLINE BUNDLED FALLBACK LAYER", "Zero Network Dependency", fill="#FEF2F2", stroke="#DC2626")
    svg += draw_arrow(1020, 288, 1020, 325)
    svg += draw_box(840, 325, 360, 52, "PREINSTALLED LOCAL VOICE LIBRARY", "6 Bundled High-Quality Audio Clips\n(Male/Female x En/Hi/Mr)", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_arrow(1020, 377, 1020, 415)
    svg += draw_box(840, 415, 360, 48, "MALE / FEMALE VOICE SELECTION", "Loads Matching Local WAV Asset", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(1020, 463, 1020, 500)
    svg += draw_box(840, 500, 360, 52, "CONTEXT-BASED PRE-RECORDED CLIPS", "Pre-recorded Safety Check Dialogue", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_arrow(1020, 552, 1020, 690)
    svg += draw_box(840, 690, 360, 52, "SIMULATED CALL UI PLAYBACK", "expo-audio Player Active Call Screen", fill="#E6FFE6", stroke="#009933")

    svg += '<rect x="100" y="775" width="1100" height="40" rx="6" fill="#FFFBEB" stroke="#D97706" stroke-width="1.5"/>\n'
    svg += '<text x="650" y="800" font-family="Arial" font-size="13" font-weight="bold" fill="#92400E" text-anchor="middle">📌 Product Specification Note: Simulated Safety Call UI for personal reassurance. No real cellular telephony call is initiated.</text>\n'

    svg += make_legend(900)
    svg += "</svg>"
    return svg

# ==============================================================================
# FLOWCHART 7: SOS / EMERGENCY WORKFLOW
# ==============================================================================
def generate_flowchart_7():
    w, h = 1200, 940
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#374151" />
    </marker>
  </defs>
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  <rect x="0" y="0" width="{w}" height="60" fill="#800000"/>
  <text x="{w/2}" y="38" font-family="Arial" font-size="20" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Flowchart 7 — SOS / Emergency Architecture</text>
'''
    svg += '<rect x="40" y="85" width="1120" height="105" rx="8" fill="#FEF2F2" stroke="#DC2626" stroke-width="1.5"/>\n'
    svg += '<text x="600" y="110" font-family="Arial" font-size="14" font-weight="bold" fill="#991B1B" text-anchor="middle">EMERGENCY SOS TRIGGER SOURCES</text>\n'

    svg += draw_box(60, 125, 340, 52, "MANUAL SOS BUTTON", "One-Tap Emergency Trigger", fill="#800000", stroke="#5A0000", title_color="#FFFFFF")
    svg += draw_box(430, 125, 340, 52, "SHAKE-TO-SOS", "Accelerometer Sensor Detection", fill="#FFF0F0", stroke="#800000")
    svg += draw_box(800, 125, 340, 52, "DEAD-MAN SWITCH", "Timer-based Safety Check", fill="#FFF0F0", stroke="#800000")

    svg += draw_arrow(600, 190, 600, 225)
    svg += draw_box(430, 225, 340, 50, "SOS ACTIVATION ENGINE", "Emergency Protocol Triggered", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(600, 275, 600, 310)
    svg += draw_box(430, 310, 340, 50, "LOCATION & CONTEXT SNAPSHOT", "Fetches Current / Selected Coordinates", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_arrow(600, 360, 600, 395)

    svg += draw_box(410, 395, 380, 50, "EMERGENCY COMMUNICATION DISPATCH", "Routes SOS to Emergency Network", fill="#FFF0F0", stroke="#800000")

    svg += draw_arrow(600, 445, 320, 490)
    svg += draw_arrow(600, 445, 880, 490)

    svg += draw_box(140, 490, 360, 80, "CURRENT IMPLEMENTATION", "Local Emergency Alert Screen\n+ SMS Fallback to Safety Contacts", fill="#E6FFE6", stroke="#009933")
    svg += draw_box(700, 490, 360, 80, "PLANNED / FUTURE COMMUNICATION", "Direct 112 Dispatch API Integration\n+ Live Emergency Response Dashboard", fill="#F0F0F0", stroke="#666666", stroke_dash="4")

    svg += draw_arrow(320, 570, 600, 630)
    svg += draw_arrow(880, 570, 600, 630)

    svg += draw_box(430, 630, 340, 52, "ACTIVE EMERGENCY STATUS DISPLAY", "Tracks Emergency Alert & Response", fill="#E6FFE6", stroke="#009933")

    svg += '<rect x="40" y="730" width="1120" height="110" rx="8" fill="#FAFAFA" stroke="#D1D5DB" stroke-width="1.5"/>\n'
    svg += '<text x="600" y="755" font-family="Arial" font-size="14" font-weight="bold" fill="#1F2937" text-anchor="middle">EMERGENCY SYSTEM ARCHITECTURE LEGEND</text>\n'

    svg += draw_box(80, 770, 510, 50, "CURRENTLY IMPLEMENTED FEATURE (Solid Box)", "App Notifications + Local Emergency UI + SMS Fallback", fill="#E6FFE6", stroke="#009933")
    svg += draw_box(610, 770, 510, 50, "PLANNED / FUTURE FEATURE (Dashed Box)", "Direct 112 National Emergency Hotline API Integration", fill="#F0F0F0", stroke="#666666", stroke_dash="4")

    svg += make_legend(880)
    svg += "</svg>"
    return svg

# ==============================================================================
# FLOWCHART 8: OFFLINE / RESILIENT SAKHI ARCHITECTURE
# ==============================================================================
def generate_flowchart_8():
    w, h = 1200, 960
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#374151" />
    </marker>
    <marker id="arrow-orange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#E65100" />
    </marker>
  </defs>
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  <rect x="0" y="0" width="{w}" height="60" fill="#800000"/>
  <text x="{w/2}" y="38" font-family="Arial" font-size="20" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Flowchart 8 — Offline / Resilient SAKHI Architecture</text>
'''
    svg += draw_box(450, 85, 300, 48, "SAKHI ACTIVE JOURNEY", "Navigation & Safety Monitoring", fill="#800000", stroke="#5A0000", title_color="#FFFFFF")
    svg += draw_arrow(600, 133, 600, 165)

    svg += draw_box(430, 165, 340, 50, "NETWORK AVAILABILITY CHECK", "Continuous NetInfo Connectivity Monitor", fill="#FFF0F0", stroke="#800000")

    svg += draw_arrow(430, 190, 250, 240)
    svg += draw_arrow_label(320, 205, "YES (ONLINE)", color="#0066CC")

    svg += draw_box(80, 240, 340, 52, "LIVE API & DATA STREAM", "FastAPI Backend + Live OSRM + Live Models", fill="#EFF6FF", stroke="#2563EB")

    svg += draw_arrow(770, 190, 950, 240)
    svg += draw_arrow_label(880, 205, "NO (OFFLINE)", color="#DC2626")

    svg += draw_box(780, 240, 340, 52, "LOCAL CACHE & OFFLINE ENGINE", "Zero Network Local Fallback Layer", fill="#FFF3E0", stroke="#E65100")

    svg += draw_arrow(250, 292, 600, 350)
    svg += draw_arrow(950, 292, 600, 350)

    svg += draw_box(410, 350, 380, 52, "ACTIVE JOURNEY SAFETY SUPPORT", "Uninterrupted Guidance & Monitoring", fill="#E6FFE6", stroke="#009933")

    svg += '<rect x="40" y="440" width="1120" height="230" rx="8" fill="#F8FAFC" stroke="#64748B" stroke-width="1.5"/>\n'
    svg += '<text x="600" y="465" font-family="Arial" font-size="14" font-weight="bold" fill="#1E293B" text-anchor="middle">OFFLINE CACHED ASSETS & DATA MATRIX (PRE-STORED ON DEVICE)</text>\n'

    cached_items = [
        ("JOURNEY & ROUTE GEOMETRY", "Pre-calculated Waypoints & Coordinates"),
        ("RISK SCORES & SHAP EXPLANATIONS", "Pre-evaluated Segment Risk & Attribution"),
        ("CONFIDENCE & QUALITY SCORES", "Data Reliability Ratings"),
        ("NEARBY AMENITIES DATA", "Cached Washrooms & Emergency Shelters"),
        ("EMERGENCY CONTACTS & SOS PROTOCOL", "Local SMS & Contact Information"),
        ("BUNDLED SAFETY AUDIO LIBRARY", "Pre-recorded Voice Audio Clips (Male/Female)")
    ]

    for k, (ct, csub) in enumerate(cached_items):
        rx_pos = 70 + (k % 2) * 540
        ry_pos = 485 + (k // 2) * 55
        svg += draw_box(rx_pos, ry_pos, 510, 45, ct, csub, fill="#E6F2FF", stroke="#0066CC")

    svg += draw_box(410, 695, 380, 50, "NETWORK RESTORED DETECTED", "Triggers Background Synchronization", fill="#FFF3E0", stroke="#E65100")
    svg += draw_arrow(600, 745, 600, 780)
    svg += draw_box(410, 780, 380, 50, "SYNC & UPDATE LATEST DATA", "Uploads Offline Logs & Refreshes Live Context", fill="#E6FFE6", stroke="#009933")

    svg += draw_arrow(790, 805, 1140, 805, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")
    svg += draw_arrow(1140, 805, 1140, 266, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")
    svg += draw_arrow(1140, 266, 420, 266, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")
    svg += draw_arrow_label(1140, 530, "Re-sync Live Stream", color="#E65100")

    svg += make_legend(900)
    svg += "</svg>"
    return svg

# ==============================================================================
# FLOWCHART 9: OVERALL INNOVATION LOOP
# ==============================================================================
def generate_flowchart_9():
    w, h = 1100, 1100
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#374151" />
    </marker>
    <marker id="arrow-orange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#E65100" />
    </marker>
  </defs>
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  <rect x="0" y="0" width="{w}" height="60" fill="#800000"/>
  <text x="{w/2}" y="38" font-family="Arial" font-size="20" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Flowchart 9 — SAKHI: Continuous Safety Intelligence Loop</text>
'''
    nodes = [
        ("REAL DATA + MODEL + CONTEXT", "NCRB Data + Machine Learning Models + Real-time Features", "#E6F2FF", "#0066CC", "#1A1A1A"),
        ("CONTEXTUAL RISK ENGINE", "XGBoost Evaluates Segment Safety Risk", "#F2E6FF", "#6600CC", "#1A1A1A"),
        ("EXPLAINABLE ROUTING (SHAP)", "Explainable Risk Scoring & SHAP Feature Attribution", "#F2E6FF", "#6600CC", "#1A1A1A"),
        ("USER JOURNEY", "Active User Navigation & Real-time Monitoring", "#FFF0F0", "#800000", "#1A1A1A"),
        ("USER SAFETY OBSERVATION", "Crowdsourced Incident & Observation Reports", "#E6F2FF", "#0066CC", "#1A1A1A"),
        ("VALIDATION & CORROBORATION", "Spatial/Temporal Clustering & Confidence Scoring", "#FFF0F0", "#800000", "#1A1A1A"),
        ("UPDATED CONTEXT", "Real-time Map & Environment Data Refresh", "#FFF3E0", "#E65100", "#1A1A1A"),
        ("UPDATED RISK", "Recalculated Segment Safety Risk Scores", "#F2E6FF", "#6600CC", "#1A1A1A"),
        ("UPDATED ROUTE", "Dynamic Route Adaptation & Safety Re-ranking", "#E6FFE6", "#009933", "#1A1A1A"),
        ("FUTURE MODEL IMPROVEMENT", "Long-term Model Retraining with Verified Data", "#F2E6FF", "#6600CC", "#1A1A1A")
    ]

    bx, bw, bh = 340, 420, 52
    sy = 85
    gap = 22
    centers = []

    for i, (t, sub, f, s, tc) in enumerate(nodes):
        cy = sy + i * (bh + gap)
        svg += draw_box(bx, cy, bw, bh, t, sub, fill=f, stroke=s, title_color=tc)
        centers.append((bx + bw/2, cy, cy + bh))
        if i > 0:
            svg += draw_arrow(bx + bw/2, centers[i-1][2], bx + bw/2, cy)

    last_y_bottom = centers[-1][2]
    first_y_top = centers[0][1]

    svg += draw_arrow(bx + bw/2, last_y_bottom, bx + bw/2, last_y_bottom + 30, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")
    svg += draw_arrow(bx + bw/2, last_y_bottom + 30, 950, last_y_bottom + 30, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")
    svg += draw_arrow(950, last_y_bottom + 30, 950, first_y_top + 26, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")
    svg += draw_arrow(950, first_y_top + 26, bx + bw, first_y_top + 26, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")

    svg += draw_arrow_label(950, 520, "Continuous Intelligence Loop ↺", color="#E65100")

    svg += '<rect x="40" y="320" width="260" height="380" rx="8" fill="#FFFBEB" stroke="#D97706" stroke-width="2"/>\n'
    svg += '<text x="170" y="350" font-family="Arial" font-size="14" font-weight="bold" fill="#92400E" text-anchor="middle">WHY SAKHI IS MORE</text>\n'
    svg += '<text x="170" y="370" font-family="Arial" font-size="14" font-weight="bold" fill="#92400E" text-anchor="middle">THAN A MAP APP</text>\n'

    bullets = [
        "1. Dynamic Risk Layer",
        "Over standard OSRM routes",
        "",
        "2. Explainable AI",
        "SHAP value attributions",
        "",
        "3. Multi-Factor Trust",
        "Spatial/Temporal Corroboration",
        "",
        "4. Network Resilient",
        "Online Sarvam AI + Offline Fallback",
        "",
        "5. Self-Improving",
        "Verified crowdsourced data",
        "retrains models continuously"
    ]
    for m, b_text in enumerate(bullets):
        by_pos = 405 + m * 18
        font_w = "bold" if b_text.startswith(("1.", "2.", "3.", "4.", "5.")) else "normal"
        fill_c = "#92400E" if font_w == "bold" else "#B45309"
        svg += f'<text x="55" y="{by_pos}" font-family="Arial" font-size="11" font-weight="{font_w}" fill="{fill_c}">{b_text}</text>\n'

    svg += make_legend(1030, width=1020)
    svg += "</svg>"
    return svg

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
generators = [
    ("flowchart_1_overall_system_flow", generate_flowchart_1, 1200, 1000),
    ("flowchart_2_data_ml_risk_pipeline", generate_flowchart_2, 1300, 1000),
    ("flowchart_3_safety_aware_route_decision", generate_flowchart_3, 1200, 960),
    ("flowchart_4_user_feedback_incident_loop", generate_flowchart_4, 1300, 1000),
    ("flowchart_5_right_to_pee_amenities", generate_flowchart_5, 1200, 960),
    ("flowchart_6_call_a_friend_architecture", generate_flowchart_6, 1300, 960),
    ("flowchart_7_sos_emergency_architecture", generate_flowchart_7, 1200, 940),
    ("flowchart_8_offline_resilient_sakhi", generate_flowchart_8, 1200, 960),
    ("flowchart_9_continuous_safety_intelligence_loop", generate_flowchart_9, 1100, 1100)
]

print("Generating 9 Flowcharts...")
for filename, gen_fn, width, height in generators:
    svg_content = gen_fn()
    
    svg_path_docs = os.path.join(out_dir_docs, f"{filename}.svg")
    png_path_docs = os.path.join(out_dir_docs, f"{filename}.png")
    
    with open(svg_path_docs, "w", encoding="utf-8") as f:
        f.write(svg_content)
        
    svg_path_artifacts = os.path.join(out_dir_artifacts, f"{filename}.svg")
    png_path_artifacts = os.path.join(out_dir_artifacts, f"{filename}.png")
    
    with open(svg_path_artifacts, "w", encoding="utf-8") as f:
        f.write(svg_content)
        
    render_svg_to_png(svg_path_docs, png_path_docs, width, height)
    render_svg_to_png(svg_path_artifacts, png_path_artifacts, width, height)
    
    print(f"GENERATED: {filename}.svg and {filename}.png ({width}x{height})")

print("ALL 9 FLOWCHARTS GENERATED SUCCESSFULLY!")
