from .base import BaseEntity, BaseRepository


class AgentEnvironmentVariable(BaseEntity):
    def __init__(
        self,
        id: str = None,
        agent_id: str = None,
        agent_environment_id: str = None,
        name: str = None,
        value: str = None,
        masked: bool = False,
        created_at: str = None,
        updated_at: str = None,
        deleted_at: str = None,
    ):
        self.id = id
        self.agent_id = agent_id
        self.agent_environment_id = agent_environment_id
        self.name = name
        self.value = value
        self.masked = masked
        self.created_at = created_at
        self.updated_at = updated_at
        self.deleted_at = deleted_at or None


class AgentEnvironmentVariableRepository(BaseRepository[AgentEnvironmentVariable]):
    def __init__(self, agent_id: str, environment_id: str):
        super().__init__(
            "agent", f"/v1/agents/{agent_id}/environments/{environment_id}/variables", AgentEnvironmentVariable
        )
