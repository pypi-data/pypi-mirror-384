{ nixpkgs, pynix, }:
let
  inherit (pynix) lib;

  layer_1 = python_pkgs:
    python_pkgs // {
      arch-lint = let
        result = import ./arch_lint.nix { inherit nixpkgs pynix python_pkgs; };
      in result;
      types-simplejson = import ./simplejson/stubs.nix python_pkgs lib;
    };
  python_pkgs = pynix.utils.compose [ layer_1 ] pynix.lib.pythonPackages;
in { inherit lib python_pkgs; }
