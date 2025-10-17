#!/usr/bin/env python3
"""
CLI interface for lecture_downloader package.
"""

import os
import click
from .processor import LectureProcessor
from .completion import (
    print_completion_instructions,
    complete_video_files,
    complete_directories,
    complete_links_files,
    complete_json_files,
)


@click.group(context_settings={'help_option_names': ['-h', '--help']})
@click.option('--verbose/--quiet', default=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """Lecture Downloader - Download, merge, and transcribe lecture videos."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


@cli.command()
@click.option('--links', '-l', required=True, shell_complete=complete_links_files, help='Path to links file or single URL')
@click.option('--titles', '-t', default=None, shell_complete=complete_json_files, help='Path to titles JSON file')
@click.option('--base-dir', '-b', default='.', shell_complete=complete_directories, help='Base project directory (downloads to base-dir/lecture-downloads)')
@click.option('--max-workers', '-w', default=5, type=int, help='Concurrent downloads')
@click.option('--no-custom-titles', is_flag=True, help='Do not use custom titles')
# Legacy options (auto-detected)
@click.option('--output-dir', '-o', default=None, shell_complete=complete_directories, help='Legacy: Output directory (if provided, uses direct paths mode)')
@click.pass_context
def download(ctx, links, titles, base_dir, max_workers, no_custom_titles, output_dir):
    """Download lectures from URLs."""
    verbose = ctx.obj['verbose']
    
    processor = LectureProcessor(verbose=verbose, interactive=False)
    
    try:
        results = processor.download_lectures(
            links=links,
            titles=titles,
            base_dir=base_dir,
            max_workers=max_workers,
            use_custom_titles=not no_custom_titles,
            output_dir=output_dir
        )
        
        click.echo(f"✅ Download completed!")
        click.echo(f"   Successful: {len(results['successful'])}")
        click.echo(f"   Failed: {len(results['failed'])}")
        
        # Display output directory with Rich formatting
        from rich.console import Console
        console = Console()
        
        # Determine the output directory
        if output_dir:
            final_output_dir = output_dir
        else:
            final_output_dir = os.path.join(base_dir, "lecture-downloads")
        
        # Convert to absolute path for display
        abs_output_dir = os.path.abspath(final_output_dir)
        console.print(f"[bold green]Output saved to:[/bold green]")
        print(f"   '{abs_output_dir}'")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--base-dir', '-b', default='.', shell_complete=complete_directories, help='Base project directory (auto-detects input, outputs to base-dir/merged-lectures)')
# Legacy options (auto-detected)
@click.option('--input-dir', '-i', default=None, shell_complete=complete_directories, help='Legacy: Input directory (auto-detects direct vs smart mode)')
@click.option('--output-dir', '-o', default=None, shell_complete=complete_directories, help='Legacy: Output directory (if provided with input-dir, uses direct paths mode)')
@click.pass_context
def merge(ctx, base_dir, input_dir, output_dir):
    """Merge videos by module with chapter markers."""
    verbose = ctx.obj['verbose']
    
    processor = LectureProcessor(verbose=verbose, interactive=False)
    
    try:
        results = processor.merge_videos(
            base_dir=base_dir,
            input_dir=input_dir,
            output_dir=output_dir
        )
        
        click.echo(f"✅ Merge completed!")
        click.echo(f"   Successful: {len(results['successful'])}")
        click.echo(f"   Failed: {len(results['failed'])}")
        
        # Display output directory with Rich formatting
        from rich.console import Console
        console = Console()
        
        # Determine the output directory
        if output_dir:
            final_output_dir = output_dir
        elif input_dir:
            final_output_dir = os.path.join(input_dir, "merged-lectures")
        else:
            final_output_dir = os.path.join(base_dir, "merged-lectures")
        
        # Convert to absolute path for display
        abs_output_dir = os.path.abspath(final_output_dir)
        console.print(f"[bold green]Output saved to:[/bold green]")
        print(f"   '{abs_output_dir}'")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('path', required=False, shell_complete=complete_video_files)
@click.option('--base-dir', '-b', default='.', shell_complete=complete_directories, help='Base project directory (auto-detects input, outputs to base-dir/transcripts)')
@click.option('--method', '-m', default='auto', type=click.Choice(['auto', 'gcloud', 'whisper']), help='Transcription method')
@click.option('--model', default='base', help='Whisper model size (tiny, tiny.en, base, base.en, small, small.en, distil-small.en, medium, medium.en, distil-medium.en, large-v1, large-v2, large-v3, large, distil-large-v2, distil-large-v3) or path to a custom model.')
@click.option('--language', '-lang', default='en-US', help='Language code')
@click.option('--max-workers', '-w', default=3, type=int, help='Concurrent workers')
@click.option('--no-inject', is_flag=True, help='Skip subtitle injection')
@click.option('--save-txt/--no-save-txt', default=True, help='Save transcript TXT files (default: enabled)')
@click.option('--save-srt/--no-save-srt', default=False, help='Save subtitle SRT files (default: disabled)')
@click.option('--resume', is_flag=True, help='Skip already-transcribed files')
@click.option('--watch', is_flag=True, help='Watch directory for new MP4 files and auto-transcribe')
@click.option('--recursive', '-r', is_flag=True, help='Find MP4 files in subdirectories recursively')
# Legacy options (auto-detected)
@click.option('--input-path', '-i', default=None, shell_complete=complete_video_files, help='Legacy: Video file or directory (auto-detects direct vs smart mode)')
@click.option('--output-dir', '-o', default=None, shell_complete=complete_directories, help='Legacy: Output directory (if provided with input-path, uses direct paths mode)')
@click.pass_context
def transcribe(ctx, path, base_dir, method, model, language, max_workers, no_inject, save_txt, save_srt, resume, watch, recursive, input_path, output_dir):
    """Transcribe videos using Google Cloud or Whisper.
    
    PATH can be a video file or directory. If not provided, uses --base-dir (or current directory).
    
    Examples:
      lecture-downloader transcribe /path/to/video.mp4
      lecture-downloader transcribe ./videos-dir
      lecture-downloader transcribe -b /path/to/videos
    """
    verbose = ctx.obj['verbose']
    
    # Use positional path argument if provided, otherwise fall back to base_dir
    effective_base_dir = path if path is not None else base_dir
    
    processor = LectureProcessor(verbose=verbose, interactive=False)
    
    try:
        results = processor.transcribe_videos(
            base_dir=effective_base_dir,
            language=language,
            method=method,
            model_size_or_path=model,
            max_workers=max_workers,
            inject_subtitles=not no_inject,
            save_txt=save_txt,
            save_srt=save_srt,
            resume=resume,
            watch=watch,
            recursive=recursive,
            input_path=input_path,
            output_dir=output_dir
        )
        
        
        # Display output directory with Rich formatting
        from rich.console import Console
        console = Console()
        
        # Determine the output directory
        if output_dir:
            final_output_dir = output_dir
        elif input_path:
            if os.path.isfile(input_path):
                final_output_dir = os.path.dirname(input_path)
            else:
                final_output_dir = os.path.join(input_path, "transcripts")
        else:
            if os.path.isfile(effective_base_dir):
                final_output_dir = os.path.dirname(effective_base_dir)
            else:
                final_output_dir = os.path.join(effective_base_dir, "transcripts")
        
        # Convert to absolute path for display
        abs_output_dir = os.path.abspath(final_output_dir)
        console.print(f"[bold green]Output saved to:[/bold green]")
        print(f"   '{abs_output_dir}'")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('shell', required=False, type=click.Choice(['bash', 'zsh', 'fish', 'powershell'], case_sensitive=False))
@click.option('--install', is_flag=True, help='Install completion for current shell')
def completion(shell, install):
    """Show or install shell completion.

    Examples:
        lecture-downloader completion bash
        lecture-downloader completion --install
        eval "$(_LECTURE_DOWNLOADER_COMPLETE=bash_source lecture-downloader)"
    """
    if install:
        # Auto-detect shell from environment
        import subprocess
        try:
            detected_shell = os.path.basename(os.environ.get('SHELL', 'bash'))
            if detected_shell not in ['bash', 'zsh', 'fish', 'powershell']:
                detected_shell = 'bash'
            shell = detected_shell
        except Exception:
            shell = 'bash'

    if shell:
        from .completion import get_completion_script
        click.echo(get_completion_script(shell))
    else:
        # Show all completion instructions
        print_completion_instructions()


@cli.command()
@click.option('--links', '-l', required=True, shell_complete=complete_links_files, help='Path to links file')
@click.option('--titles', '-t', default=None, shell_complete=complete_json_files, help='Path to titles JSON file')
@click.option('--output-dir', '-o', default='lecture_processing', shell_complete=complete_directories, help='Base output directory')
@click.option('--max-download-workers', default=5, type=int, help='Concurrent downloads')
@click.option('--max-transcribe-workers', default=3, type=int, help='Concurrent transcriptions')
@click.option('--method', '-m', default='auto', type=click.Choice(['auto', 'gcloud', 'whisper']), help='Transcription method')
@click.option('--model', default='base', help='Whisper model size (tiny, tiny.en, base, base.en, small, small.en, distil-small.en, medium, medium.en, distil-medium.en, large-v1, large-v2, large-v3, large, distil-large-v2, distil-large-v3) or path to a custom model.')
@click.option('--language', '-lang', default='en-US', help='Language code')
@click.option('--download-only', is_flag=True, help='Only download')
@click.option('--merge-only', is_flag=True, help='Only merge')
@click.option('--transcribe-only', is_flag=True, help='Only transcribe')
@click.option('--no-inject', is_flag=True, help='Skip subtitle injection')
@click.pass_context
def pipeline(ctx, links, titles, output_dir, max_download_workers, max_transcribe_workers,
             method, model, language, download_only, merge_only, transcribe_only, no_inject):
    """Run the complete pipeline: download -> merge -> transcribe."""
    verbose = ctx.obj['verbose']
    
    # Validate mutually exclusive options
    exclusive_flags = [download_only, merge_only, transcribe_only]
    if sum(exclusive_flags) > 1:
        click.echo("❌ Error: Only one of --download-only, --merge-only, --transcribe-only can be used", err=True)
        raise click.Abort()
    
    processor = LectureProcessor(verbose=verbose, interactive=False)
    
    try:
        results = processor.process_pipeline(
            links=links,
            titles=titles,
            output_dir=output_dir,
            max_download_workers=max_download_workers,
            max_transcribe_workers=max_transcribe_workers,
            transcription_method=method,
            model_size_or_path=model,
            language=language,
            inject_subtitles=not no_inject,
            download_only=download_only,
            merge_only=merge_only,
            transcribe_only=transcribe_only
        )
        
        click.echo(f"🎉 Pipeline completed!")
        for step, result in results.items():
            if result['successful'] or result['failed']:
                click.echo(f"   {step.title()}: {len(result['successful'])} successful, {len(result['failed'])} failed")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
