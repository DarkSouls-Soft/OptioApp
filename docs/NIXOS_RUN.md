# Running Opcio on NixOS

This file documents the practical workflow that worked reliably for this project.

## 1. `shell.nix`

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = [
    (pkgs.python312.withPackages (ps: with ps; [
      tkinter
      pip
      numpy
      pandas
      scipy
      matplotlib
      mplcursors
    ]))
  ];
}
```

## 2. Start the shell

```bash
nix-shell
```

## 3. Install Python-only GUI extras locally

These packages were easier to keep outside the main Nix package set for this project:

```bash
mkdir -p .pylibs
python -m pip install --target ./.pylibs tkcalendar ttkthemes
```

## 4. Run the application

```bash
PYTHONPATH=./.pylibs python main.py
```

## 5. Why this workflow is used

In this project, the Tk-enabled Python from `nix-shell` works more reliably than combining Nix Python with a regular `venv`.

## 6. Quick diagnostics

Check Tk support:

```bash
python -c "import _tkinter; print('tk ok')"
```

Check GUI extras:

```bash
PYTHONPATH=./.pylibs python -c "import tkcalendar, ttkthemes; print('extra gui libs ok')"
```
