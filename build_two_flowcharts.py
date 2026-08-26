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

def draw_box(x, y, w, h, title, subtitle="", fill="#FFF0F0", stroke="#800000", title_color="#1A1A1A", rx=6, stroke_dash="", font_size=13):
    dash_attr = f'stroke-dasharray="{stroke_dash}"' if stroke_dash else ''
    res = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="2" {dash_attr}/>\n'
    if subtitle:
        ty = y + h/2 - 9
        sy = y + h/2 + 10
        res += f'<text x="{x + w/2}" y="{ty}" font-family="Arial" font-size="{font_size}" font-weight="bold" fill="{title_color}" text-anchor="middle">{title}</text>\n'
        res += f'<text x="{x + w/2}" y="{sy}" font-family="Arial" font-size="{font_size - 2}" fill="#4B5563" text-anchor="middle">{subtitle}</text>\n'
    else:
        ty = y + h/2 + 4
        res += f'<text x="{x + w/2}" y="{ty}" font-family="Arial" font-size="{font_size}" font-weight="bold" fill="{title_color}" text-anchor="middle">{title}</text>\n'
    return res

def draw_arrow(x1, y1, x2, y2, color="#374151", stroke_width=2, dash="", marker="arrow"):
    dash_attr = f'stroke-dasharray="{dash}"' if dash else ''
    res = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{stroke_width}" {dash_attr} marker-end="url(#{marker})"/>\n'
    return res

def draw_arrow_label(x, y, text, color="#374151", bg="#FFFFFF"):
    w = len(text) * 7.5 + 12
    return f'<rect x="{x - w/2}" y="{y - 10}" width="{w}" height="20" rx="4" fill="{bg}" stroke="#D1D5DB" stroke-width="1"/>\n<text x="{x}" y="{y + 4}" font-family="Arial" font-size="11" font-weight="bold" fill="{color}" text-anchor="middle">{text}</text>\n'

def make_legend(y_pos, width=1720):
    return f'''
  <!-- Legend -->
  <g transform="translate(40, {y_pos})">
    <rect x="0" y="0" width="{width}" height="42" rx="6" fill="#FAFAFA" stroke="#E5E7EB" stroke-width="1.5"/>
    <text x="20" y="26" font-family="Arial" font-size="12" font-weight="bold" fill="#374151">COLOR CODING LEGEND:</text>
    
    <rect x="180" y="13" width="16" height="16" rx="3" fill="#800000"/>
    <text x="202" y="26" font-family="Arial" font-size="11" fill="#374151">Main Flow / Start-End</text>

    <rect x="360" y="13" width="16" height="16" rx="3" fill="#FFF0F0" stroke="#800000" stroke-width="1.5"/>
    <text x="382" y="26" font-family="Arial" font-size="11" fill="#374151">Frontend / Component</text>

    <rect x="540" y="13" width="16" height="16" rx="3" fill="#E6F2FF" stroke="#0066CC" stroke-width="1.5"/>
    <text x="562" y="26" font-family="Arial" font-size="11" fill="#374151">Data / Location / Input</text>

    <rect x="720" y="13" width="16" height="16" rx="3" fill="#F2E6FF" stroke="#6600CC" stroke-width="1.5"/>
    <text x="742" y="26" font-family="Arial" font-size="11" fill="#374151">ML / XGBoost / SHAP / Confidence</text>

    <rect x="980" y="13" width="16" height="16" rx="3" fill="#E6FFE6" stroke="#009933" stroke-width="1.5"/>
    <text x="1002" y="26" font-family="Arial" font-size="11" fill="#374151">User Output / Success</text>

    <rect x="1170" y="13" width="16" height="16" rx="3" fill="#FFF3E0" stroke="#E65100" stroke-width="1.5"/>
    <text x="1192" y="26" font-family="Arial" font-size="11" fill="#374151">Feedback / Rerouting / Recalculation</text>

    <rect x="1440" y="13" width="16" height="16" rx="3" fill="#F0F0F0" stroke="#666666" stroke-width="1.5"/>
    <text x="1462" y="26" font-family="Arial" font-size="11" fill="#374151">External Services</text>
  </g>
'''

# ==============================================================================
# FLOWCHART 1: FRONTEND / USER FLOW
# ==============================================================================
def generate_frontend_flowchart():
    w, h = 1800, 1400
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
  
  <!-- Title Banner -->
  <rect x="0" y="0" width="{w}" height="60" fill="#800000"/>
  <text x="{w/2}" y="38" font-family="Arial" font-size="22" font-weight="bold" fill="#FFFFFF" text-anchor="middle">SAKHI — User Flow (Frontend)</text>

  <!-- Section 1: Main Initialization Stream (Top Center) -->
  <g id="main_init_stream">
'''
    # Top linear vertical flow (x=730, w=340)
    svg += draw_box(730, 80, 340, 44, "START", "User Opens Application", fill="#800000", stroke="#5A0000", title_color="#FFFFFF")
    svg += draw_arrow(900, 124, 900, 145)
    svg += draw_box(730, 145, 340, 44, "OPEN SAKHI", "React Native + Expo Mobile Interface", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(900, 189, 900, 210)
    svg += draw_box(730, 210, 340, 44, "HOME / JOURNEY DASHBOARD", "Main Map Screen & Safety Hub", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(900, 254, 900, 275)

    # Location Selection Container
    svg += '<rect x="420" y="275" width="960" height="95" rx="8" fill="#F4F8FB" stroke="#0066CC" stroke-width="1.5"/>\n'
    svg += '<text x="900" y="295" font-family="Arial" font-size="13" font-weight="bold" fill="#0066CC" text-anchor="middle">LOCATION SELECTION MODES (Explicit Choice Required)</text>\n'
    svg += draw_box(440, 308, 280, 48, "MANUAL LOCATION INPUT", "Search Delhi Address / Landmark", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_box(760, 308, 280, 48, "SELECT LOCATION ON MAP", "Tap Directly on Interactive Map", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_box(1080, 308, 280, 48, "EXPLICIT CURRENT LOCATION", "Choose 'Use My GPS'", fill="#E6F2FF", stroke="#0066CC")

    svg += draw_arrow(900, 370, 900, 390)
    svg += draw_box(730, 390, 340, 44, "ENTER ORIGIN", "Set Starting Location", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_arrow(900, 434, 900, 455)
    svg += draw_box(730, 455, 340, 44, "ENTER DESTINATION", "Set Target Destination", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_arrow(900, 499, 900, 520)
    svg += draw_box(730, 520, 340, 44, "GENERATE ROUTES", "Triggers Journey Backend Engine", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(900, 564, 900, 585)

    # 3 Route Options Branching
    svg += draw_box(730, 585, 340, 44, "DISPLAY AVAILABLE ROUTES", "Safest, Balanced, Fastest Options", fill="#FFF0F0", stroke="#800000")
    
    svg += draw_arrow(900, 629, 900, 655)
    svg += draw_arrow(900, 642, 530, 655)
    svg += draw_arrow(900, 642, 1270, 655)

    svg += draw_box(390, 655, 280, 65, "🟢 SAFEST ROUTE", "Lowest Risk Score\nMinimal Exposure to Unsafe Segments", fill="#ECFDF5", stroke="#10B981")
    svg += draw_box(760, 655, 280, 65, "🟡 BALANCED ROUTE", "Optimal Trade-off\nBalances Safety Score & Travel Time", fill="#FEF3C7", stroke="#F59E0B")
    svg += draw_box(1130, 655, 280, 65, "🔴 FASTEST ROUTE", "Minimum Travel Time\nDirect Standard Routing Path", fill="#FEF2F2", stroke="#EF4444")

    svg += draw_arrow(530, 720, 900, 745)
    svg += draw_arrow(900, 720, 900, 745)
    svg += draw_arrow(1270, 720, 900, 745)

    svg += draw_box(730, 745, 340, 44, "VIEW SELECTED / PREFERRED ROUTE", "User Confirms Chosen Option", fill="#E6FFE6", stroke="#009933")
    svg += draw_arrow(900, 789, 900, 810)

    # Safety Analysis Report Container
    svg += '<rect x="440" y="810" width="920" height="75" rx="6" fill="#F8F5FF" stroke="#6600CC" stroke-width="1.5"/>\n'
    svg += '<text x="900" y="830" font-family="Arial" font-size="13" font-weight="bold" fill="#6600CC" text-anchor="middle">SAFETY ANALYSIS REPORT & EXPLANABILITY METRICS</text>\n'
    svg += draw_box(460, 840, 200, 32, "RISK SCORE (0 - 100)", "", fill="#F2E6FF", stroke="#6600CC", font_size=11)
    svg += draw_box(680, 840, 200, 32, "DISTANCE & TIME", "", fill="#FFF0F0", stroke="#800000", font_size=11)
    svg += draw_box(900, 840, 200, 32, "CONFIDENCE RATING", "", fill="#F2E6FF", stroke="#6600CC", font_size=11)
    svg += draw_box(1120, 840, 220, 32, "SHAP: WHY THIS ROUTE?", "", fill="#F2E6FF", stroke="#6600CC", font_size=11)

    svg += draw_arrow(900, 885, 900, 905)
    svg += draw_box(730, 905, 340, 44, "START JOURNEY", "Initiates Active Tracking Mode", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(900, 949, 900, 970)
    svg += draw_box(700, 970, 400, 48, "ACTIVE JOURNEY / MAP MONITORING", "Live Route Guidance & Continuous Risk Assessment", fill="#FFF0F0", stroke="#800000")

    # Section 2: Four During-Journey Parallel Branches (Middle Row: y=1050 to 1230)
    svg += '<rect x="40" y="1035" width="1720" height="230" rx="8" fill="#FAFAFA" stroke="#D1D5DB" stroke-width="1.5"/>\n'
    svg += '<text x="900" y="1055" font-family="Arial" font-size="14" font-weight="bold" fill="#1F2937" text-anchor="middle">DURING JOURNEY — INTERACTIVE SAFETY FEATURES</text>\n'

    # Connector from ACTIVE JOURNEY to 4 Branches
    svg += draw_arrow(900, 1018, 900, 1070)
    svg += draw_arrow(900, 1045, 230, 1070)
    svg += draw_arrow(900, 1045, 670, 1070)
    svg += draw_arrow(900, 1045, 1130, 1070)
    svg += draw_arrow(900, 1045, 1570, 1070)

    # Branch 1: Dynamic Re-ranking (Far Left: x=60)
    svg += draw_box(60, 1070, 340, 44, "CONTEXT CHANGES DETECTED", "Environmental / Traffic / Incident Update", fill="#FFF3E0", stroke="#E65100")
    svg += draw_arrow(230, 1114, 230, 1135)
    svg += draw_box(60, 1135, 340, 44, "RISK SCORE RECALCULATION", "Re-evaluates Active Segment Risks", fill="#F2E6FF", stroke="#6600CC")
    svg += draw_arrow(230, 1179, 230, 1200)
    svg += draw_box(60, 1200, 340, 44, "DYNAMIC RE-RANKING / REROUTING", "Adapts Active Journey Route", fill="#FFF3E0", stroke="#E65100")

    # Branch 2: Amenities / Right to Pee (Left Center: x=460)
    svg += draw_box(460, 1070, 420, 38, "FIND AMENITIES / RIGHT TO PEE", "User Requests Safe Washrooms / Facilities", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(670, 1108, 670, 1120)
    svg += draw_box(460, 1120, 420, 35, "CHOOSE ORIGIN LOCATION", "Manual / Map Tap / Explicit GPS Choice", fill="#E6F2FF", stroke="#0066CC", font_size=11)
    svg += draw_arrow(670, 1155, 670, 1165)
    svg += draw_box(460, 1165, 420, 35, "REAL DELHI AMENITIES DATA", "Queries Verified Restroom Database", fill="#E6F2FF", stroke="#0066CC", font_size=11)
    svg += draw_arrow(670, 1200, 670, 1210)
    svg += draw_box(460, 1210, 420, 42, "SELECT WASHROOM → VIEW DETAILS → NAVIGATE", "Google Maps Launch (Origin → Selected Coordinates)", fill="#E6FFE6", stroke="#009933", font_size=11)

    # Branch 3: Incident Reporting (Right Center: x=940)
    svg += draw_box(940, 1070, 380, 38, "REPORT SAFETY ISSUE", "Categories: Lighting, Harassment, Infrastructure", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_arrow(1130, 1108, 1130, 1120)
    svg += draw_box(940, 1120, 380, 35, "CATEGORY + LOCATION + TIME + DESC", "Gathers Incident Details", fill="#FFF0F0", stroke="#800000", font_size=11)
    svg += draw_arrow(1130, 1155, 1130, 1165)
    svg += draw_box(940, 1165, 380, 35, "VALIDATION / TRUST CHECK", "Spam & Corroboration Engine", fill="#FFF0F0", stroke="#800000", font_size=11)
    svg += draw_arrow(1130, 1200, 1130, 1210)
    svg += draw_box(940, 1210, 380, 42, "REPORT SUBMITTED → CONTEXT UPDATED", "Triggers Immediate Risk & Route Re-evaluation", fill="#FFF3E0", stroke="#E65100", font_size=11)

    # Branch 4: Call a Friend (Far Right: x=1360)
    svg += draw_box(1360, 1070, 400, 38, "CALL A FRIEND TRIGGER", "Simulated Call UI for Personal Reassurance", fill="#800000", stroke="#5A0000", title_color="#FFFFFF")
    svg += draw_arrow(1560, 1108, 1560, 1118)
    
    svg += draw_box(1360, 1118, 400, 32, "INTERNET CONNECTIVITY CHECK", "", fill="#FFF0F0", stroke="#800000", font_size=11)
    svg += draw_arrow(1560, 1150, 1450, 1165)
    svg += draw_arrow(1560, 1150, 1670, 1165)

    svg += draw_box(1360, 1165, 180, 42, "ONLINE (SARVAM AI)", "Custom/Suggested Script\nMale/Female Voice Synthesis", fill="#EFF6FF", stroke="#2563EB", font_size=10)
    svg += draw_box(1560, 1165, 190, 42, "OFFLINE (LOCAL VOICE)", "Pre-installed Voice Clips\nMale/Female Audio Fallback", fill="#FEF2F2", stroke="#DC2626", font_size=10)

    svg += draw_arrow(1450, 1207, 1560, 1215)
    svg += draw_arrow(1670, 1207, 1560, 1215)
    svg += draw_box(1360, 1215, 400, 38, "SIMULATED CALL SCREEN PLAYBACK", "expo-audio Player Active Call Screen", fill="#E6FFE6", stroke="#009933", font_size=11)

    # Convergence to Journey Completion (Bottom)
    svg += draw_arrow(230, 1244, 900, 1280)
    svg += draw_arrow(670, 1252, 900, 1280)
    svg += draw_arrow(1130, 1252, 900, 1280)
    svg += draw_arrow(1560, 1253, 900, 1280)

    svg += draw_box(730, 1280, 340, 44, "REACH DESTINATION", "User Arrives Safely", fill="#E6FFE6", stroke="#009933")
    svg += draw_arrow(900, 1324, 900, 1340)
    svg += draw_box(730, 1340, 340, 44, "JOURNEY COMPLETE", "Session Closed & Summary Displayed", fill="#800000", stroke="#5A0000", title_color="#FFFFFF")

    svg += make_legend(1345, width=1720)
    svg += "</svg>"
    return svg

# ==============================================================================
# FLOWCHART 2: BACKEND / SYSTEM ARCHITECTURE
# ==============================================================================
def generate_backend_flowchart():
    w, h = 2000, 1500
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
  
  <!-- Title Banner -->
  <rect x="0" y="0" width="{w}" height="60" fill="#800000"/>
  <text x="{w/2}" y="38" font-family="Arial" font-size="22" font-weight="bold" fill="#FFFFFF" text-anchor="middle">SAKHI — Backend System Architecture</text>

  <!-- Core Gateway (Top Center) -->
  <g id="backend_gateway">
'''
    svg += draw_box(820, 80, 360, 48, "MOBILE APP (React Native + Expo)", "Client-side Application Layer", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(1000, 128, 1000, 150)
    svg += draw_box(820, 150, 360, 48, "FASTAPI API LAYER", "Main Backend Service Entry Gateway", fill="#FFF0F0", stroke="#800000")

    # Section 1: ROUTING & RISK ML PIPELINE (Middle Core Column: x=750 to 1250)
    svg += '<rect x="680" y="220" width="640" height="640" rx="8" fill="#FBF9FF" stroke="#6600CC" stroke-width="1.5"/>\n'
    svg += '<text x="1000" y="245" font-family="Arial" font-size="14" font-weight="bold" fill="#6600CC" text-anchor="middle">1. ROUTING & CONTEXTUAL RISK ENGINE PIPELINE</text>\n'

    svg += draw_arrow(1000, 198, 1000, 260)
    svg += draw_box(780, 260, 440, 44, "JOURNEY / ROUTING SERVICE", "Handles Origin/Destination Requests", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(1000, 304, 1000, 325)
    svg += draw_box(780, 325, 440, 44, "OSRM + OPENSTREETMAP ENGINE", "Generates Geometry Candidate Paths", fill="#F0F0F0", stroke="#666666")
    svg += draw_arrow(1000, 369, 1000, 390)
    svg += draw_box(780, 390, 440, 44, "ROUTE SEGMENTATION SERVICE", "Splits Geometry into Spatial Segments", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(1000, 434, 1000, 455)

    svg += draw_box(780, 455, 440, 44, "CONTEXTUAL FEATURE SERVICE", "Extracts Spatial + Temporal + Context Features", fill="#F2E6FF", stroke="#6600CC")
    svg += draw_arrow(1000, 499, 1000, 520)
    svg += draw_box(780, 520, 440, 44, "XGBOOST RISK ENGINE MODEL", "Evaluates Segment Contextual Safety Risk", fill="#F2E6FF", stroke="#6600CC")

    # Parallel Outputs from XGBoost (SHAP & Confidence)
    svg += draw_arrow(1000, 564, 870, 595)
    svg += draw_arrow(1000, 564, 1130, 595)

    svg += draw_box(710, 595, 320, 44, "SHAP EXPLANATION SERVICE", "TreeSHAP Feature Attribution", fill="#F2E6FF", stroke="#6600CC")
    svg += draw_box(1050, 595, 320, 44, "CONFIDENCE SERVICE", "Uncertainty & Data Quality Metric", fill="#F2E6FF", stroke="#6600CC")

    svg += draw_arrow(870, 639, 1000, 670)
    svg += draw_arrow(1130, 639, 1000, 670)

    svg += draw_box(780, 670, 440, 44, "RISK + SHAP + CONFIDENCE AGGREGATOR", "Combines Risk, Explanation & Quality Scores", fill="#F2E6FF", stroke="#6600CC")
    svg += draw_arrow(1000, 714, 1000, 735)
    svg += draw_arrow_label(1000, 725, "Rank Routes", color="#6600CC")

    svg += draw_box(780, 735, 440, 44, "ROUTE RANKING SERVICE", "Evaluates Safest / Balanced / Fastest", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(1000, 779, 1000, 800)
    svg += draw_box(780, 800, 440, 44, "JOURNEY RESPONSE GENERATOR", "Formats Map Coordinates + Report JSON", fill="#E6FFE6", stroke="#009933")

    # Connect Journey Response back to Mobile App
    svg += draw_arrow(1220, 822, 1350, 822, color="#009933", stroke_width=2)
    svg += draw_arrow(1350, 822, 1350, 104, color="#009933", stroke_width=2)
    svg += draw_arrow(1350, 104, 1180, 104, color="#009933", stroke_width=2)
    svg += draw_arrow_label(1350, 460, "Journey Response JSON", color="#009933")

    # Section 2: DATA LAYER & PREPROCESSING (Far Left Column: x=40 to 620)
    svg += '<rect x="40" y="220" width="600" height="640" rx="8" fill="#F4F8FB" stroke="#0066CC" stroke-width="1.5"/>\n'
    svg += '<text x="340" y="245" font-family="Arial" font-size="14" font-weight="bold" fill="#0066CC" text-anchor="middle">2. DATA STORAGE & SPATIAL ENGINE LAYER</text>\n'

    svg += '<rect x="60" y="265" width="560" height="200" rx="6" fill="#FFFFFF" stroke="#0066CC" stroke-width="1"/>\n'
    svg += '<text x="340" y="288" font-family="Arial" font-size="13" font-weight="bold" fill="#0066CC" text-anchor="middle">DELHI DATA SOURCES</text>\n'

    sources = [
        "NCRB / Crime Statistics Data",
        "Population & Grid Density Data",
        "Police Station Coordinates & Boundaries",
        "Hospitals & Emergency Medical Facilities",
        "Public Washrooms & Amenities (Right to Pee)",
        "OpenStreetMap GIS Infrastructure Features"
    ]
    for k, sname in enumerate(sources):
        sy_pos = 300 + k * 26
        svg += f'<text x="80" y="{sy_pos}" font-family="Arial" font-size="11" fill="#374151">• {sname}</text>\n'

    svg += draw_arrow(340, 465, 340, 495)
    svg += draw_box(120, 495, 440, 44, "DATA PREPROCESSING ENGINE", "Cleans, Validates & Normalizes Spatial Data", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(340, 539, 340, 570)
    svg += draw_box(120, 570, 440, 44, "FEATURE ENGINEERING PIPELINE", "Extracts Spatial & Temporal Risk Features", fill="#F2E6FF", stroke="#6600CC")
    svg += draw_arrow(340, 614, 340, 645)

    svg += draw_box(80, 645, 520, 100, "POSTGRESQL / POSTGIS DATABASE", "Central Spatial & Safety Data Repository\n• Crime & Risk Feature Store  • Spatial Features & Geometries\n• Verified Restrooms & Amenities  • Incident Reports Store", fill="#E6F2FF", stroke="#0066CC")

    # Connect PostGIS to Contextual Feature Service
    svg += draw_arrow(600, 695, 780, 477, color="#0066CC", stroke_width=2)
    svg += draw_arrow_label(680, 570, "Feeds Spatial Features", color="#0066CC")

    # Section 3: USER FEEDBACK / INCIDENT REPORTING BACKEND (Far Right: x=1360 to 1940)
    svg += '<rect x="1360" y="220" width="580" height="640" rx="8" fill="#FFF8F0" stroke="#E65100" stroke-width="1.5"/>\n'
    svg += '<text x="1650" y="245" font-family="Arial" font-size="14" font-weight="bold" fill="#E65100" text-anchor="middle">3. USER FEEDBACK & INCIDENT ENGINE</text>\n'

    svg += draw_box(1430, 270, 440, 44, "FEEDBACK / INCIDENT API", "Receives Crowdsourced Safety Observations", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(1650, 314, 1650, 340)
    svg += draw_box(1430, 340, 440, 44, "VALIDATION / TRUST / DUPLICATE CHECK", "Corroboration & Spam Prevention Engine", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(1650, 384, 1650, 410)
    svg += draw_box(1430, 410, 440, 44, "INCIDENT STORAGE SERVICE", "Persists Validated Incident Metrics", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_arrow(1650, 454, 1650, 480)

    svg += draw_box(1430, 480, 440, 44, "CONTEXT UPDATE SERVICE", "Triggers Real-time Safety Map Refresh", fill="#FFF3E0", stroke="#E65100")
    svg += draw_arrow(1650, 524, 1650, 550)
    svg += draw_box(1430, 550, 440, 44, "RISK RECALCULATION & REROUTING", "Re-evaluates Active Journey Risk Scores", fill="#FFF3E0", stroke="#E65100")

    # Long-term Learning Cycle
    svg += draw_arrow(1650, 594, 1650, 620)
    svg += draw_box(1410, 620, 480, 90, "LONG-TERM MODEL RETRAINING LOOP", "Validated Incidents → Retraining Dataset → XGBoost Retraining\n→ Upgraded Risk Engine Weights", fill="#FFF3E0", stroke="#E65100")

    svg += draw_arrow(1410, 665, 1220, 542, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")
    svg += draw_arrow_label(1310, 600, "Retrains XGBoost", color="#E65100")

    # Trust Specification Box
    svg += '<rect x="1390" y="735" width="520" height="110" rx="6" fill="#FFFBEB" stroke="#D97706" stroke-width="2"/>\n'
    svg += '<text x="1650" y="760" font-family="Arial" font-size="12" font-weight="bold" fill="#92400E" text-anchor="middle">⚠️ TRUST vs INCIDENT VALIDATION SPECIFICATION</text>\n'
    svg += '<text x="1650" y="785" font-family="Arial" font-size="11" fill="#B45309" text-anchor="middle">"Identity / account verification does NOT mean an incident report is true."</text>\n'
    svg += '<text x="1650" y="805" font-family="Arial" font-size="11" fill="#B45309" text-anchor="middle">"Trust scoring and incident corroboration remain strictly separate."</text>\n'
    svg += '<text x="1650" y="825" font-family="Arial" font-size="11" fill="#B45309" text-anchor="middle">"Incident validity depends on spatial/temporal consensus & duplicate filtering."</text>\n'

    # Section 4: AMENITIES BACKEND (Bottom Left: x=40 to 620, y=900)
    svg += '<rect x="40" y="900" width="600" height="420" rx="8" fill="#F4F8FB" stroke="#0066CC" stroke-width="1.5"/>\n'
    svg += '<text x="340" y="925" font-family="Arial" font-size="14" font-weight="bold" fill="#0066CC" text-anchor="middle">4. AMENITIES / RIGHT TO PEE BACKEND</text>\n'

    svg += draw_box(120, 945, 440, 44, "AMENITIES API ENDPOINT", "/api/v1/amenities Queries", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(340, 989, 340, 1010)

    svg += draw_box(80, 1010, 520, 52, "REAL DELHI AMENITY DATA SOURCES", "OpenStreetMap / Overpass API + Government Official Open Data", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_arrow(340, 1062, 340, 1085)
    svg += draw_box(120, 1085, 440, 44, "POSTGRESQL / POSTGIS AMENITIES STORE", "Stores Filtered Restroom Coordinates & Ratings", fill="#E6F2FF", stroke="#0066CC")
    svg += draw_arrow(340, 1129, 340, 1150)
    svg += draw_box(120, 1150, 440, 44, "NEARBY / ALONG-ROUTE AMENITIES RESPONSE", "Returns Validated Washroom Markers to App", fill="#E6FFE6", stroke="#009933")
    svg += draw_arrow(340, 1194, 340, 1215)
    svg += draw_box(120, 1215, 440, 44, "GOOGLE MAPS NAVIGATION LAUNCH", "Selected Origin → Selected Amenity Coordinates", fill="#E6FFE6", stroke="#009933")

    # Section 5: TWO-LAYER CALL A FRIEND BACKEND (Bottom Center: x=680 to 1320, y=900)
    svg += '<rect x="680" y="900" width="640" height="420" rx="8" fill="#F8FAFC" stroke="#334155" stroke-width="1.5"/>\n'
    svg += '<text x="1000" y="925" font-family="Arial" font-size="14" font-weight="bold" fill="#1E293B" text-anchor="middle">5. TWO-LAYER CALL A FRIEND BACKEND ARCHITECTURE</text>\n'

    svg += draw_box(780, 945, 440, 44, "CALL A FRIEND BACKEND API", "/api/v1/call-friend Endpoint", fill="#FFF0F0", stroke="#800000")
    svg += draw_arrow(1000, 989, 1000, 1010)

    svg += draw_box(780, 1010, 440, 40, "NETWORK CONNECTIVITY ROUTER", "Detects Internet Availability", fill="#FFF0F0", stroke="#800000", font_size=11)
    
    svg += draw_arrow(1000, 1050, 840, 1080)
    svg += draw_arrow_label(900, 1060, "YES (ONLINE)", color="#0066CC")
    
    svg += draw_arrow(1000, 1050, 1160, 1080)
    svg += draw_arrow_label(1100, 1060, "NO (OFFLINE)", color="#DC2626")

    svg += draw_box(710, 1080, 270, 44, "SARVAM AI TTS SERVICE", "Bulbul V3 Synthesis (shubh/priya)", fill="#F2E6FF", stroke="#6600CC", font_size=11)
    svg += draw_box(1020, 1080, 270, 44, "LOCAL PRE-INSTALLED AUDIO CLIPS", "6 Local WAV Clips (Zero Network)", fill="#FEF2F2", stroke="#DC2626", font_size=11)

    svg += draw_arrow(845, 1124, 1000, 1150)
    svg += draw_arrow(1155, 1124, 1000, 1150)

    svg += draw_box(780, 1150, 440, 44, "SIMULATED CALL PLAYBACK UI", "expo-audio Player Active Call Screen", fill="#E6FFE6", stroke="#009933")
    svg += draw_box(780, 1210, 440, 36, "📌 Note: Simulated Safety Call UI. No direct cellular call initiated.", "", fill="#FFFBEB", stroke="#D97706", font_size=11)

    # Section 6: OFFLINE / LOCAL CACHE BACKEND (Bottom Right: x=1360 to 1940, y=900)
    svg += '<rect x="1360" y="900" width="580" height="420" rx="8" fill="#FFF3E0" stroke="#E65100" stroke-width="1.5"/>\n'
    svg += '<text x="1650" y="925" font-family="Arial" font-size="14" font-weight="bold" fill="#E65100" text-anchor="middle">6. OFFLINE / RESILIENT LOCAL CACHE MATRIX</text>\n'

    svg += draw_box(1430, 945, 440, 44, "LIVE DATA STREAM", "Active API Connection Stream", fill="#EFF6FF", stroke="#2563EB")
    svg += draw_arrow(1650, 989, 1650, 1010)

    svg += draw_box(1390, 1010, 520, 100, "MOBILE LOCAL CACHE MATRIX", "Pre-stored Non-Emergency Offline Assets:\n• Journey Details & Waypoints  • Route Geometries\n• Segment Risk Scores & SHAP  • Confidence Ratings\n• Nearby Restroom Data  • Local Call-a-Friend Audio Library", fill="#FFF3E0", stroke="#E65100")

    svg += draw_arrow(1650, 1110, 1530, 1140)
    svg += draw_arrow(1650, 1110, 1770, 1140)

    svg += draw_box(1390, 1140, 250, 44, "NETWORK UNAVAILABLE", "Loads Cached Local Data", fill="#FEF2F2", stroke="#DC2626", font_size=11)
    svg += draw_box(1660, 1140, 250, 44, "NETWORK RESTORED", "Triggers Refresh & Sync", fill="#E6FFE6", stroke="#009933", font_size=11)

    svg += draw_arrow(1785, 1184, 1650, 1215)
    svg += draw_box(1430, 1215, 440, 44, "SYNCHRONIZE & REFRESH LIVE STREAM", "Re-syncs Client Data with FastAPI Backend", fill="#E6FFE6", stroke="#009933")

    # Section 7: SYSTEM FEEDBACK LOOP (Bottom Full Connector)
    svg += draw_arrow(1650, 1259, 1650, 1370, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")
    svg += draw_arrow(1650, 1370, 1000, 1370, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")
    svg += draw_arrow(1000, 1370, 1000, 860, color="#E65100", stroke_width=2, dash="4", marker="arrow-orange")
    svg += draw_arrow_label(1320, 1360, "System Feedback & Continuous Model Improvement ↺", color="#E65100")

    svg += make_legend(1440, width=1920)
    svg += "</svg>"
    return svg

# ==============================================================================
# MAIN EXECUTION: GENERATE ONLY THE 4 REQUIRED FILES
# ==============================================================================
# Clean up any existing flowchart files in docs/flowcharts to guarantee exactly the 4 required files exist
for existing_file in os.listdir(out_dir_docs):
    file_path = os.path.join(out_dir_docs, existing_file)
    if os.path.isfile(file_path):
        os.remove(file_path)

print("Cleaned docs/flowcharts directory.")

# 1. Frontend Flowchart
svg_frontend = generate_frontend_flowchart()
svg_path_f_docs = os.path.join(out_dir_docs, "sakhi_frontend_user_flow.svg")
png_path_f_docs = os.path.join(out_dir_docs, "sakhi_frontend_user_flow.png")
svg_path_f_art = os.path.join(out_dir_artifacts, "sakhi_frontend_user_flow.svg")
png_path_f_art = os.path.join(out_dir_artifacts, "sakhi_frontend_user_flow.png")

with open(svg_path_f_docs, "w", encoding="utf-8") as f:
    f.write(svg_frontend)
with open(svg_path_f_art, "w", encoding="utf-8") as f:
    f.write(svg_frontend)

render_svg_to_png(svg_path_f_docs, png_path_f_docs, 1800, 1400)
render_svg_to_png(svg_path_f_art, png_path_f_art, 1800, 1400)
print("GENERATED: sakhi_frontend_user_flow.svg & sakhi_frontend_user_flow.png")

# 2. Backend Flowchart
svg_backend = generate_backend_flowchart()
svg_path_b_docs = os.path.join(out_dir_docs, "sakhi_backend_system_architecture.svg")
png_path_b_docs = os.path.join(out_dir_docs, "sakhi_backend_system_architecture.png")
svg_path_b_art = os.path.join(out_dir_artifacts, "sakhi_backend_system_architecture.svg")
png_path_b_art = os.path.join(out_dir_artifacts, "sakhi_backend_system_architecture.png")

with open(svg_path_b_docs, "w", encoding="utf-8") as f:
    f.write(svg_backend)
with open(svg_path_b_art, "w", encoding="utf-8") as f:
    f.write(svg_backend)

render_svg_to_png(svg_path_b_docs, png_path_b_docs, 2000, 1500)
render_svg_to_png(svg_path_b_art, png_path_b_art, 2000, 1500)
print("GENERATED: sakhi_backend_system_architecture.svg & sakhi_backend_system_architecture.png")

print("EXACTLY TWO FLOWCHARTS (4 FILES TOTAL) GENERATED SUCCESSFULLY!")
