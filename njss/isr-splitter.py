import os
import json
import pathlib
import re

from dotenv import load_dotenv
from PyPDF2 import PdfFileWriter, PdfFileReader

load_dotenv()

input_dir = os.getenv("INPUT_DIR")
student_file = os.getenv("STUDENT_FILE")

regex_pattern = "LocalStudentIdentification:(?P<LocalStudentIdentification>\d+)"

with open(student_file) as f:
    student_lookup = json.load(f)

input_path = pathlib.Path(input_dir)
processed_path = input_path / "processed"

input_pdfs = [f for f in input_path.glob("*.pdf")]

if not processed_path.exists():
    processed_path.mkdir(parents=True)

for pdf in sorted(input_pdfs):
    print(pdf.stem)
    pdf_in = PdfFileReader(open(pdf, "rb"))

    for p in range(pdf_in.numPages - 1):
        if p % 2 == 0:
            page = pdf_in.getPage(p)
            page_text = page.extractText()

            regex_match = re.search(regex_pattern, page_text)
            if regex_match:
                regex_group = regex_match.groupdict()
            else:
                regex_group = {}
            student_number = int(regex_group.get("LocalStudentIdentification", "0"))

            student_match = next(
                iter(
                    [s for s in student_lookup if s["student_number"] == student_number]
                ),
                {
                    "student_number": p,
                    "abbreviation": "UNMATCHED",
                },
            )

            student_file_name = f"{student_match['abbreviation']}_{student_match['student_number']}_{pdf.name}"
            student_file_path = (
                input_path / "out" / student_match["abbreviation"] / student_file_name
            )

            if not student_file_path.exists():
                if not student_file_path.parent.exists():
                    print(f"\tCreating {student_file_path.parent}...")
                    student_file_path.parent.mkdir(parents=True)

                pdf_out = PdfFileWriter()
                pdf_out.addPage(pdf_in.getPage(p))
                pdf_out.addPage(pdf_in.getPage(p + 1))

                print(f"\t{student_file_name}")
                with student_file_path.open("wb+") as f:
                    pdf_out.write(f)

    pdf.rename(pdf.parent / "processed" / pdf.name)
    print(f"Moved to ./processed/{pdf.name}")
