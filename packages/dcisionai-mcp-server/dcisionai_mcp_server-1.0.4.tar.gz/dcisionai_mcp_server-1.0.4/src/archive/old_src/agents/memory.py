#!/usr/bin/env python3
"""
AgentMemoryLayer - Cross-Session Learning System
===============================================

This module implements persistent agent memory that learns from optimization patterns.
This is a key component of the AgentCore architecture that creates a defensible moat.

Key Features:
- Cross-session learning and pattern recognition
- Predictive optimization based on historical data
- Success metrics tracking and user feedback integration
- Domain knowledge accumulation

Author: DcisionAI Team
Copyright (c) 2025 DcisionAI. All rights reserved.
"""

import json
import time
import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import pickle

logger = logging.getLogger(__name__)

@dataclass
class OptimizationRecord:
    """Record of a single optimization for learning."""
    timestamp: float
    intent: str
    entities: List[str]
    model_complexity: str
    objective_value: float
    solve_time: float
    status: str
    user_feedback: Optional[float] = None
    session_id: Optional[str] = None
    query_hash: str = ""

class AgentMemoryLayer:
    """
    Persistent agent memory that learns from optimization patterns.
    
    MOAT: Cross-session learning, pattern recognition, predictive optimization.
    This creates a data moat that grows stronger with usage.
    """
    
    def __init__(self, memory_file: str = "agent_memory.pkl"):
        self.memory_file = Path(memory_file)
        self.optimization_history: List[OptimizationRecord] = []
        self.pattern_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.success_metrics: Dict[str, float] = {}
        self.domain_knowledge: Dict[str, Any] = {}
        
        # Load existing memory
        self._load_memory()
        
        logger.info(f"🧠 AgentMemoryLayer initialized with {len(self.optimization_history)} historical optimizations")
    
    def store_optimization(self, intent: str, entities: List[str], model_complexity: str,
                          objective_value: float, solve_time: float, status: str,
                          user_feedback: Optional[float] = None, session_id: Optional[str] = None,
                          query: str = "") -> None:
        """
        Store optimization with success metrics for learning.
        
        Args:
            intent: The classified intent (e.g., "production_optimization")
            entities: Key entities from the query
            model_complexity: Complexity level of the model
            objective_value: The optimization result value
            solve_time: Time taken to solve
            status: Optimization status ("optimal", "infeasible", etc.)
            user_feedback: User rating (0-1) if available
            session_id: Session identifier for cross-session learning
            query: Original query for pattern matching
        """
        # Create query hash for deduplication
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()[:8]
        
        record = OptimizationRecord(
            timestamp=time.time(),
            intent=intent,
            entities=entities,
            model_complexity=model_complexity,
            objective_value=objective_value,
            solve_time=solve_time,
            status=status,
            user_feedback=user_feedback,
            session_id=session_id,
            query_hash=query_hash
        )
        
        self.optimization_history.append(record)
        
        # Learn patterns
        self._update_pattern_cache(record)
        
        # Update success metrics
        self._update_success_metrics(record)
        
        # Save memory periodically
        if len(self.optimization_history) % 10 == 0:
            self._save_memory()
        
        logger.info(f"📚 Stored optimization: {intent} -> {status} (obj: {objective_value:.2f})")
    
    def suggest_optimization_strategy(self, intent: str, entities: List[str]) -> Dict[str, Any]:
        """
        Use historical data to suggest best optimization approach.
        
        MOAT: Predictive optimization based on learned patterns.
        This gives us a significant advantage over stateless systems.
        
        Args:
            intent: The classified intent
            entities: Key entities from the query
            
        Returns:
            Strategy suggestion with confidence metrics
        """
        pattern_key = self._generate_pattern_key(intent, entities)
        
        if pattern_key in self.pattern_cache:
            history = self.pattern_cache[pattern_key]
            
            # Calculate success metrics
            total_optimizations = len(history)
            successful_optimizations = sum(1 for h in history if h['status'] == 'optimal')
            success_rate = successful_optimizations / total_optimizations if total_optimizations > 0 else 0
            
            avg_solve_time = sum(h['solve_time'] for h in history) / total_optimizations
            avg_objective_value = sum(h['objective_value'] for h in history if h['objective_value'] is not None) / total_optimizations
            
            # Calculate confidence based on data quality
            confidence = min(0.95, 0.3 + (total_optimizations * 0.1) + (success_rate * 0.4))
            
            return {
                'strategy': 'learned_pattern',
                'confidence': confidence,
                'expected_solve_time': avg_solve_time,
                'success_probability': success_rate,
                'expected_objective_value': avg_objective_value,
                'similar_optimizations': total_optimizations,
                'pattern_key': pattern_key,
                'recommendation': self._generate_recommendation(history, success_rate)
            }
        
        return {
            'strategy': 'explore',
            'confidence': 0.0,
            'expected_solve_time': 5.0,  # Default estimate
            'success_probability': 0.7,  # Default estimate
            'similar_optimizations': 0,
            'pattern_key': pattern_key,
            'recommendation': 'No historical data available. Using default optimization approach.'
        }
    
    def get_optimization_insights(self, intent: str = None) -> Dict[str, Any]:
        """
        Get insights about optimization patterns and performance.
        
        Returns:
            Comprehensive insights for monitoring and improvement
        """
        if intent:
            # Filter by intent
            relevant_records = [r for r in self.optimization_history if r.intent == intent]
        else:
            relevant_records = self.optimization_history
        
        if not relevant_records:
            return {'message': 'No optimization data available'}
        
        # Calculate insights
        total_optimizations = len(relevant_records)
        successful_optimizations = sum(1 for r in relevant_records if r.status == 'optimal')
        success_rate = successful_optimizations / total_optimizations
        
        avg_solve_time = sum(r.solve_time for r in relevant_records) / total_optimizations
        avg_objective_value = sum(r.objective_value for r in relevant_records if r.objective_value is not None) / total_optimizations
        
        # Intent distribution
        intent_counts = {}
        for record in relevant_records:
            intent_counts[record.intent] = intent_counts.get(record.intent, 0) + 1
        
        # Recent performance (last 24 hours)
        recent_cutoff = time.time() - (24 * 60 * 60)
        recent_records = [r for r in relevant_records if r.timestamp > recent_cutoff]
        recent_success_rate = sum(1 for r in recent_records if r.status == 'optimal') / len(recent_records) if recent_records else 0
        
        return {
            'total_optimizations': total_optimizations,
            'success_rate': success_rate,
            'recent_success_rate': recent_success_rate,
            'avg_solve_time': avg_solve_time,
            'avg_objective_value': avg_objective_value,
            'intent_distribution': intent_counts,
            'recent_optimizations_24h': len(recent_records),
            'memory_size': len(self.optimization_history),
            'pattern_cache_size': len(self.pattern_cache),
            'top_patterns': self._get_top_patterns()
        }
    
    def _update_pattern_cache(self, record: OptimizationRecord) -> None:
        """Learn patterns from optimization records."""
        pattern_key = self._generate_pattern_key(record.intent, record.entities)
        
        if pattern_key not in self.pattern_cache:
            self.pattern_cache[pattern_key] = []
        
        # Store pattern data
        pattern_data = {
            'timestamp': record.timestamp,
            'objective_value': record.objective_value,
            'solve_time': record.solve_time,
            'status': record.status,
            'model_complexity': record.model_complexity,
            'user_feedback': record.user_feedback
        }
        
        self.pattern_cache[pattern_key].append(pattern_data)
        
        # Keep only recent patterns (last 100 per pattern)
        if len(self.pattern_cache[pattern_key]) > 100:
            self.pattern_cache[pattern_key] = self.pattern_cache[pattern_key][-100:]
    
    def _update_success_metrics(self, record: OptimizationRecord) -> None:
        """Update success metrics for monitoring."""
        intent = record.intent
        
        if intent not in self.success_metrics:
            self.success_metrics[intent] = {
                'total': 0,
                'successful': 0,
                'avg_solve_time': 0.0,
                'avg_objective_value': 0.0
            }
        
        metrics = self.success_metrics[intent]
        metrics['total'] += 1
        
        if record.status == 'optimal':
            metrics['successful'] += 1
        
        # Update averages
        metrics['avg_solve_time'] = (metrics['avg_solve_time'] * (metrics['total'] - 1) + record.solve_time) / metrics['total']
        
        if record.objective_value is not None:
            metrics['avg_objective_value'] = (metrics['avg_objective_value'] * (metrics['total'] - 1) + record.objective_value) / metrics['total']
    
    def _generate_pattern_key(self, intent: str, entities: List[str]) -> str:
        """Generate a pattern key for caching."""
        # Sort entities for consistent keys
        sorted_entities = sorted(entities)
        pattern_data = f"{intent}:{','.join(sorted_entities)}"
        return hashlib.md5(pattern_data.encode()).hexdigest()[:12]
    
    def _generate_recommendation(self, history: List[Dict[str, Any]], success_rate: float) -> str:
        """Generate human-readable recommendation based on history."""
        if success_rate > 0.9:
            return "High success rate pattern. Expected to work well."
        elif success_rate > 0.7:
            return "Good success rate pattern. Should work reliably."
        elif success_rate > 0.5:
            return "Moderate success rate pattern. May need tuning."
        else:
            return "Low success rate pattern. Consider alternative approaches."
    
    def _get_top_patterns(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top patterns by frequency and success rate."""
        pattern_stats = []
        
        for pattern_key, history in self.pattern_cache.items():
            if len(history) >= 3:  # Only patterns with sufficient data
                success_rate = sum(1 for h in history if h['status'] == 'optimal') / len(history)
                avg_solve_time = sum(h['solve_time'] for h in history) / len(history)
                
                pattern_stats.append({
                    'pattern_key': pattern_key,
                    'frequency': len(history),
                    'success_rate': success_rate,
                    'avg_solve_time': avg_solve_time
                })
        
        # Sort by frequency and success rate
        pattern_stats.sort(key=lambda x: (x['frequency'], x['success_rate']), reverse=True)
        return pattern_stats[:limit]
    
    def _load_memory(self) -> None:
        """Load memory from disk."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'rb') as f:
                    data = pickle.load(f)
                    self.optimization_history = data.get('optimization_history', [])
                    self.pattern_cache = data.get('pattern_cache', {})
                    self.success_metrics = data.get('success_metrics', {})
                    self.domain_knowledge = data.get('domain_knowledge', {})
                
                logger.info(f"📖 Loaded memory: {len(self.optimization_history)} optimizations, {len(self.pattern_cache)} patterns")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load memory: {e}")
                self.optimization_history = []
                self.pattern_cache = {}
                self.success_metrics = {}
                self.domain_knowledge = {}
    
    def _save_memory(self) -> None:
        """Save memory to disk."""
        try:
            data = {
                'optimization_history': self.optimization_history,
                'pattern_cache': self.pattern_cache,
                'success_metrics': self.success_metrics,
                'domain_knowledge': self.domain_knowledge,
                'saved_at': time.time()
            }
            
            with open(self.memory_file, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"💾 Saved memory: {len(self.optimization_history)} optimizations")
        except Exception as e:
            logger.error(f"❌ Failed to save memory: {e}")
    
    def clear_memory(self) -> None:
        """Clear all memory (for testing)."""
        self.optimization_history = []
        self.pattern_cache = {}
        self.success_metrics = {}
        self.domain_knowledge = {}
        self._save_memory()
        logger.info("🗑️ Memory cleared")
    
    def export_memory(self, filepath: str) -> None:
        """Export memory to JSON for analysis."""
        export_data = {
            'optimization_history': [asdict(record) for record in self.optimization_history],
            'pattern_cache': self.pattern_cache,
            'success_metrics': self.success_metrics,
            'domain_knowledge': self.domain_knowledge,
            'exported_at': time.time()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"📤 Memory exported to {filepath}")


# Global memory instance
agent_memory = AgentMemoryLayer()
