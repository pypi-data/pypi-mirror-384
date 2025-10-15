{
  description = "Pure functional and typing utilities";
  inputs = {
    nixpkgs_flake.url = "github:nixos/nixpkgs";
    nix_filter.url = "github:numtide/nix-filter";
    pynix_flake.url = "gitlab:dmurciaatfluid/python_nix_builder";
  };
  outputs = { self, nixpkgs_flake, nix_filter, pynix_flake, }:
    let
      path_filter = nix_filter.outputs.lib;
      build_bundle = system: python_version:
        let
          pkgs = nixpkgs_flake.legacyPackages."${system}";
          nixpkgs = pkgs // { nix-filter = path_filter; };
          pynix = import "${pynix_flake}/pynix" {
            inherit nixpkgs;
            pythonVersion = python_version;
          };
        in import ./build {
          inherit nixpkgs pynix;
          src = self;
        };
      supported =
        [ "python39" "python310" "python311" "python312" "python313" ];
      outputs = system:
        let
          nixpkgs = nixpkgs_flake.legacyPackages."${system}";
          scripts = import ./build/scripts.nix { inherit nixpkgs; };
          bundles = builtins.listToAttrs (map (name: {
            inherit name;
            value = build_bundle system name;
          }) supported);
        in bundles // scripts;
      systems =
        [ "aarch64-darwin" "aarch64-linux" "x86_64-darwin" "x86_64-linux" ];
      forAllSystems = nixpkgs_flake.lib.genAttrs systems;
    in {
      packages = forAllSystems outputs;
      defaultPackage = self.packages;
      inherit nixpkgs_flake;
    };
}
