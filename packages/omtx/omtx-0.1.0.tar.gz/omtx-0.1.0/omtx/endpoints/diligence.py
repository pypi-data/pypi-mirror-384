"""Diligence-related endpoints"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .base import Endpoint
from . import register_endpoint


@dataclass
class DiligenceResult:
    """Result from diligence generation"""
    target: str
    summary: str
    status: str
    report_data: Dict[str, Any]
    
    def __str__(self):
        """User-friendly string representation"""
        return f"Diligence Report for {self.target}:\n{self.summary[:200]}..."


@dataclass
class ResearchResult:
    """Result from deep research"""
    query: str
    findings: list
    final_report: str
    execution_time: float
    
    def __str__(self):
        """User-friendly string representation"""
        return f"Research on '{self.query}':\n{self.final_report[:500]}..."


@register_endpoint
class GenerateDiligenceEndpoint(Endpoint):
    """Generate a diligence report for a molecular target"""
    
    name = "generate_diligence"
    path = "/v2/diligence/generate"
    method = "POST"
    
    def build_request(self, target: str) -> Dict[str, Any]:
        """Build request for diligence generation
        
        Args:
            target: Molecular target (e.g., "BRAF", "KRAS")
        
        Returns:
            Request dictionary
        """
        return {"target": target}
    
    def parse_response(self, data: Dict[str, Any]) -> DiligenceResult:
        """Parse diligence response into result object"""
        return DiligenceResult(
            target=data.get("target", ""),
            summary=data.get("summary", {}).get("target_summary", ""),
            status=data.get("status", "unknown"),
            report_data=data
        )


@register_endpoint
class DeepResearchEndpoint(Endpoint):
    """Perform deep research on a scientific query"""
    
    name = "deep_research"
    path = "/v2/diligence/deep-research"
    method = "POST"
    
    def build_request(self, query: str, max_iterations: Optional[int] = None) -> Dict[str, Any]:
        """Build request for deep research
        
        Args:
            query: Research query (e.g., "CRISPR applications in cancer")
            max_iterations: Maximum research iterations (default: 3)
        
        Returns:
            Request dictionary
        """
        request = {"query": query}
        if max_iterations is not None:
            request["max_iterations"] = max_iterations
        return request
    
    def parse_response(self, data: Dict[str, Any]) -> ResearchResult:
        """Parse research response into result object"""
        return ResearchResult(
            query=data.get("query", ""),
            findings=data.get("detailed_claims", []),
            final_report=data.get("final_report", ""),
            execution_time=data.get("execution_time_seconds", 0.0)
        )