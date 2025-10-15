{
  inputs = {
    nixpkgs.url = "nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config = { allowUnfree = true; };
        };
      in
      {
        # for use by nix fmt
        formatter = pkgs.nixfmt-rfc-style;

        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.nodejs
            pkgs.python3Full
            pkgs.pyright
            pkgs.uv
            pkgs.ruff
            pkgs.stdenv.cc.cc.lib
            pkgs.kubernetes-helm
            pkgs.terraform
            pkgs.berglas
            pkgs.postgresql
            # pkgs.neo4j
            (pkgs.google-cloud-sdk.withExtraComponents
              [ pkgs.google-cloud-sdk.components.cloud_sql_proxy ])
          ];
          env = (if pkgs.stdenv.isDarwin then {
            LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib ];
          } else {
            LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib ];
            NIX_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc ];
            NIX_LD = pkgs.lib.fileContents "${pkgs.stdenv.cc}/nix-support/dynamic-linker";
          });
        };
      });
}