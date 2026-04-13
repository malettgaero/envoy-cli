# envoy-cli

> A lightweight CLI for managing and validating `.env` files across multiple environments with secret diffing support.

---

## Installation

```bash
pip install envoy-cli
```

Or with [pipx](https://pypa.github.io/pipx/) for isolated installs:

```bash
pipx install envoy-cli
```

---

## Usage

```bash
# Validate a .env file against a required keys template
envoy validate --env .env --template .env.example

# Diff secrets between two environments
envoy diff --from .env.staging --to .env.production

# List all keys in a .env file (values masked by default)
envoy list --env .env

# Check for missing or extra keys
envoy check --env .env.local --template .env.example --strict
```

**Example output:**

```
✔ All required keys present in .env.local
⚠ Extra keys found: DEBUG_MODE, TEMP_TOKEN
✘ Missing keys: STRIPE_SECRET_KEY
```

---

## Features

- Validate `.env` files against a template or schema
- Diff keys and values across multiple environment files
- Mask sensitive values in output by default
- Supports `.env`, `.env.local`, `.env.staging`, `.env.production`, and more

---

## License

[MIT](LICENSE) © 2024 envoy-cli contributors