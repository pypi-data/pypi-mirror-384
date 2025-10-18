# mediawiki-to-pdf 

## session
**MediaWikiSession(access_token: str, apiurl: str)** returns a requests.Session subclass that adds Mediawik authorization headers.
apiurl is typically https://example.com/api.php
*MediaWikiSession.parse_yaml(file)* is convenience method that reads access token and url from YAML file:
```
mediawiki:
  url: https://wiki.example.com/api.php
  access token: /usr/local/x/wiki_token
```
where access token is a file name.

## PDF
**save_pdf_from_authenticated_session(session: MediaWikiSession, page_title: str, output_path: str)->Path:**
Fetchs a MediaWiki page via API and convert it to PDF using pdfkit. Returns output.
/usr/bin/wkhtmlpdf must be installed.

## Command line
Processes list of pages specified in YAML file.
```
usage: mediawiki_to_pdf [-h] [-l LOGLEVEL] yaml

positional arguments:
  yaml                  Configuration file

options:
  -h, --help            show this help message and exit
  -l LOGLEVEL, --loglevel LOGLEVEL
                        Python logging level (default: WARN)
```
Example:
```
---
mediawiki:
  url: https://wiki.example.com/api.php
  access token: /usr/local/x/wiki_token
pages:
  -  First_page 
  -  Second_page 
...
```
