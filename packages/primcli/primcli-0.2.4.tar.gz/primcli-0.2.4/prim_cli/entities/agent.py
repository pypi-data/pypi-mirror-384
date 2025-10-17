from .base import BaseEntity, BaseRepository


class Agent(BaseEntity):
    def __init__(
        self,
        id: str = None,
        user_id: str = None,
        organization_id: str = None,
        name: str = None,
        description: str = None,
        telephony_id: str = None,
        default_voice_id: str = None,
        default_voice_name: str = None,
        debug_environment_id: str = None,
        created_at: str = None,
        updated_at: str = None,
        deleted_at: str = None,
    ):
        self.id = id
        self.user_id = user_id
        self.organization_id = organization_id
        self.name = name
        self.description = description
        self.telephony_id = telephony_id
        self.default_voice_id = default_voice_id
        self.default_voice_name = default_voice_name
        self.debug_environment_id = debug_environment_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.deleted_at = deleted_at or None


class AgentRepository(BaseRepository[Agent]):
    def __init__(self):
        super().__init__("agent", f"/v1/agents", Agent)
