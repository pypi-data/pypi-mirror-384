"""Test data constants for Google Datasource tests"""

GOOGLE_DOC_URL = "https://docs.google.com/document/d/19EXgnFCgJontz0ToCAH6zMGwBTdhi5X97P9JIby4wHs/edit?tab=t.0#heading=h.b01c2ig0adfg"
GOOGLE_GUIDE_URL = (
    "https://docs.google.com/document/d/1ZNWwxN8ukpJZyTbYjWQPym3Bc1-bQvBxBpTL0yfVF-w"
)

USER_PROMPT = 'Tell context of the What is "Platform A"? section?'

RESPONSE_FOR_GOOGLE_DOC = """
    The context for the "What is 'Platform A'?" section is as follows:
    - The heading for the title must be at level 3.
    - The title number must follow the format (x.x.x.).
    - The section content is just a paragraph.
"""
