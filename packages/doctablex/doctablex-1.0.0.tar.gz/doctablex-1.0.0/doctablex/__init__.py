"""
doctablex
=========
A lightweight tool for extracting and cleaning tables from Word (.docx) files.

Example:
--------
>>> from doctablex import extract_tables
>>> tables = extract_tables("statement.docx")
>>> for t in tables:
...     print(t.head())

Note:
-----
PDFs are not yet supported directly. Convert them to DOCX using ilovepdf.com/pdf_to_word first.
"""

from .extractor import extract_tables
