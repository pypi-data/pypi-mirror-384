# url_checker_lib

A simple Python library to check the safety of URLs using NordVPN's public URL checker API.

## Installation

```bash
pip install url_checker_lib
```

## Usage

```python
from url_checker_JACK.checker import check_url

url_to = "https://example.com"
verdict = check_url(url_to)
print(f"The URL {url_to} is: {verdict}")
```

