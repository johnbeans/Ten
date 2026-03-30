# Contributing to Ten

## Getting Started

Ten is a monorepo with three layers:

- **libten** (C) — core algebra library
- **tenlang** (Python) — ctypes bindings around libten
- **ten_mcp_server** / **ten_rest_api** (Python) — MCP and HTTP interfaces

To build and test everything:

```bash
cd libten && make test          # 69 C tests
cd .. && python -m pytest tenlang/tests/ -v        # 53 binding tests
python -m pytest ten_mcp_server/tests/ -v           # 31 MCP tests
python -m pytest ten_rest_api/tests/ -v             # 35 REST tests
```

## AI-Assisted Development

This project uses AI tools (currently Claude) during development. When a commit includes significant AI-generated or AI-assisted code, it is noted with a `Co-Authored-By` trailer in the commit message. If you contribute to Ten using AI tools, please follow the same convention.

## Submitting Changes

Open a pull request against `main`. Please include tests for new functionality and make sure existing tests pass before submitting.

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
