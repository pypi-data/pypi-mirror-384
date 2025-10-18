# Any document Extractor

A Python library for extracting text content from any document format.

## Features

- Supports multiple document formats (PPTX, DOCX, PDF, XLSX.)
- Returns clean extracted text

## Installation

```bash
pip install any-document-extractor
````



## Usage
Basic usage example:

```python

from anydocumentextractor import DocumentExtractor


def main(fp: str):
    extra = DocumentExtractor(fp)
    return extra.extract()


if __name__ == '__main__':
    fp = 'text.docx'  # Can be any supported document
    content = main(fp)
    print(content)

```

## Supported Formats
- Microsoft Office: PPTX, DOCX, XLSX
- OpenDocument: ODT, ODP
- PDF documents
- Plain text files
- And more...

## License
MIT License - Free for commercial and personal use.

You can customize this further by adding:
- More detailed installation instructions
- Specific version requirements
- Advanced usage examples
- Error handling documentation
- Contribution guidelines
- Project status badges

