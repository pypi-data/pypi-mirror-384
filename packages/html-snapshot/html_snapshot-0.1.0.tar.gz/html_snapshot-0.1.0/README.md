# html-snapshot

Capture a PNG screenshot from a local HTML presentation using Playwright.

## Quick start

```bash
# one-time: install Playwright browser assets
uvx playwright install chromium

# run the script with uvx
uvx --with playwright python html_snapshot.py /path/to/slide.html --output slide.png
```

Once the package is published to PyPI you can install it and use the console entry point:

```bash
pip install html-snapshot
html-snapshot /path/to/slide.html --output slide.png
```

## CLI options

| Option | Description |
| ------ | ----------- |
| `html_path` | Path to the local HTML file to render |
| `-o / --output` | Output PNG path (default: same as input with `.png` suffix) |
| `--width` / `--height` | Viewport size (default: 1400×900) |
| `--delay` | Seconds to wait after load before capturing |
| `--no-full-page` | Capture only the viewport instead of the full page |

## Development

```bash
uv venv           # optional: create a local env for hacking
uv pip install -r requirements.txt  # not necessary if using uvx
```

For remote execution, the script can be invoked directly from this GitHub repo:

```bash
uvx --with playwright python gh:oneryalcin/html-snapshot/html_snapshot.py sample.html
```
