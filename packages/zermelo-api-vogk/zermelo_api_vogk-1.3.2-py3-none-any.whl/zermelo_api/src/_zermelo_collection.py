from ._zermelo_api import zermelo
from typing import TypeVar, Type
import inspect
import logging

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

# Define a TypeVar for the specific type of object we want to create
_T = TypeVar("_T")


def from_zermelo_dict(obj: Type[_T], data: dict, *args, **kwargs) -> _T:
    """
    Generates an object of type obj from a dictionary,
    passing only keys that match obj's constructor parameters.

    Args:
        obj: The class (type) to instantiate.
        data: The dictionary containing data for the object's constructor.
        *args: Positional arguments to pass to the constructor.
        **kwargs: Keyword arguments to pass to the constructor.

    Returns:
        An instance of type obj.
    """

    # Get the constructor parameters of the class
    obj_signature = inspect.signature(obj).parameters
    for k, v in data.items():
        if k not in obj_signature:
            logger.debug(f"{k} ({v}) not defined in {obj.__name__}")

    # Filter data to include only keys that match constructor parameters
    filtered_data = {k: v for k, v in data.items() if k in obj_signature}

    # Instantiate the object
    return obj(*args, **filtered_data, **kwargs)


class ZermeloCollection[T](list[T]):

    def __init__(self, item_type: Type[T], query: str = ""):
        super().__init__()
        self.type = item_type
        self.query = query

    def __repr__(self):
        return ", ".join([f"{item!r}" for item in self])

    def print_list(self):
        return (
            f" = [" + ", ".join([str(item) for item in self]) + "]" if len(self) else ""
        )

    async def get_collection(self, query: str = "") -> list[dict]:
        query = self.get_query(query)
        logger.debug(f"type: {self.type}")
        return await zermelo.load_query(query)

    async def load_collection(self, query: str, *args, **kwargs):
        for row in await self.get_collection(query):
            self.append(from_zermelo_dict(self.type, row, *args, **kwargs))

    def get_query(self, query: str) -> str:
        if not query:
            if not self.query:
                raise Exception(f"No query given")
            return self.query
        return query

    async def _init(self, query: str = ""):
        if not self.type:
            raise Exception(f"No Type set for {self}")
        query = self.get_query(query)
        await self.load_collection(query)
