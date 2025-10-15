{ nixpkgs, pynix, python_pkgs }:
let
  commit = "4b622d659276fda6bd472b9db27c1d10a04f2fd6"; # v2.5.2
  sha256 = "0hg13s2arflyhjfkl2p8y8kiqf9zjisn2cgh0r43kk42a4imb3ck";
  bundle = let
    src = builtins.fetchTarball {
      inherit sha256;
      url =
        "https://gitlab.com/dmurciaatfluid/purity/-/archive/${commit}/purity-${commit}.tar";
    };
  in import "${src}/build" {
    inherit src;
    inherit nixpkgs pynix;
  };
  extended_python_pkgs = python_pkgs // {
    inherit (bundle.deps) types-simplejson;
  };
in bundle.builders.pkgBuilder
(bundle.builders.requirements extended_python_pkgs)
