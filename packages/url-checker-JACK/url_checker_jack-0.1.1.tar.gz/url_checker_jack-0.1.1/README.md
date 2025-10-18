# URL Checker Library

A simple Python library to check the safety of URLs using .

## Installation

```bash
pip install url-checker-JACK
```

## Usage

```python
import sys
from url_checker_JACK import check_url

def main():
    try:
        input_url = input("أدخل الرابط للفحص ثم اضغط Enter: ").strip()
    except KeyboardInterrupt:
        sys.exit(1)

    if not input_url:
        print("لم تُدخل رابطاً.")
        sys.exit(1)

    verdict = check_url(input_url)
    print(verdict)

if __name__ == "__main__":
    main()
```

## Development

To install for development:

```bash
pip install -e .
```

## License

MIT License

