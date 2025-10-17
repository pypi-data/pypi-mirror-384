{ nixpkgs, pynix, python_pkgs }:
let
  commit = "e669114103b334e532aec34dc5b2ec06dfd24247"; # v2.5.0+1
  sha256 = "1x0ipsklpsxyrzy8j6agkqppj4n2x67kaz7zsi3mkycan9z9z3f8";
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
