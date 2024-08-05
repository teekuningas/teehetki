{
  description = "Teehetki deps";

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
      devShells.default = pkgs.mkShell {
        buildInputs = [
          pkgs.nodejs
          pkgs.python3
          pkgs.stdenv.cc.cc.lib
        ];

        shellHook = ''
          echo "Setting up Python virtual environment..."
          if [ ! -d ".venv" ]; then
            python -m venv .venv
          fi
          source .venv/bin/activate
          echo "Python virtual environment activated."

          if [ -f "requirements.txt" ]; then
            echo "Installing Python dependencies..."
            pip install -r requirements.txt
          fi

          if [ -f "package.json" ]; then
            echo "Installing npm dependencies..."
            npm install
          fi

          if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS specific environment setup
            export DYLD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib/"
          else
            # Linux specific environment setup
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib/"
          fi
        '';
      };
    });
}
