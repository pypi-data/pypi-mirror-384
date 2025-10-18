import sys
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter


def split_pdf(input_path: Path):
    if not input_path.exists() or input_path.suffix.lower() != ".pdf":
        print(f"Error: {input_path} does not exist or is not a pdf.", file=sys.stderr)
        sys.exit(1)

    output_dir = input_path.parent / input_path.stem
    output_dir.mkdir(exist_ok=True)

    reader = PdfReader(input_path)
    num_pages = len(reader.pages)

    print(f"{num_pages} pages save to: {output_dir}")

    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)

        output_file = output_dir / f"page_{i:03d}.pdf"
        with open(output_file, "wb") as f:
            writer.write(f)
        print(f"  → {output_file.name}")

    print("Done")


def main():
    if len(sys.argv) != 2:
        print("Usage: python split_pdf.py /path/to/document.pdf", file=sys.stderr)
        sys.exit(1)

    input_file = Path(sys.argv[1]).resolve()
    split_pdf(input_file)


if __name__ == "__main__":
    main()
