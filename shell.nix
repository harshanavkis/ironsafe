let
  pkgs = import <nixpkgs>  {};
  stdenv = pkgs.stdenv;
in
  stdenv.mkDerivation {
    name = "env";
    buildInputs = with pkgs; [ hello gnumake ];
}
