"""
Unit tests for prompt_debugger
"""

import unittest
import os
from prompt_debugger import AIDebugger, PromptChecker, ResponseAnalyzer, DebugLogger


class TestPromptChecker(unittest.TestCase):
    """Test prompt analysis functionality."""
    
    def setUp(self):
        self.checker = PromptChecker()
    
    def test_good_prompt(self):
        """Test a well-formed prompt."""
        result = self.checker.check_prompt("What is machine learning and how does it work?")
        self.assertGreaterEqual(result['quality_score'], 7)
    
    def test_vague_prompt(self):
        """Test detection of vague language."""
        result = self.checker.check_prompt("Tell me about things and stuff")
        self.assertGreater(result['total_issues'], 0)
        issue_types = [issue['type'] for issue in result['issues']]
        self.assertIn('too_vague', issue_types)
    
    def test_short_prompt(self):
        """Test detection of too-short prompts."""
        result = self.checker.check_prompt("Hi")
        self.assertGreater(result['total_issues'], 0)
        issue_types = [issue['type'] for issue in result['issues']]
        self.assertIn('too_short', issue_types)


class TestResponseAnalyzer(unittest.TestCase):
    """Test response analysis functionality."""
    
    def setUp(self):
        self.analyzer = ResponseAnalyzer()
    
    def test_good_response(self):
        """Test analysis of a good response."""
        prompt = "What is Python?"
        response = "Python is a high-level programming language known for its simplicity and readability."
        result = self.analyzer.analyze_response(prompt, response)
        self.assertGreaterEqual(result['quality_score'], 7)
    
    def test_empty_response(self):
        """Test detection of empty response."""
        result = self.analyzer.analyze_response("Test", "")
        self.assertEqual(result['quality_score'], 0)
        self.assertGreater(len(result['issues']), 0)
    
    def test_refusal_detection(self):
        """Test detection of AI refusals."""
        prompt = "How to hack?"
        response = "I'm sorry, but I cannot help with that."
        result = self.analyzer.analyze_response(prompt, response)
        issue_problems = [issue['problem'] for issue in result['issues']]
        self.assertTrue(any('refused' in str(p).lower() for p in issue_problems))


class TestAIDebugger(unittest.TestCase):
    """Test main AIDebugger functionality."""
    
    def setUp(self):
        self.test_log_dir = ".test_prompt_debugger_logs"
        self.debugger = AIDebugger(log_dir=self.test_log_dir, verbose=False)
    
    def tearDown(self):
        """Clean up test logs."""
        import shutil
        if os.path.exists(self.test_log_dir):
            shutil.rmtree(self.test_log_dir)
    
    def mock_llm(self, prompt):
        """Mock LLM function for testing."""
        return f"Response to: {prompt}"
    
    def test_debug_call(self):
        """Test basic debug_call functionality."""
        result = self.debugger.debug_call(self.mock_llm, "What is AI?")
        
        self.assertIn('call_id', result)
        self.assertIn('prompt_analysis', result)
        self.assertIn('response_analysis', result)
        self.assertTrue(result['success'])
    
    def test_get_improved_prompt(self):
        """Test automatic prompt improvement."""
        original = "Tell me about stuff"
        improved = self.debugger.get_improved_prompt(original)
        self.assertNotEqual(original, improved)
        self.assertIn(original, improved)
    
    def test_session_summary(self):
        """Test session summary."""
        self.debugger.debug_call(self.mock_llm, "Test 1")
        self.debugger.debug_call(self.mock_llm, "Test 2")
        
        summary = self.debugger.get_session_summary()
        self.assertEqual(summary['total_calls'], 2)
        self.assertIn('session_id', summary)


if __name__ == '__main__':
    unittest.main()
