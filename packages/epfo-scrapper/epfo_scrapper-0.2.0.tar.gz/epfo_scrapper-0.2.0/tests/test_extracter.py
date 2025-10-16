from epfo_scrapper import EPFOScrapper, pretty_print_json

def test_extract():
    pdf_path = "epfo.pdf"
    scrapper = EPFOScrapper()
    data = scrapper.extract_from_pdf(pdf_path)
    assert isinstance(data, list), "Output should be a list"
    pretty_print_json(data)
    return data

if __name__ == "__main__":
    test_extract()
