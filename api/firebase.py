"""Database adapter.

The module keeps the original function names so the restaurant API remains small,
but production data is stored in Upstash Redis. Firebase is used only for
Authentication; no database secret is exposed to the browser.
"""
import copy
import json
import os
import threading
import urllib.parse
import urllib.request
import urllib.error

try:
    from .config import UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN, UPSTASH_KEY_PREFIX, LOCAL_DB_PATH, is_local_mode
except ImportError:
    from config import UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN, UPSTASH_KEY_PREFIX, LOCAL_DB_PATH, is_local_mode


class FirebaseError(Exception):
    pass

_FILE_LOCK = threading.RLock()


def _split_path(path):
    return [part for part in str(path).strip("/").split("/") if part]


def _ensure_local_file():
    folder = os.path.dirname(LOCAL_DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    if not os.path.exists(LOCAL_DB_PATH):
        with open(LOCAL_DB_PATH, "w", encoding="utf-8") as handle:
            json.dump({"users": {}, "menus": {}, "tables": {}, "reservations": {}, "orders": {}, "kitchen": {}, "audit_logs": {}}, handle, ensure_ascii=False, indent=2)


def _read_local():
    _ensure_local_file()
    with _FILE_LOCK, open(LOCAL_DB_PATH, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise FirebaseError("ฐานข้อมูล Local ต้องเป็น JSON object")
    return data


def _write_local(data):
    _ensure_local_file()
    temp_path = f"{LOCAL_DB_PATH}.tmp"
    with _FILE_LOCK:
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        os.replace(temp_path, LOCAL_DB_PATH)


def _local_get(path):
    node = _read_local()
    for part in _split_path(path):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return copy.deepcopy(node)


def _local_set(path, payload):
    data = _read_local()
    parts = _split_path(path)
    if not parts:
        data = payload
    else:
        node = data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = copy.deepcopy(payload)
    _write_local(data)
    return copy.deepcopy(payload)


def _local_patch(path, payload):
    current = _local_get(path) or {}
    merged = {**current, **copy.deepcopy(payload)} if isinstance(current, dict) and isinstance(payload, dict) else payload
    return _local_set(path, merged)


def _upstash_key(collection):
    return f"{UPSTASH_KEY_PREFIX}:{collection}"


def _upstash_command(command):
    if not UPSTASH_REDIS_REST_URL or not UPSTASH_REDIS_REST_TOKEN:
        raise FirebaseError("ยังไม่ได้ตั้งค่า Upstash Redis")
    body = json.dumps(command, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        UPSTASH_REDIS_REST_URL,
        data=body,
        headers={"Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            result = json.loads(response.read().decode("utf-8"))
        if "error" in result:
            raise FirebaseError(f"Upstash error: {result['error']}")
        return result.get("result")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise FirebaseError(f"Upstash HTTP {exc.code}: {detail}")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise FirebaseError(f"เชื่อมต่อ Upstash ไม่สำเร็จ: {exc}")


def _remote_collection(collection):
    raw = _upstash_command(["GET", _upstash_key(collection)])
    if raw in (None, ""):
        return {}
    try:
        value = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise FirebaseError(f"ข้อมูลใน Upstash ไม่ใช่ JSON ที่ถูกต้อง: {exc}")
    return value if isinstance(value, dict) else {}


def _remote_save(collection, data):
    _upstash_command(["SET", _upstash_key(collection), json.dumps(data, ensure_ascii=False, separators=(",", ":"))])
    return data


def get(path):
    parts = _split_path(path)
    if is_local_mode():
        return _local_get(path)
    if not parts:
        return None
    node = _remote_collection(parts[0])
    for part in parts[1:]:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return copy.deepcopy(node)


def put(path, payload):
    parts = _split_path(path)
    if is_local_mode():
        return _local_set(path, payload)
    if len(parts) != 2:
        raise FirebaseError("Upstash adapter รองรับการเขียนระดับ collection/item เท่านั้น")
    data = _remote_collection(parts[0])
    data[parts[1]] = copy.deepcopy(payload)
    _remote_save(parts[0], data)
    return copy.deepcopy(payload)


def patch(path, payload):
    parts = _split_path(path)
    if is_local_mode():
        return _local_patch(path, payload)
    current = get(path) or {}
    merged = {**current, **copy.deepcopy(payload)} if isinstance(current, dict) and isinstance(payload, dict) else payload
    return put(path, merged)


def post(path, payload):
    import uuid
    item_id = uuid.uuid4().hex[:20]
    put(f"{str(path).strip('/')}/{item_id}", payload)
    return {"name": item_id}


def delete(path):
    parts = _split_path(path)
    if is_local_mode():
        data = _read_local()
        node = data
        for part in parts[:-1]:
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        if parts:
            node.pop(parts[-1], None)
        _write_local(data)
        return None
    if len(parts) != 2:
        raise FirebaseError("Upstash adapter รองรับการลบระดับ item เท่านั้น")
    data = _remote_collection(parts[0])
    data.pop(parts[1], None)
    _remote_save(parts[0], data)
    return None
