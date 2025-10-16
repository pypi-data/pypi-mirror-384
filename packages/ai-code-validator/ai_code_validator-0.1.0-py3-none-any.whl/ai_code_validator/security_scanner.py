"""
Security scanner that detects common vulnerabilities in AI-generated code.
"""

import re
from typing import List, Dict, Any


class SecurityScanner:
    """Scans code for security vulnerabilities."""

    def __init__(self):
        self.issues = []

    def scan_file(self, filepath: str, content: str) -> List[Dict[str, Any]]:
        """
        Scan a file for security vulnerabilities.

        Args:
            filepath: Path to the file
            content: File content as string

        Returns:
            List of security issues found
        """
        self.issues = []

        # Run security checks
        self._check_sql_injection(content, filepath)
        self._check_xss(content, filepath)
        self._check_command_injection(content, filepath)
        self._check_hardcoded_secrets(content, filepath)
        self._check_input_validation(content, filepath)

        return self.issues

    def _check_sql_injection(self, content: str, filepath: str):
        """Check for SQL injection vulnerabilities."""
        lines = content.split('\n')

        # Patterns that indicate SQL injection risk
        sql_patterns = [
            # String concatenation in SQL queries
            (r'["\']SELECT.*?\+.*?["\']', 'String concatenation in SQL query'),
            (r'["\']INSERT.*?\+.*?["\']', 'String concatenation in SQL query'),
            (r'["\']UPDATE.*?\+.*?["\']', 'String concatenation in SQL query'),
            (r'["\']DELETE.*?\+.*?["\']', 'String concatenation in SQL query'),
            (r'f["\']SELECT.*?\{.*?\}', 'F-string in SQL query (potential injection)'),
            (r'f["\']INSERT.*?\{.*?\}', 'F-string in SQL query (potential injection)'),
            # JavaScript template literals
            (r'`SELECT.*?\$\{.*?\}`', 'Template literal in SQL query'),
            (r'`INSERT.*?\$\{.*?\}`', 'Template literal in SQL query'),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, message in sql_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.issues.append({
                        'type': 'sql_injection',
                        'severity': 'critical',
                        'message': f'Potential SQL injection: {message}',
                        'file': filepath,
                        'line': i,
                        'suggestion': 'Use parameterized queries or prepared statements instead'
                    })

    def _check_xss(self, content: str, filepath: str):
        """Check for XSS vulnerabilities."""
        lines = content.split('\n')

        xss_patterns = [
            (r'innerHTML\s*=', 'Direct innerHTML assignment can lead to XSS'),
            (r'dangerouslySetInnerHTML', 'Using dangerouslySetInnerHTML without sanitization'),
            (r'document\.write\(', 'document.write() can lead to XSS'),
            (r'eval\(', 'eval() is dangerous and can lead to code injection'),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, message in xss_patterns:
                if re.search(pattern, line):
                    self.issues.append({
                        'type': 'xss',
                        'severity': 'high',
                        'message': f'Potential XSS vulnerability: {message}',
                        'file': filepath,
                        'line': i,
                        'suggestion': 'Sanitize user input and use safe alternatives'
                    })

    def _check_command_injection(self, content: str, filepath: str):
        """Check for command injection vulnerabilities."""
        lines = content.split('\n')

        command_patterns = [
            (r'os\.system\(', 'os.system() with user input can lead to command injection'),
            (r'subprocess\.(call|run|Popen)\([^)]*shell\s*=\s*True', 'shell=True with user input is dangerous'),
            (r'eval\(', 'eval() can execute arbitrary code'),
            (r'exec\(', 'exec() can execute arbitrary code'),
            (r'child_process\.exec\(', 'child_process.exec() can lead to command injection'),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, message in command_patterns:
                if re.search(pattern, line):
                    self.issues.append({
                        'type': 'command_injection',
                        'severity': 'critical',
                        'message': f'Potential command injection: {message}',
                        'file': filepath,
                        'line': i,
                        'suggestion': 'Avoid shell=True and validate/sanitize all inputs'
                    })

    def _check_hardcoded_secrets(self, content: str, filepath: str):
        """Check for hardcoded secrets."""
        lines = content.split('\n')

        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key'),
            (r'secret[_-]?key\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret key'),
            (r'token\s*=\s*["\'][a-zA-Z0-9]{20,}["\']', 'Hardcoded token'),
            (r'aws[_-]?access[_-]?key', 'AWS access key detected'),
        ]

        for i, line in enumerate(lines, 1):
            # Skip comments and obvious placeholders
            if line.strip().startswith('#') or 'your_' in line.lower() or 'example' in line.lower():
                continue

            for pattern, message in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.issues.append({
                        'type': 'hardcoded_secret',
                        'severity': 'critical',
                        'message': f'Potential hardcoded secret: {message}',
                        'file': filepath,
                        'line': i,
                        'suggestion': 'Use environment variables or a secrets manager'
                    })

    def _check_input_validation(self, content: str, filepath: str):
        """Check for missing input validation (AI's most common mistake)."""
        lines = content.split('\n')

        # Look for functions that accept user input without validation
        for i, line in enumerate(lines, 1):
            # Check for request handlers without validation
            if any(keyword in line for keyword in ['request.', 'req.body', 'req.query', 'req.params']):
                # Look ahead to see if there's validation
                context_start = max(0, i - 5)
                context_end = min(len(lines), i + 10)
                context = '\n'.join(lines[context_start:context_end])

                validation_keywords = ['validate', 'sanitize', 'check', 'assert', 'isinstance', 'if not', 'raise']

                if not any(keyword in context.lower() for keyword in validation_keywords):
                    self.issues.append({
                        'type': 'missing_input_validation',
                        'severity': 'high',
                        'message': 'User input without validation detected',
                        'file': filepath,
                        'line': i,
                        'suggestion': 'AI often omits input validation. Add validation before using user input.'
                    })
                    break  # Only report once per function
