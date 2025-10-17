from pathlib import Path
from docling.document_converter import DocumentConverter

try:
    from docs_scraper.webscraper import scrape_all_links
except ModuleNotFoundError:
    from webscraper import scrape_all_links


def markdown_converter(source, filename):
    all_links: set = scrape_all_links(source)

    path: Path = Path(f"docs/{filename}/")
    path.mkdir(parents=True, exist_ok=True)

    text: str = ""

    for i, link in enumerate(all_links):
        converter = DocumentConverter()
        result = converter.convert(link)
        print(f"{i}.{link}")
        text = text + f"# {result.document.name}\n\n" + result.document.export_to_markdown() + "\n---\n"

    with open(str(path) + f"/{filename}.md", "w+") as file:
        file.write(text)


if __name__ == "__main__":
    source = "https://docs.astral.sh/uv/"
    filename_path = "astral_uv"
    markdown_converter(source, filename_path)
