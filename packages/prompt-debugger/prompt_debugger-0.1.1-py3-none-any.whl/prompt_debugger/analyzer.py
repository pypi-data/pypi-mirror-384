"""
Analyze LLM responses for quality and issues
"""

import re
from typing import Dict, Any, Optional, List


class ResponseAnalyzer:
    """
    Analyze LLM responses for quality, correctness, and issues.
    
    Detects:
    - Empty or minimal responses
    - Refusals
    - Hallucination indicators
    - Incomplete responses
    - Low relevance
    """
    
    def analyze_response(
        self,
        prompt: str,
        response: Any,
        expected: Optional[Any] = None
    ) -> Dict:
        """
        Comprehensive response analysis.
        
        Args:
            prompt: Original prompt
            response: LLM response
            expected: Expected output (if known)
        
        Returns:
            Analysis dictionary with quality score and issues
        """
        response_text = str(response) if response else ""
        issues = []
        
        # Check if response is empty
        if not response_text or len(response_text.strip()) < 5:
            issues.append({
                'problem': 'Empty or minimal response',
                'fix': 'Rephrase prompt with more specific instructions',
                'severity': 'high'
            })
            return {
                'quality_score': 0,
                'issues': issues,
                'metrics': {'length': 0, 'relevance': 0}
            }
        
        # Check for refusals
        if self._is_refusal(response_text):
            issues.append({
                'problem': 'AI refused to answer or lacks information',
                'fix': 'Rephrase to avoid safety triggers or provide more context',
                'severity': 'high'
            })
        
        # Check for hallucination indicators
        hallucination_score = self._detect_hallucination(response_text)
        if hallucination_score > 0.5:
            issues.append({
                'problem': 'Possible hallucination detected',
                'fix': 'Add explicit instruction to only use factual information',
                'severity': 'high'
            })
        
        # Check for incomplete responses
        if self._is_incomplete(response_text):
            issues.append({
                'problem': 'Response appears incomplete',
                'fix': 'Increase max_tokens or simplify prompt',
                'severity': 'medium'
            })
        
        # Check relevance to prompt
        relevance_score = self._calculate_relevance(prompt, response_text)
        if relevance_score < 0.3:
            issues.append({
                'problem': f'Low relevance to prompt ({relevance_score:.2f})',
                'fix': 'Make prompt more specific and clear',
                'severity': 'high'
            })
        
        # Check for expected output match
        if expected:
            match_score = self._compare_with_expected(response_text, expected)
            if match_score < 0.7:
                issues.append({
                    'problem': f'Output differs from expected ({match_score:.2f} match)',
                    'fix': 'Review prompt clarity or expected output',
                    'severity': 'medium'
                })
        
        # Calculate overall quality score
        quality_score = self._calculate_quality_score(response_text, issues)
        
        return {
            'quality_score': quality_score,
            'issues': issues,
            'metrics': {
                'length': len(response_text),
                'relevance': round(relevance_score, 2),
                'hallucination_risk': round(hallucination_score, 2),
                'completeness': 1.0 if not self._is_incomplete(response_text) else 0.5
            }
        }
    
    def _is_refusal(self, response: str) -> bool:
        """Check if response is a refusal."""
        refusal_patterns = [
            r"i cannot", r"i can't", r"i'm unable", r"i am unable",
            r"i don't have", r"i apologize.*cannot", r"as an ai",
            r"against my programming"
        ]
        response_lower = response.lower()
        return any(re.search(pattern, response_lower) for pattern in refusal_patterns)
    
    def _detect_hallucination(self, response: str) -> float:
        """Estimate likelihood of hallucination (0-1)."""
        score = 0.0
        
        specific_numbers = re.findall(r'\d{4,}', response)
        if len(specific_numbers) > 3 and 'source' not in response.lower():
            score += 0.3
        
        hedging = ['approximately', 'about', 'roughly', 'estimated', 'likely', 'may', 'might']
        if not any(word in response.lower() for word in hedging) and len(response) > 100:
            score += 0.2
        
        fake_patterns = [r'www\.example\d+\.com', r'source\d+\.org']
        if any(re.search(pattern, response) for pattern in fake_patterns):
            score += 0.5
        
        return min(1.0, score)
    
    def _is_incomplete(self, response: str) -> bool:
        """Check if response appears incomplete."""
        incomplete_indicators = [
            response.endswith('...'),
            response.endswith(' and'),
            response.endswith(' or'),
            response.endswith(','),
            'continued' in response.lower()[-50:] if len(response) > 50 else False,
            '[incomplete]' in response.lower()
        ]
        return any(incomplete_indicators)
    
    def _calculate_relevance(self, prompt: str, response: str) -> float:
        """Calculate relevance score (0-1) using keyword overlap."""
        prompt_words = set(prompt.lower().split())
        response_words = set(response.lower().split())
        
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are'}
        prompt_words -= stop_words
        response_words -= stop_words
        
        if not prompt_words:
            return 0.5
        
        overlap = len(prompt_words & response_words)
        return min(1.0, overlap / len(prompt_words))
    
    def _compare_with_expected(self, actual: str, expected: Any) -> float:
        """Compare actual output with expected."""
        actual_str = str(actual).lower()
        expected_str = str(expected).lower()
        
        if actual_str == expected_str:
            return 1.0
        
        actual_words = set(actual_str.split())
        expected_words = set(expected_str.split())
        
        if not expected_words:
            return 0.0
        
        overlap = len(actual_words & expected_words)
        return overlap / len(expected_words)
    
    def _calculate_quality_score(self, response: str, issues: List[Dict]) -> int:
        """Calculate overall quality score (0-10)."""
        base_score = 10
        severity_penalties = {'high': 3, 'medium': 2, 'low': 1}
        
        for issue in issues:
            penalty = severity_penalties.get(issue['severity'], 1)
            base_score -= penalty
        
        return max(0, base_score)
