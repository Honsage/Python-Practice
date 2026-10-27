from typing import TypeVar, Union

from YP_Blogicum.tests.adapters.post import PostModelAdapter
from YP_Blogicum.tests.adapters.user import UserModelAdapter

CommentModelAdapterT = TypeVar("CommentModelAdapterT", bound=type)
ModelAdapterT = Union[CommentModelAdapterT, PostModelAdapter, UserModelAdapter]
