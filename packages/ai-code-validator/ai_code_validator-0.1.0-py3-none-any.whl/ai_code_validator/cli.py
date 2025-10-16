"""
Command-line interface for AI Code Validator.
"""

import click
import os
import sys
from pathlib import Path
from typing import List

from .analyzer import CodeAnalyzer
from .dependency_checker import DependencyChecker
from .security_scanner import SecurityScanner
from .scorer import ConfidenceScorer
from .reporter import Reporter


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """
    AI Code Validator - Catch AI-generated code mistakes before they cause problems.

    Analyzes code for common AI mistakes, hallucinated dependencies,
    and security vulnerabilities.
    """
    pass


@cli.command()
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text',
              help='Output format (text or json)')
@click.option('--severity', '-s', type=click.Choice(['all', 'critical', 'high', 'medium', 'low']),
              default='all', help='Minimum severity level to report')
@click.option('--no-deps', is_flag=True, help='Skip dependency checking (faster)')
def check(paths, format, severity, no_deps):
    """
    Check files or directories for AI-generated code issues.

    Examples:
        aivalidate check myfile.py
        aivalidate check src/
        aivalidate check . --format json
        aivalidate check app.py --severity critical
    """
    if not paths:
        click.echo("Error: Please provide at least one file or directory to check.", err=True)
        sys.exit(1)

    # Collect all files to check
    files_to_check = []
    for path in paths:
        path_obj = Path(path)
        if path_obj.is_file():
            files_to_check.append(path_obj)
        elif path_obj.is_dir():
            # Find all code files in directory
            files_to_check.extend(_find_code_files(path_obj))

    if not files_to_check:
        click.echo("No code files found to check.", err=True)
        sys.exit(1)

    click.echo(f"Checking {len(files_to_check)} file(s)...\n")

    # Run all checks
    all_issues = []

    for filepath in files_to_check:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Run analyzers
            analyzer = CodeAnalyzer()
            issues = analyzer.analyze_file(str(filepath), content)
            all_issues.extend(issues)

            # Check dependencies
            if not no_deps:
                dep_checker = DependencyChecker()
                dep_issues = dep_checker.check_file(str(filepath), content)
                all_issues.extend(dep_issues)

            # Security scan
            scanner = SecurityScanner()
            sec_issues = scanner.scan_file(str(filepath), content)
            all_issues.extend(sec_issues)

        except Exception as e:
            click.echo(f"Warning: Could not process {filepath}: {str(e)}", err=True)

    # Filter by severity if specified
    if severity != 'all':
        severity_order = ['critical', 'high', 'medium', 'low']
        min_index = severity_order.index(severity)
        all_issues = [
            issue for issue in all_issues
            if severity_order.index(issue.get('severity', 'low')) <= min_index
        ]

    # Calculate score
    scorer = ConfidenceScorer()
    score_data = scorer.calculate_score(all_issues)

    # Generate report
    reporter = Reporter(format=format)
    reporter.report(all_issues, score_data)

    # Exit with error code if critical issues found
    if score_data['critical_issues'] > 0:
        sys.exit(1)


@cli.command()
def install_hook():
    """
    Install git pre-commit hook to automatically validate code.

    This will create a pre-commit hook in .git/hooks/ that runs
    aivalidate on staged files before each commit.
    """
    # Check if we're in a git repo
    if not os.path.exists('.git'):
        click.echo("Error: Not in a git repository.", err=True)
        sys.exit(1)

    hook_path = Path('.git/hooks/pre-commit')

    # Create hook script
    hook_content = """#!/bin/bash
# AI Code Validator pre-commit hook

echo "Running AI Code Validator..."

# Get list of staged Python and JavaScript files
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(py|js|jsx|ts|tsx)$')

if [ -z "$FILES" ]; then
    echo "No code files to check."
    exit 0
fi

# Run validator on staged files
aivalidate check $FILES --severity high

# Get exit code
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ AI Code Validator found critical issues!"
    echo "Please fix the issues above or use 'git commit --no-verify' to skip validation."
    exit 1
fi

echo "✅ AI Code Validator passed!"
exit 0
"""

    try:
        hook_path.write_text(hook_content)
        hook_path.chmod(0o755)  # Make executable
        click.echo(f"✅ Pre-commit hook installed successfully at {hook_path}")
        click.echo("\nThe validator will now run automatically on every commit.")
        click.echo("To bypass: git commit --no-verify")
    except Exception as e:
        click.echo(f"Error installing hook: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def examples():
    """Show example usage and common patterns."""
    examples_text = """
🤖 AI Code Validator - Examples

BASIC USAGE:
  Check a single file:
    $ aivalidate check myfile.py

  Check multiple files:
    $ aivalidate check app.py utils.py

  Check entire directory:
    $ aivalidate check src/

  Check current directory:
    $ aivalidate check .

OUTPUT FORMATS:
  JSON output (for CI/CD):
    $ aivalidate check . --format json

  Only show critical issues:
    $ aivalidate check . --severity critical

  Only show high and critical:
    $ aivalidate check . --severity high

SPEED OPTIONS:
  Skip dependency checks (faster):
    $ aivalidate check . --no-deps

GIT INTEGRATION:
  Install pre-commit hook:
    $ aivalidate install-hook

  Check only staged files:
    $ git diff --cached --name-only | xargs aivalidate check

CI/CD INTEGRATION:
  # In your CI pipeline (e.g., GitHub Actions)
  - name: Validate AI-generated code
    run: |
      pip install ai-code-validator
      aivalidate check . --format json --severity high

WHAT IT DETECTS:
  ✓ Hallucinated functions and APIs
  ✓ Non-existent dependencies (20% of AI code has these!)
  ✓ SQL injection vulnerabilities
  ✓ Missing input validation
  ✓ XSS vulnerabilities
  ✓ Command injection risks
  ✓ Hardcoded secrets
  ✓ Outdated patterns from old training data

For more info: https://github.com/yourusername/ai-code-validator
"""
    click.echo(examples_text)


def _find_code_files(directory: Path) -> List[Path]:
    """Find all code files in a directory recursively."""
    code_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.kt'}
    code_files = []

    for item in directory.rglob('*'):
        if item.is_file() and item.suffix in code_extensions:
            # Skip common directories
            if any(part in item.parts for part in ['node_modules', '.git', '__pycache__', 'venv', 'env']):
                continue
            code_files.append(item)

    return code_files


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
