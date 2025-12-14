"""Historical pattern learning for server selection."""
from typing import Dict, List, Optional
from collections import defaultdict
from mcp_switchboard.state.manager import StateManager


class PatternLearner:
    """Learn from historical patterns to improve server recommendations."""
    
    def __init__(self, state_manager: Optional[StateManager] = None):
        self.state_manager = state_manager or StateManager()
    
    def get_recommendations(
        self,
        task_fingerprint: str,
        current_servers: List[str],
        limit: int = 3
    ) -> List[Dict[str, float]]:
        """Get server recommendations based on historical patterns.
        
        Args:
            task_fingerprint: Fingerprint of current task
            current_servers: Servers already selected
            limit: Max number of recommendations
            
        Returns:
            List of {server_name, confidence} dicts
        """
        # Get historical patterns
        patterns = self.state_manager.get_historical_patterns(task_fingerprint)
        
        if not patterns:
            return []
        
        # Count server usage frequency
        server_counts = defaultdict(int)
        total_tasks = len(patterns)
        
        for pattern in patterns:
            servers = pattern.get("servers", [])
            for server in servers:
                if server not in current_servers:
                    server_counts[server] += 1
        
        # Calculate confidence scores
        recommendations = []
        for server, count in server_counts.items():
            confidence = count / total_tasks
            recommendations.append({
                "server_name": server,
                "confidence": confidence,
                "usage_count": count
            })
        
        # Sort by confidence and limit
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)
        return recommendations[:limit]
    
    def boost_confidence(
        self,
        server_name: str,
        base_confidence: float,
        task_fingerprint: str
    ) -> float:
        """Boost confidence score based on historical success.
        
        Args:
            server_name: Server to boost
            base_confidence: Original confidence score
            task_fingerprint: Current task fingerprint
            
        Returns:
            Boosted confidence score (0.0-1.0)
        """
        patterns = self.state_manager.get_historical_patterns(task_fingerprint)
        
        if not patterns:
            return base_confidence
        
        # Count successful uses
        successful_uses = sum(
            1 for p in patterns
            if server_name in p.get("servers", [])
        )
        
        if successful_uses == 0:
            return base_confidence
        
        # Boost by up to 0.2 based on usage frequency
        boost = min(0.2, successful_uses / len(patterns) * 0.2)
        
        return min(1.0, base_confidence + boost)
