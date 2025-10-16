# MD2Slack - Markdown to Slack Converter

![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)  
![Build Status](https://github.com/MayzTex/MD2Slack/actions/workflows/ci.yml/badge.svg)
![PyPI version](https://img.shields.io/pypi/v/md2slack)  
![Python](https://img.shields.io/badge/python-3.6%2B-blue)  

MD2Slack is a Python package that converts **Markdown** into **Slack-compatible formatting**.  
Easily transform Markdown syntax into a format that works seamlessly in Slack messages, preserving formatting like **bold, italics, headers, lists, tables, and code blocks**.  

---

## Features
- Converts standard **Markdown** syntax to **Slack-formatted** text  
- Supports **headers, lists, blockquotes, code blocks, and tables**  
- Handles **inline styles** (bold, italics, strikethrough, and links)  
- Preserves **Slack-specific mentions** (`@user`, `#channel`)  
- Lightweight and efficient  

---

## Installation

You can install MD2Slack via pip:

```bash
pip install md2slack
```

---

## Usage

### Basic Example
Convert Markdown text into Slack-formatted output:

```python
from md2slack import SlackMarkdown

parser = SlackMarkdown()
slack_text = parser("## Hello *world*")
print(slack_text)  # Outputs: *Hello _world_*
```
---

## Development & Contribution

I welcome contributions! Follow these steps to contribute:

1. **Fork** the repository  
2. **Clone** your fork locally  
   ```bash
   git clone https://github.com/MayzTex/md2slack.git
   cd md2slack
   ```
3. **Create a new branch**  
   ```bash
   git checkout -b feature-branch
   ```
4. **Make changes & commit**  
   ```bash
   git add .
   git commit -m "Added new feature"
   ```
5. **Push & open a Pull Request**  
   ```bash
   git push origin feature-branch
   ```

---

## Running Tests

To run tests locally:

```bash
pytest
```

---

## License

MD2Slack is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## Support & Feedback

If you find this project useful, consider starring it on GitHub.  
For issues or feature requests, please open an [issue](https://github.com/MayzTex/md2slack/issues).

