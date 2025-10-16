"""
Reporter that formats and displays validation results.
"""

from typing import List, Dict, Any
import json
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


class Reporter:
    """Formats and displays validation results."""

    def __init__(self, format: str = 'text'):
        """
        Initialize reporter.

        Args:
            format: Output format ('text' or 'json')
        """
        self.format = format

    def report(self, issues: List[Dict[str, Any]], score_data: Dict[str, Any]):
        """
        Generate report from issues and score.

        Args:
            issues: List of all issues found
            score_data: Score calculation results
        """
        if self.format == 'json':
            self._report_json(issues, score_data)
        else:
            self._report_text(issues, score_data)

    def _report_text(self, issues: List[Dict[str, Any]], score_data: Dict[str, Any]):
        """Generate colored text report."""
        print("\n" + "="*70)
        print(f"{Fore.CYAN}🤖 AI CODE VALIDATOR - RESULTS{Style.RESET_ALL}")
        print("="*70 + "\n")

        # Display score
        score = score_data['score']
        rating = score_data['rating']

        # Color based on score
        if score >= 90:
            score_color = Fore.GREEN
        elif score >= 75:
            score_color = Fore.YELLOW
        elif score >= 60:
            score_color = Fore.LIGHTYELLOW_EX
        else:
            score_color = Fore.RED

        print(f"{score_color}Confidence Score: {score}/100 ({rating}){Style.RESET_ALL}")
        print(f"Total Issues: {score_data['total_issues']}")
        print(f"  Critical: {score_data['critical_issues']} | High: {score_data['high_issues']} | " +
              f"Medium: {score_data['medium_issues']} | Low: {score_data['low_issues']}\n")

        print(f"{Fore.CYAN}Recommendation:{Style.RESET_ALL}")
        print(f"  {score_data['recommendation']}\n")

        if not issues:
            print(f"{Fore.GREEN}✓ No issues found!{Style.RESET_ALL}\n")
            return

        # Group issues by severity
        critical = [i for i in issues if i.get('severity') == 'critical']
        high = [i for i in issues if i.get('severity') == 'high']
        medium = [i for i in issues if i.get('severity') == 'medium']
        low = [i for i in issues if i.get('severity') == 'low']

        # Display critical issues first
        if critical:
            print(f"{Fore.RED}{'='*70}")
            print(f"🚨 CRITICAL ISSUES ({len(critical)})")
            print(f"{'='*70}{Style.RESET_ALL}\n")
            for issue in critical:
                self._print_issue(issue, Fore.RED)

        if high:
            print(f"{Fore.LIGHTRED_EX}{'='*70}")
            print(f"⚠️  HIGH SEVERITY ISSUES ({len(high)})")
            print(f"{'='*70}{Style.RESET_ALL}\n")
            for issue in high:
                self._print_issue(issue, Fore.LIGHTRED_EX)

        if medium:
            print(f"{Fore.YELLOW}{'='*70}")
            print(f"⚡ MEDIUM SEVERITY ISSUES ({len(medium)})")
            print(f"{'='*70}{Style.RESET_ALL}\n")
            for issue in medium:
                self._print_issue(issue, Fore.YELLOW)

        if low:
            print(f"{Fore.LIGHTYELLOW_EX}{'='*70}")
            print(f"💡 LOW SEVERITY ISSUES ({len(low)})")
            print(f"{'='*70}{Style.RESET_ALL}\n")
            for issue in low:
                self._print_issue(issue, Fore.LIGHTYELLOW_EX)

        print("="*70 + "\n")

    def _print_issue(self, issue: Dict[str, Any], color: str):
        """Print a single issue with formatting."""
        print(f"{color}[{issue['type'].upper()}]{Style.RESET_ALL}")
        print(f"  File: {issue['file']}:{issue['line']}")
        print(f"  {issue['message']}")
        if 'suggestion' in issue:
            print(f"  💡 Suggestion: {issue['suggestion']}")
        print()

    def _report_json(self, issues: List[Dict[str, Any]], score_data: Dict[str, Any]):
        """Generate JSON report."""
        report = {
            'score': score_data,
            'issues': issues
        }
        print(json.dumps(report, indent=2))
