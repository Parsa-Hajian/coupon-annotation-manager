"""Generate a PowerPoint presentation about the Coupon Annotation Manager project."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor

# Brand colors
DARK_BLUE = RGBColor(0x1A, 0x3C, 0x6E)
ACCENT_BLUE = RGBColor(0x2E, 0x75, 0xB6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xF2, 0xF2, 0xF2)
DARK_GRAY = RGBColor(0x33, 0x33, 0x33)
GREEN = RGBColor(0x27, 0xAE, 0x60)
ORANGE = RGBColor(0xE6, 0x7E, 0x22)


def add_title_slide(prs, title, subtitle=""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank
    # Background
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = DARK_BLUE

    # Title
    txBox = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(1.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER

    if subtitle:
        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(18)
        p2.font.color.rgb = RGBColor(0xBB, 0xDE, 0xFB)
        p2.alignment = PP_ALIGN.CENTER
        p2.space_before = Pt(12)


def add_content_slide(prs, title, bullets, sub_bullets=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank

    # Title bar
    shape = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(1.2))  # Rectangle
    shape.fill.solid()
    shape.fill.fore_color.rgb = DARK_BLUE
    shape.line.fill.background()

    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(9), Inches(0.8))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = WHITE

    # Bullets
    txBox2 = slide.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(8.5), Inches(5))
    tf2 = txBox2.text_frame
    tf2.word_wrap = True

    for i, bullet in enumerate(bullets):
        if i == 0:
            p = tf2.paragraphs[0]
        else:
            p = tf2.add_paragraph()
        p.text = bullet
        p.font.size = Pt(18)
        p.font.color.rgb = DARK_GRAY
        p.space_before = Pt(10)
        p.level = 0

        # Add sub-bullets if provided
        if sub_bullets and i in sub_bullets:
            for sb in sub_bullets[i]:
                sp = tf2.add_paragraph()
                sp.text = sb
                sp.font.size = Pt(15)
                sp.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
                sp.space_before = Pt(4)
                sp.level = 1


def add_two_column_slide(prs, title, left_title, left_items, right_title, right_items):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Title bar
    shape = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(1.2))
    shape.fill.solid()
    shape.fill.fore_color.rgb = DARK_BLUE
    shape.line.fill.background()

    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(9), Inches(0.8))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = WHITE

    # Left column
    left_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(4.2), Inches(5))
    ltf = left_box.text_frame
    ltf.word_wrap = True
    lp = ltf.paragraphs[0]
    lp.text = left_title
    lp.font.size = Pt(20)
    lp.font.bold = True
    lp.font.color.rgb = ACCENT_BLUE

    for item in left_items:
        p = ltf.add_paragraph()
        p.text = item
        p.font.size = Pt(15)
        p.font.color.rgb = DARK_GRAY
        p.space_before = Pt(8)

    # Right column
    right_box = slide.shapes.add_textbox(Inches(5.3), Inches(1.5), Inches(4.2), Inches(5))
    rtf = right_box.text_frame
    rtf.word_wrap = True
    rp = rtf.paragraphs[0]
    rp.text = right_title
    rp.font.size = Pt(20)
    rp.font.bold = True
    rp.font.color.rgb = ACCENT_BLUE

    for item in right_items:
        p = rtf.add_paragraph()
        p.text = item
        p.font.size = Pt(15)
        p.font.color.rgb = DARK_GRAY
        p.space_before = Pt(8)


def main():
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # Slide 1: Title
    add_title_slide(
        prs,
        "Coupon Annotation Manager",
        "Structured Data Enrichment for UniversityBox Coupons"
    )

    # Slide 2: The Problem
    add_content_slide(prs, "The Problem", [
        "Coupon data in our CRM lacks structured product & discount information",
        "No standardized categorization of products across coupons",
        "Discount structures vary widely and are stored as free text",
        "No visibility tracking for coupon positioning on the website",
        "Difficult to analyze coupon performance without structured data",
    ])

    # Slide 3: The Solution
    add_content_slide(prs, "Our Solution", [
        "A web-based annotation tool that enriches coupon data",
        "Operators browse coupons and add structured annotations:",
    ], sub_bullets={
        1: [
            "Product categories (3-level hierarchy: Macro > Sub > Micro)",
            "Discount structures (type, modifier, values)",
            "Visibility/positioning data (High, Medium, Low)",
        ]
    })

    # Slide 4: Key Features
    add_two_column_slide(
        prs, "Key Features",
        "Data Annotation",
        [
            "Browse & search all coupons from CRM",
            "Product-by-product annotation form",
            "Each product has its own discount blocks",
            "11 macro categories, 60+ sub-categories",
            "Automatic brand category suggestions",
            "Edit or delete existing annotations",
        ],
        "Tracking & Export",
        [
            "Visibility tracking (High/Medium/Low)",
            "Manual + automated visibility scheduling",
            "Activation/deactivation history",
            "One-click Excel export",
            "Activity log for all operators",
            "Notification badge for unprocessed coupons",
        ]
    )

    # Slide 5: How It Works
    add_content_slide(prs, "How It Works", [
        "1. Operator opens the app and sees unprocessed coupons",
        "2. Selects a coupon from the browser (click-to-select)",
        "3. Views coupon details from CRM (name, brand, dates, status)",
        "4. Fills in product data: name, category hierarchy",
        "5. Adds discount blocks for each product",
        "6. Sets visibility positioning (manual or scheduled)",
        "7. Saves annotation — data is stored and ready for export",
        "8. Excel export generates a structured, wide-format spreadsheet",
    ])

    # Slide 6: Technical Architecture
    add_two_column_slide(
        prs, "Technical Architecture",
        "Data Sources",
        [
            "Google BigQuery: CRM coupon & brand data",
            "SQLite: Annotation storage",
            "Cached queries for fast performance",
            "Status change tracking (auto-sync)",
        ],
        "Application",
        [
            "Streamlit web framework",
            "Deployed on Streamlit Cloud",
            "Accessible from any browser",
            "No installation needed for operators",
            "Secure via Google service account",
        ]
    )

    # Slide 7: Value & Impact
    add_content_slide(prs, "Value & Impact", [
        "Structured data enables better coupon analysis & reporting",
        "Standardized product categorization across all coupons",
        "Visibility tracking provides insight into coupon positioning",
        "Excel exports feed into business intelligence workflows",
        "Operator activity logs ensure accountability",
        "Reduces manual effort compared to spreadsheet-based annotation",
    ])

    # Slide 8: Current Limitations
    add_content_slide(prs, "Current Limitations & Effort", [
        "Annotation is currently a manual process",
        "Each coupon must be individually processed by an operator",
        "Data is stored locally (SQLite) — resets on cloud reboot",
        "Excel export serves as the persistent record",
        "No direct integration with the website backend yet",
    ])

    # Slide 9: Next Phase — Backend Integration
    add_content_slide(prs, "Next Phase: Backend Integration", [
        "Phase 2A: Retrieve visibility data from the platform backend",
    ], sub_bullets={
        0: [
            "Connect to the website's API to read current coupon positions",
            "Auto-populate visibility field from live data",
            "Track position changes in real-time, not just manually",
        ]
    })

    add_content_slide(prs, "Next Phase: Backend Integration (cont.)", [
        "Phase 2B: Integrate annotation tool into the website backend",
    ], sub_bullets={
        0: [
            "Embed the annotation workflow where coupons are uploaded",
            "Operators annotate coupons as part of the upload process",
            "Eliminate the need for a separate tool",
            "Direct database storage instead of local SQLite + Excel",
        ]
    })

    # Slide 11: Roadmap
    add_content_slide(prs, "Roadmap", [
        "Phase 1 (Current): Standalone annotation tool with Excel export",
        "Phase 2: Backend API integration for visibility data",
        "Phase 3: Embed into coupon upload workflow",
        "Phase 4: Automated categorization using AI/ML",
    ], sub_bullets={
        3: [
            "Train a model on existing annotations to suggest categories",
            "Reduce manual effort to validation rather than data entry",
        ]
    })

    # Slide 12: Thank You
    add_title_slide(
        prs,
        "Thank You",
        "Questions?"
    )

    output_path = "/Users/parsahajiannejad/desktop/universitybox/Coupon Form/Coupon_Annotation_Manager_Presentation.pptx"
    prs.save(output_path)
    print(f"Presentation saved to: {output_path}")


if __name__ == "__main__":
    main()
