{ nixpkgs, pynix, src, }:
let
  filtered_src = import ./_filter.nix nixpkgs.nix-filter src;
  scripts = import ./scripts.nix { inherit nixpkgs; };
  deps = import ./deps { inherit nixpkgs pynix; };
  requirements = python_pkgs: {
    runtime_deps = [ python_pkgs.grimp python_pkgs.deprecated ];
    build_deps = [ python_pkgs.flit-core ];
    test_deps = [
      python_pkgs.mypy
      python_pkgs.pytest
      python_pkgs.ruff
      python_pkgs.types-deprecated
    ];
  };
  bundle = pynix.stdBundle {
    inherit requirements;
    pkgBuilder = pkgDeps:
      pynix.stdPkg {
        inherit pkgDeps;
        src = filtered_src;
      };
    defaultDeps = deps.python_pkgs;
  };
  devShell = (pynix.vscodeSettingsShell {
    pythonEnv = bundle.env.dev;
    extraPackages = [ scripts.run-lint ];
  }).shell;
in bundle // { inherit devShell; }
