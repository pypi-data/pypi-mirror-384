
import importlib.metadata 
import logging


mediawiki_to_pdf_logger = logging.getLogger(__name__)

__version__ =  importlib.metadata.version('mediawiki-to-pdf')
from mediawiki_to_pdf.wsession import MediaWikiSession
from mediawiki_to_pdf.pdf import save_pdf_from_authenticated_session

