{
  description = "Development environment with npm and Python";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in
    {
      devShells.${system}.default = pkgs.mkShell {
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

          export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib/"
        '';
      };
    };
}
