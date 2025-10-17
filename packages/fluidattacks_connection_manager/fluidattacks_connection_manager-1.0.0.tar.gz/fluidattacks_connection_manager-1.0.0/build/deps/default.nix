{ nixpkgs, pynix, local_lib }:
let
  python_overlay = final: prev: {
    arch-lint = import ./arch_lint.nix {
      inherit nixpkgs pynix;
      python_pkgs = prev;
    };
    fa-purity = import ./fa_purity.nix {
      inherit nixpkgs pynix;
      python_pkgs = final;
    };
    etl-utils = local_lib.etl_utils_bundle.builders.pkgBuilder
      (local_lib.etl_utils_bundle.builders.requirements {
        inherit nixpkgs;
        python_pkgs = final;
      });
    s3transfer = prev.s3transfer.overridePythonAttrs (oldAttrs: {
      preCheck = nixpkgs.lib.optionalString nixpkgs.stdenv.isDarwin ''
        export TMPDIR="/tmp"
      '';
    });
    snowflake-client = let
      bundle =
        import ./snowflake_client.nix { inherit nixpkgs pynix python_pkgs; };
    in bundle.pkg;
  };
  python = pynix.lib.python.override {
    packageOverrides = python_overlay;
    self = python;
  };
  python_pkgs = python.pkgs;
in { inherit python_pkgs; }
