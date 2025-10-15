"""
File: src/linters/file_header/atemporal_detector.py
Purpose: Detects temporal language patterns in file headers
Exports: AtemporalDetector class
Depends: re module for regex matching
Implements: Regex-based pattern matching with configurable patterns
Related: linter.py for detector usage, violation_builder.py for violation creation

Overview:
    Implements pattern-based detection of temporal language that violates atemporal
    documentation requirements. Detects dates, temporal qualifiers, state change language,
    and future references using regex patterns. Provides violation details for each pattern match.

Usage:
    detector = AtemporalDetector()
    violations = detector.detect_violations(header_text)

Notes: Four pattern categories - dates, temporal qualifiers, state changes, future references
"""

import re


class AtemporalDetector:
    """Detects temporal language patterns in text."""

    # Date patterns
    DATE_PATTERNS = [
        (r"\d{4}-\d{2}-\d{2}", "ISO date format (YYYY-MM-DD)"),
        (
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",
            "Month Year format",
        ),
        (r"(?:Created|Updated|Modified):\s*\d{4}", "Date metadata"),
    ]

    # Temporal qualifiers
    TEMPORAL_QUALIFIERS = [
        (r"\bcurrently\b", 'temporal qualifier "currently"'),
        (r"\bnow\b", 'temporal qualifier "now"'),
        (r"\brecently\b", 'temporal qualifier "recently"'),
        (r"\bsoon\b", 'temporal qualifier "soon"'),
        (r"\bfor now\b", 'temporal qualifier "for now"'),
    ]

    # State change language
    STATE_CHANGE = [
        (r"\breplaces?\b", 'state change "replaces"'),
        (r"\bmigrated from\b", 'state change "migrated from"'),
        (r"\bformerly\b", 'state change "formerly"'),
        (r"\bold implementation\b", 'state change "old"'),
        (r"\bnew implementation\b", 'state change "new"'),
    ]

    # Future references
    FUTURE_REFS = [
        (r"\bwill be\b", 'future reference "will be"'),
        (r"\bplanned\b", 'future reference "planned"'),
        (r"\bto be added\b", 'future reference "to be added"'),
        (r"\bcoming soon\b", 'future reference "coming soon"'),
    ]

    def detect_violations(  # thailint: ignore[nesting]
        self, text: str
    ) -> list[tuple[str, str, int]]:
        """Detect all temporal language violations in text.

        Args:
            text: Text to check for temporal language

        Returns:
            List of (pattern, description, line_number) tuples for each violation
        """
        violations = []

        # Check all pattern categories
        all_patterns = (
            self.DATE_PATTERNS + self.TEMPORAL_QUALIFIERS + self.STATE_CHANGE + self.FUTURE_REFS
        )

        lines = text.split("\n")
        for line_num, line in enumerate(lines, start=1):
            for pattern, description in all_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append((pattern, description, line_num))

        return violations
