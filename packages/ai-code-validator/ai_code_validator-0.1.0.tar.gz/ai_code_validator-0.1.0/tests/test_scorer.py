"""
Unit tests for ConfidenceScorer module.
"""

import pytest
from ai_code_validator.scorer import ConfidenceScorer


class TestConfidenceScorer:
    """Test cases for ConfidenceScorer class."""

    def test_scorer_initialization(self):
        """Test scorer can be initialized."""
        scorer = ConfidenceScorer()
        assert scorer.score == 100

    def test_perfect_score_no_issues(self):
        """Test perfect score when no issues found."""
        scorer = ConfidenceScorer()
        result = scorer.calculate_score([])

        assert result['score'] == 100
        assert result['rating'] == 'EXCELLENT'
        assert result['total_issues'] == 0
        assert result['critical_issues'] == 0

    def test_score_with_critical_issues(self):
        """Test score calculation with critical issues."""
        issues = [
            {'type': 'sql_injection', 'severity': 'critical'},
            {'type': 'command_injection', 'severity': 'critical'},
        ]
        scorer = ConfidenceScorer()
        result = scorer.calculate_score(issues)

        assert result['score'] < 100
        assert result['critical_issues'] == 2
        assert result['total_issues'] == 2

    def test_score_with_mixed_severities(self):
        """Test score with issues of different severities."""
        issues = [
            {'type': 'sql_injection', 'severity': 'critical'},
            {'type': 'xss', 'severity': 'high'},
            {'type': 'suspicious_function', 'severity': 'medium'},
            {'type': 'outdated_pattern', 'severity': 'low'},
        ]
        scorer = ConfidenceScorer()
        result = scorer.calculate_score(issues)

        assert result['score'] < 100
        assert result['score'] > 0
        assert result['critical_issues'] == 1
        assert result['high_issues'] == 1
        assert result['medium_issues'] == 1
        assert result['low_issues'] == 1

    def test_hallucinated_dependency_multiplier(self):
        """Test that hallucinated dependencies get higher weight."""
        issues_with_hallucination = [
            {'type': 'hallucinated_dependency', 'severity': 'critical'},
        ]
        issues_without = [
            {'type': 'other_issue', 'severity': 'critical'},
        ]

        scorer1 = ConfidenceScorer()
        score1 = scorer1.calculate_score(issues_with_hallucination)

        scorer2 = ConfidenceScorer()
        score2 = scorer2.calculate_score(issues_without)

        # Hallucinated dependency should result in lower score
        assert score1['score'] < score2['score']

    def test_rating_levels(self):
        """Test different rating levels."""
        # Excellent (90-100)
        scorer = ConfidenceScorer()
        assert scorer._get_rating(95) == 'EXCELLENT'
        assert scorer._get_rating(90) == 'EXCELLENT'

        # Good (75-89)
        assert scorer._get_rating(80) == 'GOOD'
        assert scorer._get_rating(75) == 'GOOD'

        # Fair (60-74)
        assert scorer._get_rating(65) == 'FAIR'
        assert scorer._get_rating(60) == 'FAIR'

        # Poor (40-59)
        assert scorer._get_rating(50) == 'POOR'
        assert scorer._get_rating(40) == 'POOR'

        # Critical (0-39)
        assert scorer._get_rating(30) == 'CRITICAL'
        assert scorer._get_rating(0) == 'CRITICAL'

    def test_score_bounds(self):
        """Test that score stays within 0-100 bounds."""
        # Many critical issues should not go below 0
        issues = [
            {'type': 'critical_issue', 'severity': 'critical'}
            for _ in range(20)
        ]
        scorer = ConfidenceScorer()
        result = scorer.calculate_score(issues)

        assert result['score'] >= 0
        assert result['score'] <= 100

    def test_recommendations(self):
        """Test recommendation generation."""
        # No issues
        scorer = ConfidenceScorer()
        result = scorer.calculate_score([])
        assert 'good' in result['recommendation'].lower()

        # Critical hallucinated dependency
        issues = [{'type': 'hallucinated_dependency', 'severity': 'critical'}]
        scorer = ConfidenceScorer()
        result = scorer.calculate_score(issues)
        assert 'hallucinated' in result['recommendation'].lower()

        # Security vulnerabilities
        issues = [{'type': 'sql_injection', 'severity': 'critical'}]
        scorer = ConfidenceScorer()
        result = scorer.calculate_score(issues)
        assert 'security' in result['recommendation'].lower()

    def test_issue_counting(self):
        """Test accurate issue counting by severity."""
        issues = [
            {'type': 'issue1', 'severity': 'critical'},
            {'type': 'issue2', 'severity': 'critical'},
            {'type': 'issue3', 'severity': 'high'},
            {'type': 'issue4', 'severity': 'medium'},
            {'type': 'issue5', 'severity': 'medium'},
            {'type': 'issue6', 'severity': 'low'},
        ]
        scorer = ConfidenceScorer()
        result = scorer.calculate_score(issues)

        assert result['total_issues'] == 6
        assert result['critical_issues'] == 2
        assert result['high_issues'] == 1
        assert result['medium_issues'] == 2
        assert result['low_issues'] == 1

    def test_score_consistency(self):
        """Test that same issues produce same score."""
        issues = [
            {'type': 'sql_injection', 'severity': 'critical'},
            {'type': 'xss', 'severity': 'high'},
        ]

        scorer1 = ConfidenceScorer()
        result1 = scorer1.calculate_score(issues)

        scorer2 = ConfidenceScorer()
        result2 = scorer2.calculate_score(issues)

        assert result1['score'] == result2['score']
