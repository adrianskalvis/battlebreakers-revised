"""
Smoke tests for login, QueryProfile, InitializeLevel and FinalizeLevel.

Request bodies and expected response shapes come from the captured examples in the docs submodule
(docs/docs/...). The tests run against a live server, so start MongoDB and the server first:

    uv run sanic main:app            # serves http://127.0.0.1:8000
    uv run python tests/smoke_test.py [--base-url http://127.0.0.1:8000]

Only the Python standard library is used. Exit code 0 means every check passed.
"""
import argparse
import base64
import copy
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "docs"
MCP_DOCS = DOCS / "World Explorers Service" / "wex" / "api" / "game" / "v2" / "profile" / "accountId"
TOKEN_DOC = DOCS / "Account Service" / "account" / "api" / "oauth" / "token.md"

# Public wexclient id:secret from docs/docs/common/tokens/wexclient.md
WEX_BASIC = "basic M2NmNzhjZDNiMDBiNDM5YTg3NTVhODc4YjE2MGM3YWQ6YjM4M2UwZjQtZjBjYy00ZDE0LTk5ZTMtODEzYzMzZmMxZTlk"
USER_AGENT = "WorldExplorers/1.88.244-r17036752 Windows/10.0.22621.1.256.64bit"
PROFILE_REVISIONS = json.dumps([{"profileId": p, "clientCommandRevision": -1}
                                for p in ("profile0", "levels", "friends", "monsterpit", "multiplayer")])

results: list[tuple[str, bool, str]] = []


def doc_json_blocks(path: Path) -> dict[str, object]:
    """Returns the JSON blocks under '### Request Body' and '### Response Body' of a docs page."""
    text = path.read_text(encoding="utf-8")
    out = {}
    for name in ("Request Body", "Response Body"):
        match = re.search(rf"### {name}\s*```json\s*(.*?)```", text, re.S)
        if match:
            out[name] = json.loads(match.group(1))
    return out


def check(name: str, condition: bool, detail: str = "") -> bool:
    results.append((name, bool(condition), detail))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f": {detail}" if detail and not condition else ""))
    return bool(condition)


def request(base: str, method: str, path: str, *, headers=None, body=None, form=None):
    data = None
    hdrs = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    hdrs.update(headers or {})
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, raw.decode(errors="replace")


def missing_keys(expected: dict, actual: dict) -> list[str]:
    return sorted(k for k in expected if k not in actual)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    # ---------- login ----------
    token_doc = doc_json_blocks(TOKEN_DOC)
    username = "Smoke" + uuid.uuid4().hex[:8]
    password = "smoke-password"
    status, signup = request(base, "POST", "/id/login/token", headers={"Authorization": WEX_BASIC,
                                                                       "X-Request-Source-Form": "signup-form"},
                             body={"username": username, "password": password})
    if not check("signup via /id/login/token", status == 200 and "authorisationCode" in signup, f"{status} {signup}"):
        return summary()
    status, token = request(base, "POST", "/account/api/oauth/token", headers={"Authorization": WEX_BASIC},
                            form={"grant_type": "authorization_code", "code": signup["authorisationCode"],
                                  "token_type": "eg1"})
    check("oauth token (authorization_code)", status == 200 and "access_token" in token, f"{status} {token}")
    bearer = {"Authorization": f"bearer {token.get('access_token')}"}
    # The docs example uses an exchange code, so mint one and replay the documented request body.
    status, exchange = request(base, "GET", "/account/api/oauth/exchange", headers=bearer)
    check("oauth exchange", status == 200 and "code" in exchange, f"{status} {exchange}")
    form = {"grant_type": "exchange_code", "exchange_code": exchange.get("code", ""), "token_type": "eg1"}
    status, token = request(base, "POST", "/account/api/oauth/token", headers={"Authorization": WEX_BASIC},
                            form=form)
    expected_token = token_doc["Response Body"]
    core = ["access_token", "expires_in", "expires_at", "token_type", "refresh_token", "refresh_expires",
            "refresh_expires_at", "account_id", "client_id", "internal_client", "client_service", "displayName",
            "app", "in_app_id"]
    check("oauth token (exchange_code) matches docs keys", status == 200 and not missing_keys(
        {k: expected_token[k] for k in core}, token), f"{status} missing={missing_keys(expected_token, token)}")
    status, pw_token = request(base, "POST", "/account/api/oauth/token", headers={"Authorization": WEX_BASIC},
                               form={"grant_type": "password", "username": username, "password": password})
    check("oauth token (password)", status == 200 and pw_token.get("account_id") == token.get("account_id"),
          f"{status} {pw_token}")
    account_id = token.get("account_id")
    bearer = {"Authorization": f"bearer {token.get('access_token')}",
              "X-EpicGames-ProfileRevisions": PROFILE_REVISIONS}
    mcp = f"/wex/api/game/v2/profile/{account_id}"

    # ---------- QueryProfile ----------
    for profile_id in ("profile0", "levels"):
        doc = doc_json_blocks(MCP_DOCS / f"QueryProfile({profile_id}).md")
        status, resp = request(base, "POST", f"{mcp}/QueryProfile?profileId={profile_id}&rvn=-1", headers=bearer,
                               body=doc["Request Body"])
        expected = doc["Response Body"]
        ok = status == 200 and not missing_keys(expected, resp)
        check(f"QueryProfile {profile_id} top-level keys", ok, f"{status} {str(resp)[:300]}")
        if not ok:
            continue
        full = resp["profileChanges"][0] if resp.get("profileChanges") else {}
        check(f"QueryProfile {profile_id} returns fullProfileUpdate",
              full.get("changeType") == "fullProfileUpdate" and full.get("profile", {}).get("profileId") == profile_id,
              str(full)[:300])
        exp_profile = expected["profileChanges"][0]["profile"]
        check(f"QueryProfile {profile_id} profile keys match docs",
              not missing_keys(exp_profile, full.get("profile", {})),
              f"missing={missing_keys(exp_profile, full.get('profile', {}))}")

    # ---------- InitializeLevel ----------
    init_doc = doc_json_blocks(MCP_DOCS / "InitializeLevel.md")
    status, p0 = request(base, "POST", f"{mcp}/QueryProfile?profileId=profile0&rvn=-1", headers=bearer, body={})
    items = p0["profileChanges"][0]["profile"]["items"] if status == 200 else {}
    hero_ids = [guid for guid, item in items.items() if item.get("templateId", "").startswith("Character:")]
    status, lv = request(base, "POST", f"{mcp}/QueryProfile?profileId=levels&rvn=-1", headers=bearer, body={})
    # Send the current revision, like the client does, so the server returns deltas (docs use rvn=29643).
    levels_rvn = lv.get("profileRevision", -1) if status == 200 else -1
    level_runs = []
    for level_id in (init_doc["Request Body"]["levelId"], "Level.BlessedPlains.Map1.D1"):
        body = copy.deepcopy(init_doc["Request Body"])
        body["levelId"] = level_id
        # The docs hero ids belong to the capture account. Swap in heroes owned by the new account.
        local = [m for m in body["partyMembers"] if m["heroType"] in ("LocalHero", "LocalCommander")]
        for member, hero in zip(local, hero_ids):
            member["heroItemId"] = hero
        for member in local[len(hero_ids):]:
            member["heroType"], member["heroItemId"] = "Empty", ""
        status, resp = request(base, "POST", f"{mcp}/InitializeLevel?profileId=levels&rvn={levels_rvn}", headers=bearer,
                               body=body)
        expected = init_doc["Response Body"]
        if isinstance(resp, dict):
            levels_rvn = resp.get("profileRevision", levels_rvn)
        if not check(f"InitializeLevel {level_id} status 200 and docs keys",
                     status == 200 and not missing_keys(expected, resp), f"{status} {str(resp)[:400]}"):
            continue
        added = [c for c in resp["profileChanges"] if c.get("changeType") == "itemAdded"
                 and c["item"]["templateId"] == "Level:InProgress"]
        check(f"InitializeLevel {level_id} adds Level:InProgress", len(added) == 1, str(resp["profileChanges"])[:300])
        notes = [n for n in resp.get("notifications", []) if n.get("type") == "WExpLevelCreated"]
        exp_level = expected["notifications"][0]["level"]
        level = notes[0]["level"] if notes else {}
        check(f"InitializeLevel {level_id} WExpLevelCreated with rooms", bool(notes) and len(level.get("rooms", [])) > 0,
              str(notes)[:300])
        if level.get("rooms"):
            exp_room, room = exp_level["rooms"][0], level["rooms"][0]
            check(f"InitializeLevel {level_id} room keys match docs", not missing_keys(exp_room, room),
                  f"missing={missing_keys(exp_room, room)}")
            check(f"InitializeLevel {level_id} levelItemId matches item", added and level.get("levelItemId") == added[0]["itemId"])
        if added:
            level_runs.append((level_id, added[0]["itemId"], len(level.get("rooms", []))))

    # ---------- FinalizeLevel ----------
    fin_doc = doc_json_blocks(MCP_DOCS / "FinalizeLevel.md")
    for level_id, level_item_id, room_count in level_runs:
        body = copy.deepcopy(fin_doc["Request Body"])
        body["levelItemId"] = level_item_id
        body["claimDepth"] = max(room_count, 1)
        body["postBattleResults"]["uniqueHeroesDefeated"] = []
        status, resp = request(base, "POST", f"{mcp}/FinalizeLevel?profileId=levels&rvn={levels_rvn}", headers=bearer,
                               body=body)
        expected = fin_doc["Response Body"]
        if isinstance(resp, dict):
            levels_rvn = resp.get("profileRevision", levels_rvn)
        if not check(f"FinalizeLevel {level_id} status 200 and docs keys",
                     status == 200 and not missing_keys(expected, resp), f"{status} {str(resp)[:400]}"):
            continue
        removed = [c for c in resp["profileChanges"] if c.get("changeType") == "itemRemoved"
                   and c.get("itemId") == level_item_id]
        check(f"FinalizeLevel {level_id} removes the level item", len(removed) == 1, str(resp["profileChanges"])[:300])
        notes = [n for n in resp.get("notifications", []) if n.get("type") == "WExpLevelCompleted"]
        exp_note = expected["notifications"][0]
        check(f"FinalizeLevel {level_id} WExpLevelCompleted keys match docs",
              bool(notes) and not missing_keys(exp_note, notes[0]),
              f"missing={missing_keys(exp_note, notes[0]) if notes else 'no notification'}")
        check(f"FinalizeLevel {level_id} completed with loot", bool(notes) and notes[0].get("completed") is True
              and len(notes[0].get("loot", [])) > 0, str(notes)[:300])
    return summary()


def summary() -> int:
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
