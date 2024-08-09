{
  description = "Teehetki server deps";

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
            (pkgs.python3.withPackages (ps: [ ps.pydub ps.black ps.aiohttp ps.aiohttp-cors ps.numpy ps.scipy ps.python-socketio ps.librosa ]))
            pkgs.ffmpeg
          ];
        };

        packages = {
          dockerImage = pkgs.dockerTools.buildImage {
            name = "teehetki-server";
            tag = "latest";
            runAsRoot = ''
              mkdir -p app
              cp -r ${./src} /app/src
              chmod -R +w /app
            '';
            config = {
              Cmd = [ "python" "src/main.py" ];
              WorkingDir = "/app";
              Expose = [ "5000" ]; # Expose the port your app is running on
              Env = [
                "PYTHONUNBUFFERED=1"
              ];
            };
            copyToRoot = with pkgs; [
              (python3.withPackages (ps: [ ps.pydub ps.aiohttp ps.aiohttp-cors ps.numpy ps.scipy ps.python-socketio ps.librosa ]))
              ffmpeg
              bashInteractive
              coreutils
              fakeNss
              pkgs.dockerTools.caCertificates
            ];
          };
        };
      });
}
