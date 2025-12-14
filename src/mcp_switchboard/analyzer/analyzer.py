"""Task analyzer combining keyword parsing and future LLM analysis."""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
from .parser import TaskParser, ParsedTask
from ..utils.metrics import timed


class TaskAnalysis(BaseModel):
    """Complete task analysis result."""
    aws_account: Optional[str]
    aws_region: Optional[str]
    jira_project: Optional[str]
    jira_ticket: Optional[str]
    required_services: List[str]
    required_capabilities: List[str]
    confidence: float
    source: str  # "keyword", "llm", or "hybrid"


class TaskAnalyzer:
    """Analyze tasks to determine required MCP servers."""
    
    def __init__(self) -> None:
        self.parser = TaskParser()
    
    @timed("task_analysis_ms")
    def analyze(self, task_description: str, project_path: str = "") -> TaskAnalysis:
        """Analyze task and return structured analysis."""
        # Parse with keywords
        parsed = self.parser.parse(task_description)
        
        # For now, use keyword-based analysis only
        # LLM sampling will be added in Task 2.2
        return TaskAnalysis(
            aws_account=parsed.aws_account,
            aws_region=parsed.aws_region,
            jira_project=parsed.jira_project,
            jira_ticket=parsed.jira_ticket,
            required_services=parsed.mentioned_services,
            required_capabilities=parsed.mentioned_services,
            confidence=self._calculate_confidence(parsed),
            source="keyword",
        )
    
    def _calculate_confidence(self, parsed: ParsedTask) -> float:
        """Calculate confidence score based on extracted information."""
        score = 0.0
        
        # More extracted info = higher confidence
        if parsed.aws_account:
            score += 0.2
        if parsed.aws_region:
            score += 0.2
        if parsed.jira_ticket:
            score += 0.2
        if parsed.mentioned_services:
            score += 0.3
        
        # Minimum baseline
        return max(score, 0.3)
