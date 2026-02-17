import sqlite3
from typing import Any, Dict, List, Optional

DB_PATH = "assets.db"


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            short_summary TEXT NOT NULL,

            primary_bu TEXT NOT NULL,
            secondary_bus TEXT NOT NULL,

            use_cases TEXT NOT NULL,
            asset_type TEXT NOT NULL,

            license_flag TEXT NOT NULL,
            license_notes TEXT NOT NULL,

            readiness_score INTEGER NOT NULL,
            engineering_score INTEGER NOT NULL,
            maintenance_score INTEGER NOT NULL,

            last_validated_on TEXT NOT NULL,
            owner TEXT NOT NULL,
            notes TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def serialize_list(xs: List[str]) -> str:
    return "|".join([x.strip() for x in xs if x and x.strip()])


def deserialize_list(s: str) -> List[str]:
    if not s:
        return []
    return [x for x in s.split("|") if x.strip()]


def insert_asset(a: Dict[str, Any]) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO assets (
            name, url, short_summary,
            primary_bu, secondary_bus,
            use_cases, asset_type,
            license_flag, license_notes,
            readiness_score, engineering_score, maintenance_score,
            last_validated_on, owner, notes
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            a["name"],
            a["url"],
            a["short_summary"],
            a["primary_bu"],
            serialize_list(a.get("secondary_bus", [])),
            serialize_list(a.get("use_cases", [])),
            a["asset_type"],
            a["license_flag"],
            a.get("license_notes", ""),
            int(a["readiness_score"]),
            int(a["engineering_score"]),
            int(a["maintenance_score"]),
            a.get("last_validated_on", ""),
            a.get("owner", ""),
            a.get("notes", ""),
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return int(new_id)


def update_asset(asset_id: int, a: Dict[str, Any]) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE assets SET
            name=?,
            url=?,
            short_summary=?,
            primary_bu=?,
            secondary_bus=?,
            use_cases=?,
            asset_type=?,
            license_flag=?,
            license_notes=?,
            readiness_score=?,
            engineering_score=?,
            maintenance_score=?,
            last_validated_on=?,
            owner=?,
            notes=?
        WHERE id=?
        """,
        (
            a["name"],
            a["url"],
            a["short_summary"],
            a["primary_bu"],
            serialize_list(a.get("secondary_bus", [])),
            serialize_list(a.get("use_cases", [])),
            a["asset_type"],
            a["license_flag"],
            a.get("license_notes", ""),
            int(a["readiness_score"]),
            int(a["engineering_score"]),
            int(a["maintenance_score"]),
            a.get("last_validated_on", ""),
            a.get("owner", ""),
            a.get("notes", ""),
            int(asset_id),
        ),
    )
    conn.commit()
    conn.close()


def delete_asset(asset_id: int) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM assets WHERE id=?", (int(asset_id),))
    conn.commit()
    conn.close()


def list_assets() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM assets ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    keys = [
        "id",
        "name",
        "url",
        "short_summary",
        "primary_bu",
        "secondary_bus",
        "use_cases",
        "asset_type",
        "license_flag",
        "license_notes",
        "readiness_score",
        "engineering_score",
        "maintenance_score",
        "last_validated_on",
        "owner",
        "notes",
    ]

    out = []
    for r in rows:
        d = dict(zip(keys, r))
        d["secondary_bus"] = deserialize_list(d["secondary_bus"])
        d["use_cases"] = deserialize_list(d["use_cases"])
        out.append(d)
    return out


def get_asset(asset_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM assets WHERE id=?", (int(asset_id),))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    keys = [
        "id",
        "name",
        "url",
        "short_summary",
        "primary_bu",
        "secondary_bus",
        "use_cases",
        "asset_type",
        "license_flag",
        "license_notes",
        "readiness_score",
        "engineering_score",
        "maintenance_score",
        "last_validated_on",
        "owner",
        "notes",
    ]

    d = dict(zip(keys, row))
    d["secondary_bus"] = deserialize_list(d["secondary_bus"])
    d["use_cases"] = deserialize_list(d["use_cases"])
    return d


def count_assets() -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM assets")
    n = cur.fetchone()[0]
    conn.close()
    return int(n)
