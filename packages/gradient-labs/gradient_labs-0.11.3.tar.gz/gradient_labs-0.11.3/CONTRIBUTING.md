## Project setup

This library uses [uv].

[uv]: https://docs.astral.sh/uv/

You can set up a virtual environment for this library with:

```bash
make install
```

## Publishing a new version

- Update the version number in [`pyproject.toml`](./pyproject.toml)
- Run `make release`
- Wait for the GitHub [machinery](https://github.com/gradientlabs-ai/python-client/actions/workflows/publish.yaml) to do its magic
