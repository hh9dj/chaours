{
  description = "nucliplan development shell";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in
    {
      devShells = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          default = pkgs.mkShell {
            env = {
              UV_PYTHON_DOWNLOADS = "never";
              UV_PYTHON = "${pkgs.python312}/bin/python";
              LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
                pkgs.stdenv.cc.cc.lib
                pkgs.zlib
              ];
            };
            packages = with pkgs; [
              nodejs_22
              pnpm
              python312
              uv
              sqlite
              ruff
              pyright
              just
            ];
          };
        }
      );
    };
}
