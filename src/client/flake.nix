{
  description = "Teehetki client deps";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        formatter = pkgs.nixpkgs-fmt;
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.nodejs
          ];

          shellHook = ''
            if [ -f "package.json" ]; then
              echo "Installing npm dependencies..."
              npm install
            fi
          '';
        };
      });
}
