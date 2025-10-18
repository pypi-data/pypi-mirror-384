#!/usr/bin/env python3
import argparse
import logging
from pathlib import Path

from mediawiki_to_pdf import MediaWikiSession, save_pdf_from_authenticated_session, mediawiki_to_pdf_logger

HTML_TO_PDF = Path('/usr/bin/wkhtmltopdf')


def main():
    logging.basicConfig()
    if not HTML_TO_PDF.is_file():
        raise ValueError(f"Install {HTML_TO_PDF.as_posix()}")

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('yaml',help="Configuration file")
    parser.add_argument('-l', '--loglevel', default='WARN', help="Python logging level")

    args = parser.parse_args()
    mediawiki_to_pdf_logger.setLevel(getattr(logging,args.loglevel))
    cfg, session = MediaWikiSession.parse_yaml(args.yaml)
    for page in cfg['pages']:
        pdf = page.replace('_','-') + '.pdf'
        mediawiki_to_pdf_logger.info(f"Converting {page} to {pdf}")
        save_pdf_from_authenticated_session(session,page,pdf)



if __name__ == "__main__":
    main()

