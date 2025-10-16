import os
import pytest
import sys
sys.path.append('..')
from src.henotace_ai import HenotaceAI, create_tutor


@pytest.mark.asyncio
async def test_status_ok():
    api_key = os.getenv("HENOTACE_API_KEY", "test_key")
    sdk = HenotaceAI(api_key=api_key)
    # We don't assert True here because CI might not have network; just ensure it doesn't crash
    ok = sdk.get_status_ok()
    assert isinstance(ok, bool)


@pytest.mark.asyncio
async def test_create_and_send():
    api_key = os.getenv("HENOTACE_API_KEY", "test_key")
    sdk = HenotaceAI(api_key=api_key)
    tutor = await create_tutor(sdk=sdk, student_id="test_student", tutor_name="test_tutor")
    assert tutor.ids["student_id"] == "test_student"
    # Do not actually call the API in tests without key; ensure method call path works
    if os.getenv("HENOTACE_API_KEY"):
        reply = await tutor.send("Hello")
        assert isinstance(reply, str)
    else:
        # No API key; skip network call
        assert True


