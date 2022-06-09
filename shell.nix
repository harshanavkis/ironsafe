with (import <nixpkgs> {});
let
  my-python-packages = python-packages: with python-packages; [
    pandas
    seaborn
  ];
  python-with-my-packages = python3.withPackages my-python-packages;
in
mkShell {
  buildInputs = [
    python-with-my-packages
    pkgs.openssl
    pkgs.gnumake
  ];
}
