"""
Main debugger class - wraps LLM calls with debugging capabilities
"""

import time
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from prompt_debugger.analyzer import ResponseAnalyzer
from prompt_debugger.prompt_checker import PromptChecker
from prompt_debugger.logger import DebugLogger


class AIDebugger:
    """Wrap LLM calls with automatic debugging and analysis."""
    
    def __init__(self, log_dir: str = ".prompt_debugger_logs", auto_analyze: bool = True, verbose: bool = True):
        """Initialize AIDebugger."""
        self.log_dir = log_dir
        self.auto_analyze = auto_analyze
        self.verbose = verbose
        self.analyzer = ResponseAnalyzer()
        self.prompt_checker = PromptChecker()
        self.logger = DebugLogger(log_dir)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.call_count = 0
        self.issues_found = []
    
    def debug_call(self, llm_function: Callable, prompt: str, expected_output: Optional[Any] = None, **kwargs) -> Dict[str, Any]:
        """Make LLM call with debugging enabled."""
        self.call_count += 1
        call_id = f"{self.session_id}_{self.call_count}"
        prompt_analysis = self.prompt_checker.check_prompt(prompt)
        
        if self.verbose and prompt_analysis['issues']:
            print(f"\n  Prompt Issues Detected:")
            for issue in prompt_analysis['issues']:
                print(f"   - {issue['type']}: {issue['message']}")
        
        start_time = time.time()
        try:
            response = llm_function(prompt, **kwargs)
            success = True
            error = None
        except Exception as e:
            response = None
            success = False
            error = str(e)
        
        latency = time.time() - start_time
        
        if self.auto_analyze and response:
            response_analysis = self.analyzer.analyze_response(prompt=prompt, response=response, expected=expected_output)
        else:
            response_analysis = {}
        
        debug_info = {
            'call_id': call_id,
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'latency': round(latency, 3),
            'prompt': prompt,
            'response': response,
            'error': error,
            'prompt_analysis': prompt_analysis,
            'response_analysis': response_analysis,
            'kwargs': kwargs
        }
        
        self.logger.log_interaction(debug_info)
        
        if prompt_analysis['issues'] or (response_analysis and response_analysis.get('issues')):
            self.issues_found.append(debug_info)
        
        if self.verbose:
            self._print_debug_summary(debug_info)
        
        return debug_info
    
    def get_suggestions(self, call_id: Optional[str] = None) -> List[Dict]:
        """Get improvement suggestions."""
        if call_id:
            debug_info = self.logger.get_interaction(call_id)
        else:
            debug_info = self.issues_found[-1] if self.issues_found else None
        
        if not debug_info:
            return []
        
        suggestions = []
        if debug_info['prompt_analysis']['issues']:
            for issue in debug_info['prompt_analysis']['issues']:
                suggestions.append({'type': 'prompt_fix', 'issue': issue['message'], 'suggestion': issue['suggestion']})
        
        if debug_info.get('response_analysis', {}).get('issues'):
            for issue in debug_info['response_analysis']['issues']:
                suggestions.append({'type': 'response_quality', 'issue': issue['problem'], 'suggestion': issue['fix']})
        
        return suggestions
    
    def get_improved_prompt(self, original_prompt: str) -> str:
        """Get an automatically improved version of the prompt."""
        analysis = self.prompt_checker.check_prompt(original_prompt)
        if not analysis['issues']:
            return original_prompt
        
        improved = original_prompt
        for issue in analysis['issues']:
            if issue['type'] == 'too_vague':
                improved = f"Please provide a detailed, specific response. {improved}"
            elif issue['type'] == 'missing_context':
                improved = f"{improved}\n\nContext: [Add relevant background information]"
        
        return improved
    
    def _print_debug_summary(self, debug_info: Dict):
        """Print formatted debug summary."""
        print(f"\n{'='*70}")
        print(f"Debug Report - Call {debug_info['call_id']}")
        print(f"{'='*70}")
        print(f"\nStatus: {' SUCCESS' if debug_info['success'] else ' FAILED'}")
        print(f"Latency: {debug_info['latency']}s")
        
        if debug_info['prompt_analysis']['issues']:
            print(f"\n  Prompt Issues ({len(debug_info['prompt_analysis']['issues'])}):")
            for issue in debug_info['prompt_analysis']['issues']:
                print(f"   • {issue['type'].upper()}: {issue['message']}")
        else:
            print(f"\n No prompt issues detected")
        
        if debug_info.get('response_analysis'):
            score = debug_info['response_analysis'].get('quality_score', 0)
            print(f"\nResponse Quality: {score}/10")
        
        print(f"\n{'='*70}\n")
    
    def get_session_summary(self) -> Dict:
        """Get summary of entire debug session."""
        return {
            'session_id': self.session_id,
            'total_calls': self.call_count,
            'issues_found': len(self.issues_found),
            'log_directory': self.log_dir
        }
    
    def export_report(self, filename: Optional[str] = None):
        """Export complete debug report to JSON file."""
        if filename is None:
            filename = f"prompt_debugger_report_{self.session_id}.json"
        
        report = {
            'session_summary': self.get_session_summary(),
            'all_issues': self.issues_found
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDebug report exported to: {filename}")
