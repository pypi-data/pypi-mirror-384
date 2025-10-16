"""
Update plan resource management for Maven dependency remediation.

Provides structured storage and retrieval of update plans with progress tracking
following enterprise workflow patterns with full data validation.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """Task completion status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class UpdatePriority(str, Enum):
    """Update priority levels following enterprise workflow pattern."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class UpdateTask(BaseModel):
    """Individual update task within a plan."""

    task_id: str = Field(..., description="Unique task identifier")
    dependency: str = Field(..., description="Maven coordinates")
    current_version: str = Field(..., description="Current version")
    target_version: str = Field(..., description="Target version")
    update_type: str = Field(..., description="MAJOR/MINOR/PATCH")
    priority: UpdatePriority = Field(..., description="Task priority")
    complexity: str = Field(..., description="LOW/MEDIUM/HIGH")
    file_location: str = Field(..., description="POM file to modify")
    line_number: Optional[int] = Field(None, description="Line number for change")
    change_description: str = Field(..., description="Description of required change")
    traceability_link: str = Field(..., description="Link to triage finding")
    cve_ids: List[str] = Field(default_factory=list, description="Related CVE IDs")
    testing_requirements: List[str] = Field(
        default_factory=list, description="Required tests"
    )
    acceptance_criteria: List[str] = Field(
        default_factory=list, description="Success criteria"
    )
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status")
    estimated_effort_hours: float = Field(default=1.0, description="Estimated effort")


class PlanPhase(BaseModel):
    """Plan phase containing related tasks."""

    phase_id: str = Field(..., description="Phase identifier")
    phase_name: str = Field(..., description="Human-readable phase name")
    priority: UpdatePriority = Field(..., description="Phase priority")
    description: str = Field(..., description="Phase description")
    prerequisites: List[str] = Field(
        default_factory=list, description="Required prerequisites"
    )
    tasks: List[UpdateTask] = Field(
        default_factory=list, description="Tasks in this phase"
    )
    success_criteria: List[str] = Field(
        default_factory=list, description="Phase success criteria"
    )
    estimated_effort_hours: float = Field(default=0.0, description="Total phase effort")


class PlanMetadata(BaseModel):
    """Plan metadata following enterprise workflow pattern."""

    plan_id: str = Field(..., description="Unique plan identifier")
    service_name: str = Field(..., description="Service being updated")
    triage_report_id: str = Field(..., description="Source triage report ID")
    created_timestamp: str = Field(..., description="Plan creation timestamp")
    priority_filter: List[str] = Field(..., description="Priorities included in plan")
    total_updates: int = Field(..., description="Total number of updates")
    total_estimated_hours: float = Field(..., description="Total estimated effort")


class UpdatePlan(BaseModel):
    """Complete update plan structure following enterprise workflow pattern."""

    metadata: PlanMetadata
    phases: List[PlanPhase] = Field(default_factory=list)
    version_control_strategy: Dict[str, str] = Field(default_factory=dict)
    testing_strategy: Dict[str, Any] = Field(default_factory=dict)
    deployment_strategy: Dict[str, Any] = Field(default_factory=dict)
    progress_summary: Dict[str, int] = Field(default_factory=dict)


class UpdatePlanResource:
    """Manages update plan storage and progress tracking following enterprise patterns."""

    def __init__(self):
        self._plans: Dict[str, UpdatePlan] = {}
        self._history: Dict[str, List[UpdatePlan]] = {}

    async def get_plan(self, service_name: str) -> Optional[UpdatePlan]:
        """Retrieve the latest update plan for a service."""
        return self._plans.get(service_name)

    async def save_plan(
        self, service_name: str, plan_data: Dict[str, Any], triage_report_id: str
    ) -> UpdatePlan:
        """Save an update plan with full structure validation."""
        timestamp = datetime.now().isoformat()
        plan_id = f"{service_name}-plan-{timestamp[:10]}"

        # Create metadata
        metadata = PlanMetadata(
            plan_id=plan_id,
            service_name=service_name,
            triage_report_id=triage_report_id,
            created_timestamp=timestamp,
            priority_filter=plan_data.get("priority_filter", ["CRITICAL", "HIGH"]),
            total_updates=len(plan_data.get("all_tasks", [])),
            total_estimated_hours=sum(
                task.get("estimated_effort_hours", 1.0)
                for task in plan_data.get("all_tasks", [])
            ),
        )

        # Create phases with tasks
        phases = []
        for phase_data in plan_data.get("phases", []):
            tasks = [UpdateTask(**task) for task in phase_data.get("tasks", [])]
            phase = PlanPhase(
                **{k: v for k, v in phase_data.items() if k != "tasks"},
                tasks=tasks,
                estimated_effort_hours=sum(
                    task.estimated_effort_hours for task in tasks
                ),
            )
            phases.append(phase)

        # Create complete plan
        plan = UpdatePlan(
            metadata=metadata,
            phases=phases,
            version_control_strategy=plan_data.get("version_control_strategy", {}),
            testing_strategy=plan_data.get("testing_strategy", {}),
            deployment_strategy=plan_data.get("deployment_strategy", {}),
            progress_summary=self._calculate_progress_summary(phases),
        )

        # Store plan
        self._plans[service_name] = plan

        # Store in history
        if service_name not in self._history:
            self._history[service_name] = []
        self._history[service_name].append(plan)

        return plan

    async def update_task_status(
        self, service_name: str, task_id: str, status: TaskStatus
    ) -> bool:
        """Update the status of a specific task."""
        plan = await self.get_plan(service_name)
        if not plan:
            return False

        # Find and update task
        for phase in plan.phases:
            for task in phase.tasks:
                if task.task_id == task_id:
                    task.status = status
                    # Recalculate progress summary
                    plan.progress_summary = self._calculate_progress_summary(
                        plan.phases
                    )
                    return True

        return False

    def _calculate_progress_summary(self, phases: List[PlanPhase]) -> Dict[str, int]:
        """Calculate progress summary across all phases."""
        all_tasks = [task for phase in phases for task in phase.tasks]

        return {
            "total_tasks": len(all_tasks),
            "pending": len([t for t in all_tasks if t.status == TaskStatus.PENDING]),
            "in_progress": len(
                [t for t in all_tasks if t.status == TaskStatus.IN_PROGRESS]
            ),
            "completed": len(
                [t for t in all_tasks if t.status == TaskStatus.COMPLETED]
            ),
            "failed": len([t for t in all_tasks if t.status == TaskStatus.FAILED]),
            "completion_percentage": (
                int(
                    (
                        len([t for t in all_tasks if t.status == TaskStatus.COMPLETED])
                        / len(all_tasks)
                    )
                    * 100
                )
                if all_tasks
                else 0
            ),
        }

    async def get_plan_summary(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get plan summary for status reporting."""
        plan = await self.get_plan(service_name)
        if not plan:
            return None

        return {
            "plan_id": plan.metadata.plan_id,
            "service_name": plan.metadata.service_name,
            "created_timestamp": plan.metadata.created_timestamp,
            "triage_report_id": plan.metadata.triage_report_id,
            "total_updates": plan.metadata.total_updates,
            "progress": plan.progress_summary,
            "phases": [
                {
                    "phase_id": phase.phase_id,
                    "phase_name": phase.phase_name,
                    "priority": phase.priority,
                    "task_count": len(phase.tasks),
                    "estimated_hours": phase.estimated_effort_hours,
                }
                for phase in plan.phases
            ],
        }

    async def get_plan_data(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get complete plan data as dictionary for resource access."""
        plan = await self.get_plan(service_name)
        if not plan:
            return None

        return plan.model_dump()

    def list_services(self) -> List[str]:
        """List all services with update plans."""
        return list(self._plans.keys())
