import pydantic
import pytest

from papa_events.exceptions import PapaException


class Event(pydantic.BaseModel):
    name: str
    age: int


async def test_none_param(app):
    async def wrong_callback(): ...

    with pytest.raises(PapaException, match=r"You need one pydantic.BaseModel function param"):
        app.on_event(["test_event.new"], "test_event_use_case")(wrong_callback)


async def test_wrong_event_param(app):
    async def wrong_callback(num: int): ...

    with pytest.raises(PapaException, match=r"You need one pydantic.BaseModel function param"):
        app.on_event(["test_event.new"], "test_event_use_case")(wrong_callback)


async def test_missing_event_name_param(app):
    async def callback_without_event_name(event: Event): ...

    # This should now work without requiring a string-typed parameter for event name
    app.on_event(["test_event.new"], "test_event_use_case")(callback_without_event_name)

async def test_duplicate_event(app):
    async def wrong_callback(event_name: str, event: Event): ...

    with pytest.raises(PapaException, match=r"^Duplicate functions for"):
        app.on_event(["test_event.new"], "test_event_use_case")(wrong_callback)
        app.on_event(["test_event.new"], "test_event_use_case")(wrong_callback)

async def test_event_name_param_by_type(app):
    async def callback_with_custom_event_name_param(routing_key: str, event: Event): ...

    # This should work because routing_key is of type str
    app.on_event(["test_event.new"], "test_event_use_case_custom")(callback_with_custom_event_name_param)
