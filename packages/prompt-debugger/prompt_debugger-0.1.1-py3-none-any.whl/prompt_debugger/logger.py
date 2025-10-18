"""
Log all AI interactions for debugging
"""

import json
from pathlib import Path
from typing import Dict, Optional, List


class DebugLogger:
    """
    Persistent logging of all AI interactions.
    """
    
    def __init__(self, log_dir: str = ".prompt_debugger_logs"):
        """
        Initialize logger.
        
        Args:
            log_dir: Directory to store logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.index_file = self.log_dir / "index.json"
        self.index = self._load_index()
    
    def log_interaction(self, debug_info: Dict):
        """Log a single interaction."""
        call_id = debug_info['call_id']
        log_file = self.log_dir / f"{call_id}.json"
        
        with open(log_file, 'w') as f:
            json.dump(debug_info, f, indent=2)
        
        self.index[call_id] = {
            'timestamp': debug_info['timestamp'],
            'success': debug_info['success'],
            'has_issues': bool(debug_info['prompt_analysis']['issues'] or 
                             debug_info.get('response_analysis', {}).get('issues')),
            'file': str(log_file)
        }
        self._save_index()
    
    def get_interaction(self, call_id: str) -> Optional[Dict]:
        """Retrieve logged interaction by ID."""
        if call_id not in self.index:
            return None
        
        log_file = Path(self.index[call_id]['file'])
        if not log_file.exists():
            return None
        
        with open(log_file, 'r') as f:
            return json.load(f)
    
    def get_all_interactions(self) -> List[Dict]:
        """Get all logged interactions."""
        interactions = []
        for call_id in self.index.keys():
            interaction = self.get_interaction(call_id)
            if interaction:
                interactions.append(interaction)
        return interactions
    
    def get_failed_calls(self) -> List[Dict]:
        """Get all failed calls."""
        return [
            self.get_interaction(call_id)
            for call_id, info in self.index.items()
            if not info['success']
        ]
    
    def get_problematic_calls(self) -> List[Dict]:
        """Get all calls with detected issues."""
        return [
            self.get_interaction(call_id)
            for call_id, info in self.index.items()
            if info['has_issues']
        ]
    
    def _load_index(self) -> Dict:
        """Load index file."""
        if not self.index_file.exists():
            return {}
        
        try:
            with open(self.index_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    
    def _save_index(self):
        """Save index file."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def clear_logs(self):
        """Clear all logs."""
        for log_file in self.log_dir.glob('*.json'):
            if log_file.name != 'index.json':
                log_file.unlink()
        self.index = {}
        self._save_index()
