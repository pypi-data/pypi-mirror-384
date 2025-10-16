from typing import Literal, TypedDict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from planar.config import PlanarConfig, get_environment
from planar.data.config import DataConfig
from planar.files.storage.config import StorageConfig
from planar.human.models import HumanTask, HumanTaskStatus
from planar.logging import get_logger
from planar.object_registry import ObjectRegistry
from planar.session import get_session
from planar.version import FALLBACK_VERSION, get_version
from planar.workflows.models import Workflow, WorkflowStatus

logger = get_logger(__name__)

StorageInfo = Literal["s3", "localdir", "azure_blob"]


class DatasetsInfo(BaseModel):
    catalog: Literal["postgres", "sqlite"]
    storage: StorageInfo


class SystemFeatures(BaseModel):
    storage: StorageInfo | None = None
    datasets: DatasetsInfo | None = None


class SystemInfo(BaseModel):
    """Combined application information and system statistics"""

    # App info
    title: str
    description: str

    version: str
    environment: str

    features: SystemFeatures

    # System stats
    total_workflow_runs: int = 0
    completed_runs: int = 0
    in_progress_runs: int = 0
    pending_human_tasks: int = 0
    active_agents: int = 0


class SystemStats(TypedDict):
    total_workflow_runs: int
    completed_runs: int
    in_progress_runs: int
    pending_human_tasks: int
    active_agents: int


async def get_system_stats(
    registry: ObjectRegistry,
    session: AsyncSession = Depends(get_session),
) -> SystemStats:
    """
    Get system-wide statistics directly from the database.

    This optimizes the calculation by doing aggregations at the database level
    rather than fetching all records and calculating in the application.
    """
    try:
        agent_count = len(registry.get_agents())

        # Get workflow run counts
        workflow_stats = await session.exec(
            select(
                func.count().label("total_runs"),
                func.count(col(Workflow.id))
                .filter(col(Workflow.status) == WorkflowStatus.SUCCEEDED)
                .label("completed_runs"),
                func.count(col(Workflow.id))
                .filter(col(Workflow.status) == WorkflowStatus.PENDING)
                .label("in_progress_runs"),
            ).select_from(Workflow)
        )
        total_runs, completed_runs, in_progress_runs = workflow_stats.one()

        # Get pending human task count
        human_task_query = await session.exec(
            select(func.count())
            .select_from(HumanTask)
            .where(HumanTask.status == HumanTaskStatus.PENDING)
        )
        pending_tasks = human_task_query.one()

        # Return stats dict
        return {
            "total_workflow_runs": total_runs,
            "completed_runs": completed_runs,
            "in_progress_runs": in_progress_runs,
            "pending_human_tasks": pending_tasks,
            "active_agents": agent_count,
        }
    except Exception:
        logger.exception("error fetching system stats")
        # Return default stats if there's an error
        return {
            "total_workflow_runs": 0,
            "completed_runs": 0,
            "in_progress_runs": 0,
            "pending_human_tasks": 0,
            "active_agents": 0,
        }


def get_storage_info(cfg: StorageConfig) -> StorageInfo:
    return cfg.backend


def get_datasets_info(cfg: DataConfig) -> DatasetsInfo | None:
    return DatasetsInfo(catalog=cfg.catalog.type, storage=get_storage_info(cfg.storage))


def create_info_router(
    title: str, description: str, config: PlanarConfig, registry: ObjectRegistry
) -> APIRouter:
    """
    Create a router for serving combined application information and system statistics.

    This router provides a single endpoint to retrieve the application's title,
    description, and system-wide statistics on workflow runs, human tasks,
    and registered agents, as well as the application's features and configuration.

    Args:
        title: The application title
        description: The application description

    Returns:
        An APIRouter instance with a combined info route
    """
    router = APIRouter()

    @router.get("/system-info", response_model=SystemInfo)
    async def get_system_info(
        session: AsyncSession = Depends(get_session),
    ) -> SystemInfo:
        """
        Get combined application information and system statistics.

        Returns:
            SystemInfo object containing app details and system stats
        """
        stats = await get_system_stats(registry, session)
        version = get_version()
        if version == FALLBACK_VERSION:
            logger.warning(
                "planar package version not found",
                package_name="planar",
                fallback_version=FALLBACK_VERSION,
            )

        return SystemInfo(
            title=title,
            description=description,
            version=version,
            environment=get_environment(),
            features=SystemFeatures(
                storage=get_storage_info(config.storage) if config.storage else None,
                datasets=get_datasets_info(config.data) if config.data else None,
            ),
            **stats,
        )

    return router
