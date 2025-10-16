import os
import json
import google.generativeai as genai
from .token_fetcher import TokenFetcher
from .utils import pretty_print_json


class EPFOScrapper:
    def __init__(self, api_key: str = None):
        if api_key is None:
            token_fetcher = TokenFetcher()
            api_key = token_fetcher.fetch()
        self.api_key = api_key

    def extract_from_pdf(self, pdf_path: str) -> list:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"The file was not found: {pdf_path}")

        if not self.api_key:
            raise ValueError("API key is missing.")

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(model_name="gemini-flash-latest")

        prompt = """
        From the provided PDF document, extract the employment history details.
        For each distinct company listed, create a JSON object with the following keys: "uan_num", "name", "company", "doj", "doe", and "member_id".
        Combine all these JSON objects into a single JSON array.
        Date should be in the format "dd/mm/yyyy".
        NOT AVAILABLE should be as NOT_AVAILABLE.
        The UAN and Name will be the same for all entries in the document.
        Provide only the raw JSON array in your response, no additional text or formatting.
        """

        pdf_file_data = {
            'mime_type': 'application/pdf',
            'data': open(pdf_path, 'rb').read()
        }

        response = model.generate_content([prompt, pdf_file_data])
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            raise ValueError("Failed to parse JSON from Gemini response.")


if __name__ == "__main__":
    pdf_path = "epfo.pdf"
    scrapper = EPFOScrapper()
    data = scrapper.extract_from_pdf(pdf_path)
    pretty_print_json(data)
