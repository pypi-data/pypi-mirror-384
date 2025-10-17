
# flake8: noqa

# Import all APIs into this package.
# If you have many APIs here with many many models used in each API this may
# raise a `RecursionError`.
# In order to avoid this, import only the API that you directly need like:
#
#   from eis.document.api.document_templates_api import DocumentTemplatesApi
#
# or import this package, but before doing it, use:
#
#   import sys
#   sys.setrecursionlimit(n)

# Import APIs into API package:
from eis.document.api.document_templates_api import DocumentTemplatesApi
from eis.document.api.documents_api import DocumentsApi
from eis.document.api.docx_templates_api import DocxTemplatesApi
from eis.document.api.layouts_api import LayoutsApi
from eis.document.api.product_documents_api import ProductDocumentsApi
from eis.document.api.search_keywords_api import SearchKeywordsApi
from eis.document.api.searchable_document_owners_api import SearchableDocumentOwnersApi
from eis.document.api.searchable_documents_api import SearchableDocumentsApi
from eis.document.api.default_api import DefaultApi
