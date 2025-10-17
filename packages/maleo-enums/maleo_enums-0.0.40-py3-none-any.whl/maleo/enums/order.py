from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Annotated, Generic, Sequence, TypeVar
from maleo.types.string import ListOfStrs


class Order(StrEnum):
    ASC = "asc"
    DESC = "desc"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OrderT = TypeVar("OrderT", bound=Order)
OptOrder = Order | None
OptOrderT = TypeVar("OptOrderT", bound=OptOrder)


class OrderMixin(BaseModel, Generic[OptOrderT]):
    order: Annotated[OptOrderT, Field(..., description="Order")]


ListOfOrders = list[Order]
ListOfOrdersT = TypeVar("ListOfOrdersT", bound=ListOfOrders)
OptListOfOrders = ListOfOrders | None
OptListOfOrdersT = TypeVar("OptListOfOrdersT", bound=OptListOfOrders)


class OrdersMixin(BaseModel, Generic[OptListOfOrdersT]):
    orders: Annotated[OptListOfOrdersT, Field(..., description="Orders")]


SeqOfOrders = Sequence[Order]
SeqOfOrdersT = TypeVar("SeqOfOrdersT", bound=SeqOfOrders)
OptSeqOfOrders = SeqOfOrders | None
OptSeqOfOrdersT = TypeVar("OptSeqOfOrdersT", bound=OptSeqOfOrders)
