"""
HWELBEING — CLINICAL DATA SEEDER (HUMAN-READABLE PRESCRIPTION)

Purpose:
- Parse Disease.txt
- Convert into layman-readable prescriptions
- Store structured + readable instructions

Output Example:
Ciprofloxacin → 1 tablet morning, 1 tablet night (after food) for 14 days
"""

import asyncio
import re
from pathlib import Path

from src.db.core import execute_many, fetch_one
from src.core.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_FILE = BASE_DIR / "data" / "Disease.txt"


# =========================================================
# HELPERS
# =========================================================

def parse_dose(text):
    """
    Extract 1+0+1 → (1,0,1)
    """
    try:
        text = text.replace("and half", ".5")
        match = re.search(r"(\d+\.?\d*)\+(\d+\.?\d*)\+(\d+\.?\d*)", text)
        if not match:
            return None, None, None

        return float(match.group(1)), float(match.group(2)), float(match.group(3))
    except Exception:
        return None, None, None


def extract_duration(text):
    days = None
    months = None

    d = re.search(r"(\d+)\s*day", text.lower())
    if d:
        days = int(d.group(1))

    m = re.search(r"(\d+)\s*month", text.lower())
    if m:
        months = int(m.group(1))

    return days, months


def detect_food_instruction(text):
    t = text.lower()

    if "before meal" in t or "before food" in t:
        return "Before food"
    if "after meal" in t or "after food" in t:
        return "After food"
    if "empty stomach" in t:
        return "Empty stomach"

    return None


def detect_formulation(line):
    l = line.lower()

    if "tab" in l:
        return "tablet"
    if "cap" in l:
        return "capsule"
    if "inhaler" in l:
        return "inhaler"
    if "cream" in l:
        return "cream"
    if "iv" in l or "injection" in l:
        return "injection"

    return "medicine"


def extract_name(line):
    line = re.sub(r"\(.*?\)", "", line)
    line = re.sub(r"(tab|cap|inj|cream|inhaler)\.?", "", line, flags=re.I)
    line = re.sub(r"\d+.*", "", line)
    return line.strip().title()


def build_instruction(name, form, m, a, e, food, days, months):
    """
    Convert to human readable prescription
    """

    timing = []

    if m:
        timing.append(f"{int(m)} {form} morning")
    if a:
        timing.append(f"{int(a)} {form} afternoon")
    if e:
        timing.append(f"{int(e)} {form} night")

    if not timing:
        timing.append("Use as directed by doctor")

    instruction = ", ".join(timing)

    if food:
        instruction += f" ({food})"

    if days:
        instruction += f" for {days} days"
    elif months:
        instruction += f" for {months} months"

    return instruction


def is_dose_line(line):
    return bool(re.search(r"\d+\s*\+\s*\d+\s*\+\s*\d+", line))


def is_medicine_line(line):
    if is_dose_line(line):
        return False
    return bool(re.search(r"[A-Za-z]{3,}", line))


# =========================================================
# MAIN
# =========================================================

async def seed_data():

    if not DATA_FILE.exists():
        raise FileNotFoundError("Disease.txt missing")

    count = await fetch_one("SELECT COUNT(*) FROM HWELLBEING.DISEASES")
    if count and count[0] > 0:
        logger.info("Seed skipped (already exists)")
        return

    content = DATA_FILE.read_text(encoding="utf-8")

    blocks = re.split(r"(?i)Treatment of ", content)[1:]

    disease_rows = []
    med_rows = []
    regimen_rows = []
    regimen_line_rows = []

    med_map = {}
    med_id = 1
    disease_id = 1
    regimen_id = 1
    line_id = 1

    for block in blocks:

        disease_name = block.split("\n")[0].strip().title()
        if not disease_name:
            continue

        disease_rows.append((disease_id, disease_name, "", f"ICD-{disease_id}"))
        regimen_rows.append((regimen_id, disease_id, f"{disease_name} Regimen"))

        lines = block.split("\n")[1:]

        current_med = None
        current_form = None
        order = 1

        for raw_line in lines:
            line = raw_line.strip()

            if not line:
                continue

            # ---------------- MEDICINE ----------------
            if is_medicine_line(line):
                med_name = extract_name(line)
                current_form = detect_formulation(line)

                if med_name not in med_map:
                    med_map[med_name] = med_id
                    med_rows.append((med_id, med_name, None, None))
                    med_id += 1

                current_med = med_map[med_name]
                continue

            # ---------------- DOSE ----------------
            if is_dose_line(line) and current_med:
                m, a, e = parse_dose(line)
                days, months = extract_duration(line)
                food = detect_food_instruction(line)

                instruction = build_instruction(
                    med_name,
                    current_form,
                    m, a, e,
                    food,
                    days,
                    months
                )

                regimen_line_rows.append((
                    line_id,
                    regimen_id,
                    current_med,
                    m, a, e,
                    "DAILY",
                    days, months,
                    food,
                    instruction,
                    order
                ))

                line_id += 1
                order += 1
                continue

        disease_id += 1
        regimen_id += 1

    # ================= INSERT =================

    await execute_many("""
        INSERT INTO HWELLBEING.DISEASES
        (ID, NAME, DESCRIPTION, ICD_CODE)
        VALUES (?, ?, ?, ?)
    """, disease_rows)

    await execute_many("""
        INSERT INTO HWELLBEING.MEDICATIONS
        (ID, NAME, DOSAGE, CONTRAINDICATIONS)
        VALUES (?, ?, ?, ?)
    """, med_rows)

    await execute_many("""
        INSERT INTO HWELLBEING.TREATMENT_REGIMENS
        (ID, DISEASE_ID, NAME)
        VALUES (?, ?, ?)
    """, regimen_rows)

    await execute_many("""
        INSERT INTO HWELLBEING.REGIMEN_LINES
        (ID, REGIMEN_ID, MEDICATION_ID,
         MORNING_DOSE, AFTERNOON_DOSE, EVENING_DOSE,
         FREQUENCY,
         DURATION_DAYS, DURATION_MONTHS,
         FOOD_INSTRUCTION,
         SPECIAL_INSTRUCTION,
         LINE_ORDER)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, regimen_line_rows)

    logger.info("Seeding completed successfully")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    from src.db.connection import init_pool, close_pool

    async def run():
        await init_pool()
        try:
            await seed_data()
        finally:
            await close_pool()

    asyncio.run(run())