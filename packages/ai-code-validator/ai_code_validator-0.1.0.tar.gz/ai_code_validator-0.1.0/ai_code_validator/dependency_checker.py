"""
Dependency checker that verifies packages actually exist.
"""

import re
import requests
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed


class DependencyChecker:
    """Checks if imported dependencies actually exist."""

    def __init__(self):
        self.issues = []

    def check_file(self, filepath: str, content: str) -> List[Dict[str, Any]]:
        """
        Check if dependencies in a file actually exist.

        Args:
            filepath: Path to the file
            content: File content as string

        Returns:
            List of issues found
        """
        self.issues = []

        if filepath.endswith('.py'):
            self._check_python_imports(content, filepath)
        elif filepath.endswith(('.js', '.jsx', '.ts', '.tsx')):
            self._check_javascript_imports(content, filepath)
        elif filepath.endswith('requirements.txt'):
            self._check_requirements(content, filepath)
        elif filepath.endswith('package.json'):
            self._check_package_json(content, filepath)

        return self.issues

    def _check_python_imports(self, content: str, filepath: str):
        """Check Python imports for hallucinated packages."""
        lines = content.split('\n')

        # Extract import statements
        import_pattern = r'^(?:from|import)\s+([a-zA-Z0-9_]+)'

        suspicious_packages = []
        for i, line in enumerate(lines, 1):
            match = re.match(import_pattern, line.strip())
            if match:
                package = match.group(1)
                # Skip standard library and common packages
                if package not in self._get_python_stdlib() and package not in ['numpy', 'pandas', 'requests', 'flask', 'django']:
                    suspicious_packages.append((package, i))

        # Check suspicious packages (in parallel for speed)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self._check_pypi_package, pkg): (pkg, line)
                      for pkg, line in suspicious_packages}

            for future in as_completed(futures):
                pkg, line = futures[future]
                exists = future.result()
                if not exists:
                    self.issues.append({
                        'type': 'hallucinated_dependency',
                        'severity': 'critical',
                        'message': f'Package "{pkg}" does not exist on PyPI',
                        'file': filepath,
                        'line': line,
                        'suggestion': 'AI may have hallucinated this package. This creates a "slopsquatting" security risk.'
                    })

    def _check_javascript_imports(self, content: str, filepath: str):
        """Check JavaScript imports for hallucinated packages."""
        lines = content.split('\n')

        # Extract import/require statements
        import_patterns = [
            r'(?:from|require\()\s*[\'"]([a-zA-Z0-9@/-]+)[\'"]',
            r'import\s+.*?\s+from\s+[\'"]([a-zA-Z0-9@/-]+)[\'"]',
        ]

        suspicious_packages = []
        for i, line in enumerate(lines, 1):
            for pattern in import_patterns:
                matches = re.findall(pattern, line)
                for package in matches:
                    # Skip relative imports and core modules
                    if not package.startswith('.') and not package.startswith('/'):
                        # Extract base package name
                        base_package = package.split('/')[0]
                        if base_package not in ['react', 'vue', 'angular', 'express', 'lodash', 'axios']:
                            suspicious_packages.append((base_package, i))

        # Check packages on npm
        checked = set()
        for pkg, line in suspicious_packages:
            if pkg not in checked:
                checked.add(pkg)
                if not self._check_npm_package(pkg):
                    self.issues.append({
                        'type': 'hallucinated_dependency',
                        'severity': 'critical',
                        'message': f'Package "{pkg}" does not exist on npm',
                        'file': filepath,
                        'line': line,
                        'suggestion': 'AI may have hallucinated this package. Verify before installing.'
                    })

    def _check_requirements(self, content: str, filepath: str):
        """Check requirements.txt for hallucinated packages."""
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (before ==, >=, etc.)
                package = re.split(r'[=<>!]', line)[0].strip()
                if package and not self._check_pypi_package(package):
                    self.issues.append({
                        'type': 'hallucinated_dependency',
                        'severity': 'critical',
                        'message': f'Package "{package}" does not exist on PyPI',
                        'file': filepath,
                        'line': i,
                        'suggestion': 'Remove this line or verify the package name'
                    })

    def _check_package_json(self, content: str, filepath: str):
        """Check package.json dependencies."""
        import json

        try:
            data = json.loads(content)
            dependencies = {**data.get('dependencies', {}), **data.get('devDependencies', {})}

            for package in dependencies:
                if not self._check_npm_package(package):
                    self.issues.append({
                        'type': 'hallucinated_dependency',
                        'severity': 'critical',
                        'message': f'Package "{package}" does not exist on npm',
                        'file': filepath,
                        'line': 0,
                        'suggestion': 'AI may have hallucinated this package'
                    })
        except json.JSONDecodeError:
            pass

    def _check_pypi_package(self, package: str) -> bool:
        """Check if a package exists on PyPI."""
        try:
            response = requests.head(f'https://pypi.org/pypi/{package}/json', timeout=3)
            return response.status_code == 200
        except:
            # If we can't check, assume it exists to avoid false positives
            return True

    def _check_npm_package(self, package: str) -> bool:
        """Check if a package exists on npm."""
        try:
            response = requests.head(f'https://registry.npmjs.org/{package}', timeout=3)
            return response.status_code == 200
        except:
            # If we can't check, assume it exists to avoid false positives
            return True

    def _get_python_stdlib(self) -> set:
        """Return common Python standard library modules."""
        return {
            'os', 'sys', 'json', 're', 'math', 'random', 'datetime', 'time',
            'collections', 'itertools', 'functools', 'typing', 'pathlib',
            'subprocess', 'threading', 'multiprocessing', 'asyncio', 'http',
            'urllib', 'email', 'html', 'xml', 'csv', 'sqlite3', 'logging',
            'unittest', 'argparse', 'configparser', 'io', 'gzip', 'zipfile',
            'hashlib', 'hmac', 'secrets', 'base64', 'struct', 'socket',
        }
