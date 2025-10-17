from prim_cli.utils.utils import make_request
from .base import BaseEntity, BaseRepository


class PhoneNumber(BaseEntity):
    def __init__(
        self,
        id: str = None,
        user_id: str = None,
        telephony_id: str = None,
        phone_number: str = None,
        created_at: str = None,
        updated_at: str = None,
        deleted_at: str = None,
    ):
        self.id = id
        self.user_id = user_id
        self.telephony_id = telephony_id
        self.phone_number = phone_number
        self.created_at = created_at
        self.updated_at = updated_at
        self.deleted_at = deleted_at or None


class PhoneNumberRepository(BaseRepository[PhoneNumber]):
    def __init__(self):
        super().__init__("phone_number", f"/v1/users/phoneNumber", PhoneNumber)

    def debug(self, agent, environment, function) -> dict:
        env = f"{environment.name}|{function.id}"
        response = make_request(f"/v1/agents/{agent.id}/debugPhoneNumber", "POST", json={"environment": env})
        return response
