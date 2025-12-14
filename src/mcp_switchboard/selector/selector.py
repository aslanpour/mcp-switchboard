"""Server selector for choosing MCP servers based on task analysis."""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ..config.registry import ServerRegistry
from ..analyzer.analyzer import TaskAnalysis


class ServerMatch(BaseModel):
    """A matched server with confidence score."""
    server_name: str
    confidence: float
    reasoning: str


class ServerSelection(BaseModel):
    """Result of server selection."""
    selected_servers: List[ServerMatch]
    rejected_servers: List[ServerMatch]
    decision_report: Dict[str, Any]


class ServerSelector:
    """Select MCP servers based on task analysis."""
    
    def __init__(
        self,
        registry: ServerRegistry,
        confidence_threshold: float = 0.7,
        use_learning: bool = True
    ) -> None:
        self.registry = registry
        self.threshold = confidence_threshold
        self.use_learning = use_learning
        self._learner = None
        
        if use_learning:
            try:
                from .learning import PatternLearner
                self._learner = PatternLearner()
            except Exception:
                self.use_learning = False
    
    def select(self, analysis: TaskAnalysis) -> ServerSelection:
        """Select servers based on task analysis."""
        # Get all potential matches
        all_matches = self._match_servers(analysis)
        
        # Split by threshold
        selected = [m for m in all_matches if m.confidence >= self.threshold]
        rejected = [m for m in all_matches if m.confidence < self.threshold]
        
        return ServerSelection(
            selected_servers=selected,
            rejected_servers=rejected,
            decision_report=self._generate_report(analysis, selected, rejected),
        )
    
    def _match_servers(self, analysis: TaskAnalysis) -> List[ServerMatch]:
        """Match servers to task requirements."""
        matches = []
        
        for server_name in self.registry.list_servers():
            server_config = self.registry.get_server(server_name)
            confidence = self._calculate_confidence(analysis, server_config)
            
            if confidence > 0:
                matches.append(ServerMatch(
                    server_name=server_name,
                    confidence=confidence,
                    reasoning=self._generate_reasoning(analysis, server_config),
                ))
        
        # Sort by confidence
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches
    
    def _calculate_confidence(self, analysis: TaskAnalysis, server_config: Dict) -> float:
        """Calculate confidence score for a server."""
        score = 0.0
        
        # Check capability matches
        server_caps = set(server_config.get("capabilities", []))
        required_caps = set(analysis.required_capabilities)
        
        if server_caps & required_caps:
            score += 0.6
        
        # Check keyword matches
        keywords = server_config.get("confidence_keywords", [])
        for keyword in keywords:
            if any(keyword in service for service in analysis.required_services):
                score += 0.2
                break
        
        base_score = min(score, 1.0)
        
        # Boost with historical learning if available
        if self.use_learning and self._learner:
            try:
                # Create task fingerprint
                task_fp = f"{analysis.aws_account}:{','.join(analysis.required_services)}"
                server_name = server_config.get("name", "")
                
                # Boost confidence based on historical success
                boosted_score = self._learner.boost_confidence(
                    server_name, base_score, task_fp
                )
                return boosted_score
            except Exception:
                pass
        
        return base_score
    
    def _generate_reasoning(self, analysis: TaskAnalysis, server_config: Dict) -> str:
        """Generate reasoning for server selection."""
        reasons = []
        
        server_caps = set(server_config.get("capabilities", []))
        required_caps = set(analysis.required_capabilities)
        matches = server_caps & required_caps
        
        if matches:
            reasons.append(f"Provides capabilities: {', '.join(matches)}")
        
        return "; ".join(reasons) if reasons else "General match"
    
    def _generate_report(
        self,
        analysis: TaskAnalysis,
        selected: List[ServerMatch],
        rejected: List[ServerMatch],
    ) -> Dict[str, Any]:
        """Generate decision report."""
        return {
            "task_analysis": analysis.dict(),
            "selected_count": len(selected),
            "rejected_count": len(rejected),
            "threshold": self.threshold,
        }
