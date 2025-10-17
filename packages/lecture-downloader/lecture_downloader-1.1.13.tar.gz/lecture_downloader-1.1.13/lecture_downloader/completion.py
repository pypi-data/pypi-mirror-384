#!/usr/bin/env python3
"""
Shell completion utilities for lecture_downloader.
"""

import click
import os
from pathlib import Path


def get_completion_script(shell: str) -> str:
    """
    Get the shell completion installation instructions.

    Args:
        shell: Shell type (bash, zsh, fish, or powershell)

    Returns:
        Installation instructions for the specified shell
    """
    command_name = "lecture-downloader"

    instructions = {
        "bash": f"""
# Add this to ~/.bashrc:
eval "$(_LECTURE_DOWNLOADER_COMPLETE=bash_source {command_name})"

# Or generate the completion script:
_{command_name.upper().replace('-', '_')}_COMPLETE=bash_source {command_name} > ~/.{command_name}-complete.bash
echo "source ~/.{command_name}-complete.bash" >> ~/.bashrc
""",
        "zsh": f"""
# Add this to ~/.zshrc:
eval "$(_LECTURE_DOWNLOADER_COMPLETE=zsh_source {command_name})"

# Or generate the completion script:
_{command_name.upper().replace('-', '_')}_COMPLETE=zsh_source {command_name} > ~/.{command_name}-complete.zsh
echo "source ~/.{command_name}-complete.zsh" >> ~/.zshrc
""",
        "fish": f"""
# Add this to ~/.config/fish/completions/{command_name}.fish:
_{command_name.upper().replace('-', '_')}_COMPLETE=fish_source {command_name} | source

# Or generate the completion script:
_{command_name.upper().replace('-', '_')}_COMPLETE=fish_source {command_name} > ~/.config/fish/completions/{command_name}.fish
""",
        "powershell": f"""
# Add this to your PowerShell profile:
_{command_name.upper().replace('-', '_')}_COMPLETE=powershell_source {command_name} | Invoke-Expression

# Or save to a file:
$_LECTURE_DOWNLOADER_COMPLETE='powershell_source' {command_name} > {command_name}.ps1
"""
    }

    return instructions.get(shell.lower(), "Unsupported shell type")


def print_completion_instructions():
    """Print completion installation instructions for all shells."""
    click.echo("Shell Completion Setup Instructions")
    click.echo("=" * 50)

    for shell in ["bash", "zsh", "fish", "powershell"]:
        click.echo(f"\n{shell.upper()}:")
        click.echo(get_completion_script(shell))


# Custom completion functions for path arguments
def complete_video_files(ctx, param, incomplete):
    """Complete video file paths (MP4, MOV, AVI, etc.)."""
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv']
    results = []
    path = Path(incomplete or '.')

    try:
        if path.is_dir():
            for item in path.iterdir():
                if item.is_dir():
                    results.append(str(item) + '/')
                elif item.suffix.lower() in video_extensions:
                    results.append(str(item))
        else:
            parent = path.parent if path.parent.exists() else Path('.')
            pattern = path.name
            for item in parent.iterdir():
                if item.name.startswith(pattern):
                    if item.is_dir():
                        results.append(str(item) + '/')
                    elif item.suffix.lower() in video_extensions:
                        results.append(str(item))
    except (OSError, PermissionError):
        pass

    return results


def complete_directories(ctx, param, incomplete):
    """Complete directory paths."""
    results = []
    path = Path(incomplete or '.')

    try:
        if path.is_dir():
            for item in path.iterdir():
                if item.is_dir():
                    results.append(str(item) + '/')
        else:
            parent = path.parent if path.parent.exists() else Path('.')
            pattern = path.name
            for item in parent.iterdir():
                if item.is_dir() and item.name.startswith(pattern):
                    results.append(str(item) + '/')
    except (OSError, PermissionError):
        pass

    return results


def complete_links_files(ctx, param, incomplete):
    """Complete paths to text files that might contain links."""
    results = []
    path = Path(incomplete or '.')

    try:
        if path.is_dir():
            for item in path.iterdir():
                if item.is_dir():
                    results.append(str(item) + '/')
                elif item.suffix in ['.txt', '.csv', '.md']:
                    results.append(str(item))
        else:
            parent = path.parent if path.parent.exists() else Path('.')
            pattern = path.name
            for item in parent.iterdir():
                if item.name.startswith(pattern):
                    if item.is_dir():
                        results.append(str(item) + '/')
                    elif item.suffix in ['.txt', '.csv', '.md']:
                        results.append(str(item))
    except (OSError, PermissionError):
        pass

    return results


def complete_json_files(ctx, param, incomplete):
    """Complete paths to JSON files."""
    results = []
    path = Path(incomplete or '.')

    try:
        if path.is_dir():
            for item in path.iterdir():
                if item.is_dir():
                    results.append(str(item) + '/')
                elif item.suffix == '.json':
                    results.append(str(item))
        else:
            parent = path.parent if path.parent.exists() else Path('.')
            pattern = path.name
            for item in parent.iterdir():
                if item.name.startswith(pattern):
                    if item.is_dir():
                        results.append(str(item) + '/')
                    elif item.suffix == '.json':
                        results.append(str(item))
    except (OSError, PermissionError):
        pass

    return results
