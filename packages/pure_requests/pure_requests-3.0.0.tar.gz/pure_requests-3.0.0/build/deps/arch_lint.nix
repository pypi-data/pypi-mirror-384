{ nixpkgs, pynix, python_pkgs }:
let
  commit = "463b295a9d3543692541978388811e6fa0046b3d"; # v4.0.4
  sha256 = "11m39a9b4ipjqqwhwp5gb28vvzl30npp98xyd3xgnq22rcc9698s";
  bundle = let
    src = builtins.fetchTarball {
      inherit sha256;
      url =
        "https://gitlab.com/dmurciaatfluid/arch_lint/-/archive/${commit}/arch_lint-${commit}.tar";
    };
  in import "${src}/build" {
    inherit src;
    inherit nixpkgs pynix;
  };
  extended_python_pkgs = python_pkgs // { inherit (bundle.deps) grimp; };
in bundle.builders.pkgBuilder
(bundle.builders.requirements extended_python_pkgs)
