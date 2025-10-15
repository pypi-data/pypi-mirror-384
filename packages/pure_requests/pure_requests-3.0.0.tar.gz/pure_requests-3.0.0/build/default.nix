{ nixpkgs, pynix, src, }:
let
  filtered_src = import ./_filter.nix nixpkgs.nix-filter src;
  scripts = import ./scripts.nix { inherit nixpkgs; };
  deps = import ./deps { inherit nixpkgs pynix; };
  requirements = python_pkgs: {
    runtime_deps = with python_pkgs; [
      deprecated
      fa-purity
      requests
      types-deprecated
      types-requests
    ];
    build_deps = with python_pkgs; [ flit-core ];
    test_deps = with python_pkgs; [ arch-lint mypy pytest ruff ];
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
    extraPackages = [ scripts.run-lint nixpkgs.nixfmt-classic ];
  }).shell;
in bundle // { inherit devShell; }
