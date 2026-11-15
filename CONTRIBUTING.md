# Contributing

Contributions and reproducible bug reports are welcome. Please do not include real bot tokens or user messages in issues, screenshots, or test fixtures.

## Development

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python -m compileall -q src
ruff check src tests
```

New adapters or methods should include: an upstream documentation link, input/output notes, MockTransport tests, and updated platform status. Never assume Telegram method parity with Bale or Soroush Plus without upstream evidence.

For changes to public API, update both README files, examples, `CHANGELOG.md`, and `docs/STATUS.md`. Use focused pull requests and conventional commit-style subjects where possible.
