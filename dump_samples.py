import pdfplumber
import os

def dump_samples():
    files = [
        "statements/moneyfarm/23_q4.pdf",
        "statements/interactive-investor/Statement 2024-12-31.pdf"
    ]
    for f in files:
        if os.path.exists(f):
            print(f"\n--- {f} ---")
            with pdfplumber.open(f) as pdf:
                text = pdf.pages[0].extract_text()
                print(text[:1000])

if __name__ == "__main__":
    dump_samples()

