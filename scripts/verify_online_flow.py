import argparse
import json
import time

import httpx
import redis


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="http://127.0.0.1:8080")
    parser.add_argument("--rec", default="http://127.0.0.1:8000")
    parser.add_argument("--item-id", type=int, default=102)
    args = parser.parse_args()

    user_id = f"online-e2e-{int(time.time())}"
    redis_client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
    redis_client.delete(
        f"adrec:user:history:{user_id}",
        f"adrec:user:features:{user_id}",
        f"adrec:home:{user_id}",
    )

    with httpx.Client(timeout=5.0) as client:
        cold = client.post(
            f"{args.rec}/v1/recommend",
            json={"user_id": user_id, "scene": "home", "size": 5, "debug": True},
        ).json()
        cold_sources = [item["recall_source"] for item in cold["items"]]
        assert cold_sources and all(source == "popular" for source in cold_sources)

        before = client.get(
            f"{args.backend}/api/v1/home",
            headers={"X-User-Id": user_id},
        ).json()["data"]["items"]
        before_ids = {int(item["id"]) for item in before}

        event_id = f"evt-online-e2e-{int(time.time() * 1000)}"
        client.post(
            f"{args.backend}/api/v1/events",
            json={
                "eventId": event_id,
                "userId": user_id,
                "sessionId": f"session-{user_id}",
                "itemId": args.item_id,
                "eventType": "click",
                "page": "home",
                "position": 1,
                "source": "home_card",
                "requestId": f"req-{event_id}",
                "recommendationId": f"rec-{event_id}",
                "eventTime": int(time.time() * 1000),
            },
        ).raise_for_status()

        for _ in range(20):
            if redis_client.lrange(f"adrec:user:history:{user_id}", 0, -1):
                break
            time.sleep(0.5)
        history = redis_client.lrange(f"adrec:user:history:{user_id}", 0, -1)
        assert str(args.item_id) in history

        after = client.get(
            f"{args.backend}/api/v1/home",
            headers={"X-User-Id": user_id},
        ).json()["data"]["items"]
        after_ids = {int(item["id"]) for item in after}

    assert before_ids != after_ids
    print(
        json.dumps(
            {
                "user_id": user_id,
                "clicked_item_id": args.item_id,
                "cold_start_sources": cold_sources,
                "before_count": len(before_ids),
                "after_count": len(after_ids),
                "new_items": len(after_ids - before_ids),
                "removed_items": len(before_ids - after_ids),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
