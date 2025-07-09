import json
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


class LogLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class AuditEvent:
    timestamp: datetime
    event_type: str
    session_id: str
    tool_name: Optional[str]
    level: LogLevel
    message: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['level'] = self.level.value
        return result


class AuditMonitor:
    def __init__(self, log_dir: str = "audit_logs"):
        # Make log directory absolute relative to this file's directory
        if not os.path.isabs(log_dir):
            log_dir = os.path.join(os.path.dirname(__file__), log_dir)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup structured logging
        self.logger = logging.getLogger("audit_monitor")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler for audit logs
        log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
        
        # In-memory storage for real-time monitoring
        self.events: List[AuditEvent] = []
        self.session_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.tool_performance: Dict[str, List[float]] = {}
        self.policy_violations: List[AuditEvent] = []
        
        # Load existing audit data from files
        self._load_existing_audit_data()
    
    def _load_existing_audit_data(self):
        """Load existing audit data from JSONL files to restore session metrics."""
        try:
            events_file = self.log_dir / f"events_{datetime.now().strftime('%Y%m%d')}.jsonl"
            if not events_file.exists():
                return
            
            with open(events_file, 'r') as f:
                for line in f:
                    try:
                        event_data = json.loads(line.strip())
                        event_type = event_data.get('event_type')
                        session_id = event_data.get('session_id')
                        
                        # Reconstruct session metrics from events
                        if event_type == 'session_start':
                            if session_id not in self.session_metrics:
                                self.session_metrics[session_id] = {
                                    "start_time": datetime.fromisoformat(event_data['timestamp']),
                                    "tool_calls": 0,
                                    "successful_calls": 0,
                                    "failed_calls": 0,
                                    "policy_violations": 0,
                                    "total_duration": 0.0
                                }
                        
                        elif event_type == 'tool_call_attempt':
                            if session_id in self.session_metrics:
                                self.session_metrics[session_id]["tool_calls"] += 1
                        
                        elif event_type == 'tool_call_completion':
                            if session_id in self.session_metrics:
                                success = event_data.get('metadata', {}).get('success', False)
                                if success:
                                    self.session_metrics[session_id]["successful_calls"] += 1
                                else:
                                    self.session_metrics[session_id]["failed_calls"] += 1
                        
                        elif event_type == 'policy_violation':
                            if session_id in self.session_metrics:
                                self.session_metrics[session_id]["policy_violations"] += 1
                            
                            # Reconstruct policy violation event
                            violation_event = AuditEvent(
                                timestamp=datetime.fromisoformat(event_data['timestamp']),
                                event_type=event_type,
                                session_id=session_id,
                                tool_name=event_data.get('tool_name'),
                                level=LogLevel(event_data.get('level')),
                                message=event_data.get('message'),
                                metadata=event_data.get('metadata', {})
                            )
                            self.policy_violations.append(violation_event)
                            
                    except (json.JSONDecodeError, ValueError, KeyError) as e:
                        # Skip malformed lines but log the error
                        self.logger.warning(f"Skipping malformed audit log line: {e}")
                        continue
                        
            self.logger.info(f"Loaded audit data for {len(self.session_metrics)} sessions")
            
        except Exception as e:
            self.logger.error(f"Error loading existing audit data: {e}")
    
    def _create_event(self, event_type: str, session_id: str, tool_name: Optional[str], 
                     level: LogLevel, message: str, metadata: Dict[str, Any] = None) -> AuditEvent:
        if metadata is None:
            metadata = {}
        
        event = AuditEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            session_id=session_id,
            tool_name=tool_name,
            level=level,
            message=message,
            metadata=metadata
        )
        
        self.events.append(event)
        self._write_event_to_file(event)
        
        return event
    
    def _write_event_to_file(self, event: AuditEvent):
        event_file = self.log_dir / f"events_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(event_file, 'a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')
    
    def log_session_start(self, session_id: str, metadata: Dict[str, Any] = None):
        self.session_metrics[session_id] = {
            "start_time": datetime.now(),
            "tool_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "policy_violations": 0,
            "total_duration": 0.0
        }
        
        event = self._create_event(
            "session_start",
            session_id,
            None,
            LogLevel.INFO,
            f"Session {session_id} started",
            metadata or {}
        )
        
        self.logger.info(f"Session {session_id} started")
    
    def log_session_end(self, session_id: str, metadata: Dict[str, Any] = None):
        if session_id in self.session_metrics:
            metrics = self.session_metrics[session_id]
            metrics["end_time"] = datetime.now()
            metrics["total_duration"] = (metrics["end_time"] - metrics["start_time"]).total_seconds()
        
        event = self._create_event(
            "session_end",
            session_id,
            None,
            LogLevel.INFO,
            f"Session {session_id} ended",
            metadata or {}
        )
        
        self.logger.info(f"Session {session_id} ended")
    
    def log_tool_call_attempt(self, session_id: str, tool_name: str, arguments: Dict[str, Any]):
        if session_id in self.session_metrics:
            self.session_metrics[session_id]["tool_calls"] += 1
        
        event = self._create_event(
            "tool_call_attempt",
            session_id,
            tool_name,
            LogLevel.INFO,
            f"Attempting to call tool {tool_name}",
            {"arguments": arguments, "attempt_time": datetime.now().isoformat()}
        )
        
        self.logger.info(f"Session {session_id}: Attempting tool call {tool_name}")
    
    def log_tool_call_completion(self, session_id: str, tool_name: str, result: Any, 
                                success: bool, error: Optional[str] = None, 
                                duration: Optional[float] = None):
        if session_id in self.session_metrics:
            if success:
                self.session_metrics[session_id]["successful_calls"] += 1
            else:
                self.session_metrics[session_id]["failed_calls"] += 1
        
        # Track performance metrics
        if duration and tool_name:
            if tool_name not in self.tool_performance:
                self.tool_performance[tool_name] = []
            self.tool_performance[tool_name].append(duration)
        
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"Tool {tool_name} {'completed successfully' if success else 'failed'}"
        
        metadata = {
            "success": success,
            "completion_time": datetime.now().isoformat()
        }
        
        if result is not None:
            metadata["result"] = result
        if error:
            metadata["error"] = error
        if duration:
            metadata["duration_seconds"] = duration
        
        event = self._create_event(
            "tool_call_completion",
            session_id,
            tool_name,
            level,
            message,
            metadata
        )
        
        log_message = f"Session {session_id}: Tool {tool_name} {'completed' if success else 'failed'}"
        if duration:
            log_message += f" in {duration:.2f}s"
        
        if success:
            self.logger.info(log_message)
        else:
            self.logger.error(f"{log_message} - Error: {error}")
    
    def log_policy_violation(self, session_id: str, tool_name: str, violation_reason: str):
        if session_id in self.session_metrics:
            self.session_metrics[session_id]["policy_violations"] += 1
        
        event = self._create_event(
            "policy_violation",
            session_id,
            tool_name,
            LogLevel.WARNING,
            f"Policy violation for tool {tool_name}: {violation_reason}",
            {"violation_reason": violation_reason}
        )
        
        self.policy_violations.append(event)
        self.logger.warning(f"Session {session_id}: Policy violation - {tool_name}: {violation_reason}")
    
    def log_approval_request(self, session_id: str, tool_name: str, arguments: Dict[str, Any]):
        event = self._create_event(
            "approval_request",
            session_id,
            tool_name,
            LogLevel.INFO,
            f"Manual approval requested for tool {tool_name}",
            {"arguments": arguments}
        )
        
        self.logger.info(f"Session {session_id}: Manual approval requested for {tool_name}")
    
    def log_approval_response(self, session_id: str, tool_name: str, approved: bool, 
                             approver: Optional[str] = None):
        event = self._create_event(
            "approval_response",
            session_id,
            tool_name,
            LogLevel.INFO,
            f"Manual approval {'granted' if approved else 'denied'} for tool {tool_name}",
            {"approved": approved, "approver": approver}
        )
        
        self.logger.info(f"Session {session_id}: Approval {'granted' if approved else 'denied'} for {tool_name}")
    
    def get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.session_metrics:
            return {}
        
        metrics = self.session_metrics[session_id].copy()
        
        # Calculate additional metrics
        if "start_time" in metrics:
            if "end_time" not in metrics:
                metrics["duration_seconds"] = (datetime.now() - metrics["start_time"]).total_seconds()
            else:
                metrics["duration_seconds"] = metrics["total_duration"]
        
        # Success rate
        total_calls = metrics.get("tool_calls", 0)
        if total_calls > 0:
            metrics["success_rate"] = metrics.get("successful_calls", 0) / total_calls
        else:
            metrics["success_rate"] = 0.0
        
        return metrics
    
    def get_tool_performance_metrics(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        if tool_name:
            if tool_name not in self.tool_performance:
                return {}
            
            durations = self.tool_performance[tool_name]
            return {
                "tool_name": tool_name,
                "call_count": len(durations),
                "avg_duration": sum(durations) / len(durations) if durations else 0,
                "min_duration": min(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0,
                "total_duration": sum(durations)
            }
        
        # Return metrics for all tools
        metrics = {}
        for tool, durations in self.tool_performance.items():
            metrics[tool] = {
                "call_count": len(durations),
                "avg_duration": sum(durations) / len(durations) if durations else 0,
                "min_duration": min(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0,
                "total_duration": sum(durations)
            }
        
        return metrics
    
    def get_policy_violations(self, session_id: Optional[str] = None, 
                             since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        violations = self.policy_violations
        
        if session_id:
            violations = [v for v in violations if v.session_id == session_id]
        
        if since:
            violations = [v for v in violations if v.timestamp >= since]
        
        return [v.to_dict() for v in violations]
    
    def get_recent_events(self, session_id: Optional[str] = None, 
                         event_type: Optional[str] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        events = self.events
        
        if session_id:
            events = [e for e in events if e.session_id == session_id]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Sort by timestamp descending and limit
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
        
        return [e.to_dict() for e in events]
    
    def generate_compliance_report(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        
        # Filter events for the report period
        events = self.events
        if session_id:
            events = [e for e in events if e.session_id == session_id]
        
        recent_events = [e for e in events if e.timestamp >= day_ago]
        
        # Calculate metrics from session_metrics (more accurate)
        if session_id:
            # Report for specific session
            session_metrics = self.session_metrics.get(session_id, {})
            total_sessions = 1 if session_id in self.session_metrics else 0
            tool_calls = session_metrics.get("tool_calls", 0)
            successful_calls = session_metrics.get("successful_calls", 0)
            failed_calls = session_metrics.get("failed_calls", 0)
            policy_violations = session_metrics.get("policy_violations", 0)
        else:
            # Report for all sessions
            total_sessions = len(self.session_metrics)
            tool_calls = sum(metrics.get("tool_calls", 0) for metrics in self.session_metrics.values())
            successful_calls = sum(metrics.get("successful_calls", 0) for metrics in self.session_metrics.values())
            failed_calls = sum(metrics.get("failed_calls", 0) for metrics in self.session_metrics.values())
            policy_violations = sum(metrics.get("policy_violations", 0) for metrics in self.session_metrics.values())
        
        # Calculate success rate
        success_rate = successful_calls / tool_calls if tool_calls > 0 else 0.0
        
        return {
            "report_period": {
                "start": day_ago.isoformat(),
                "end": now.isoformat()
            },
            "session_id": session_id,
            "total_sessions": total_sessions,
            "policy_violations": policy_violations,
            "success_rate": success_rate,
            "summary": {
                "total_events": len(recent_events),
                "tool_calls": tool_calls,
                "successful_calls": successful_calls,
                "failed_calls": failed_calls,
                "policy_violations": policy_violations,
                "success_rate": success_rate,
                "compliance_score": max(0, 100 - (policy_violations * 10))  # Simple scoring
            },
            "tool_performance": self.get_tool_performance_metrics(),
            "recent_violations": self.get_policy_violations(session_id, day_ago),
            "violations": [f"Session {v.session_id}: {v.metadata.get('violation_reason', 'Unknown violation')}" for v in self.policy_violations if not session_id or v.session_id == session_id]
        }