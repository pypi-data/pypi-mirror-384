# Pre requisites

- nix (with flakes enabled)
- direnv
- makes

# Development

- enable the environment with `direvn allow`
- build the package with `nix build ".#python311.pkg"`
- test with `mypy .` and `pytest .`
- format code with `m . /formatPython/default`
