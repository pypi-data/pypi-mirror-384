"""
Fuzzy String Matching for Guardrails

Provides fuzzy string matching capabilities to catch typos, character substitutions,
and variations that bypass exact pattern matching. Uses RapidFuzz for performance.
"""

import logging
import re
from functools import lru_cache
from typing import List, Tuple

logger = logging.getLogger(__name__)


class FuzzyMatcher:
    """
    Performs fuzzy string matching to detect misspellings and character variations.

    Uses token-based matching with RapidFuzz for efficient similarity scoring.
    Supports caching for repeated tokens to improve performance.
    """

    # Pre-compiled regex for tokenization (compile once at class level)
    _TOKENIZE_PATTERN = re.compile(r"\w+")

    def __init__(self, threshold: int = 70):
        """
        Initialize FuzzyMatcher with similarity threshold.

        Args:
            threshold: Minimum similarity score (0-100) to consider a match.
                      Default is 70% for balanced accuracy/false positives.

        Raises:
            ImportError: If rapidfuzz library is not installed.
        """
        try:
            from rapidfuzz import fuzz, process
            self.fuzz = fuzz
            self.process = process
        except ImportError as e:
            logger.error(
                "RapidFuzz library not installed. Fuzzy matching will not be available. "
                "Install with: pip install rapidfuzz"
            )
            raise ImportError(
                "rapidfuzz library is required for fuzzy matching. "
                "Install with: pip install rapidfuzz"
            ) from e

        self.threshold = threshold
        logger.debug(f"FuzzyMatcher initialized with threshold={threshold}")

    @staticmethod
    @lru_cache(maxsize=1024)
    def tokenize(text: str) -> Tuple[str, ...]:
        """
        Extract words from text using regex pattern matching.

        Uses LRU cache to avoid re-tokenizing repeated messages for performance.
        Returns tuple instead of list to be hashable for caching.

        Args:
            text: Input text to tokenize

        Returns:
            Tuple of extracted word tokens (lowercase)
        """
        if not text:
            return tuple()

        # Extract all word tokens (alphanumeric sequences)
        tokens = FuzzyMatcher._TOKENIZE_PATTERN.findall(text.lower())
        return tuple(tokens)

    def check_fuzzy_match(
        self,
        text: str,
        domains: List[str],
        threshold: int = 70
    ) -> List[Tuple[str, str, float]]:
        """
        Check if any tokens in text fuzzy-match domain keywords.

        Uses token-based matching for performance:
        1. Tokenizes input text
        2. For each token, finds best match from domains using partial_ratio
        3. Returns matches above similarity threshold

        Note: Performance instrumentation has been moved to the caller level
        (FastRulesEngine) to reduce span overhead. Individual calls no longer
        create spans; instead, aggregated telemetry is collected.

        Args:
            text: Input text to check
            domains: List of domain keywords to match against
            threshold: Minimum similarity score (0-100). Uses instance threshold if not provided.

        Returns:
            List of tuples: (token, matched_domain, similarity_score)
            Empty list if no matches found.

        Example:
            >>> matcher = FuzzyMatcher(threshold=70)
            >>> matcher.check_fuzzy_match("I h8te this", ["hate", "slur", "toxic"])
            [("h8te", "hate", 75.0)]
        """
        # Direct call - instrumentation moved to caller level
        return self._check_fuzzy_match_internal(text, domains, threshold)

    def _check_fuzzy_match_internal(
        self,
        text: str,
        domains: List[str],
        threshold: int = 70
    ) -> List[Tuple[str, str, float]]:
        """Internal fuzzy matching implementation (extracted for performance instrumentation)."""
        if not text or not domains:
            return []

        # Use provided threshold or fall back to instance threshold
        score_cutoff = threshold if threshold != 70 else self.threshold

        # Tokenize input text
        tokens = self.tokenize(text)
        if not tokens:
            return []

        matches: List[Tuple[str, str, float]] = []

        # Check each token against domain keywords
        for token in tokens:
            # Skip very short tokens (< 5 chars) to reduce false positives
            if len(token) < 5:
                continue

            # Find best match from domains using partial_ratio (substring matching)
            result = self.process.extractOne(
                query=token,
                choices=domains,
                scorer=self.fuzz.partial_ratio,
                score_cutoff=score_cutoff
            )

            if result:
                matched_domain, score, _ = result
                matches.append((token, matched_domain, score))
                logger.debug(
                    f"Fuzzy match found: '{token}' -> '{matched_domain}' "
                    f"(score: {score:.1f})"
                )

        return matches