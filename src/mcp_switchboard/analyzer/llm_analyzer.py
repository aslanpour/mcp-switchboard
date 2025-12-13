"""LLM-based semantic task analyzer using MCP sampling."""
from typing import Optional
from mcp.types import SamplingMessage, TextContent, Role
from mcp_switchboard.analyzer.parser import TaskParser, ParsedTask


class LLMTaskAnalyzer:
    """Analyzes tasks using LLM sampling for semantic understanding."""
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        self.model = model
        self.parser = TaskParser()
    
    def _create_analysis_prompt(self, task_description: str) -> str:
        """Create prompt for LLM analysis."""
        return f"""Analyze this DevOps task and extract structured information:

Task: "{task_description}"

Extract and return ONLY a JSON object with these fields:
{{
  "aws_account": "prod|staging|dev|uat or null",
  "aws_region": "AWS region code or null",
  "jira_project": "JIRA project key or null",
  "jira_ticket": "Full ticket ID (e.g., DEVOPS-123) or null",
  "required_services": ["list", "of", "services"],
  "required_capabilities": ["list", "of", "capabilities"],
  "confidence": 0.0-1.0
}}

Services can be: aws, jira, github, terraform, kubernetes, docker, etc.
Capabilities can be: deployment, infrastructure, monitoring, security, etc.

Return ONLY the JSON, no explanation."""
    
    async def analyze_with_llm(
        self,
        task_description: str,
        sampling_fn
    ) -> ParsedTask:
        """Analyze task using LLM sampling.
        
        Args:
            task_description: Natural language task description
            sampling_fn: MCP sampling function from client session
            
        Returns:
            ParsedTask with LLM-enhanced analysis
        """
        prompt = self._create_analysis_prompt(task_description)
        
        try:
            # Use MCP sampling
            result = await sampling_fn(
                messages=[
                    SamplingMessage(
                        role=Role.user,
                        content=TextContent(type="text", text=prompt)
                    )
                ],
                modelPreferences={
                    "hints": [{"name": self.model}]
                },
                maxTokens=500
            )
            
            # Parse LLM response
            import json
            response_text = result.content.text if hasattr(result.content, 'text') else str(result.content)
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                
                return ParsedTask(
                    aws_account=data.get("aws_account"),
                    aws_region=data.get("aws_region"),
                    jira_project=data.get("jira_project"),
                    jira_ticket=data.get("jira_ticket"),
                    required_services=data.get("required_services", []),
                    required_capabilities=data.get("required_capabilities", []),
                    confidence=data.get("confidence", 0.9),
                    source="llm"
                )
        except Exception as e:
            # Fallback to keyword-based parsing
            print(f"LLM analysis failed: {e}, falling back to keyword parsing")
            pass
        
        # Fallback to keyword-based parser
        parsed = self.parser.parse(task_description)
        parsed.source = "keyword_fallback"
        return parsed
    
    def analyze_hybrid(
        self,
        task_description: str,
        llm_result: Optional[ParsedTask] = None
    ) -> ParsedTask:
        """Combine LLM and keyword-based analysis.
        
        Args:
            task_description: Natural language task description
            llm_result: Optional LLM analysis result
            
        Returns:
            ParsedTask with hybrid analysis
        """
        keyword_result = self.parser.parse(task_description)
        
        if llm_result is None:
            return keyword_result
        
        # Merge results, preferring LLM when confidence is high
        if llm_result.confidence >= 0.8:
            # Use LLM result but fill gaps with keyword parsing
            return ParsedTask(
                aws_account=llm_result.aws_account or keyword_result.aws_account,
                aws_region=llm_result.aws_region or keyword_result.aws_region,
                jira_project=llm_result.jira_project or keyword_result.jira_project,
                jira_ticket=llm_result.jira_ticket or keyword_result.jira_ticket,
                required_services=list(set(
                    llm_result.required_services + keyword_result.required_services
                )),
                required_capabilities=list(set(
                    llm_result.required_capabilities + keyword_result.required_capabilities
                )),
                confidence=max(llm_result.confidence, keyword_result.confidence),
                source="hybrid"
            )
        else:
            # Low LLM confidence, prefer keyword parsing
            return keyword_result
