from setuptools import setup

setup(
    name='any-document-extractor',
    version='0.1.2',
    packages=['anydocumentextractor'],
    url='',
    license='',
    author='yeqing',
    description="A Python library for extracting text content from any document format.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author_email='215777@qq.com',
    python_requires=">=3.9",
    install_requires=[
        "python-docx",
        "python-multipart",
        "openpyxl",
        "pdfminer.six",
        "camelot-py",
        "python-pptx",
    ],
)
