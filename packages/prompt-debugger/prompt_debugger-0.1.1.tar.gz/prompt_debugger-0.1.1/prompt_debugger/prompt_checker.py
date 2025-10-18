"""
Analyze prompts for common issues before sending to LLM
"""

import re
from typing import Dict, List


class PromptChecker:
    """
    Detect issues in prompts before sending to LLM.
    
    Detects:
    - Vague language
    - Ambiguous references
    - Missing context
    - Length issues
    - Conflicting instructions
    """
    
    VAGUE_INDICATORS = ['something', 'things', 'stuff', 'whatever', 'anything']
    AMBIGUOUS_WORDS = ['it', 'this', 'that', 'they', 'maybe', 'might']
    
    def check_prompt(self, prompt: str) -> Dict:
        """
        Analyze prompt for potential issues.
        
        Args:
            prompt: The prompt text
        
        Returns:
            Dictionary with issues, quality score, and suggestions
        """
        issues = []
        
        # Check length
        if len(prompt) < 10:
            issues.append({
                'type': 'too_short',
                'message': 'Prompt is very short and may lack context',
                'suggestion': 'Add more details about what you want the AI to do',
                'severity': 'high'
            })
        
        # Check for vagueness
        vague_count = sum(1 for word in self.VAGUE_INDICATORS if word in prompt.lower())
        if vague_count > 0:
            issues.append({
                'type': 'too_vague',
                'message': f'Contains {vague_count} vague term(s)',
                'suggestion': 'Replace vague terms with specific requirements',
                'severity': 'medium'
            })
        
        # Check for ambiguous references
        sentences = prompt.split('.')
        if len(sentences) > 1:
            for i, sentence in enumerate(sentences[1:], 1):
                ambiguous_count = sum(1 for word in self.AMBIGUOUS_WORDS 
                                    if word in sentence.lower().split())
                if ambiguous_count > 2:
                    issues.append({
                        'type': 'ambiguous',
                        'message': f'Sentence {i} has ambiguous references',
                        'suggestion': 'Use explicit nouns instead of pronouns',
                        'severity': 'low'
                    })
                    break
        
        # Check for missing context
        if '?' in prompt and 'context:' not in prompt.lower() and len(prompt.split()) < 15:
            issues.append({
                'type': 'missing_context',
                'message': 'Question without sufficient context',
                'suggestion': 'Add background information or examples',
                'severity': 'medium'
            })
        
        # Check for conflicting instructions
        if ('do not' in prompt.lower() or "don't" in prompt.lower()) and len(prompt.split('.')) > 2:
            issues.append({
                'type': 'conflicting',
                'message': 'May contain conflicting instructions',
                'suggestion': 'Review prompt for contradictions',
                'severity': 'high'
            })
        
        # Check for overly complex prompt
        if len(prompt.split()) > 200:
            issues.append({
                'type': 'too_complex',
                'message': 'Prompt is very long and may confuse the model',
                'suggestion': 'Break into smaller, focused prompts',
                'severity': 'medium'
            })
        
        # Calculate overall score
        severity_weights = {'high': 3, 'medium': 2, 'low': 1}
        total_penalty = sum(severity_weights[issue['severity']] for issue in issues)
        quality_score = max(0, 10 - total_penalty)
        
        return {
            'quality_score': quality_score,
            'issues': issues,
            'total_issues': len(issues),
            'needs_improvement': len(issues) > 0
        }
    
    def suggest_improvements(self, prompt: str) -> List[str]:
        """
        Generate specific improvement suggestions.
        
        Args:
            prompt: Original prompt
        
        Returns:
            List of improvement suggestions
        """
        analysis = self.check_prompt(prompt)
        return [issue['suggestion'] for issue in analysis['issues']]
