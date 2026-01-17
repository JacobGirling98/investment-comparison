import pdfplumber
with pdfplumber.open("statements/interactive-investor/Statement 2024-12-31.pdf") as pdf:
    for page in pdf.pages:
        print(page.extract_text())
