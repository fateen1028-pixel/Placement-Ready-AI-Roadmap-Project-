import asyncio
from httpx import AsyncClient
from app import main  # FastAPI instance

# ---------- CONFIG ----------
BASE_URL = "http://test"
TEST_USER_TOKEN = "YOUR_TEST_USER_TOKEN"  # Use a real token if auth
HEADERS = {"Authorization": f"Bearer {TEST_USER_TOKEN}"}

VALID_SLOT_ID = "slot_in_progress"
VALID_TASK_ID = "task_1"
LOCKED_SLOT_ID = "slot_locked"
COMPLETED_SLOT_ID = "slot_completed"
FAKE_SLOT_ID = "nonexistent_slot"
WRONG_TASK_ID = "wrong_task"

# ---------- HELPER ----------
async def post_submission(client, slot_id, task_id, payload={"code": "print(1)"}):
    data = {
        "slot_id": slot_id,
        "task_instance_id": task_id,
        "payload": payload
    }
    return await client.post("/submissions", json=data, headers=HEADERS)

# ---------- MAIN TEST ----------
async def main():
    async with AsyncClient(app=main.app, base_url=BASE_URL) as client:
        results = []

        # 1️⃣ Slot missing
        r = await post_submission(client, FAKE_SLOT_ID, VALID_TASK_ID)
        results.append(("Slot missing", r.status_code, r.json()))

        # 2️⃣ Slot not in progress
        r = await post_submission(client, COMPLETED_SLOT_ID, VALID_TASK_ID)
        results.append(("Slot not in progress", r.status_code, r.json()))

        # 3️⃣ Wrong task instance
        r = await post_submission(client, VALID_SLOT_ID, WRONG_TASK_ID)
        results.append(("Wrong task instance", r.status_code, r.json()))

        # 4️⃣ Happy path (first submission)
        r = await post_submission(client, VALID_SLOT_ID, VALID_TASK_ID)
        results.append(("Happy path", r.status_code, r.json()))

        # 5️⃣ Duplicate submission
        r = await post_submission(client, VALID_SLOT_ID, VALID_TASK_ID)
        results.append(("Duplicate submission", r.status_code, r.json()))

        # 6️⃣ Slot locked
        r = await post_submission(client, LOCKED_SLOT_ID, VALID_TASK_ID)
        results.append(("Slot locked", r.status_code, r.json()))

        # 7️⃣ Edge case: empty payload
        r = await post_submission(client, VALID_SLOT_ID, VALID_TASK_ID, payload={})
        results.append(("Empty payload", r.status_code, r.json()))

        # Print results
        for name, code, resp in results:
            print(f"{name}: {code} | {resp}")

# Run
asyncio.run(main())
