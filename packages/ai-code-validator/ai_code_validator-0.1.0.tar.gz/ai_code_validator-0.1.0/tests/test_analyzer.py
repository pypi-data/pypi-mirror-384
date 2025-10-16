"""
Unit tests for CodeAnalyzer module.
"""

import pytest
from ai_code_validator.analyzer import CodeAnalyzer


class TestCodeAnalyzer:
    """Test cases for CodeAnalyzer class."""

    def test_analyzer_initialization(self):
        """Test analyzer can be initialized."""
        analyzer = CodeAnalyzer()
        assert analyzer.issues == []

    def test_analyze_python_file(self, sample_python_code):
        """Test Python code analysis."""
        analyzer = CodeAnalyzer()
        issues = analyzer.analyze_file('test.py', sample_python_code)

        assert len(issues) > 0
        assert any(issue['type'] == 'suspicious_function' for issue in issues)

    def test_analyze_good_python_file(self, sample_good_python_code):
        """Test that good Python code passes without issues."""
        analyzer = CodeAnalyzer()
        issues = analyzer.analyze_file('test.py', sample_good_python_code)

        # Good code should have minimal or no issues
        assert len(issues) == 0

    def test_analyze_javascript_file(self, sample_javascript_code):
        """Test JavaScript code analysis."""
        analyzer = CodeAnalyzer()
        issues = analyzer.analyze_file('test.js', sample_javascript_code)

        assert len(issues) > 0
        # Should detect suspicious API call
        assert any(issue['type'] == 'suspicious_api' for issue in issues)

    def test_detect_outdated_python_patterns(self):
        """Test detection of outdated Python patterns."""
        code = "from __future__ import print_function\nimport optparse"
        analyzer = CodeAnalyzer()
        issues = analyzer.analyze_file('old.py', code)

        assert len(issues) >= 2
        assert any(issue['type'] == 'outdated_pattern' for issue in issues)

    def test_detect_outdated_javascript_patterns(self):
        """Test detection of outdated JavaScript patterns."""
        code = '''
        class MyComponent extends React.Component {
            componentWillMount() {
                console.log("mounting");
            }
        }
        '''
        analyzer = CodeAnalyzer()
        issues = analyzer.analyze_file('old.jsx', code)

        assert len(issues) > 0
        assert any('componentWillMount' in issue['message'] for issue in issues)

    def test_syntax_error_detection(self):
        """Test that syntax errors are caught."""
        code = "def invalid_function(\n    pass"  # Incomplete function
        analyzer = CodeAnalyzer()
        issues = analyzer.analyze_file('broken.py', code)

        assert len(issues) > 0
        assert any(issue['type'] == 'syntax_error' for issue in issues)

    def test_hallucinated_function_detection(self):
        """Test detection of potentially hallucinated functions."""
        code = '''
user.updateProfile(data)
model.validateInput(input_data)
db.connectToDatabase(config)
'''
        analyzer = CodeAnalyzer()
        issues = analyzer.analyze_file('test.py', code)

        # Should detect suspicious function patterns
        suspicious_issues = [i for i in issues if i['type'] == 'suspicious_function']
        assert len(suspicious_issues) > 0

    def test_empty_file(self):
        """Test analysis of empty file."""
        analyzer = CodeAnalyzer()
        issues = analyzer.analyze_file('empty.py', '')

        # Empty file should not cause errors
        assert isinstance(issues, list)

    def test_java_analysis(self):
        """Test Java code analysis."""
        code = '''
        import java.util.Date;

        public class Test {
            public void test() {
                Date now = new Date();
            }
        }
        '''
        analyzer = CodeAnalyzer()
        issues = analyzer.analyze_file('Test.java', code)

        assert len(issues) > 0
        assert any('Date' in issue['message'] for issue in issues)

    def test_line_number_accuracy(self, sample_python_code):
        """Test that line numbers are accurate."""
        analyzer = CodeAnalyzer()
        issues = analyzer.analyze_file('test.py', sample_python_code)

        for issue in issues:
            assert issue['line'] >= 0
            assert 'file' in issue
            assert issue['file'] == 'test.py'

    def test_issue_structure(self, sample_python_code):
        """Test that issues have required fields."""
        analyzer = CodeAnalyzer()
        issues = analyzer.analyze_file('test.py', sample_python_code)

        for issue in issues:
            assert 'type' in issue
            assert 'severity' in issue
            assert 'message' in issue
            assert 'file' in issue
            assert 'line' in issue
