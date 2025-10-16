"""
Budget request ingestion and filtering for Yearn Treasury.

This module fetches budget requests from GitHub, parses them into
BudgetRequest objects, and provides lists of approved and rejected
requests.
"""

import os
import time
import requests
from typing import Any, Dict, Final, List

from yearn_treasury.budget._request import BudgetRequest


API_URL: Final = "https://api.github.com/repos/yearn/budget/issues"
"""URL to fetch issues from the repo."""

# Optionally use a GitHub personal access token for higher API rate limits.
# TODO move this to envs file and document
_TOKEN: Final = os.environ.get("GITHUB_TOKEN")
_HEADERS: Final = {"Authorization": f"token {_TOKEN}"} if _TOKEN else {}


def fetch_brs() -> List[BudgetRequest]:
    # Use parameters to fetch issues in all states, up to 100 per page.
    current_page = 1
    params = {"state": "all", "per_page": 100, "page": current_page}

    brs = []
    retries = 0
    while True:
        response = _make_get_request(params=params)

        data: List[dict] = response.json()  # type: ignore [type-arg]
        if not data:  # If the current page is empty, we are done.
            break

        for item in data:
            # GitHub's issues API returns pull requests as well.
            if "pull_request" in item:
                continue

            # TODO labels table in db (also dataclass) with the descriptions included
            # Extract the label names (tags) from the "labels" key.
            label_objs: List[dict] = item.get("labels", [])  # type: ignore [type-arg]
            labels = {label.get("name") for label in label_objs}

            if "budget request" not in labels:
                continue

            br = BudgetRequest(
                id=item.get("id"),  # type: ignore [arg-type]
                number=item.get("number"),  # type: ignore [arg-type]
                title=item.get("title"),  # type: ignore [arg-type]
                state=item.get("state"),  # type: ignore [arg-type]
                url=item.get("html_url"),  # type: ignore [arg-type]
                created_at=item.get("created_at"),  # type: ignore [arg-type]
                updated_at=item.get("updated_at"),  # type: ignore [arg-type]
                closed_at=item.get("closed_at"),  # type: ignore [arg-type]
                body=item.get("body"),  # type: ignore [arg-type]
                labels=labels,  # type: ignore [arg-type]
            )
            brs.append(br)

        # Move on to the next page.
        current_page += 1
        params["page"] = current_page

    return brs


def _make_get_request(params: Dict[str, Any]) -> Any:
    retries = 0
    while True:
        try:
            response = requests.get(API_URL, headers=_HEADERS, params=params)
            response.raise_for_status()
            return response
        except requests.HTTPError as e:
            if "rate limit exceeded" in str(e):
                print("Github API rate limited...")
            elif retries < 5:
                print(e)
            else:
                raise ConnectionError(
                    f"Failed to fetch issues: {response.status_code} {response.text}"
                ) from e
            retries += 1
            time.sleep(5 * (retries + 1))


budget_requests: Final = fetch_brs()
approved_requests: Final = [r for r in budget_requests if r.is_approved()]
rejected_requests: Final = [r for r in budget_requests if r.is_rejected()]
