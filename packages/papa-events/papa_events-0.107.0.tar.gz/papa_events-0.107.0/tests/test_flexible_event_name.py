import asyncio
from unittest.mock import create_autospec

import pydantic
import pytest


class Event(pydantic.BaseModel):
    name: str
    age: int


async def test_event_name_param_different_names(app):
    """Test that different parameter names work as long as they are of type str"""
    
    async def callback_with_event_name(event_name: str, event: Event):
        pass

    async def callback_with_routing_key(routing_key: str, event: Event):
        pass

    async def callback_with_event_type(event_type: str, event: Event):
        pass

    # All these should work because they have a string-typed parameter
    mocked_callback1 = create_autospec(callback_with_event_name)
    mocked_callback2 = create_autospec(callback_with_routing_key)
    mocked_callback3 = create_autospec(callback_with_event_type)

    app.on_event(["user.created"], "test_event_name_use_case")(mocked_callback1)
    app.on_event(["user.updated"], "test_routing_key_use_case")(mocked_callback2)
    app.on_event(["user.deleted"], "test_event_type_use_case")(mocked_callback3)

    await app.start()
    ev = Event(name="test user", age=30)
    
    # Test all three handlers
    await app.new_event("user.created", ev)
    await app.new_event("user.updated", ev)
    await app.new_event("user.deleted", ev)
    
    await asyncio.sleep(2)
    await app.stop()

    # Verify all callbacks were called with correct parameters
    mocked_callback1.assert_awaited_once_with(event_name="user.created", event=ev)
    mocked_callback2.assert_awaited_once_with(routing_key="user.updated", event=ev)
    mocked_callback3.assert_awaited_once_with(event_type="user.deleted", event=ev)


async def test_multiple_string_params_error(app):
    """Test that having multiple string parameters causes an error"""
    
    async def callback_with_multiple_strings(event_name: str, routing_key: str, event: Event):
        pass

    with pytest.raises(Exception, match=r"You can only have one string-typed parameter for event name"):
        app.on_event(["user.created"], "test_multiple_strings_use_case")(callback_with_multiple_strings)


async def test_no_string_param_works(app):
    """Test that no string parameter works correctly"""
    
    async def callback_without_string_param(event: Event):
        pass

    mocked_callback = create_autospec(callback_without_string_param)

    app.on_event(["user.created"], "test_no_string_use_case")(mocked_callback)

    await app.start()
    ev = Event(name="test user", age=30)
    await app.new_event("user.created", ev)
    await asyncio.sleep(2)
    await app.stop()

    mocked_callback.assert_awaited_once_with(event=ev)