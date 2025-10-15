{ nixpkgs, }:
let
  cache-build = nixpkgs.writeShellApplication {
    name = "cache-build";
    runtimeInputs = [ nixpkgs.jq nixpkgs.cachix ];
    text = ''
      nix build --print-build-logs --json "''${1}" \
        | jq -r '.[].outputs | to_entries[].value' \
        | cachix push fa-foss
      nix build "''${1}" --print-out-paths
    '';
  };
  publish = nixpkgs.writeShellApplication {
    name = "publish";
    runtimeInputs = [ nixpkgs.git nixpkgs.python311Packages.flit ];
    text = ''
      flit -f "''${1}/pyproject.toml" publish
    '';
  };
  check-lint-nix = nixpkgs.writeShellApplication {
    name = "check-lint-nix";
    runtimeInputs = [ nixpkgs.nixfmt-classic nixpkgs.statix ];
    text = ''
      nixfmt -c "''${1}"
      statix check "''${1}"
    '';
  };
  lint-nix = nixpkgs.writeShellApplication {
    name = "lint-nix";
    runtimeInputs = [ nixpkgs.nixfmt-classic nixpkgs.statix ];
    text = ''
      nixfmt "''${1}"
      statix fix "''${1}"
    '';
  };
  run-lint = nixpkgs.writeShellApplication {
    name = "run-lint";
    runtimeInputs = [ lint-nix ];
    text = ''
      echo "[CHECK] Ruff"
      ruff format
      ruff check . --fix
      ruff format
      echo "[CHECK] Nix"
      lint-nix .
      echo "[CHECK] Mypy"
      mypy .
      echo "[CHECK] Pytest"
      pytest ./tests
    '';
  };
in { inherit publish lint-nix check-lint-nix cache-build run-lint; }
