import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter
import io
import sys

# ==========================================
# ⚙️ CONFIGURATION & CALIBRATION PANEL
# ==========================================
EXCEL_FILE = "students.xlsx"
TEMPLATE_PDF = "ZipGrade_AnswerSheet.pdf"
OUTPUT_PDF = "ALL_STUDENTS_ZIPGRADE.pdf"

# The precise coordinates derived from your clicks
START_X = 154.5
START_Y = 645.5
COL_SPACING = 15.45
ROW_SPACING = 17.4
BUBBLE_RADIUS = 4.5  # Slightly reduced to prevent overflowing the circle


# ==========================================

def clean_student_id(raw_id):
    """Safely cleans the ID, preserving leading zeros and stripping pandas' floats."""
    if pd.isna(raw_id) or raw_id == "":
        return "000000000"

    id_str = str(raw_id).strip()

    if id_str.endswith('.0'):
        id_str = id_str[:-2]

    return id_str.zfill(9)


def create_overlay(fullname, class_text, student_id):
    """Generates a single transparent PDF page with the text and bubbles."""
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica", 12)

    # 1. Draw Header Text
    # (Kept these around X:149 / Y:696 based on the grid position)
    can.drawString(149, 696, str(fullname))
    can.drawString(330, 696, str(class_text))

    # 2. Draw ID Bubbles
    id_str = clean_student_id(student_id)

    for col, digit in enumerate(id_str):
        if not digit.isdigit():
            continue

        row = int(digit)

        # The Math: Move Right for columns, Move Down (subtract) for rows
        x = START_X + (col * COL_SPACING)
        y = START_Y - (row * ROW_SPACING)

        # fill=1 makes the circle solid black
        can.circle(x, y, BUBBLE_RADIUS, fill=1)

    can.save()
    packet.seek(0)
    return PdfReader(packet)


def main():
    print(f"Reading data from {EXCEL_FILE}...")
    try:
        df = pd.read_excel(EXCEL_FILE)
        df = df.fillna("")
    except FileNotFoundError:
        print(f"❌ Error: Could not find {EXCEL_FILE}")
        sys.exit(1)

    writer = PdfWriter()
    total_students = len(df)

    print(f"Processing {total_students} students...")

    for index, row in df.iterrows():
        try:
            reader = PdfReader(TEMPLATE_PDF)
            page = reader.pages[0]

            fullname = f"{row.get('surname', '')} {row.get('name', '')}".strip()

            c = str(row.get('class', '')).strip()
            s = str(row.get('section', '')).strip()
            ct = str(row.get('class_type', '')).strip()

            class_parts = f"{c} {s}".strip()
            class_text = f"{class_parts} | {ct}" if ct and class_parts else (ct or class_parts)

            overlay = create_overlay(fullname, class_text, row.get("id"))
            page.merge_page(overlay.pages[0])
            writer.add_page(page)

        except Exception as e:
            print(f"⚠️ Warning: Skipped row {index} due to error: {e}")

    with open(OUTPUT_PDF, "wb") as f:
        writer.write(f)

    print(f"✅ Success! Generated {OUTPUT_PDF}")


if __name__ == "__main__":
    main()