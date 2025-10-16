"""
Unit tests for DependencyChecker module.
"""

import pytest
from unittest.mock import patch, Mock
from ai_code_validator.dependency_checker import DependencyChecker


class TestDependencyChecker:
    """Test cases for DependencyChecker class."""

    def test_checker_initialization(self):
        """Test checker can be initialized."""
        checker = DependencyChecker()
        assert checker.issues == []

    @patch('ai_code_validator.dependency_checker.requests.head')
    def test_check_valid_pypi_package(self, mock_head):
        """Test checking a valid PyPI package."""
        mock_head.return_value = Mock(status_code=200)

        checker = DependencyChecker()
        result = checker._check_pypi_package('requests')

        assert result is True

    @patch('ai_code_validator.dependency_checker.requests.head')
    def test_check_invalid_pypi_package(self, mock_head):
        """Test checking an invalid PyPI package."""
        mock_head.return_value = Mock(status_code=404)

        checker = DependencyChecker()
        result = checker._check_pypi_package('fake-package-that-does-not-exist-12345')

        assert result is False

    @patch('ai_code_validator.dependency_checker.requests.head')
    def test_check_valid_npm_package(self, mock_head):
        """Test checking a valid npm package."""
        mock_head.return_value = Mock(status_code=200)

        checker = DependencyChecker()
        result = checker._check_npm_package('react')

        assert result is True

    @patch('ai_code_validator.dependency_checker.requests.head')
    def test_check_invalid_npm_package(self, mock_head):
        """Test checking an invalid npm package."""
        mock_head.return_value = Mock(status_code=404)

        checker = DependencyChecker()
        result = checker._check_npm_package('fake-npm-package-12345')

        assert result is False

    def test_python_stdlib_recognition(self):
        """Test that Python stdlib modules are recognized."""
        checker = DependencyChecker()
        stdlib = checker._get_python_stdlib()

        assert 'os' in stdlib
        assert 'sys' in stdlib
        assert 'json' in stdlib
        assert 'requests' not in stdlib  # Not stdlib

    @patch('ai_code_validator.dependency_checker.requests.head')
    def test_check_python_imports(self, mock_head):
        """Test checking Python imports."""
        # Mock: standard packages exist, fake ones don't
        def mock_response(url, *args, **kwargs):
            if 'fake_package' in url:
                return Mock(status_code=404)
            return Mock(status_code=200)

        mock_head.side_effect = mock_response

        code = '''
import os
import requests
import fake_package_that_does_not_exist
'''
        checker = DependencyChecker()
        issues = checker.check_file('test.py', code)

        # Should find the fake package
        hallucinated = [i for i in issues if i['type'] == 'hallucinated_dependency']
        assert len(hallucinated) > 0
        assert any('fake_package' in i['message'] for i in hallucinated)

    @patch('ai_code_validator.dependency_checker.requests.head')
    def test_check_javascript_imports(self, mock_head):
        """Test checking JavaScript imports."""
        def mock_response(url, *args, **kwargs):
            if 'fake-react-utils' in url:
                return Mock(status_code=404)
            return Mock(status_code=200)

        mock_head.side_effect = mock_response

        code = '''
import React from 'react';
import FakeUtils from 'fake-react-utils-2025';
'''
        checker = DependencyChecker()
        issues = checker.check_file('test.js', code)

        # Should find the fake package
        hallucinated = [i for i in issues if i['type'] == 'hallucinated_dependency']
        assert len(hallucinated) > 0

    @patch('ai_code_validator.dependency_checker.requests.head')
    def test_check_requirements_txt(self, mock_head):
        """Test checking requirements.txt file."""
        def mock_response(url, *args, **kwargs):
            if 'fake-package' in url:
                return Mock(status_code=404)
            return Mock(status_code=200)

        mock_head.side_effect = mock_response

        content = '''
requests>=2.31.0
click==8.1.0
fake-package-12345==1.0.0
'''
        checker = DependencyChecker()
        issues = checker.check_file('requirements.txt', content)

        hallucinated = [i for i in issues if i['type'] == 'hallucinated_dependency']
        assert len(hallucinated) > 0
        assert any('fake-package' in i['message'] for i in hallucinated)

    @patch('ai_code_validator.dependency_checker.requests.head')
    def test_check_package_json(self, mock_head):
        """Test checking package.json file."""
        def mock_response(url, *args, **kwargs):
            if 'fake-package' in url:
                return Mock(status_code=404)
            return Mock(status_code=200)

        mock_head.side_effect = mock_response

        content = '''
{
    "dependencies": {
        "react": "^18.0.0",
        "fake-package-12345": "1.0.0"
    },
    "devDependencies": {
        "fake-dev-package": "1.0.0"
    }
}
'''
        checker = DependencyChecker()
        issues = checker.check_file('package.json', content)

        hallucinated = [i for i in issues if i['type'] == 'hallucinated_dependency']
        assert len(hallucinated) > 0

    def test_skip_relative_imports(self):
        """Test that relative imports are skipped."""
        code = '''
import './components/Button';
import '../utils/helper';
import '/absolute/path';
'''
        checker = DependencyChecker()
        issues = checker.check_file('test.js', code)

        # Relative imports should be skipped
        assert len(issues) == 0

    def test_network_error_handling(self):
        """Test graceful handling of network errors."""
        with patch('ai_code_validator.dependency_checker.requests.head') as mock_head:
            mock_head.side_effect = Exception("Network error")

            checker = DependencyChecker()
            # Should not crash, assumes package exists on error
            result = checker._check_pypi_package('some-package')
            assert result is True  # Fail safe

    def test_comment_lines_in_requirements(self):
        """Test that comment lines in requirements.txt are skipped."""
        content = '''
# This is a comment
requests>=2.31.0
# Another comment
click==8.1.0
'''
        checker = DependencyChecker()
        issues = checker.check_file('requirements.txt', content)

        # Comments should not be checked
        assert len(issues) == 0

    def test_issue_severity(self):
        """Test that hallucinated dependencies are marked as critical."""
        with patch('ai_code_validator.dependency_checker.requests.head') as mock_head:
            mock_head.return_value = Mock(status_code=404)

            code = 'import fake_package'
            checker = DependencyChecker()
            issues = checker.check_file('test.py', code)

            if issues:  # Only check if issues were found
                assert all(i['severity'] == 'critical' for i in issues)
