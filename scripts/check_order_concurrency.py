"""Manually verify that two simultaneous orders cannot buy the same final unit."""

import argparse
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--token", required=True, help="Customer application JWT")
    parser.add_argument("--product-id", required=True, help="ID of an active product with stock exactly 1")
    args = parser.parse_args()

    barrier = threading.Barrier(2)
    body = json.dumps(
        {"items": [{"product_id": args.product_id, "quantity": 1}]}
    ).encode()

    def place_order(_: int) -> tuple[int, str]:
        request = Request(
            f"{args.api_url.rstrip('/')}/orders",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {args.token}",
                "Content-Type": "application/json",
            },
        )
        barrier.wait()
        try:
            with urlopen(request, timeout=15) as response:
                return response.status, response.read().decode()
        except HTTPError as error:
            return error.code, error.read().decode()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(place_order, range(2)))

    for index, (status_code, response_body) in enumerate(results, start=1):
        print(f"Request {index}: HTTP {status_code} {response_body}")

    statuses = sorted(status_code for status_code, _ in results)
    if statuses != [201, 400]:
        raise SystemExit(f"FAILED: expected one 201 and one 400, received {statuses}")
    print("PASSED: one order succeeded and the competing order was rejected.")


if __name__ == "__main__":
    main()
