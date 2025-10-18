# URL Checker Library

مكتبة Python بسيطة للتحقق من أمان عناوين URL باستخدام واجهة برمجة تطبيقات التحقق

## Installation

```bash
pip install url-checker-library
```

## Usage

```python
from url_checker_library.checker import check_url_status

url = "https://malicious-site.com"
status = check_url_status(url)
print(f"The URL {url} is: {status}")
```

## Development

