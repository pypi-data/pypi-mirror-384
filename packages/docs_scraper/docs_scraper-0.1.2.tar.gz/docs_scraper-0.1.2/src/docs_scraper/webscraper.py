import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def scrape_all_links(base_url):
    try:
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        links = set()
        for tag in soup.find_all("a", href=True):
            full_url: str = urljoin(base_url, tag["href"])
            if full_url.startswith(base_url) and "#" not in full_url:
                links.add(full_url)

        return sorted(links)

    except requests.RequestException as e:
        print(e)
        return set()


if __name__ == "__main__":
    website = "https://python.langchain.com/docs/how_to/"
    sub_links = scrape_all_links(website)
    print(sub_links)
