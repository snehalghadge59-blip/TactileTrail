import sys
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_all():
    print("Testing 1: Health check")
    r_health = client.get("/api/health")
    assert r_health.status_code == 200, f"Health check failed: {r_health.text}"
    print(" Health check OK:", r_health.json())

    print("Testing 2: Runtime config")
    r_config = client.get("/api/config")
    assert r_config.status_code == 200, f"Config failed: {r_config.text}"
    print(" Config OK:", r_config.json()["ai_engine"])

    print("Testing 3: Home HTML page")
    r_home = client.get("/")
    assert r_home.status_code == 200, f"Home page failed: {r_home.text}"
    assert "TactileTrail" in r_home.text
    print(f" Home page OK ({len(r_home.text)} bytes)")

    print("Testing 4: Walk Generation in all biomes (Offline Gemma Edge)")
    environments = ["forest", "park", "neighborhood", "water", "meadow"]
    for env in environments:
        r_walk = client.post("/api/generate-walk", json={
            "environment": env,
            "walk_length": "standard",
            "mode": "offline"
        })
        assert r_walk.status_code == 200, f"Failed for {env}: {r_walk.text}"
        data = r_walk.json()
        assert len(data["checkpoints"]) == 4, f"Expected 4 checkpoints for {env}, got {len(data['checkpoints'])}"
        print(f" Biome [{env}]: {len(data['checkpoints'])} checkpoints, Model: {data['model_name']}")

    print("Testing 5: Short Walk (3 checkpoints)")
    r_short = client.post("/api/generate-walk", json={
        "environment": "forest",
        "walk_length": "short",
        "mode": "offline"
    })
    assert r_short.status_code == 200
    assert len(r_short.json()["checkpoints"]) == 3
    print(" Short walk OK (3 checkpoints)")

    print("Testing 6: Audio Narration TTS endpoint")
    r_tts = client.post("/api/tts", json={
        "text": "Close your eyes and touch the cool moss.",
        "checkpoint_id": 1
    })
    assert r_tts.status_code == 200
    print(f" TTS OK: Content-Type = {r_tts.headers.get('content-type')}")

    print("Testing 7: Nature Journal Save")
    r_save = client.post("/api/journal/save", json={
        "walk_id": "test_walk_01",
        "environment": "forest",
        "date": "2026-10-07",
        "duration_minutes": 8,
        "reflection_notes": "Bark texture was captivating.",
        "checkpoints_completed": 4
    })
    assert r_save.status_code == 200
    print(" Journal save OK:", r_save.json())

    print("\n=== ALL INTEGRATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_all()
