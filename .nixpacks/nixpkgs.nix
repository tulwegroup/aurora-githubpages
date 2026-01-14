{ pkgs ? import <nixpkgs> {} }:

with pkgs;
[
  python311
  python311Packages.pip
  python311Packages.virtualenv
  nodejs_22
]
