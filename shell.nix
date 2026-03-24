{ pkgs ? import <nixpkgs> {} }:

let
  python = (pkgs.python312.override {
    x11Support = true;
  }).withPackages (ps: with ps; [
    tkinter
    numpy
    pandas
    scipy
    matplotlib
    mplcursors
    pip
  ]);
in
pkgs.mkShell {
  packages = [
    python
    pkgs.tk
    pkgs.tcl
  ];
}
