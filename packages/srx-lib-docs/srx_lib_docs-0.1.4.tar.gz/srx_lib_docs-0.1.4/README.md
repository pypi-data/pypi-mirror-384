# srx-lib-docs

Small helpers to extract plain text from common office document formats used by SRX services.

What it includes:
- `extract_text(path_or_bytes, mime_type=None)` supports PDF, DOCX, PPTX, XLSX

## Install

PyPI (public):
- `pip install srx-lib-docs`

uv (pyproject):
```
[project]
dependencies = ["srx-lib-docs>=0.1.0"]
```

## Usage

```
from srx_lib_docs import extract_text
text = extract_text("/path/to/file.pdf")
```

## Notes

- For XLSX, the first 20 rows of each sheet are read to keep it lightweight; adjust in code if needed.

## License

Proprietary © SRX
