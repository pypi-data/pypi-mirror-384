import inspect

from typing import Generic, List, TypeVar
from ..utils.utils import make_request, convert_dict_keys_to_snake_case, is_uuid

T = TypeVar("T")


class BaseEntity:
    def __init__(
        self,
        id: str = None,
        created_at: str = None,
        updated_at: str = None,
        deleted_at: str = None,
        **kwargs,
    ):
        self.id = id
        self.created_at = created_at
        self.updated_at = updated_at
        self.deleted_at = deleted_at

        # Set any additional keyword arguments as attributes
        for key, value in kwargs.items():
            print("Unknown attribute:", key, value)

    def to_dict(self) -> dict:
        result = {}
        for attr_name, attr_value in self.__dict__.items():
            # Convert snake_case to camelCase for API
            camel_case_name = "".join(
                word.capitalize() if i > 0 else word
                for i, word in enumerate(attr_name.split("_"))
            )

            if attr_value is not None:
                result[camel_case_name] = attr_value

        return result


class BaseRepository(Generic[T]):
    def __init__(self, name: str, endpoint: str, entity_class: T):
        self.name = name
        self.endpoint = endpoint
        self.entity_class = entity_class

    def _filter_kwargs(self, kwargs: dict) -> dict:
        entity_class_init = inspect.signature(self.entity_class.__init__)
        valid_keys = set(entity_class_init.parameters.keys()) - {"self"}
        filtered = {k: v for k, v in kwargs.items() if k in valid_keys}
        unknown_keys = set(kwargs.keys()) - valid_keys
        if unknown_keys:
            print(f"Unknown kwargs for {self.entity_class.__name__}: {unknown_keys}")

        return filtered

    def _create_entity(self, item: dict) -> T:
        snake_case_item = convert_dict_keys_to_snake_case(item)
        filtered_kwargs = self._filter_kwargs(snake_case_item)
        return self.entity_class(**filtered_kwargs)

    def get(self, query: dict = {}) -> List[T]:
        query_string = "&".join(
            [
                f"filters[{key}]={value}"
                for key, value in query.items()
                if value is not None
            ]
        )
        response = make_request(f"{self.endpoint}?{query_string}")

        if response and "data" in response:
            if isinstance(response["data"], list):
                entities = []
                for item in response["data"]:
                    entities.append(self._create_entity(item))
            else:
                entities = self._create_entity(response["data"])

            return entities

        return []

    def get_by_id(self, id: str) -> T:
        response = make_request(f"{self.endpoint}/{id}")

        if response and "data" in response:
            return self._create_entity(response["data"])

        return None

    def get_by_name_or_id(self, name_or_id: str) -> T:
        if is_uuid(name_or_id):
            return self.get_by_id(name_or_id)

        entities = self.get()
        for entity in entities:
            if entity.name == name_or_id:
                return entity

        return None

    def create(self, item: T) -> T:
        item_dict = item.to_dict()
        response = make_request(self.endpoint, "POST", json=item_dict)

        if response and "data" in response:
            return self._create_entity(response["data"])

        return None

    def update_by_id(self, id: str, item: T) -> T:
        item_dict = item.to_dict()

        # Remove id if it exists in the dictionary
        if "id" in item_dict:
            del item_dict["id"]

        response = make_request(f"{self.endpoint}/{id}", "PATCH", json=item_dict)

        if response and "data" in response:
            return self._create_entity(response["data"])

        return None

    def delete_by_id(self, id: str) -> bool:
        response = make_request(f"{self.endpoint}/{id}", "DELETE")
        return response is not None
