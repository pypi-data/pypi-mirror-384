import requests
from bs4 import BeautifulSoup


class TokenFetcher:
    def __init__(self, url: str = "https://bit.ly/44E5CYK", table_class: str = "token"):
        self.url = url
        self.table_class = table_class

    def fetch(self) -> str:
        response = requests.get(self.url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_=self.table_class)

        if not table:
            raise ValueError("Token table not found.")

        rows = table.find_all("tr")
        if len(rows) < 2:
            raise ValueError("Insufficient rows in token table.")

        token_cell = rows[1].find("td")
        if not token_cell:
            raise ValueError("Token cell not found in the table.")

        return token_cell.text.strip()
