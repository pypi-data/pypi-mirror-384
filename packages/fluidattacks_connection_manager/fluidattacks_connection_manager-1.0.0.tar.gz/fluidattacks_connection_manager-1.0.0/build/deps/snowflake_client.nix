{ nixpkgs, pynix, python_pkgs }:
let
  commit = "b516409c11a25af8acf933dee055f9784c994b2f"; # v3.2.3
  sha256 = "0jv5h7wbcn437l3rf41qc7sdg31q900lhn2pcjix00s181psmihq";
  bundle = let
    src = builtins.fetchTarball {
      inherit sha256;
      url =
        "https://gitlab.com/dmurciaatfluid/snowflake_client/-/archive/${commit}/snowflake_client-${commit}.tar";
    };
  in import "${src}/build" {
    inherit src;
    inherit nixpkgs pynix;
  };
  extended_python_pkgs = python_pkgs // {
    inherit (bundle.deps) redshift-client s3transfer boto3;
    snowflake-connector-python = let
      pkg = bundle.deps.snowflake-connector-python.overridePythonAttrs (old: {
        version = "3.14.0";
        src = nixpkgs.fetchFromGitHub {
          owner = "snowflakedb";
          repo = "snowflake-connector-python";
          tag = "v3.14.0";
          hash = "sha256-r3g+eVVyK9t5qpAGvimapuWilAh3eHJEFUw8VBwtKw8=";
        };
        disabledTestPaths = old.disabledTestPaths ++ [
          "test/unit/test_wiremock_client.py"
          "test/unit/test_put_get.py"
        ];
      });
    in pynix.utils.compose [
      pynix.patch.homelessPatch
      pynix.patch.disableChecks
    ] pkg;
  };
in {
  inherit extended_python_pkgs;
  pkg = bundle.builders.pkgBuilder
    (bundle.builders.requirements extended_python_pkgs);
}
