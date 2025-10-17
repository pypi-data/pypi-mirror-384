# random-32-key-base64

Generate a 32-byte random key using random.org and encode it in base64.

## Installation

You can run this tool directly using `uvx` without installation:

```bash
uvx random-32-key-base64
```

Or install it with uv:

```bash
uv tool install random-32-key-base64
```

Or with pip:

```bash
pip install random-32-key-base64
```

## Usage

Simply run the command:

```bash
random-32-key-base64
```

This will generate 32 random bytes from random.org, encode them in base64, and print the result.

## Example Output

```
dGhpcyBpcyBhbiByYW5kb20gYmFzZTY0IGVuY29kZWQgc3RyaW5n
```

## Requirements

- Python 3.12 or higher
- Internet connection (to access random.org)

## How it works

The tool uses the random.org API to generate cryptographically secure random bytes, then encodes them using base64 encoding for easy copying and use in various applications.
