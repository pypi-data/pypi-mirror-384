"""
Confidence scorer that rates the quality of AI-generated code.
"""

from typing import List, Dict, Any


class ConfidenceScorer:
    """Calculates confidence scores for code quality."""

    def __init__(self):
        self.score = 100

    def calculate_score(self, all_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate confidence score based on issues found.

        Args:
            all_issues: List of all issues found by analyzers

        Returns:
            Dict with score and rating
        """
        self.score = 100

        # Severity weights
        severity_weights = {
            'critical': 25,
            'high': 15,
            'medium': 8,
            'low': 3,
        }

        # Type multipliers (some issues are more concerning)
        type_multipliers = {
            'hallucinated_dependency': 1.5,  # Very concerning
            'sql_injection': 1.3,
            'command_injection': 1.3,
            'hardcoded_secret': 1.2,
        }

        # Calculate deductions
        for issue in all_issues:
            severity = issue.get('severity', 'low')
            issue_type = issue.get('type', '')

            deduction = severity_weights.get(severity, 3)

            # Apply type multiplier if applicable
            multiplier = type_multipliers.get(issue_type, 1.0)
            deduction = int(deduction * multiplier)

            self.score -= deduction

        # Ensure score stays within 0-100
        self.score = max(0, min(100, self.score))

        # Determine rating
        rating = self._get_rating(self.score)

        # Generate recommendation
        recommendation = self._get_recommendation(self.score, all_issues)

        return {
            'score': self.score,
            'rating': rating,
            'recommendation': recommendation,
            'total_issues': len(all_issues),
            'critical_issues': len([i for i in all_issues if i.get('severity') == 'critical']),
            'high_issues': len([i for i in all_issues if i.get('severity') == 'high']),
            'medium_issues': len([i for i in all_issues if i.get('severity') == 'medium']),
            'low_issues': len([i for i in all_issues if i.get('severity') == 'low']),
        }

    def _get_rating(self, score: int) -> str:
        """Get text rating based on score."""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 75:
            return "GOOD"
        elif score >= 60:
            return "FAIR"
        elif score >= 40:
            return "POOR"
        else:
            return "CRITICAL"

    def _get_recommendation(self, score: int, issues: List[Dict[str, Any]]) -> str:
        """Generate recommendation based on score and issues."""
        if score >= 90:
            return "Code looks good! Only minor issues found."

        if score >= 75:
            return "Code is mostly safe but has some issues to address."

        if score >= 60:
            return "Review and fix issues before committing."

        # Check for specific critical issues
        critical_types = [i['type'] for i in issues if i.get('severity') == 'critical']

        if 'hallucinated_dependency' in critical_types:
            return "⚠️  CRITICAL: Hallucinated dependencies detected! Do NOT install these packages."

        if 'sql_injection' in critical_types or 'command_injection' in critical_types:
            return "⚠️  CRITICAL: Security vulnerabilities detected! Fix before deployment."

        return "⚠️  Multiple serious issues found. Careful review required."
