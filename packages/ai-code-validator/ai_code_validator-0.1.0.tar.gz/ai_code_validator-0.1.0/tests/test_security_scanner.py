"""
Unit tests for SecurityScanner module.
"""

import pytest
from ai_code_validator.security_scanner import SecurityScanner


class TestSecurityScanner:
    """Test cases for SecurityScanner class."""

    def test_scanner_initialization(self):
        """Test scanner can be initialized."""
        scanner = SecurityScanner()
        assert scanner.issues == []

    def test_sql_injection_detection_python(self):
        """Test SQL injection detection in Python."""
        code = '''
query = "SELECT * FROM users WHERE id = '" + user_id + "'"
query2 = f"INSERT INTO logs VALUES ('{data}')"
'''
        scanner = SecurityScanner()
        issues = scanner.scan_file('test.py', code)

        sql_issues = [i for i in issues if i['type'] == 'sql_injection']
        assert len(sql_issues) >= 2

    def test_sql_injection_detection_javascript(self):
        """Test SQL injection detection in JavaScript."""
        code = "const query = `SELECT * FROM users WHERE id = '${userId}'`;"
        scanner = SecurityScanner()
        issues = scanner.scan_file('test.js', code)

        assert len(issues) > 0
        assert any(i['type'] == 'sql_injection' for i in issues)

    def test_xss_detection(self):
        """Test XSS vulnerability detection."""
        code = '''
document.getElementById('content').innerHTML = userInput;
element.dangerouslySetInnerHTML = { __html: data };
document.write(content);
'''
        scanner = SecurityScanner()
        issues = scanner.scan_file('test.js', code)

        xss_issues = [i for i in issues if i['type'] == 'xss']
        assert len(xss_issues) >= 2

    def test_command_injection_detection(self):
        """Test command injection detection."""
        code = '''
import os
os.system(f"ls {user_input}")
eval(code)
exec(data)
'''
        scanner = SecurityScanner()
        issues = scanner.scan_file('test.py', code)

        command_issues = [i for i in issues if i['type'] == 'command_injection']
        assert len(command_issues) >= 3

    def test_hardcoded_secrets_detection(self):
        """Test hardcoded secrets detection."""
        code = '''
password = "super_secret_password"
api_key = "sk-1234567890abcdef"
secret_key = "my-secret-key-here"
aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"
'''
        scanner = SecurityScanner()
        issues = scanner.scan_file('test.py', code)

        secret_issues = [i for i in issues if i['type'] == 'hardcoded_secret']
        assert len(secret_issues) >= 3

    def test_no_false_positives_on_placeholders(self):
        """Test that placeholder values don't trigger false positives."""
        code = '''
# Example configuration
password = "your_password_here"
api_key = "example_key"
'''
        scanner = SecurityScanner()
        issues = scanner.scan_file('test.py', code)

        # Should skip comment lines and obvious placeholders
        secret_issues = [i for i in issues if i['type'] == 'hardcoded_secret']
        assert len(secret_issues) == 0

    def test_missing_input_validation(self):
        """Test detection of missing input validation."""
        code = '''
def process_request(request):
    user_id = request.params.get('user_id')
    data = request.body
    # No validation here
    result = database.query(user_id)
    return result
'''
        scanner = SecurityScanner()
        issues = scanner.scan_file('test.py', code)

        validation_issues = [i for i in issues if i['type'] == 'missing_input_validation']
        assert len(validation_issues) > 0

    def test_clean_code_no_issues(self):
        """Test that secure code passes without issues."""
        code = '''
def get_user(user_id: int):
    # Input validation
    if not isinstance(user_id, int):
        raise ValueError("Invalid user ID")

    # Parameterized query
    query = "SELECT * FROM users WHERE id = ?"
    return db.execute(query, (user_id,))
'''
        scanner = SecurityScanner()
        issues = scanner.scan_file('test.py', code)

        # Should have minimal critical issues
        critical_issues = [i for i in issues if i['severity'] == 'critical']
        assert len(critical_issues) == 0

    def test_severity_levels(self):
        """Test that appropriate severity levels are assigned."""
        code = '''
query = "SELECT * FROM users WHERE id = '" + user_id + "'"
eval(user_input)
api_key = "sk-123456"
'''
        scanner = SecurityScanner()
        issues = scanner.scan_file('test.py', code)

        # SQL injection and command injection should be critical
        critical = [i for i in issues if i['severity'] == 'critical']
        assert len(critical) >= 2

        # All issues should have valid severity
        valid_severities = ['critical', 'high', 'medium', 'low']
        for issue in issues:
            assert issue['severity'] in valid_severities

    def test_multiple_issues_same_line(self):
        """Test detection of multiple issues on same line."""
        code = 'result = eval("SELECT * FROM users WHERE id = \'" + user_id + "\'")'
        scanner = SecurityScanner()
        issues = scanner.scan_file('test.py', code)

        # Should detect both eval and SQL injection
        assert len(issues) >= 2

    def test_issue_suggestions(self):
        """Test that issues include helpful suggestions."""
        code = 'query = "SELECT * FROM users WHERE id = \'" + user_id + "\'"'
        scanner = SecurityScanner()
        issues = scanner.scan_file('test.py', code)

        for issue in issues:
            assert 'suggestion' in issue
            assert len(issue['suggestion']) > 0
