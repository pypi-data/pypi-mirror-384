# PDFix SDK Package

## PDFix SDK - High Performace PDF library

`keywords: pdf, accessibility, remediation, extraction, html, conversion, render, watermark, redact, sign, forms`

PDFix SDK analyses the key components of the PDF and makes it easily available for you to manipulate. It’s a high-performance library that helps software developers and end-users integrate PDF functionality into their workflows.

## Features
- Automated PDF Tagging and Remediation (PDF/UA)
- Automated Data Extraction (JSON, XML)
- PDF to HTML Conversion (Original, Responsive, by Tags)
- Standard PDF Editing Features (render, watermark, redact, sign, forms, and more)

## Change log
[https://github.com/pdfix/pdfix_sdk_builds/blob/main/changelog.md](https://github.com/pdfix/pdfix_sdk_builds/blob/main/changelog.md)

## Supported platforms
- Linux amd64, aarch64
- Windows amd64
- macOS amd64, arm64

## Installation 
```
pip install pdfix-sdk
```

## Example

```
from pdfixsdk.Pdfix import *

pdfix = GetPdfix()
doc = pdfix.OpenDoc("path/to/your.pdf", "")
print(doc.GetNumPages())
doc.Close()
```

More Python examples on [https://github.com/pdfix/pdfix_sdk_example_python](https://github.com/pdfix/pdfix_sdk_example_python)

