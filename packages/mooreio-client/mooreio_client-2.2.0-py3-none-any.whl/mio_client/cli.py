# Copyright 2020-2025 Datum Technology Corporation
# All rights reserved.
#######################################################################################################################
import argparse
import contextlib
import importlib
import pathlib
import sys
import os
from types import ModuleType

from mio_client.commands import sim, ip, misc, user, gen
from mio_client.core.root_manager import RootManager

#######################################################################################################################
# User Manual Top
#######################################################################################################################
VERSION = "2.2.0"

HELP_TEXT = f"""
                                        Moore.io (`mio`) Client - v{VERSION}
                                    User Manual: https://mooreio-client.rtfd.io/
             https://mooreio.com - Copyright 2020-2025 Datum Technology Corporation - https://datumtc.ca
Usage:
  mio [--version] [--help]
  mio [--wd WD] [--dbg] CMD [OPTIONS]

Options:
  -v, --version
    Prints the mio version and exits.

  -h, --help
    Prints the overall synopsis and a list of the most commonly used commands and exits.

  -C WD, --wd WD
    Run as if mio was started in WD (Working Directory) instead of the Present Working Directory `pwd`.

  --dbg
    Enables tracing outputs from mio.

Full Command List (`mio help CMD` for help on a specific command):
   Help and Shell/Editor Integration
      help           Prints documentation for mio commands
      
   Project and Code Management
      init           Creates essential files necessary for new Projects/IPs
      x              Generates IP HDL code using Datum SiArx (requires license)

   IP and Credentials Management
      list           Enumerates local/installed IP visible to Moore.io
      login/logout   Starts/ends session with IP Marketplace
      install        Installs all IP dependencies from IP Marketplace
      package        Creates a compressed (and encrypted) archive of an IP
      publish        Publishes IP to Server (must have mio admin account)

   EDA Automation
      clean          Delete IP EDA artifacts and/or Moore.io Project directory contents (.mio)
      sim            Performs necessary steps to simulate an IP with any simulator
      regr           Runs regression against an IP
      dox            Generates source reference documentation with Doxygen"""


#######################################################################################################################
# Global Variables
#######################################################################################################################
TEST_MODE = False
USER_HOME_PATH = pathlib.Path(os.path.expanduser("~/.mio"))
root_manager: RootManager


#######################################################################################################################
# Main
#######################################################################################################################
def main(args=None) -> int:
    """
    Main entry point. Performs the following steps in order:
    - 1. Create CLI argument parser
    - 2. Find all commands and register them
    - 3. Parse CLI arguments
    - 4. Find the command which matches the parsed arguments
    - 5. Create the Root Manage instance
    - 6. Run the command via the Root instance
    :return: Exit code
    """
    global root_manager
    # 1. Create CLI argument parser
    try:
        parser = create_top_level_parser()
        subparsers = parser.add_subparsers(dest='command', help='Sub-command help')
        # 2. Find all commands and register them
        commands = register_all_commands(subparsers)
        # 3. Parse CLI arguments
        args = parser.parse_args(args)
    except Exception as e:
        print(f"Error during parsing of CLI arguments: {e}", file=sys.stderr)
        return 1
    # Version/Help (--version, --help) commands are handled here
    if args.version:
        print_version_text()
        return 0
    if (not args.command) or args.help:
        print_help_text()
        return 0
    # 4. Find the command which matches the parsed arguments
    command = next(
        (
            cmd for cmd in commands
            if cmd.name().lower() == args.command
        ),
        None
    )
    if not command:
        print(f"Unknown command '{args.command}' specified.", file=sys.stderr)
        return 1
     # If we're using a custom Work Directory, ensure it exists
    wd = None
    if args.wd is None:
        wd = pathlib.Path.cwd()
    else:
        try:
            wd = pathlib.Path(args.wd).resolve()
        except Exception as e:
            print(f"Invalid path '{wd}' provided as working directory: {e}", file=sys.stderr)
            return 1
    # 5. Create the Root Manager instance
    root_manager = RootManager("Moore.io Client Root Manager", wd, TEST_MODE, USER_HOME_PATH)
    command.parsed_cli_arguments = args
    # Enable Moore.io debug output if specified
    if args.dbg:
        root_manager.print_trace = True
    # 6. Run the command via the Root Manager instance
    return root_manager.run(command)


#######################################################################################################################
# Helper functions
#######################################################################################################################
def create_top_level_parser():
    """
    Creates a top-level CLI argument parser.
    :return: argparse.ArgumentParser object representing the top-level parser
    """
    parser = argparse.ArgumentParser(prog="mio", description="", add_help=False)
    parser.add_argument("-h"   , "--help"   , help="Shows this help message and exits.", action="store_true", default=False, required=False)
    parser.add_argument("-v"   , "--version", help="Prints version and exit."          , action="store_true", default=False, required=False)
    parser.add_argument("--dbg",              help="Enable tracing output."            , action="store_true", default=False, required=False)
    parser.add_argument("-C"   , "--wd"     , help="Run as if mio was started in <path> instead of the current working directory.", type=pathlib.Path, required=False)
    return parser

def register_all_commands(subparsers):
    """
    Register all commands to the subparsers.
    :param subparsers: An instance of argparse.ArgumentParser that contains the subparsers.
    :return: A list of registered commands.
    """
    commands = []
    register_commands(commands, sim.get_commands())
    register_commands(commands, ip.get_commands())
    register_commands(commands, misc.get_commands())
    register_commands(commands, user.get_commands())
    register_commands(commands, gen.get_commands())
    # Custom commands from env var
    custom_cmds = _discover_commands_in_paths("MIO_CUSTOM_COMMANDS")
    register_commands(commands, custom_cmds)
    for command in commands:
        command.add_to_subparsers(subparsers)
    return commands

def register_commands(existing_commands, new_commands):
    """
    Registers new commands into an existing list of commands.
    :param existing_commands: A list of existing commands (classes).
    :param new_commands: A list (or iterable) of new command classes to be registered.
    """
    # Build a set of existing names (call name() if available)
    def _cmd_name(cmd_cls):
        try:
            return cmd_cls.name()
        except Exception:
            # Fallback: attribute or class name
            return getattr(cmd_cls, "name", None) or getattr(cmd_cls, "__name__", str(cmd_cls))
    existing_names = { _cmd_name(c) for c in existing_commands }
    for command in new_commands:
        name = _cmd_name(command)
        if name in existing_names:
            # silently skip duplicates to allow overriding, or raise if you prefer strict
            continue
        existing_commands.append(command)
        existing_names.add(name)

def _iter_python_files(root: pathlib.Path):
    """Yield .py files under root, recursively, excluding __pycache__ and __init__.py."""
    if not root.exists() or not root.is_dir():
        return
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        if p.name == "__init__.py":
            continue
        yield p

def _package_importable_root(root: pathlib.Path) -> tuple[bool, pathlib.Path, str]:
    """
    Decide if `root` is a package root we can import via a dotted name.

    Returns (is_pkg, sys_path_to_add, pkg_base_name)

    Rules:
      - If root has __init__.py → treat as a regular package (pkg name = root.name, sys.path += root.parent)
      - If no __init__.py, still try PEP 420 namespace (pkg name = root.name, sys.path += root.parent)
      - If parent isn’t a directory, return (False, root, "")
    """
    if not root.exists() or not root.is_dir():
        return (False, root, "")
    parent = root.parent
    if not parent.exists():
        return (False, root, "")
    # Accept both classic and namespace packages
    return (True, parent, root.name)

def _import_module_dotted(sys_path_entry: pathlib.Path, pkg_name: str, pyfile: pathlib.Path) -> ModuleType | None:
    """
    Import module by dotted name, e.g. pkg_name.subpkg.module, after temporarily
    inserting sys_path_entry (the dir that contains pkg_name) at the front of sys.path.
    """
    rel = pyfile.with_suffix("").relative_to(sys_path_entry / pkg_name)
    dotted = ".".join((pkg_name, *rel.parts))
    with _sys_path_prepend(sys_path_entry):
        try:
            return importlib.import_module(dotted)
        except Exception as e:
            if TEST_MODE:
                print(f"[mio] Skipping {pyfile} (package import {dotted}): {e}", file=sys.stderr)
            return None

@contextlib.contextmanager
def _sys_path_prepend(p: pathlib.Path):
    p_str = str(p)
    orig = list(sys.path)
    try:
        if p_str in sys.path:
            sys.path.remove(p_str)
        sys.path.insert(0, p_str)
        yield
    finally:
        sys.path[:] = orig

def _load_module_from_file(mod_name: str, file_path: pathlib.Path) -> ModuleType | None:
    """Safely import a module from an arbitrary file path (only as a fallback)."""
    try:
        spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            return mod
    except Exception as e:
        if TEST_MODE:
            print(f"[mio] Skipping {file_path}: {e}", file=sys.stderr)
    return None

def _discover_commands_in_paths(env_var: str = "MIO_CUSTOM_COMMANDS"):
    """
    Scan directories from MIO_CUSTOM_COMMANDS for modules exposing get_commands().

    Strategy:
      1) If the path looks like a package directory (classic or namespace), import modules by dotted name.
      2) Otherwise, fall back to file-based import.
    """
    value = os.getenv(env_var, "") or ""
    cmd_classes = []
    if not value.strip():
        return cmd_classes

    for root_str in value.split(os.pathsep):
        root_str = root_str.strip()
        if not root_str:
            continue
        root = pathlib.Path(root_str).expanduser().resolve()

        is_pkg, sys_entry, pkg_name = _package_importable_root(root)

        for pyfile in _iter_python_files(root):
            mod = None
            if is_pkg and pkg_name:
                mod = _import_module_dotted(sys_entry, pkg_name, pyfile)
            if mod is None:
                # fallback: unique synthetic name for file import
                safe_name = "mio_custom_" + "_".join(pyfile.relative_to(root).with_suffix("").parts)
                mod = _load_module_from_file(safe_name, pyfile)
            if not mod:
                continue

            get_cmds = getattr(mod, "get_commands", None)
            if callable(get_cmds):
                try:
                    cmds = list(get_cmds())
                    cmd_classes.extend(cmds)
                except Exception as e:
                    if TEST_MODE:
                        print(f"[mio] get_commands() failed in {pyfile}: {e}", file=sys.stderr)
    return cmd_classes

def print_help_text():
    print(HELP_TEXT)

def print_version_text():
    print(f"Moore.io Client v{VERSION}")


#######################################################################################################################
# Entry point
#######################################################################################################################
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
