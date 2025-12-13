"""Task parser for extracting structured information from task descriptions."""
from __future__ import annotations
import re
from typing import Optional, List
from pydantic import BaseModel


class ParsedTask(BaseModel):
    """Structured information extracted from task description."""
    aws_account: Optional[str] = None
    aws_region: Optional[str] = None
    jira_project: Optional[str] = None
    jira_ticket: Optional[str] = None
    mentioned_services: List[str] = []
    keywords: List[str] = []


class TaskParser:
    """Parse task descriptions to extract structured information."""
    
    AWS_REGIONS = {
        "tokyo": "ap-northeast-1",
        "singapore": "ap-southeast-1",
        "sydney": "ap-southeast-2",
        "virginia": "us-east-1",
        "oregon": "us-west-2",
        "ohio": "us-east-2",
        "california": "us-west-1",
        "mumbai": "ap-south-1",
        "seoul": "ap-northeast-2",
        "london": "eu-west-2",
        "paris": "eu-west-3",
        "frankfurt": "eu-central-1",
    }
    
    SERVICE_KEYWORDS = {
        "jira": ["jira", "ticket", "story", "bug", "devops-"],
        "aws": ["aws", "ec2", "ecs", "lambda", "s3", "rds", "dynamodb", "cloudwatch"],
        "terraform": ["terraform", "tf", "infrastructure", "iac"],
        "github": ["github", "pr", "pull request", "repository", "repo"],
        "cloudwatch": ["cloudwatch", "logs", "metrics", "alarms"],
    }
    
    def parse(self, task_description: str) -> ParsedTask:
        """Parse task description and extract structured information."""
        text = task_description.lower()
        
        # Extract AWS account
        aws_account = self._extract_aws_account(text)
        
        # Extract AWS region
        aws_region = self._extract_aws_region(text)
        
        # Extract Jira ticket
        jira_ticket = self._extract_jira_ticket(task_description)
        jira_project = jira_ticket.split('-')[0] if jira_ticket else None
        
        # Identify mentioned services
        mentioned_services = self._identify_services(text)
        
        # Extract keywords
        keywords = text.split()
        
        return ParsedTask(
            aws_account=aws_account,
            aws_region=aws_region,
            jira_project=jira_project,
            jira_ticket=jira_ticket,
            mentioned_services=mentioned_services,
            keywords=keywords,
        )
    
    def _extract_aws_account(self, text: str) -> Optional[str]:
        """Extract AWS account name from text."""
        accounts = ["prod", "production", "dev", "development", "staging", "uat", "test"]
        for account in accounts:
            if account in text:
                # Normalize
                if account == "production":
                    return "prod"
                elif account == "development":
                    return "dev"
                return account
        return None
    
    def _extract_aws_region(self, text: str) -> Optional[str]:
        """Extract AWS region from text."""
        for city, region in self.AWS_REGIONS.items():
            if city in text:
                return region
        return None
    
    def _extract_jira_ticket(self, text: str) -> Optional[str]:
        """Extract Jira ticket ID from text."""
        match = re.search(r'([A-Z]+-\d+)', text, re.IGNORECASE)
        return match.group(1).upper() if match else None
    
    def _identify_services(self, text: str) -> List[str]:
        """Identify mentioned services from text."""
        services = []
        for service, keywords in self.SERVICE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                services.append(service)
        return services
