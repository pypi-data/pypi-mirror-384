{
  description = "Utils for snowflake connection";

  inputs = {
    observes_flake_builder = {
      url =
        "github:fluidattacks/universe/d5147093dbd95ca7740d40a542650b9e2573f941?shallow=1&dir=observes/common/std_flake";
    };
    etl_utils = {
      url =
        "github:fluidattacks/universe/d5147093dbd95ca7740d40a542650b9e2573f941?shallow=1&dir=observes/common/etl-utils";
      inputs.observes_flake_builder.follows = "observes_flake_builder";
    };
  };

  outputs = { self, ... }@inputs:
    let
      build_args = { system, python_version, nixpkgs, pynix }:
        let
          with_python = bundle: bundle.packages."${system}"."${python_version}";
        in import ./build {
          inherit nixpkgs pynix;
          src = import ./build/filter.nix nixpkgs.nix-filter self;
          local_lib = { etl_utils_bundle = with_python inputs.etl_utils; };
        };
    in { packages = inputs.observes_flake_builder.outputs.build build_args; };
}

