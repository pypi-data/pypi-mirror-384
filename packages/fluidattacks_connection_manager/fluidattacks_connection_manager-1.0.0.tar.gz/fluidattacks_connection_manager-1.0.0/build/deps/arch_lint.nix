{ nixpkgs, pynix, python_pkgs }:
let
  commit = "43aa33ef4cfa12c37148f4653dd89233c585c368"; # v4.0.4
  sha256 = "06r2xfj50rn9m87i3vwa9bilhnrz3njhmfd992vzp4a5x937rfq2";
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
