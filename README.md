# 🌐 Global Web Scraper

A general-purpose Python web scraper that extracts data from any website while respecting the `robots.txt` exclusion standard.

## 🚀 Features

- **Robots.txt Compliant**: Automatically checks the target website's `robots.txt` to ensure scraping is allowed.
- **Generic Extraction**: Captures titles, meta descriptions, headings, paragraphs, and links.
- **JSON Export**: Saves extracted data to structured JSON files in the `scrapped-data/` directory.
- **Configurable**: Customizable User-Agent via `.env`.
- **Pure Python**: Built with functional programming patterns (no Classes/OOP).

## 🛠️ Setup

1.  **Clone the repository** (if you haven't already).
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure Environment**:
    Rename `.env.example` to `.env` (optional, to set a custom User-Agent).
    ```bash
    cp .env.example .env
    ```

## 💻 Usage

Run the `main.py` script:

```bash
python main.py
```

1.  Enter the URL you want to scrape (e.g., `https://example.com`).
2.  The script will:
    *   Check `robots.txt` permissions.
    *   Fetch the HTML.
    *   Parse the content.
    *   Save the result to `scrapped-data/<domain>_data.json`.

## 📁 Output Structure

The output JSON contains:
- `url`: Source URL.
- `title`: Page title.
- `meta_description`: Meta description tag content.
- `headings`: List of h1-h3 tags.
- `content_snippet`: First few paragraphs.
- `links`: First 20 links found on the page.

## ⚠️ Disclaimer

This tool is for educational purposes. Always respect website terms of service and robots.txt rules (which this tool attempts to do automatically).