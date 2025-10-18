#!/usr/bin/env python3
"""
AgentCoordinator - Intelligent Agent Orchestration System
========================================================

This module implements intelligent coordination of multiple AI agents with
deduplication, parallel processing, and priority management. This is a key
component of the AgentCore architecture that provides intelligent orchestration.

Key Features:
- Intelligent agent scheduling and load balancing
- Duplicate request detection and deduplication
- Parallel processing when possible
- Priority-based request handling
- Agent state management and coordination
- Performance optimization through smart scheduling

Author: DcisionAI Team
Copyright (c) 2025 DcisionAI. All rights reserved.
"""

import asyncio
import json
import time
import hashlib
import logging
import threading
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Status of individual agents."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

class RequestPriority(Enum):
    """Priority levels for optimization requests."""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10

@dataclass
class AgentState:
    """State of an individual agent."""
    agent_id: str
    status: AgentStatus
    current_request_id: Optional[str]
    queue_size: int
    last_activity: float
    total_requests: int
    success_rate: float
    avg_processing_time: float

@dataclass
class OptimizationRequest:
    """Represents an optimization request."""
    request_id: str
    query: str
    priority: RequestPriority
    session_id: Optional[str]
    timestamp: float
    status: str
    assigned_agents: List[str]
    estimated_completion: float

@dataclass
class CoordinationResult:
    """Result of agent coordination."""
    request_id: str
    status: str
    execution_plan: Dict[str, Any]
    estimated_time: float
    agents_assigned: List[str]
    parallel_execution: bool
    deduplication_info: Optional[Dict[str, Any]]

class AgentCoordinator:
    """
    Intelligent agent coordination system with deduplication and parallel processing.
    
    MOAT: Intelligent agent orchestration with priority management, duplicate detection,
    and parallel processing. This creates a significant efficiency advantage over
    stateless systems that can't coordinate or deduplicate.
    """
    
    def __init__(self, max_concurrent_requests: int = 10):
        self.max_concurrent_requests = max_concurrent_requests
        
        # Agent state management
        self.agent_states: Dict[str, AgentState] = {
            'intent_agent': AgentState(
                agent_id='intent_agent',
                status=AgentStatus.IDLE,
                current_request_id=None,
                queue_size=0,
                last_activity=time.time(),
                total_requests=0,
                success_rate=1.0,
                avg_processing_time=2.0
            ),
            'data_agent': AgentState(
                agent_id='data_agent',
                status=AgentStatus.IDLE,
                current_request_id=None,
                queue_size=0,
                last_activity=time.time(),
                total_requests=0,
                success_rate=1.0,
                avg_processing_time=3.0
            ),
            'model_agent': AgentState(
                agent_id='model_agent',
                status=AgentStatus.IDLE,
                current_request_id=None,
                queue_size=0,
                last_activity=time.time(),
                total_requests=0,
                success_rate=1.0,
                avg_processing_time=4.0
            ),
            'solver_agent': AgentState(
                agent_id='solver_agent',
                status=AgentStatus.IDLE,
                current_request_id=None,
                queue_size=0,
                last_activity=time.time(),
                total_requests=0,
                success_rate=1.0,
                avg_processing_time=1.0
            )
        }
        
        # Request management
        self.active_requests: Dict[str, OptimizationRequest] = {}
        self.request_queue: deque = deque()
        self.completed_requests: Dict[str, OptimizationRequest] = {}
        
        # Deduplication system
        self.query_signatures: Dict[str, str] = {}  # query_hash -> request_id
        self.similar_requests: Dict[str, List[str]] = defaultdict(list)
        
        # Performance tracking
        self.coordination_history: List[Dict[str, Any]] = []
        self.parallel_execution_count = 0
        self.deduplication_count = 0
        
        # Thread safety
        self.coordination_lock = threading.RLock()
        
        logger.info(f"🎯 AgentCoordinator initialized with {len(self.agent_states)} agents")
    
    async def coordinate_optimization(self, query: str, priority: int = 5, 
                                    session_id: Optional[str] = None) -> CoordinationResult:
        """
        Intelligently coordinate agents for optimization request.
        
        Args:
            query: The optimization query
            priority: Request priority (1-10)
            session_id: Optional session identifier
            
        Returns:
            CoordinationResult with execution plan
        """
        with self.coordination_lock:
            request_id = str(uuid.uuid4())
            request_priority = RequestPriority(min(max(priority, 1), 10))
            
            logger.info(f"🎯 Coordinating optimization: {query[:50]}... (priority: {request_priority.value})")
            
            # Step 1: Check for duplicate requests
            dedup_info = self._check_duplicate_request(query)
            if dedup_info:
                self.deduplication_count += 1
                logger.info(f"🔄 Duplicate request detected: {dedup_info['similar_request_id']}")
                return CoordinationResult(
                    request_id=request_id,
                    status="deduplicated",
                    execution_plan={},
                    estimated_time=0.0,
                    agents_assigned=[],
                    parallel_execution=False,
                    deduplication_info=dedup_info
                )
            
            # Step 2: Check system capacity
            if len(self.active_requests) >= self.max_concurrent_requests:
                # Queue the request
                request = OptimizationRequest(
                    request_id=request_id,
                    query=query,
                    priority=request_priority,
                    session_id=session_id,
                    timestamp=time.time(),
                    status="queued",
                    assigned_agents=[],
                    estimated_completion=0.0
                )
                self.request_queue.append(request)
                
                logger.info(f"⏳ Request queued: {request_id} (queue size: {len(self.request_queue)})")
                return CoordinationResult(
                    request_id=request_id,
                    status="queued",
                    execution_plan={"queue_position": len(self.request_queue)},
                    estimated_time=self._estimate_queue_wait_time(),
                    agents_assigned=[],
                    parallel_execution=False,
                    deduplication_info=None
                )
            
            # Step 3: Create execution plan
            execution_plan = self._create_execution_plan(query, request_priority)
            
            # Step 4: Assign agents
            agents_assigned = self._assign_agents(execution_plan, request_id)
            
            # Step 5: Create request record
            request = OptimizationRequest(
                request_id=request_id,
                query=query,
                priority=request_priority,
                session_id=session_id,
                timestamp=time.time(),
                status="active",
                assigned_agents=agents_assigned,
                estimated_completion=time.time() + execution_plan['estimated_time']
            )
            
            self.active_requests[request_id] = request
            
            # Step 6: Update agent states
            self._update_agent_states(agents_assigned, request_id)
            
            # Step 7: Record coordination
            self._record_coordination(request_id, execution_plan, agents_assigned)
            
            logger.info(f"✅ Request coordinated: {request_id} -> {len(agents_assigned)} agents")
            
            return CoordinationResult(
                request_id=request_id,
                status="active",
                execution_plan=execution_plan,
                estimated_time=execution_plan['estimated_time'],
                agents_assigned=agents_assigned,
                parallel_execution=execution_plan.get('parallel_execution', False),
                deduplication_info=None
            )
    
    def complete_request(self, request_id: str, success: bool, processing_time: float):
        """Mark a request as completed and update agent states."""
        with self.coordination_lock:
            if request_id in self.active_requests:
                request = self.active_requests.pop(request_id)
                request.status = "completed" if success else "failed"
                
                # Update agent states
                for agent_id in request.assigned_agents:
                    if agent_id in self.agent_states:
                        agent = self.agent_states[agent_id]
                        agent.status = AgentStatus.IDLE
                        agent.current_request_id = None
                        agent.last_activity = time.time()
                        agent.total_requests += 1
                        
                        # Update success rate
                        if agent.total_requests > 0:
                            current_success_rate = agent.success_rate
                            agent.success_rate = ((current_success_rate * (agent.total_requests - 1)) + (1.0 if success else 0.0)) / agent.total_requests
                        
                        # Update average processing time
                        if agent.avg_processing_time > 0:
                            agent.avg_processing_time = (agent.avg_processing_time + processing_time) / 2
                        else:
                            agent.avg_processing_time = processing_time
                
                # Store completed request
                self.completed_requests[request_id] = request
                
                # Process queue if there are waiting requests
                if self.request_queue:
                    self._process_queue()
                
                logger.info(f"✅ Request completed: {request_id} (success: {success}, time: {processing_time:.2f}s)")
    
    def get_coordination_insights(self) -> Dict[str, Any]:
        """Get comprehensive coordination insights."""
        with self.coordination_lock:
            # Calculate agent utilization
            agent_utilization = {}
            for agent_id, agent in self.agent_states.items():
                utilization = 0.0
                if agent.status == AgentStatus.BUSY:
                    utilization = 1.0
                elif agent.queue_size > 0:
                    utilization = min(agent.queue_size / 5.0, 1.0)  # Assume max queue of 5
                
                agent_utilization[agent_id] = {
                    'status': agent.status.value,
                    'utilization': utilization,
                    'total_requests': agent.total_requests,
                    'success_rate': agent.success_rate,
                    'avg_processing_time': agent.avg_processing_time
                }
            
            # Calculate system metrics
            total_requests = len(self.completed_requests) + len(self.active_requests)
            success_rate = 0.0
            if total_requests > 0:
                successful_requests = sum(1 for req in self.completed_requests.values() if req.status == "completed")
                success_rate = successful_requests / total_requests
            
            # Calculate parallel execution rate
            parallel_rate = 0.0
            if len(self.coordination_history) > 0:
                parallel_executions = sum(1 for coord in self.coordination_history if coord.get('parallel_execution', False))
                parallel_rate = parallel_executions / len(self.coordination_history)
            
            return {
                'agent_utilization': agent_utilization,
                'system_metrics': {
                    'active_requests': len(self.active_requests),
                    'queued_requests': len(self.request_queue),
                    'completed_requests': len(self.completed_requests),
                    'total_requests': total_requests,
                    'success_rate': success_rate,
                    'parallel_execution_rate': parallel_rate,
                    'deduplication_count': self.deduplication_count,
                    'parallel_execution_count': self.parallel_execution_count
                },
                'performance_insights': {
                    'avg_agent_utilization': sum(agent_utilization[aid]['utilization'] for aid in agent_utilization) / len(agent_utilization),
                    'most_utilized_agent': max(agent_utilization.keys(), key=lambda aid: agent_utilization[aid]['utilization']),
                    'least_utilized_agent': min(agent_utilization.keys(), key=lambda aid: agent_utilization[aid]['utilization']),
                    'system_load': len(self.active_requests) / self.max_concurrent_requests
                }
            }
    
    def _check_duplicate_request(self, query: str) -> Optional[Dict[str, Any]]:
        """Check if this is a duplicate or very similar request."""
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()[:12]
        
        # Check for exact duplicates
        if query_hash in self.query_signatures:
            similar_request_id = self.query_signatures[query_hash]
            if similar_request_id in self.active_requests:
                return {
                    'type': 'exact_duplicate',
                    'similar_request_id': similar_request_id,
                    'similarity_score': 1.0,
                    'estimated_time_saved': 5.0  # seconds
                }
        
        # Check for similar requests (semantic similarity)
        for active_id, request in self.active_requests.items():
            similarity = self._calculate_query_similarity(query, request.query)
            if similarity > 0.85:  # 85% similarity threshold
                return {
                    'type': 'similar_request',
                    'similar_request_id': active_id,
                    'similarity_score': similarity,
                    'estimated_time_saved': 3.0  # seconds
                }
        
        # Store query signature
        self.query_signatures[query_hash] = query_hash
        
        return None
    
    def _calculate_query_similarity(self, query1: str, query2: str) -> float:
        """Calculate semantic similarity between two queries."""
        # Simple word-based similarity (can be enhanced with embeddings)
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _create_execution_plan(self, query: str, priority: RequestPriority) -> Dict[str, Any]:
        """Create intelligent execution plan based on query and system state."""
        plan = {
            'stages': [],
            'estimated_time': 0.0,
            'parallel_execution': False,
            'priority': priority.value
        }
        
        # Analyze query complexity
        complexity = self._analyze_query_complexity(query)
        
        # Determine if agents can run in parallel
        can_parallelize = self._can_parallelize_agents()
        
        if can_parallelize and complexity < 0.7:
            # Parallel execution: Intent and Data agents can run simultaneously
            plan['stages'] = [
                {
                    'stage': 'parallel',
                    'agents': ['intent_agent', 'data_agent'],
                    'estimated_time': 3.0
                },
                {
                    'stage': 'sequential',
                    'agents': ['model_agent'],
                    'estimated_time': 4.0
                },
                {
                    'stage': 'sequential',
                    'agents': ['solver_agent'],
                    'estimated_time': 1.0
                }
            ]
            plan['parallel_execution'] = True
            plan['estimated_time'] = 8.0  # Parallel execution is faster
            self.parallel_execution_count += 1
        else:
            # Sequential execution
            plan['stages'] = [
                {
                    'stage': 'sequential',
                    'agents': ['intent_agent'],
                    'estimated_time': 2.0
                },
                {
                    'stage': 'sequential',
                    'agents': ['data_agent'],
                    'estimated_time': 3.0
                },
                {
                    'stage': 'sequential',
                    'agents': ['model_agent'],
                    'estimated_time': 4.0
                },
                {
                    'stage': 'sequential',
                    'agents': ['solver_agent'],
                    'estimated_time': 1.0
                }
            ]
            plan['estimated_time'] = 10.0
        
        return plan
    
    def _analyze_query_complexity(self, query: str) -> float:
        """Analyze query complexity (0.0 = simple, 1.0 = complex)."""
        complexity_indicators = [
            'multiple', 'several', 'various', 'different',
            'complex', 'sophisticated', 'advanced',
            'optimize', 'minimize', 'maximize',
            'constraints', 'requirements', 'conditions'
        ]
        
        query_lower = query.lower()
        complexity_score = 0.0
        
        for indicator in complexity_indicators:
            if indicator in query_lower:
                complexity_score += 0.1
        
        # Length factor
        word_count = len(query.split())
        if word_count > 20:
            complexity_score += 0.3
        elif word_count > 10:
            complexity_score += 0.1
        
        return min(complexity_score, 1.0)
    
    def _can_parallelize_agents(self) -> bool:
        """Check if agents can run in parallel based on current load."""
        # Check if intent and data agents are available
        intent_available = self.agent_states['intent_agent'].status == AgentStatus.IDLE
        data_available = self.agent_states['data_agent'].status == AgentStatus.IDLE
        
        return intent_available and data_available
    
    def _assign_agents(self, execution_plan: Dict[str, Any], request_id: str) -> List[str]:
        """Assign agents based on execution plan."""
        assigned_agents = []
        
        for stage in execution_plan['stages']:
            for agent_id in stage['agents']:
                if agent_id in self.agent_states:
                    agent = self.agent_states[agent_id]
                    if agent.status == AgentStatus.IDLE:
                        agent.status = AgentStatus.BUSY
                        agent.current_request_id = request_id
                        assigned_agents.append(agent_id)
                    else:
                        logger.warning(f"⚠️ Agent {agent_id} not available for request {request_id}")
        
        return assigned_agents
    
    def _update_agent_states(self, agents_assigned: List[str], request_id: str):
        """Update agent states after assignment."""
        for agent_id in agents_assigned:
            if agent_id in self.agent_states:
                agent = self.agent_states[agent_id]
                agent.status = AgentStatus.BUSY
                agent.current_request_id = request_id
                agent.last_activity = time.time()
    
    def _estimate_queue_wait_time(self) -> float:
        """Estimate wait time for queued requests."""
        if not self.request_queue:
            return 0.0
        
        # Simple estimation based on average processing time
        avg_processing_time = 8.0  # seconds
        queue_position = len(self.request_queue)
        
        return queue_position * avg_processing_time
    
    def _process_queue(self):
        """Process queued requests when capacity becomes available."""
        if not self.request_queue or len(self.active_requests) >= self.max_concurrent_requests:
            return
        
        # Get highest priority request from queue
        queued_request = self.request_queue.popleft()
        
        # Create execution plan and assign agents
        execution_plan = self._create_execution_plan(queued_request.query, queued_request.priority)
        agents_assigned = self._assign_agents(execution_plan, queued_request.request_id)
        
        # Update request status
        queued_request.status = "active"
        queued_request.assigned_agents = agents_assigned
        queued_request.estimated_completion = time.time() + execution_plan['estimated_time']
        
        # Move to active requests
        self.active_requests[queued_request.request_id] = queued_request
        
        logger.info(f"🔄 Processed queued request: {queued_request.request_id}")
    
    def _record_coordination(self, request_id: str, execution_plan: Dict[str, Any], agents_assigned: List[str]):
        """Record coordination for analytics."""
        coordination_record = {
            'request_id': request_id,
            'timestamp': time.time(),
            'execution_plan': execution_plan,
            'agents_assigned': agents_assigned,
            'parallel_execution': execution_plan.get('parallel_execution', False)
        }
        
        self.coordination_history.append(coordination_record)
        
        # Keep only recent history (last 100 coordinations)
        if len(self.coordination_history) > 100:
            self.coordination_history = self.coordination_history[-100:]


# Global coordinator instance
agent_coordinator = AgentCoordinator()
