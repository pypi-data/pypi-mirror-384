from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Suggestion:
    title: str
    file: Optional[str] = None
    class_name: Optional[str] = None
    line: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class ProjectSuggestions:
    solid_principles: List[Suggestion]
    design_patterns: List[Suggestion]
    security_issues: List[Suggestion]
    architecture: List[Suggestion]
    final_recommendations: List[Suggestion]
