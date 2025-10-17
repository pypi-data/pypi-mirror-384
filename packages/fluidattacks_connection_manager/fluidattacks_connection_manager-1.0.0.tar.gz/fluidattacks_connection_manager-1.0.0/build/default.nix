{ nixpkgs, pynix, src, local_lib }:
let
  deps = import ./deps { inherit nixpkgs pynix local_lib; };
  requirements = python_pkgs: {
    runtime_deps = with python_pkgs; [ etl-utils fa-purity snowflake-client ];
    build_deps = with python_pkgs; [ flit-core ];
    test_deps = with python_pkgs; [ arch-lint mypy pytest pytest-cov ruff ];
  };
in {
  inherit src requirements;
  root_path = "observes/common/connection-manager";
  module_name = "fluidattacks_connection_manager";
  pypi_token_var = "CONNECTION_MANAGER_TOKEN";
  defaultDeps = deps.python_pkgs;
  override = b: b;
}
