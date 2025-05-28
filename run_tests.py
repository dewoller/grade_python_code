"""
Test runner script for the marking system.

This script provides different testing modes and configurations
for running the complete test suite.
"""

import sys
import subprocess
from pathlib import Path
import click


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    if description:
        click.echo(f"Running: {description}")
    
    click.echo(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            click.echo(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        if e.stdout:
            click.echo("STDOUT:")
            click.echo(e.stdout)
        if e.stderr:
            click.echo("STDERR:")
            click.echo(e.stderr)
        return False


@click.group()
def cli():
    """Test runner for the marking system."""
    pass


@cli.command()
@click.option('--coverage', is_flag=True, help='Run with coverage reporting')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--parallel', '-n', type=int, help='Number of parallel workers')
def unit(coverage, verbose, parallel):
    """Run unit tests only."""
    cmd = ['python', '-m', 'pytest']
    
    if coverage:
        cmd.extend(['--cov=src', '--cov-report=html', '--cov-report=term-missing'])
    
    if verbose:
        cmd.append('-v')
    
    if parallel:
        cmd.extend(['-n', str(parallel)])
    
    # Exclude integration tests
    cmd.extend(['-m', 'not integration and not slow'])
    cmd.append('tests/')
    
    success = run_command(cmd, "Unit tests")
    if not success:
        sys.exit(1)


@cli.command()
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def integration(verbose):
    """Run integration tests only."""
    cmd = ['python', '-m', 'pytest']
    
    if verbose:
        cmd.append('-v')
    
    # Run only integration tests
    cmd.extend(['-m', 'integration'])
    cmd.append('tests/')
    
    success = run_command(cmd, "Integration tests")
    if not success:
        sys.exit(1)


@cli.command()
@click.option('--coverage', is_flag=True, help='Run with coverage reporting')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--parallel', '-n', type=int, help='Number of parallel workers')
@click.option('--skip-slow', is_flag=True, help='Skip slow tests')
def all(coverage, verbose, parallel, skip_slow):
    """Run all tests."""
    cmd = ['python', '-m', 'pytest']
    
    if coverage:
        cmd.extend(['--cov=src', '--cov-report=html', '--cov-report=term-missing'])
    
    if verbose:
        cmd.append('-v')
    
    if parallel:
        cmd.extend(['-n', str(parallel)])
    
    if skip_slow:
        cmd.extend(['-m', 'not slow'])
    
    cmd.append('tests/')
    
    success = run_command(cmd, "All tests")
    if not success:
        sys.exit(1)


@cli.command()
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def fast(verbose):
    """Run fast tests only (excludes slow and integration tests)."""
    cmd = ['python', '-m', 'pytest']
    
    if verbose:
        cmd.append('-v')
    
    # Exclude slow and integration tests
    cmd.extend(['-m', 'not slow and not integration'])
    cmd.append('tests/')
    
    success = run_command(cmd, "Fast tests")
    if not success:
        sys.exit(1)


@cli.command()
@click.argument('pattern')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def pattern(pattern, verbose):
    """Run tests matching a specific pattern."""
    cmd = ['python', '-m', 'pytest']
    
    if verbose:
        cmd.append('-v')
    
    cmd.extend(['-k', pattern])
    cmd.append('tests/')
    
    success = run_command(cmd, f"Tests matching pattern: {pattern}")
    if not success:
        sys.exit(1)


@cli.command()
@click.argument('test_file')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def file(test_file, verbose):
    """Run tests from a specific file."""
    cmd = ['python', '-m', 'pytest']
    
    if verbose:
        cmd.append('-v')
    
    test_path = Path('tests') / test_file
    if not test_path.exists():
        test_path = Path(test_file)
    
    if not test_path.exists():
        click.echo(click.style(f"Test file not found: {test_file}", fg="red"))
        sys.exit(1)
    
    cmd.append(str(test_path))
    
    success = run_command(cmd, f"Tests from file: {test_file}")
    if not success:
        sys.exit(1)


@cli.command()
def lint():
    """Run code linting."""
    commands = [
        (['python', '-m', 'flake8', 'src/', 'tests/'], "Flake8 linting"),
        (['python', '-m', 'black', '--check', 'src/', 'tests/'], "Black formatting check"),
        (['python', '-m', 'isort', '--check-only', 'src/', 'tests/'], "Import sorting check"),
    ]
    
    all_passed = True
    for cmd, description in commands:
        if not run_command(cmd, description):
            all_passed = False
    
    if not all_passed:
        click.echo(click.style("Linting failed", fg="red"))
        sys.exit(1)
    else:
        click.echo(click.style("All linting checks passed", fg="green"))


@cli.command()
def format():
    """Format code automatically."""
    commands = [
        (['python', '-m', 'black', 'src/', 'tests/'], "Black formatting"),
        (['python', '-m', 'isort', 'src/', 'tests/'], "Import sorting"),
    ]
    
    all_passed = True
    for cmd, description in commands:
        if not run_command(cmd, description):
            all_passed = False
    
    if not all_passed:
        click.echo(click.style("Code formatting failed", fg="red"))
        sys.exit(1)
    else:
        click.echo(click.style("Code formatting completed", fg="green"))


@cli.command()
def typecheck():
    """Run type checking with mypy."""
    cmd = ['python', '-m', 'mypy', 'src/']
    
    success = run_command(cmd, "Type checking")
    if not success:
        sys.exit(1)


@cli.command()
def validate():
    """Run full validation suite (lint, typecheck, tests)."""
    click.echo(click.style("Running full validation suite", fg="blue", bold=True))
    
    steps = [
        (lambda: run_command(['python', '-m', 'flake8', 'src/', 'tests/'], "Linting"), "Linting"),
        (lambda: run_command(['python', '-m', 'mypy', 'src/'], "Type checking"), "Type checking"),
        (lambda: run_command(['python', '-m', 'pytest', '-m', 'not slow and not integration', 'tests/'], "Fast tests"), "Fast tests"),
    ]
    
    for step_func, step_name in steps:
        click.echo(f"\n{click.style(f'Step: {step_name}', fg='cyan')}")
        if not step_func():
            click.echo(click.style(f"Validation failed at step: {step_name}", fg="red"))
            sys.exit(1)
    
    click.echo(click.style("\nAll validation steps passed!", fg="green", bold=True))


@cli.command()
def setup():
    """Set up the testing environment."""
    commands = [
        (['pip', 'install', '-e', '.'], "Installing package in development mode"),
        (['pip', 'install', '-r', 'requirements.txt'], "Installing requirements"),
    ]
    
    all_passed = True
    for cmd, description in commands:
        if not run_command(cmd, description):
            all_passed = False
    
    if not all_passed:
        click.echo(click.style("Setup failed", fg="red"))
        sys.exit(1)
    else:
        click.echo(click.style("Test environment setup completed", fg="green"))


@cli.command()
def clean():
    """Clean up test artifacts."""
    import shutil
    
    artifacts = [
        '.pytest_cache',
        'htmlcov',
        '.coverage',
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '.mypy_cache'
    ]
    
    for artifact in artifacts:
        if Path(artifact).exists():
            if Path(artifact).is_dir():
                shutil.rmtree(artifact)
                click.echo(f"Removed directory: {artifact}")
            else:
                Path(artifact).unlink()
                click.echo(f"Removed file: {artifact}")
    
    # Remove __pycache__ directories recursively
    for pycache_dir in Path('.').rglob('__pycache__'):
        shutil.rmtree(pycache_dir)
        click.echo(f"Removed: {pycache_dir}")
    
    # Remove .pyc files recursively
    for pyc_file in Path('.').rglob('*.pyc'):
        pyc_file.unlink()
        click.echo(f"Removed: {pyc_file}")
    
    click.echo(click.style("Cleanup completed", fg="green"))


if __name__ == '__main__':
    cli()
