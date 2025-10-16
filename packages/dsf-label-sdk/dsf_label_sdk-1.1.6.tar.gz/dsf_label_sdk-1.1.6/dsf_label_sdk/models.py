# dsf_label_sdk/models.py
"""Data models for the SDK"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class Field:
    """
    Field configuration for adaptive formula.
    
    Attributes:
        name: Field identifier
        default: Reference/default value
        weight: Importance factor (default: 1.0)
        criticality: Sensitivity factor (default: 1.5)
    """
    name: str
    default: Any
    weight: float = 1.0
    criticality: float = 1.5
    
    def to_dict(self) -> Dict:
        """Convert to API-compatible dictionary."""
        return {
            'default': self.default,
            'weight': self.weight,
            'criticality': self.criticality
        }


class Config:
    """
    Configuration builder for field definitions.
    
    Example:
        >>> config = Config()
        ...     .add_field('temp', default=20, weight=1.0)
        ...     .add_field('pressure', default=1.0, weight=0.8)
    """
    
    def __init__(self):
        self.fields: Dict[str, Field] = {}
    
    def add_field(
        self,
        name: str,
        default: Any,
        weight: float = 1.0,
        criticality: float = 1.5
    ) -> 'Config':
        """
        Add a field to configuration.
        
        Args:
            name: Field name
            default: Default/reference value
            weight: Importance (0.0-inf)
            criticality: Sensitivity (0.0-inf)
            
        Returns:
            Self for chaining
        """
        self.fields[name] = Field(name, default, weight, criticality)
        return self
    
    def remove_field(self, name: str) -> 'Config':
        """Remove a field from configuration."""
        self.fields.pop(name, None)
        return self
    
    def to_dict(self) -> Dict:
        """Convert to API-compatible dictionary."""
        return {
            name: field.to_dict()
            for name, field in self.fields.items()
        }
    
    def __repr__(self):
        return f"Config(fields={list(self.fields.keys())})"


@dataclass
class EvaluationResult:
    """
    Result from evaluation request.
    
    Attributes:
        score: Evaluation score (0.0-1.0)
        tier: Active tier used
        confidence_level: Confidence threshold
        metrics: Performance metrics (premium only)
    """
    score: float
    tier: str = 'community'
    confidence_level: float = 0.65
    metrics: Optional[Dict] = None
    
    @classmethod
    def from_response(cls, response: Dict) -> 'EvaluationResult':
        """Create from API response."""
        return cls(
            score=response.get('score', 0.0),
            tier=response.get('tier', 'community'),
            confidence_level=response.get('confidence_level', 0.65),
            metrics=response.get('metrics')
        )
    
    @property
    def is_above_threshold(self) -> bool:
        """Check if score exceeds confidence level."""
        return self.score >= self.confidence_level
    
    def __repr__(self):
        return (f"EvaluationResult(score={self.score:.3f}, "
                f"tier='{self.tier}', threshold={self.confidence_level:.3f})")