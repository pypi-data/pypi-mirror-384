from abc import abstractmethod
from typing import Generic, Type, TypeVar

from buz import Handler
from buz.query import Query, QueryResponse


TQuery = TypeVar("TQuery", bound=Query)
TQueryResponse = TypeVar("TQueryResponse", bound=QueryResponse)


class QueryHandler(Generic[TQuery, TQueryResponse], Handler[TQuery]):
    @classmethod
    @abstractmethod
    def handles(cls) -> Type[TQuery]:
        pass

    @abstractmethod
    async def handle(self, query: Query) -> TQueryResponse:
        pass
