#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: charlescostanzo
"""

from cmdstanpy import CmdStanModel, cmdstan_path, install_cmdstan
import importlib.resources as pkg_resources
import os

_checked_cmdstan = False


def ensure_cmdstan_installed(interactive: bool = False):
    """
    Ensure CmdStan is installed and available.
    If found, does nothing.
    If not found:
    	interactive=False: raises RuntimeError with instructions.
    	interactive=True: asks user whether to install now.
    """
    global _checked_cmdstan

    if _checked_cmdstan:
        return

    try:
        path = cmdstan_path()
        if not os.path.exists(path):
            raise ValueError("CmdStan path not found.")
    except ValueError:
        if interactive:
            response = input(
                "CmdStan is not installed. Would you like to install it now? [y/n]: "
            ).strip().lower()
            if response == "y":
                print("Installing CmdStan... this may take a few minutes...")
                install_cmdstan()
                print(f"CmdStan installed at: {cmdstan_path()}")
            else:
                raise RuntimeError(
                    "CmdStan is required but not installed. "
                    "Run `from cmdstanpy import install_cmdstan; install_cmdstan()` "
                    "to install manually."
                )
        else:
            raise RuntimeError(
                "CmdStan is not installed. "
                "Please install it by running:\n\n"
                "    from cmdstanpy import install_cmdstan\n"
                "    install_cmdstan()\n\n"
                "This may take several minutes."
            )

    _checked_cmdstan = True


def load_stan_model(model_name: str) -> CmdStanModel:
    """
    Load and compile a Stan model from the package's stan/ directory.
    Ensures CmdStan is installed before compiling.
    """
    ensure_cmdstan_installed(interactive=False)

    # Locate the .stan file inside the package
    stan_path = pkg_resources.files("networkscaleup").joinpath("stan", f"{model_name}.stan")

    if not stan_path.exists():
        raise FileNotFoundError(f"Stan file not found: {stan_path}")

    return CmdStanModel(stan_file=str(stan_path))


if __name__ == "__main__":
    # Running this file directly acts like a "setup script"
    ensure_cmdstan_installed(interactive=True)
