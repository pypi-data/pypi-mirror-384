{ nixpkgs, pynix, }:
let
  inherit (pynix) lib;

  layer_1 = python_pkgs:
    python_pkgs // {
      grimp = import ./grimp { inherit lib python_pkgs; };
    };

  python_pkgs = pynix.utils.compose [ layer_1 ] pynix.lib.pythonPackages;
in { inherit lib python_pkgs; }
