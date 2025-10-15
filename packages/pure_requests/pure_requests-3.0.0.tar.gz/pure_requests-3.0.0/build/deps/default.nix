{ nixpkgs, pynix, }:
let
  layer_1 = python_pkgs:
    python_pkgs // {
      arch-lint = import ./arch_lint.nix { inherit nixpkgs pynix python_pkgs; };
    };

  layer_2 = python_pkgs:
    python_pkgs // {
      fa-purity = import ./fa_purity.nix { inherit nixpkgs pynix python_pkgs; };
    };
  python_pkgs =
    pynix.utils.compose [ layer_2 layer_1 ] pynix.lib.pythonPackages;
in { inherit python_pkgs; }
