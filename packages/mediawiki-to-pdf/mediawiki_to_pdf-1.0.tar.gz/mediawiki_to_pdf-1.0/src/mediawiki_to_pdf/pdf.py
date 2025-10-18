import tempfile
from pathlib import Path

import pdfkit
from mediawiki_session import MediaWikiSession


def save_pdf_from_authenticated_session(session: MediaWikiSession, page_title: str, output_path: str)->Path:
    """
    Fetch a MediaWiki page via API and convert it to PDF using pdfkit. Return output.
    """
    # Here’s what each of those MediaWiki API query parameters does:
    #  action=parse
    #  Tells the API you want to parse page content. Instead of returning the raw wikitext, it processes it (resolving templates, formatting, etc.) into HTML or other specified formats.
    # prop=text
    #  Specifies which part(s) of the parsed output you want returned.
    #  text means: return the rendered HTML of the page (or section) after parsing.
    # format=json
    #  Sets the output format to JSON.
    #  Without this, the default output format might be XML; JSON is more convenient for most applications.
    response = session.get(
        f"{session.apiurl}?action=parse&prop=text&format=json&page={page_title}"
    )
    response.raise_for_status()
    html = response.json()["parse"]["text"]["*"]  # Full rendered HTML body

    # Wrap in basic HTML structure so wkhtmltopdf doesn’t choke
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{page_title}</title>
    </head>
    <body>
        {html}
    </body>
    </html>
    """

    # Save to temp file and convert to PDF
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tmp_html:
        tmp_html.write(full_html)
        tmp_html.flush()
        pdfkit.from_file(tmp_html.name, output_path)
    if (rval := Path(output_path)).is_file():
        return rval
    raise RuntimeError(f"pdkfit did not generate {rval.as_posix()} from {tmp_html.name}")
