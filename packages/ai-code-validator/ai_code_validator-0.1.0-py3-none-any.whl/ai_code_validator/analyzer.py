"""
Code analyzer that detects common AI-generated code issues.
"""

import ast
import re
from typing import List, Dict, Any


class CodeAnalyzer:
    """Analyzes code for AI-specific issues."""

    def __init__(self):
        self.issues = []

    def analyze_file(self, filepath: str, content: str) -> List[Dict[str, Any]]:
        """
        Analyze a file for AI-generated code issues.

        Args:
            filepath: Path to the file
            content: File content as string

        Returns:
            List of issues found
        """
        self.issues = []

        # Determine language and run appropriate checks
        if filepath.endswith('.py'):
            self._analyze_python(content, filepath)
        elif filepath.endswith(('.js', '.jsx', '.ts', '.tsx')):
            self._analyze_javascript(content, filepath)
        elif filepath.endswith(('.java', '.kt')):
            self._analyze_java(content, filepath)

        return self.issues

    def _analyze_python(self, content: str, filepath: str):
        """Analyze Python code for common AI mistakes."""
        try:
            tree = ast.parse(content)

            # Check for suspicious function calls
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    self._check_suspicious_call(node, filepath)

            # Check for common AI hallucination patterns
            self._check_outdated_patterns_python(content, filepath)

        except SyntaxError as e:
            self.issues.append({
                'type': 'syntax_error',
                'severity': 'high',
                'message': f'Syntax error (AI may have generated invalid code): {str(e)}',
                'file': filepath,
                'line': e.lineno if hasattr(e, 'lineno') else 0
            })

    def _check_suspicious_call(self, node: ast.Call, filepath: str):
        """Check for potentially hallucinated function calls."""
        # Common AI hallucination patterns
        suspicious_patterns = [
            'updateProfile',
            'handleSubmit',
            'processData',
            'validateInput',
            'connectToDatabase',
        ]

        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            if any(pattern in func_name for pattern in suspicious_patterns):
                self.issues.append({
                    'type': 'suspicious_function',
                    'severity': 'medium',
                    'message': f'Potentially hallucinated function: {func_name}. Verify this function exists.',
                    'file': filepath,
                    'line': node.lineno,
                    'suggestion': f'Check if {func_name} is defined in your codebase or imported library'
                })

    def _check_outdated_patterns_python(self, content: str, filepath: str):
        """Check for outdated Python patterns."""
        lines = content.split('\n')

        # Check for outdated imports
        outdated_imports = {
            'from __future__ import print_function': 'Python 2 style - not needed in Python 3',
            'import optparse': 'Deprecated - use argparse instead',
            'import imp': 'Deprecated - use importlib instead',
        }

        for i, line in enumerate(lines, 1):
            for pattern, message in outdated_imports.items():
                if pattern in line:
                    self.issues.append({
                        'type': 'outdated_pattern',
                        'severity': 'low',
                        'message': f'Outdated pattern detected: {message}',
                        'file': filepath,
                        'line': i,
                        'suggestion': 'AI may have used outdated training data'
                    })

    def _analyze_javascript(self, content: str, filepath: str):
        """Analyze JavaScript/TypeScript code for common AI mistakes."""
        lines = content.split('\n')

        # Check for suspicious API calls
        api_patterns = [
            r'fetch\([\'"]\/api\/[^\'"]+[\'"]',
            r'axios\.(get|post|put|delete)\([\'"]\/api\/[^\'"]+[\'"]',
        ]

        for i, line in enumerate(lines, 1):
            for pattern in api_patterns:
                if re.search(pattern, line):
                    self.issues.append({
                        'type': 'suspicious_api',
                        'severity': 'medium',
                        'message': 'API endpoint detected - verify this endpoint exists',
                        'file': filepath,
                        'line': i,
                        'suggestion': 'AI may have hallucinated this API endpoint'
                    })

        # Check for outdated patterns
        self._check_outdated_patterns_js(content, filepath)

    def _check_outdated_patterns_js(self, content: str, filepath: str):
        """Check for outdated JavaScript patterns."""
        lines = content.split('\n')

        outdated_patterns = {
            r'componentWillMount': 'Deprecated React lifecycle method',
            r'componentWillReceiveProps': 'Deprecated React lifecycle method',
            r'componentWillUpdate': 'Deprecated React lifecycle method',
            r'findDOMNode': 'Deprecated React method',
        }

        for i, line in enumerate(lines, 1):
            for pattern, message in outdated_patterns.items():
                if re.search(pattern, line):
                    self.issues.append({
                        'type': 'outdated_pattern',
                        'severity': 'medium',
                        'message': f'Outdated pattern: {message}',
                        'file': filepath,
                        'line': i,
                        'suggestion': 'Use modern alternatives instead'
                    })

    def _analyze_java(self, content: str, filepath: str):
        """Analyze Java/Kotlin code for common AI mistakes."""
        lines = content.split('\n')

        # Check for outdated patterns
        for i, line in enumerate(lines, 1):
            if 'new Date()' in line:
                self.issues.append({
                    'type': 'outdated_pattern',
                    'severity': 'low',
                    'message': 'Using legacy Date class',
                    'file': filepath,
                    'line': i,
                    'suggestion': 'Consider using java.time API (Java 8+) instead'
                })
