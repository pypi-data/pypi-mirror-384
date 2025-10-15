"""
Detection algorithms for AI monitoring.
"""
import numpy as np
import time
from typing import List, Dict, Any, Optional, Tuple
from collections import deque, defaultdict
from dataclasses import dataclass
import logging
import json
import re

logger = logging.getLogger(__name__)

@dataclass
class HallucinationResult:
    """Result of hallucination detection."""
    is_hallucination: bool
    confidence_score: float
    reasons: List[str]
    metadata: Dict[str, Any]

@dataclass
class DriftResult:
    """Result of drift detection."""
    has_drift: bool
    drift_score: float
    drift_type: str  # 'quality', 'latency', 'tokens', 'cost'
    baseline_value: float
    current_value: float
    metadata: Dict[str, Any]

class HallucinationDetector:
    """Detect hallucinations in AI responses."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)
        
        # Pattern-based detection rules
        self.uncertainty_patterns = [
            r"i'm not sure",
            r"i think",
            r"i believe",
            r"maybe", 
            r"perhaps",
            r"it seems",
            r"appears to be",
            r"might be",
            r"could be"
        ]
        
        self.fabrication_patterns = [
            r"according to my knowledge",
            r"i remember",
            r"i recall",
            r"based on what i know"
        ]
        
        # Compile patterns for efficiency
        self.uncertainty_regex = re.compile('|'.join(self.uncertainty_patterns), re.IGNORECASE)
        self.fabrication_regex = re.compile('|'.join(self.fabrication_patterns), re.IGNORECASE)
    
    def detect(self, 
               prompt: str,
               response: str, 
               context: Optional[str] = None,
               metadata: Optional[Dict[str, Any]] = None) -> HallucinationResult:
        """
        Detect potential hallucinations in AI response.
        
        Args:
            prompt: The input prompt
            response: The AI response to analyze
            context: Optional context/source material
            metadata: Optional metadata about the call
            
        Returns:
            HallucinationResult with detection results
        """
        reasons = []
        confidence_scores = []
        
        # 1. Pattern-based detection
        uncertainty_score = self._detect_uncertainty_patterns(response)
        if uncertainty_score > 0.3:
            reasons.append(f"High uncertainty language detected (score: {uncertainty_score:.2f})")
            confidence_scores.append(uncertainty_score)
        
        fabrication_score = self._detect_fabrication_patterns(response)
        if fabrication_score > 0.2:
            reasons.append(f"Potential fabrication patterns detected (score: {fabrication_score:.2f})")
            confidence_scores.append(fabrication_score)
        
        # 2. Factual consistency checks
        if context:
            consistency_score = self._check_context_consistency(response, context)
            if consistency_score < 0.5:
                reasons.append(f"Low context consistency (score: {consistency_score:.2f})")
                confidence_scores.append(1 - consistency_score)
        
        # 3. Response quality indicators
        quality_score = self._assess_response_quality(response)
        if quality_score < 0.4:
            reasons.append(f"Low response quality indicators (score: {quality_score:.2f})")
            confidence_scores.append(1 - quality_score)
        
        # 4. Specificity and detail analysis
        specificity_score = self._analyze_specificity(response)
        if specificity_score > 0.8:  # Too specific might indicate fabrication
            reasons.append(f"Unusually high specificity (score: {specificity_score:.2f})")
            confidence_scores.append(specificity_score * 0.5)  # Lower weight
        
        # Calculate overall confidence
        overall_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
        is_hallucination = overall_confidence > self.confidence_threshold
        
        return HallucinationResult(
            is_hallucination=is_hallucination,
            confidence_score=overall_confidence,
            reasons=reasons,
            metadata={
                'uncertainty_score': uncertainty_score,
                'fabrication_score': fabrication_score,
                'response_length': len(response),
                'prompt_length': len(prompt),
                **(metadata or {})
            }
        )
    
    def _detect_uncertainty_patterns(self, text: str) -> float:
        """Detect uncertainty language patterns."""
        matches = len(self.uncertainty_regex.findall(text))
        words = len(text.split())
        return min(matches / max(words / 100, 1), 1.0)  # Normalize by text length
    
    def _detect_fabrication_patterns(self, text: str) -> float:
        """Detect potential fabrication patterns."""
        matches = len(self.fabrication_regex.findall(text))
        sentences = len(text.split('.'))
        return min(matches / max(sentences, 1), 1.0)
    
    def _check_context_consistency(self, response: str, context: str) -> float:
        """Check consistency between response and provided context."""
        # Simple keyword overlap analysis
        response_words = set(response.lower().split())
        context_words = set(context.lower().split())
        
        if not context_words:
            return 0.5  # Neutral if no context
        
        overlap = len(response_words.intersection(context_words))
        return min(overlap / len(context_words), 1.0)
    
    def _assess_response_quality(self, response: str) -> float:
        """Assess general response quality indicators."""
        quality_score = 0.5  # Start neutral
        
        # Length checks
        if len(response) < 10:
            quality_score -= 0.3  # Too short
        elif len(response) > 5000:
            quality_score -= 0.1  # Very long might indicate rambling
        
        # Structure checks
        if '.' in response:
            quality_score += 0.2  # Has sentences
        if response.count('\n') > 0:
            quality_score += 0.1  # Has structure
        
        # Repetition detection
        words = response.split()
        unique_words = set(words)
        if len(words) > 0:
            repetition_ratio = 1 - (len(unique_words) / len(words))
            if repetition_ratio > 0.3:
                quality_score -= 0.2  # High repetition
        
        return max(0.0, min(1.0, quality_score))
    
    def _analyze_specificity(self, response: str) -> float:
        """Analyze specificity level of the response."""
        # Count specific indicators
        numbers = len(re.findall(r'\d+', response))
        dates = len(re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}\b', response))
        names = len(re.findall(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', response))
        
        words = len(response.split())
        if words == 0:
            return 0.0
        
        specificity = (numbers + dates * 2 + names * 2) / words
        return min(specificity, 1.0)

class DriftDetector:
    """Detect model drift in AI responses."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.window_size = self.config.get('window_size', 100)
        self.drift_threshold = self.config.get('drift_threshold', 0.2)
        
        # Historical data storage
        self.latency_history = deque(maxlen=self.window_size)
        self.token_history = deque(maxlen=self.window_size)
        self.quality_history = deque(maxlen=self.window_size)
        self.cost_history = deque(maxlen=self.window_size)
        
        # Baselines (calculated from initial data)
        self.baselines = {}
        self.baseline_calculated = False
    
    def update(self, 
               latency: float,
               input_tokens: int,
               output_tokens: int,
               cost: float,
               response: str,
               metadata: Optional[Dict[str, Any]] = None):
        """Update drift detector with new data point."""
        
        # Calculate quality score (simple heuristic)
        quality_score = self._calculate_quality_score(response, input_tokens, output_tokens)
        
        # Add to history
        self.latency_history.append(latency)
        self.token_history.append(output_tokens)
        self.quality_history.append(quality_score)
        self.cost_history.append(cost)
        
        # Calculate baselines after sufficient data
        if not self.baseline_calculated and len(self.latency_history) >= min(20, self.window_size // 2):
            self._calculate_baselines()
    
    def detect_drift(self) -> List[DriftResult]:
        """Detect drift across all monitored metrics."""
        if not self.baseline_calculated:
            return []
        
        results = []
        
        # Latency drift
        if len(self.latency_history) >= 10:
            drift_result = self._detect_metric_drift(
                'latency',
                list(self.latency_history),
                self.baselines['latency']
            )
            if drift_result:
                results.append(drift_result)
        
        # Token drift
        if len(self.token_history) >= 10:
            drift_result = self._detect_metric_drift(
                'tokens',
                list(self.token_history),
                self.baselines['tokens']
            )
            if drift_result:
                results.append(drift_result)
        
        # Quality drift
        if len(self.quality_history) >= 10:
            drift_result = self._detect_metric_drift(
                'quality',
                list(self.quality_history),
                self.baselines['quality']
            )
            if drift_result:
                results.append(drift_result)
        
        # Cost drift
        if len(self.cost_history) >= 10:
            drift_result = self._detect_metric_drift(
                'cost',
                list(self.cost_history),
                self.baselines['cost']
            )
            if drift_result:
                results.append(drift_result)
        
        return results
    
    def _calculate_baselines(self):
        """Calculate baseline metrics from initial data."""
        if len(self.latency_history) == 0:
            return
        
        self.baselines = {
            'latency': np.mean(list(self.latency_history)),
            'tokens': np.mean(list(self.token_history)),
            'quality': np.mean(list(self.quality_history)),
            'cost': np.mean(list(self.cost_history))
        }
        self.baseline_calculated = True
        logger.info(f"Drift baselines calculated: {self.baselines}")
    
    def _detect_metric_drift(self, 
                           metric_name: str,
                           values: List[float], 
                           baseline: float) -> Optional[DriftResult]:
        """Detect drift for a specific metric."""
        if len(values) < 10:
            return None
        
        # Use recent window for comparison
        recent_window = values[-10:]
        current_mean = np.mean(recent_window)
        
        # Calculate drift score (relative change)
        if baseline == 0:
            drift_score = 0.0
        else:
            drift_score = abs(current_mean - baseline) / baseline
        
        has_drift = drift_score > self.drift_threshold
        
        if has_drift:
            return DriftResult(
                has_drift=True,
                drift_score=drift_score,
                drift_type=metric_name,
                baseline_value=baseline,
                current_value=current_mean,
                metadata={
                    'recent_values': recent_window,
                    'baseline_window_size': len(values),
                    'detection_time': time.time()
                }
            )
        
        return None
    
    def _calculate_quality_score(self, response: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate a simple quality score for the response."""
        score = 0.5  # Start neutral
        
        # Length appropriateness (output should be reasonable vs input)
        if input_tokens > 0:
            ratio = output_tokens / input_tokens
            if 0.5 <= ratio <= 3.0:  # Reasonable ratio
                score += 0.2
            else:
                score -= 0.1
        
        # Response completeness
        if response.endswith('.') or response.endswith('!') or response.endswith('?'):
            score += 0.1  # Proper ending
        
        # Structure
        sentences = response.count('.') + response.count('!') + response.count('?')
        if sentences > 0:
            avg_sentence_length = len(response.split()) / sentences
            if 5 <= avg_sentence_length <= 30:  # Reasonable sentence length
                score += 0.1
        
        # Avoid extreme values
        return max(0.0, min(1.0, score))
    
    def get_drift_summary(self) -> Dict[str, Any]:
        """Get summary of drift detection status."""
        return {
            'baseline_calculated': self.baseline_calculated,
            'baselines': self.baselines.copy() if self.baseline_calculated else {},
            'data_points': {
                'latency': len(self.latency_history),
                'tokens': len(self.token_history),
                'quality': len(self.quality_history), 
                'cost': len(self.cost_history)
            },
            'window_size': self.window_size,
            'drift_threshold': self.drift_threshold
        }
