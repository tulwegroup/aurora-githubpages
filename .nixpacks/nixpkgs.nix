{ pkgs ? import <nixpkgs> {} }:

with pkgs;
[
  python311
  python311Packages.pip
  python311Packages.virtualenv
  python311Packages.setuptools
  python311Packages.wheel
  python311Packages.gunicorn
  python311Packages.uvicorn
  python311Packages.psutil
  python311Packages.psycopg2
  python311Packages.redis
  python311Packages.celery
  python311Packages.numpy
  python311Packages.scipy
  python311Packages.requests
  python311Packages.pydantic
  python311Packages.fastapi
  python311Packages.python-dotenv
  nodejs_22
]
