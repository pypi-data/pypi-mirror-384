import argparse

try:
    from docs_scraper.markdown_converter import markdown_converter
except ModuleNotFoundError:
    from markdown_converter import markdown_converter


def main():
    parser = argparse.ArgumentParser(prog="")

    parser.add_argument("--url", default="https://docs.astral.sh/uv/")
    parser.add_argument("--path", default="astral_uv")

    arguments = parser.parse_args()

    markdown_converter(arguments.url, arguments.path)


if __name__ == "__main__":
    main()
