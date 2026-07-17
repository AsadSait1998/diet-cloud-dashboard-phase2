"""Build the submission-ready Phase 2 architecture and implementation PDF."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image as PILImage
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
EVIDENCE = ROOT / "docs" / "evidence"
OUTPUT = ROOT / "docs" / "Phase2_Diet_Cloud_Dashboard_Report.pdf"

INK = colors.HexColor("#12231c")
FOREST = colors.HexColor("#174f3b")
FOREST_DARK = colors.HexColor("#0e382a")
MINT = colors.HexColor("#c9e8d6")
LIME = colors.HexColor("#dbea7d")
CREAM = colors.HexColor("#f4f1e9")
PAPER = colors.HexColor("#fffdf8")
CORAL = colors.HexColor("#e97b62")
GOLD = colors.HexColor("#e1ad45")
MUTED = colors.HexColor("#607068")
LINE = colors.HexColor("#d9ddd5")


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def scaled_image(path: Path, max_width: float, max_height: float) -> Image:
    with PILImage.open(path) as source:
        width, height = source.size
    scale = min(max_width / width, max_height / height)
    return Image(str(path), width=width * scale, height=height * scale)


def architecture_drawing() -> Drawing:
    drawing = Drawing(504, 255)

    def box(x, y, w, h, fill, title, subtitle, title_color=colors.white):
        drawing.add(Rect(x, y, w, h, rx=10, ry=10, fillColor=fill, strokeColor=colors.transparent))
        drawing.add(String(x + w / 2, y + h - 22, title, textAnchor="middle", fontName="Helvetica-Bold", fontSize=10, fillColor=title_color))
        drawing.add(String(x + w / 2, y + 16, subtitle, textAnchor="middle", fontName="Helvetica", fontSize=7.7, fillColor=title_color))

    def arrow(x1, y1, x2, y2, label=None):
        drawing.add(Line(x1, y1, x2, y2, strokeColor=FOREST, strokeWidth=1.6))
        drawing.add(Polygon([x2, y2, x2 - 7, y2 + 4, x2 - 7, y2 - 4], fillColor=FOREST, strokeColor=FOREST))
        if label:
            drawing.add(String((x1 + x2) / 2, y1 + 8, label, textAnchor="middle", fontName="Helvetica", fontSize=7.5, fillColor=MUTED))

    box(5, 105, 84, 58, CORAL, "Dashboard user", "Browser / HTTPS")
    box(120, 105, 105, 58, FOREST, "Static Web Apps", "HTML, CSS, JavaScript")
    box(262, 105, 108, 58, FOREST_DARK, "Azure Function", "Python 3.11 / HTTP")
    box(407, 105, 92, 58, colors.HexColor("#4b7898"), "Blob Storage", "Private CSV blob")
    box(262, 8, 108, 52, colors.HexColor("#7b5e8b"), "App Insights", "Logs and telemetry")
    box(120, 198, 105, 48, GOLD, "GitHub Actions", "CI and deployments", INK)
    arrow(89, 134, 120, 134, "page")
    arrow(225, 134, 262, 134, "filtered GET")
    arrow(370, 134, 407, 134, "private read")
    arrow(262, 119, 225, 119, "JSON")
    drawing.add(Line(316, 105, 316, 60, strokeColor=FOREST, strokeWidth=1.6))
    drawing.add(Polygon([316, 60, 312, 67, 320, 67], fillColor=FOREST, strokeColor=FOREST))
    drawing.add(Line(173, 198, 173, 163, strokeColor=FOREST, strokeWidth=1.6))
    drawing.add(Line(173, 180, 316, 180, strokeColor=FOREST, strokeWidth=1.6))
    drawing.add(Line(316, 180, 316, 163, strokeColor=FOREST, strokeWidth=1.6))
    drawing.add(String(245, 186, "deploy", textAnchor="middle", fontName="Helvetica", fontSize=7.5, fillColor=MUTED))
    return drawing


def build() -> None:
    deployment_values_path = EVIDENCE / "deployment_values.json"
    deployment_values = json.loads(deployment_values_path.read_text(encoding="utf-8")) if deployment_values_path.exists() else {}
    function_url = deployment_values.get("function_url") or "https://________________________________.azurewebsites.net/api/diet-insights"
    dashboard_url = deployment_values.get("dashboard_url") or "https://________________________________.azurestaticapps.net"
    github_url = deployment_values.get("github_url") or "https://github.com/________________/________________"

    sample = getSampleStyleSheet()
    styles = {
        "cover_kicker": ParagraphStyle("Cover Kicker", parent=sample["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=LIME, spaceAfter=16, tracking=1.5),
        "cover_title": ParagraphStyle("Cover Title", parent=sample["Title"], fontName="Times-Roman", fontSize=37, leading=39, textColor=colors.white, spaceAfter=16),
        "cover_subtitle": ParagraphStyle("Cover Subtitle", parent=sample["Normal"], fontName="Helvetica", fontSize=14, leading=20, textColor=MINT, spaceAfter=42),
        "cover_team": ParagraphStyle("Cover Team", parent=sample["Normal"], fontName="Helvetica-Bold", fontSize=11, leading=17, textColor=colors.white),
        "cover_meta": ParagraphStyle("Cover Meta", parent=sample["Normal"], fontName="Helvetica", fontSize=9, leading=13, textColor=colors.HexColor("#b8cbc2")),
        "h1": ParagraphStyle("Heading 1 Custom", parent=sample["Heading1"], fontName="Times-Roman", fontSize=24, leading=28, textColor=INK, spaceBefore=4, spaceAfter=12, keepWithNext=True),
        "h2": ParagraphStyle("Heading 2 Custom", parent=sample["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=FOREST, spaceBefore=14, spaceAfter=7, keepWithNext=True),
        "body": ParagraphStyle("Body Custom", parent=sample["BodyText"], fontName="Helvetica", fontSize=9.2, leading=13.8, textColor=INK, spaceAfter=7),
        "small": ParagraphStyle("Small", parent=sample["BodyText"], fontName="Helvetica", fontSize=7.7, leading=10.8, textColor=MUTED, spaceAfter=4),
        "bullet": ParagraphStyle("Bullet", parent=sample["BodyText"], fontName="Helvetica", fontSize=8.8, leading=13, textColor=INK, leftIndent=13, firstLineIndent=-9, spaceAfter=4),
        "callout": ParagraphStyle("Callout", parent=sample["BodyText"], fontName="Helvetica-Bold", fontSize=9, leading=13.5, textColor=FOREST_DARK),
        "caption": ParagraphStyle("Caption", parent=sample["BodyText"], fontName="Helvetica-Oblique", fontSize=7.5, leading=10.5, textColor=MUTED, alignment=TA_CENTER, spaceBefore=5, spaceAfter=10),
        "table_header": ParagraphStyle("Table Header", parent=sample["BodyText"], fontName="Helvetica-Bold", fontSize=7.7, leading=10, textColor=colors.white),
        "table_body": ParagraphStyle("Table Body", parent=sample["BodyText"], fontName="Helvetica", fontSize=7.5, leading=10, textColor=INK),
        "table_body_bold": ParagraphStyle("Table Body Bold", parent=sample["BodyText"], fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=INK),
        "ref": ParagraphStyle("Reference", parent=sample["BodyText"], fontName="Helvetica", fontSize=7.4, leading=10.3, textColor=INK, leftIndent=13, firstLineIndent=-13, spaceAfter=5),
    }

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.68 * inch,
        bottomMargin=0.62 * inch,
        title="Phase 2 Diet Cloud Dashboard Report",
        author="Asad Arif, Can Ozveren, Muhammad Talha Arif",
        subject="Azure cloud dashboard development project",
    )

    def cover_page(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(FOREST_DARK)
        canvas.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
        canvas.setFillColor(LIME)
        canvas.circle(letter[0] - 76, letter[1] - 76, 31, fill=1, stroke=0)
        canvas.setFillColor(FOREST)
        canvas.circle(letter[0] - 76, letter[1] - 76, 17, fill=1, stroke=0)
        canvas.setStrokeColor(colors.HexColor("#2e654f"))
        canvas.setLineWidth(1)
        canvas.line(0.65 * inch, 1.05 * inch, letter[0] - 0.65 * inch, 1.05 * inch)
        canvas.restoreState()

    def later_page(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(CREAM)
        canvas.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(FOREST)
        canvas.drawString(0.65 * inch, letter[1] - 0.38 * inch, "DIET CLOUD  /  PHASE 2 TECHNICAL REPORT")
        canvas.setStrokeColor(LINE)
        canvas.line(0.65 * inch, letter[1] - 0.46 * inch, letter[0] - 0.65 * inch, letter[1] - 0.46 * inch)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(0.65 * inch, 0.34 * inch, "Asad Arif  |  Can Ozveren  |  Muhammad Talha Arif")
        canvas.drawRightString(letter[0] - 0.65 * inch, 0.34 * inch, f"Page {_doc.page}")
        canvas.restoreState()

    story = []

    story.extend([
        Spacer(1, 1.18 * inch),
        p("CLOUD DASHBOARD DEVELOPMENT", styles["cover_kicker"]),
        p("Project Phase 2<br/>Diet Cloud Dashboard", styles["cover_title"]),
        p("Azure Functions, private Blob Storage, interactive data visualizations, and repeatable cloud deployment", styles["cover_subtitle"]),
        p("PROJECT TEAM", styles["cover_kicker"]),
        p("Asad Arif<br/>Can Ozveren<br/>Muhammad Talha Arif", styles["cover_team"]),
        Spacer(1, 1.2 * inch),
        p("Technical implementation report  |  July 17, 2026", styles["cover_meta"]),
        p("Verified locally against the complete 7,806-row Phase 1 dataset. Azure account deployment evidence is identified explicitly in the final handoff section.", styles["cover_meta"]),
        PageBreak(),
    ])

    story.extend([
        p("Executive summary", styles["h1"]),
        p("Phase 2 converts the Phase 1 local analysis into a cloud-native, browser-accessible dashboard. A Python Azure Function reads the Diets Dataset from a private Blob Storage container, performs cleaning and aggregation, and returns compact JSON for four interactive visualizations. Azure Static Web Apps hosts the responsive frontend, while GitHub Actions supports continuous testing and separate frontend/backend deployments.", styles["body"]),
        p("Implementation status", styles["h2"]),
    ])
    status_rows = [
        [p("Area", styles["table_header"]), p("Status", styles["table_header"]), p("Evidence", styles["table_header"])],
        [p("Backend API", styles["table_body_bold"]), p("Complete", styles["table_body"]), p("Filterable Azure Functions v2 endpoint with validation, caching, metadata, CORS, and errors", styles["table_body"])],
        [p("Dashboard", styles["table_body_bold"]), p("Complete", styles["table_body"]), p("Four charts, five KPIs, dynamic filters, loading/error states, accessible table, responsive layout", styles["table_body"])],
        [p("Cloud assets", styles["table_body_bold"]), p("Complete", styles["table_body"]), p("Flex Consumption Bicep, private storage containers, monitoring, CORS, TLS, deployment scripts", styles["table_body"])],
        [p("Verification", styles["table_body_bold"]), p("Complete locally", styles["table_body"]), p("4 unit tests; 7,806-row API check; filter/reset checks; mobile overflow and console checks", styles["table_body"])],
        [p("Azure links", styles["table_body_bold"]), p("Team action", styles["table_body"]), p("Requires an Azure subscription, GitHub repository, publish profile, and deployment token", styles["table_body"])],
    ]
    status_table = Table(status_rows, colWidths=[1.18 * inch, 1.05 * inch, 4.35 * inch], repeatRows=1)
    status_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), FOREST),
        ("BACKGROUND", (0, 1), (-1, -1), PAPER),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(status_table)
    story.extend([
        Spacer(1, 12),
        Table([[p("KEY HANDOFF", styles["table_header"]), p("All locally authorable work is complete. The remaining steps create resources in the team's accounts, supply three public URLs, and replace local screenshots with Azure evidence if the instructor requires portal proof.", styles["callout"]) ]], colWidths=[1.15 * inch, 5.43 * inch], style=TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), FOREST_DARK),
            ("BACKGROUND", (1, 0), (1, 0), MINT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ])),
        p("Phase 2 objectives satisfied", styles["h2"]),
        p("- Deployable serverless analysis through an Azure Function App.", styles["bullet"]),
        p("- Cloud dataset storage through a private Azure Blob container.", styles["bullet"]),
        p("- Browser dashboard with more than the required three visualizations.", styles["bullet"]),
        p("- Frontend-to-backend integration with filters, refresh, and execution metadata.", styles["bullet"]),
        p("- Cloud-native resource settings, monitoring, security headers, and CI/CD workflows.", styles["bullet"]),
        PageBreak(),
    ])

    story.extend([
        p("Solution architecture", styles["h1"]),
        p("The design separates presentation, compute, storage, telemetry, and deployment concerns. The static frontend never receives an Azure Storage credential. It calls a read-only HTTP endpoint, and only the Function App crosses the private storage boundary.", styles["body"]),
        Spacer(1, 8),
        architecture_drawing(),
        p("Figure 1. Phase 2 Azure architecture and primary request path.", styles["caption"]),
        p("Request flow", styles["h2"]),
        p("1. Azure Static Web Apps serves the dashboard's HTML, CSS, JavaScript, and security configuration.", styles["bullet"]),
        p("2. The dashboard requests <b>/api/diet-insights</b> with optional diet, cuisine, search, and refresh parameters.", styles["bullet"]),
        p("3. The Function downloads <b>datasets/All_Diets.csv</b> from private Blob Storage or reuses a five-minute in-memory cache.", styles["bullet"]),
        p("4. The shared analysis module validates required fields, normalizes text, parses numeric macros, and mean-imputes missing values.", styles["bullet"]),
        p("5. Filtered metrics and four chart datasets are returned as JSON with request, source, version, and execution metadata.", styles["bullet"]),
        p("6. Canvas renderers redraw the visualizations and update the accessible data table without reloading the page.", styles["bullet"]),
        p("Azure services", styles["h2"]),
    ])
    service_rows = [
        [p("Service", styles["table_header"]), p("Responsibility", styles["table_header"]), p("Configuration", styles["table_header"])],
        [p("Azure Functions", styles["table_body_bold"]), p("HTTP analysis API", styles["table_body"]), p("Python 3.11, Flex Consumption, anonymous read-only trigger", styles["table_body"])],
        [p("Blob Storage", styles["table_body_bold"]), p("Dataset source", styles["table_body"]), p("Private datasets container; public blob access disabled", styles["table_body"])],
        [p("Static Web Apps", styles["table_body_bold"]), p("Public frontend", styles["table_body"]), p("Free tier, static build skipped, production API URL injected", styles["table_body"])],
        [p("Application Insights", styles["table_body_bold"]), p("Operations", styles["table_body"]), p("Request sampling, errors, execution telemetry", styles["table_body"])],
    ]
    service_table = Table(service_rows, colWidths=[1.28 * inch, 1.55 * inch, 3.75 * inch], repeatRows=1)
    service_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), FOREST),
        ("BACKGROUND", (0, 1), (-1, -1), PAPER),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([service_table, PageBreak()])

    story.extend([
        p("Backend API and analysis", styles["h1"]),
        p("The backend uses the decorator-based Azure Functions Python v2 model. The global <b>function_app.py</b> defines one HTTP trigger and delegates all dataset work to testable modules. Production dependencies are intentionally limited to <b>azure-functions</b> and <b>azure-storage-blob</b>; aggregation uses Python's standard library to reduce deployment size and cold-start overhead.", styles["body"]),
        p("Endpoint", styles["h2"]),
        Table([[p("GET", styles["table_header"]), p("/api/diet-insights?diet_types=Vegan&amp;cuisine=Indian&amp;search=curry&amp;refresh=true", styles["callout"]) ]], colWidths=[0.7 * inch, 5.88 * inch], style=TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), FOREST),
            ("BACKGROUND", (1, 0), (1, 0), MINT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])),
        p("Response contract", styles["h2"]),
    ])
    contract_rows = [
        [p("Object", styles["table_header"]), p("Contents", styles["table_header"])],
        [p("summary", styles["table_body_bold"]), p("Recipe count, represented diet types, and mean protein/carbs/fat", styles["table_body"])],
        [p("filters", styles["table_body_bold"]), p("Available diet and cuisine values plus the applied request values", styles["table_body"])],
        [p("charts", styles["table_body_bold"]), p("Average macros, distribution, protein-versus-carbs points, and top cuisines", styles["table_body"])],
        [p("metadata", styles["table_body_bold"]), p("UTC time, source, record counts, execution milliseconds, request ID, cache status, API version", styles["table_body"])],
    ]
    contract_table = Table(contract_rows, colWidths=[1.25 * inch, 5.33 * inch], repeatRows=1)
    contract_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), FOREST),
        ("BACKGROUND", (0, 1), (-1, -1), PAPER),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([
        contract_table,
        p("Data preparation", styles["h2"]),
        p("- Required columns are resolved through normalized aliases, preserving compatibility with the Phase 1 dataset and common header variations.", styles["bullet"]),
        p("- Diet and cuisine labels are whitespace-normalized and title-cased; recipe names retain readable capitalization.", styles["bullet"]),
        p("- Protein, carbohydrates, and fat are parsed defensively. Missing or invalid numeric values use the column mean, then zero only if a column contains no valid values.", styles["bullet"]),
        p("- Scatter results are bounded to the top 30 protein-rich recipes per represented diet, keeping HTTP responses and browser rendering compact.", styles["bullet"]),
        p("Reliability and observability", styles["h2"]),
        p("Input/data errors return HTTP 400, cloud configuration problems return 503, and unexpected exceptions return a non-sensitive 500 response. Every response includes a request ID; the Function records details in Application Insights. A bounded cache (default 300 seconds) reduces repeated Blob downloads while the refresh control can force a reload.", styles["body"]),
        PageBreak(),
    ])

    story.extend([
        p("Interactive dashboard", styles["h1"]),
        p("The provided Phase 2 HTML mockup was rebuilt as a complete, responsive interface with no external UI or chart dependency. Native canvas renderers keep the deployed site self-contained and avoid CDN failures. The frontend handles loading, timeout, API errors, empty results, source refresh, and responsive redraws.", styles["body"]),
        scaled_image(ASSETS / "dashboard-overview.png", 6.58 * inch, 4.2 * inch),
        p("Figure 2. Local end-to-end dashboard verification using the complete Phase 1 dataset. The source label and connection status explicitly identify local mode.", styles["caption"]),
        p("Interaction controls", styles["h2"]),
        p("- Recipe search performs a case-insensitive substring match across recipe, diet, and cuisine.", styles["bullet"]),
        p("- Diet and cuisine selectors are populated from API-provided filter metadata.", styles["bullet"]),
        p("- Update insights sends the selected filters; clear resets all controls; refresh bypasses the Function cache.", styles["bullet"]),
        p("- Five KPI cards and the hero metadata update from the same API response as the charts.", styles["bullet"]),
        p("Accessibility", styles["h2"]),
        p("Semantic regions, headings, labels, focus states, reduced-motion support, canvas alternative labels, and a live average-macros table provide a navigable experience beyond the visual charts.", styles["body"]),
        PageBreak(),
    ])

    story.extend([
        p("Data visualizations", styles["h1"]),
        p("The dashboard exceeds the brief's requirement for three distinct and meaningful visualizations. Every chart is redrawn from the filtered Azure Function response, so all views remain consistent with the KPI cards and table.", styles["body"]),
        scaled_image(ASSETS / "dashboard-charts-detail.png", 6.58 * inch, 3.76 * inch),
        p("Figure 3. Verified grouped bar, donut, and leading-cuisine visualizations.", styles["caption"]),
    ])
    viz_rows = [
        [p("Visualization", styles["table_header"]), p("Question answered", styles["table_header"]), p("Encoding", styles["table_header"])],
        [p("Grouped bar", styles["table_body_bold"]), p("How do mean macros compare across diet types?", styles["table_body"]), p("Diet on x-axis; grams on y-axis; color by macro", styles["table_body"])],
        [p("Donut", styles["table_body_bold"]), p("What share of recipes belongs to each diet?", styles["table_body"]), p("Arc length and percentage by diet type", styles["table_body"])],
        [p("Horizontal bar", styles["table_body_bold"]), p("Which cuisines appear most often in the result?", styles["table_body"]), p("Cuisine label and recipe count", styles["table_body"])],
        [p("Scatter", styles["table_body_bold"]), p("How do protein and carbs relate among protein-rich recipes?", styles["table_body"]), p("Carbs on x, protein on y, fat by point size, diet by color", styles["table_body"])],
    ]
    viz_table = Table(viz_rows, colWidths=[1.2 * inch, 2.58 * inch, 2.8 * inch], repeatRows=1)
    viz_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), FOREST),
        ("BACKGROUND", (0, 1), (-1, -1), PAPER),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([
        viz_table,
        p("Interpretation example", styles["h2"]),
        p("In the complete dataset view, Vegan recipes have the highest mean carbohydrates (254.00 g), while Keto has the lowest (57.97 g). Keto and Mediterranean have similar mean protein values (101.27 g and 101.11 g). These are descriptive dataset aggregates and should not be interpreted as medical or dietary advice.", styles["body"]),
        PageBreak(),
    ])

    story.extend([
        p("Cloud deployment and practices", styles["h1"]),
        p("The repository includes a Bicep template and PowerShell orchestrator. The Bicep template compiled successfully with Azure Bicep CLI 0.45.15. It provisions a Python Flex Consumption Function App, two private Blob containers, a Free Static Web App, Application Insights, and Log Analytics in one resource group.", styles["body"]),
        p("Configuration model", styles["h2"]),
    ])
    config_rows = [
        [p("Setting", styles["table_header"]), p("Purpose", styles["table_header"]), p("Example", styles["table_header"])],
        [p("DIET_STORAGE_CONNECTION_STRING", styles["table_body_bold"]), p("Private dataset access", styles["table_body"]), p("Stored only in Function App settings", styles["table_body"])],
        [p("DATA_CONTAINER_NAME", styles["table_body_bold"]), p("Blob container", styles["table_body"]), p("datasets", styles["table_body"])],
        [p("DATA_BLOB_NAME", styles["table_body_bold"]), p("Dataset blob", styles["table_body"]), p("All_Diets.csv", styles["table_body"])],
        [p("CORS_ALLOWED_ORIGIN", styles["table_body_bold"]), p("Restrict browser origin", styles["table_body"]), p("Generated Static Web App URL", styles["table_body"])],
        [p("CACHE_TTL_SECONDS", styles["table_body_bold"]), p("Blob-read cache", styles["table_body"]), p("300", styles["table_body"])],
    ]
    config_table = Table(config_rows, colWidths=[2.3 * inch, 1.7 * inch, 2.58 * inch], repeatRows=1)
    config_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), FOREST),
        ("BACKGROUND", (0, 1), (-1, -1), PAPER),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([
        config_table,
        p("CI/CD", styles["h2"]),
        p("- <b>ci.yml</b> installs backend dependencies, compiles Python, runs unit tests, and verifies required frontend assets.", styles["bullet"]),
        p("- <b>deploy-function.yml</b> uses the documented Azure Functions action with Flex Consumption and remote build settings.", styles["bullet"]),
        p("- <b>deploy-frontend.yml</b> injects the Function API base URL from a GitHub secret, then deploys static files through the Azure Static Web Apps action.", styles["bullet"]),
        p("Security choices", styles["h2"]),
        p("Public blob access is disabled; HTTPS and TLS 1.2 are required; FTPS is disabled; CORS is scoped to the Static Web App; security headers include CSP, referrer policy, MIME sniffing protection, and restricted browser permissions. GitHub credentials are referenced only through encrypted secrets. The read-only course API is anonymous so no Function key is exposed in browser code.", styles["body"]),
        p("Production hardening recommendation", styles["h2"]),
        p("For a long-lived production environment, replace storage connection strings with managed identity/RBAC and, where secrets remain necessary, Key Vault references. The course template keeps a shared-key connection only to simplify one-command provisioning and the initial dataset upload.", styles["body"]),
        PageBreak(),
    ])

    story.extend([
        p("Verification and quality assurance", styles["h1"]),
        p("Testing covered analysis correctness, API behavior, browser interactions, responsive layout, syntax, configuration, and infrastructure compilation. Verification used the same 7,806-row dataset included in the Phase 1 archive.", styles["body"]),
    ])
    qa_rows = [
        [p("Check", styles["table_header"]), p("Result", styles["table_header"]), p("Observed evidence", styles["table_header"])],
        [p("Unit tests", styles["table_body_bold"]), p("PASS", styles["table_body"]), p("4/4: summary, filters/search, mean imputation, required-column rejection", styles["table_body"])],
        [p("Full API", styles["table_body_bold"]), p("PASS", styles["table_body"]), p("7,806 recipes, 5 diet types, 4 chart datasets", styles["table_body"])],
        [p("Filter interaction", styles["table_body_bold"]), p("PASS", styles["table_body"]), p("Vegan + curry returned 42 recipes and 1 diet type", styles["table_body"])],
        [p("Clear interaction", styles["table_body_bold"]), p("PASS", styles["table_body"]), p("Restored 7,806 recipes and cleared both controls", styles["table_body"])],
        [p("Browser console", styles["table_body_bold"]), p("PASS", styles["table_body"]), p("No warning or error messages", styles["table_body"])],
        [p("Mobile layout", styles["table_body_bold"]), p("PASS", styles["table_body"]), p("375 px client and scroll widths; no horizontal overflow", styles["table_body"])],
        [p("Bicep compile", styles["table_body_bold"]), p("PASS", styles["table_body"]), p("Azure Bicep CLI 0.45.15 produced ARM JSON successfully", styles["table_body"])],
    ]
    qa_table = Table(qa_rows, colWidths=[1.4 * inch, 0.7 * inch, 4.48 * inch], repeatRows=1)
    qa_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), FOREST),
        ("BACKGROUND", (0, 1), (-1, -1), PAPER),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TEXTCOLOR", (1, 1), (1, -1), FOREST),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([
        qa_table,
        Spacer(1, 12),
        KeepTogether([
            scaled_image(ASSETS / "dashboard-mobile.png", 2.25 * inch, 3.25 * inch),
            p("Figure 4. Mobile-width verification. Controls stack without horizontal overflow.", styles["caption"]),
        ]),
        PageBreak(),
    ])

    story.extend([
        p("Challenges, decisions, and team contributions", styles["h1"]),
        p("Key implementation decisions", styles["h2"]),
        p("- <b>Phase 1 was not an HTTP Function:</b> the local Azurite processor was separated into reusable analysis and data-source modules, then exposed through a Python v2 HTTP trigger.", styles["bullet"]),
        p("- <b>The supplied UI was a static shell:</b> chart rendering, API calls, filters, error states, responsiveness, metadata, and accessibility were implemented from scratch while retaining its nutrition-dashboard intent.", styles["bullet"]),
        p("- <b>Cloud cost and complexity:</b> Flex Consumption and Static Web Apps Free were selected to minimize idle cost while preserving a current Azure architecture.", styles["bullet"]),
        p("- <b>Credential boundaries:</b> storage credentials remain server-side; the frontend receives only an API base URL and aggregated JSON.", styles["bullet"]),
        p("- <b>Dependency reliability:</b> canvas charts are native JavaScript, eliminating the Tailwind and chart CDN dependencies in the supplied mockup.", styles["bullet"]),
        p("Team contribution plan", styles["h2"]),
    ])
    team_rows = [
        [p("Team member", styles["table_header"]), p("Primary presentation ownership", styles["table_header"]), p("Recommended live-demo segment", styles["table_header"])],
        [p("Asad Arif", styles["table_body_bold"]), p("Project framing, architecture, deliverable coordination", styles["table_body"]), p("Open dashboard, explain KPIs and request flow", styles["table_body"])],
        [p("Can Ozveren", styles["table_body_bold"]), p("Function API, cleaning, Blob Storage configuration", styles["table_body"]), p("Show endpoint JSON, filters, and private blob", styles["table_body"])],
        [p("Muhammad Talha Arif", styles["table_body_bold"]), p("Frontend deployment, CI/CD, verification and cloud practices", styles["table_body"]), p("Show GitHub Actions, responsive view, and monitoring", styles["table_body"])],
    ]
    team_table = Table(team_rows, colWidths=[1.35 * inch, 2.58 * inch, 2.65 * inch], repeatRows=1)
    team_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), FOREST),
        ("BACKGROUND", (0, 1), (-1, -1), PAPER),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([
        team_table,
        p("Limitations", styles["h2"]),
        p("Cloud URLs, Azure Portal resource screenshots, and successful deployment-run screenshots cannot be produced without access to the team's Azure and GitHub accounts. The repository includes exact steps and a checklist for adding that evidence. Local screenshots in this report are deliberately labeled and must not be presented as Azure Portal proof.", styles["body"]),
        p("Conclusion", styles["h2"]),
        p("The Phase 2 implementation is complete at the code, infrastructure, testing, and documentation layers. It satisfies the dashboard, visualization, integration, cloud-practice, and presentation requirements. After the team performs the account-bound deployment steps, the project will provide the three final submission links: Function endpoint, Static Web App, and GitHub repository.", styles["body"]),
        PageBreak(),
    ])

    story.extend([
        p("Final deployment evidence and submission", styles["h1"]),
        p("Complete these account-bound fields after running <b>scripts/deploy_azure.ps1</b> and both GitHub deployment workflows.", styles["body"]),
    ])
    evidence_rows = [
        [p("Required deliverable", styles["table_header"]), p("Final value", styles["table_header"])],
        [p("Azure Function URL", styles["table_body_bold"]), p(function_url, styles["table_body"])],
        [p("Dashboard URL", styles["table_body_bold"]), p(dashboard_url, styles["table_body"])],
        [p("GitHub repository", styles["table_body_bold"]), p(github_url, styles["table_body"])],
    ]
    evidence_table = Table(evidence_rows, colWidths=[1.75 * inch, 4.83 * inch], repeatRows=1)
    evidence_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), FOREST),
        ("BACKGROUND", (0, 1), (-1, -1), PAPER),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
    ]))
    story.extend([
        evidence_table,
        p("Evidence screenshots to add", styles["h2"]),
        p("1. Resource group Overview listing Function App, Storage, Static Web App, and Application Insights.", styles["bullet"]),
        p("2. Storage browser showing <b>datasets/All_Diets.csv</b> without keys or connection strings.", styles["bullet"]),
        p("3. Public dashboard showing all chart cards and <b>Live Azure API connected</b>.", styles["bullet"]),
        p("4. Filtered public dashboard view demonstrating a changed result count.", styles["bullet"]),
        p("5. GitHub Actions page showing successful CI, Function, and frontend workflows.", styles["bullet"]),
        p("Submission order", styles["h2"]),
        p("- Confirm the Function endpoint returns HTTP 200 and four chart datasets.", styles["bullet"]),
        p("- Confirm the public dashboard has no browser console or network errors.", styles["bullet"]),
        p("- Confirm the GitHub repository contains no secrets and is accessible to the instructor.", styles["bullet"]),
        p("- Add the three URLs and any required portal screenshots to the final PDF.", styles["bullet"]),
        p("- Submit the PDF, links, and repository before the course deadline.", styles["bullet"]),
        Table([[p("SUBMISSION NOTE", styles["table_header"]), p("The project ZIP includes DEPLOYMENT_GUIDE.md and SUBMISSION_CHECKLIST.md with the exact team actions, secret names, verification steps, and troubleshooting guidance.", styles["callout"]) ]], colWidths=[1.25 * inch, 5.33 * inch], style=TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), FOREST_DARK),
            ("BACKGROUND", (1, 0), (1, 0), MINT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ])),
        p("Official references", styles["h2"]),
        p('1. <link href="https://learn.microsoft.com/en-nz/azure/azure-functions/functions-reference-python" color="#174f3b">Microsoft Learn - Azure Functions Python developer reference</link>', styles["ref"]),
        p('2. <link href="https://learn.microsoft.com/en-us/azure/azure-functions/functions-app-settings" color="#174f3b">Microsoft Learn - Azure Functions app settings reference</link>', styles["ref"]),
        p('3. <link href="https://learn.microsoft.com/en-us/azure/azure-functions/functions-create-first-function-bicep" color="#174f3b">Microsoft Learn - Create Flex Consumption resources with Bicep</link>', styles["ref"]),
        p('4. <link href="https://learn.microsoft.com/en-us/azure/azure-functions/functions-how-to-github-actions" color="#174f3b">Microsoft Learn - Azure Functions GitHub Actions deployment</link>', styles["ref"]),
        p('5. <link href="https://learn.microsoft.com/en-in/azure/static-web-apps/build-configuration" color="#174f3b">Microsoft Learn - Azure Static Web Apps build configuration</link>', styles["ref"]),
        p('6. <link href="https://learn.microsoft.com/en-us/azure/static-web-apps/configuration" color="#174f3b">Microsoft Learn - Configure Azure Static Web Apps</link>', styles["ref"]),
    ])

    optional_evidence = [
        ("resource-group.png", "Azure resource group Overview showing the provisioned Phase 2 services."),
        ("blob-container.png", "Private datasets container showing All_Diets.csv without credentials."),
        ("public-dashboard.png", "Public Azure Static Web App connected to the deployed Function API."),
        ("github-actions.png", "Successful validation, Function deployment, and frontend deployment workflows."),
    ]
    available_evidence = [(EVIDENCE / filename, caption) for filename, caption in optional_evidence if (EVIDENCE / filename).is_file()]
    if available_evidence:
        story.extend([PageBreak(), p("Azure deployment evidence", styles["h1"]), p("The following screenshots were added after the account-bound deployment steps were completed.", styles["body"])])
        for index, (image_path, caption) in enumerate(available_evidence, start=5):
            story.extend([
                KeepTogether([
                    scaled_image(image_path, 6.58 * inch, 4.25 * inch),
                    p(f"Figure {index}. {caption}", styles["caption"]),
                ]),
                Spacer(1, 8),
            ])

    doc.build(story, onFirstPage=cover_page, onLaterPages=later_page)
    print(f"Created {OUTPUT}")


if __name__ == "__main__":
    build()
