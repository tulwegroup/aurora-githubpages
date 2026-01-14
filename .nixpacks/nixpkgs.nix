{ pkgs ? import <nixpkgs> {} }:

with pkgs;
[
  python311
  python311Packages.pip
  python311Packages.virtualenv
  python311Packages.gunicorn
  python311Packages.uvicorn
  nodejs_22
]
