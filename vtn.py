# vtn_db_server.py
import os
import json
import asyncio
from datetime import datetime, timedelta, timezone
from functools import partial
from uuid import uuid4

import aiomysql
from dotenv import load_dotenv
from openleadr import OpenADRServer, enable_default_logging

# ---------- 設定 ----------
load_dotenv()
DB_CONFIG = dict(
    host=os.getenv("DB_HOST", "db"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "user"),
    password=os.getenv("DB_PASSWORD", "password"),
    db=os.getenv("DB_NAME", "mydb"),
    autocommit=True,
)
VTN_ID = "myvtn"
REQUESTED_POLL_FREQ = timedelta(seconds=30)

# ---------- DB ユーティリティ ----------
class DB:
    pool = None

    @classmethod
    async def init(cls):
        if cls.pool is None:
            cls.pool = await aiomysql.create_pool(
                minsize=1, maxsize=10, **DB_CONFIG
            )

    @classmethod
    async def execute(cls, sql, params=None):
        await cls.init()
        async with cls.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, params or ())
                return cur.rowcount

    @classmethod
    async def fetchone(cls, sql, params=None):
        await cls.init()
        async with cls.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, params or ())
                return await cur.fetchone()

    @classmethod
    async def fetchall(cls, sql, params=None):
        await cls.init()
        async with cls.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, params or ())
                return await cur.fetchall()

# ---------- ユーティリティ ----------
def now_utc():
    return datetime.now(timezone.utc)

def synth_r_id(resource_id: str, measurement: str) -> str:
    """
    簡易形式では r_id が見えないため、DB 用に安定 ID を合成する。
    （VEN 側 rID と一致はしないが、(ven_id, resource_id, measurement) に対して安定）
    """
    return f"auto::{resource_id}::{measurement}"

# ---------- ハンドラ ----------
async def on_query_registration(_payload):
    # 既定の応答は OpenLEADR が用意するが、明示しても OK
    # requested_poll_freq を 10 秒に設定
    return {
        "profiles": [{"profile_name": "2.0b", "transports": [{"transport_name": "simpleHttp"}]}],
        "requested_oadr_poll_freq": REQUESTED_POLL_FREQ,
        "vtn_id": VTN_ID
    }

async def on_create_party_registration(reg_info):
    """
    VEN 登録。既存なら再利用、新規なら生成。
    schema: vens(ven_id, ven_name, registration_id, fingerprint)
    """
    ven_name = reg_info["ven_name"]
    fingerprint = reg_info.get("fingerprint") or "NO-TLS"  # スキーマが NOT NULL のため

    row = await DB.fetchone(
        "SELECT ven_id, registration_id FROM vens WHERE ven_name = %s",
        (ven_name,)
    )
    if row:
        ven_id = row["ven_id"]
        registration_id = row["registration_id"]
        # fingerprint を最新に
        await DB.execute(
            "UPDATE vens SET fingerprint=%s, updated_at=NOW() WHERE ven_id=%s",
            (fingerprint, ven_id)
        )
        return ven_id, registration_id

    ven_id = f"ven-{uuid4().hex[:10]}"
    registration_id = f"reg-{uuid4().hex[:10]}"

    await DB.execute(
        "INSERT INTO vens (ven_id, ven_name, registration_id, fingerprint) VALUES (%s,%s,%s,%s)",
        (ven_id, ven_name, registration_id, fingerprint)
    )
    return ven_id, registration_id

async def ven_lookup(ven_id: str):
    """
    署名検証や未登録 VEN 排他に使われる参照。ドキュメント準拠の dict を返す。
    """
    print("[ven_lookup]")
    row = await DB.fetchone(
        "SELECT ven_id, ven_name, registration_id, fingerprint FROM vens WHERE ven_id = %s",
        (ven_id,)
    )
    if not row:
        return {}
    return {
        "ven_id": row["ven_id"],
        "ven_name": row["ven_name"],
        "registration_id": row["registration_id"],
        "fingerprint": row["fingerprint"]
    }

# 例: すべて購読しない（切替しやすいようにフラグ化）
SUBSCRIBE_REPORTS = True
ALLOW_MEASUREMENTS = {"powerReal"}  # 例: 許可したい測定だけ購読
DESIRED_REPORT = timedelta(seconds=30)    # 希望の送信周期（←これが「送信頻度」）

def clamp(desired, min_si, max_si):
    return max(min_si, min(desired, max_si))

async def on_register_report(ven_id, resource_id, measurement, unit, scale,
                             min_sampling_interval, max_sampling_interval):
    if not SUBSCRIBE_REPORTS or measurement not in ALLOW_MEASUREMENTS:
        return None  # 非購読

    # ven_resources upsert
    await DB.execute(
        "INSERT INTO ven_resources (ven_id, resource_id) VALUES (%s,%s) "
        "ON DUPLICATE KEY UPDATE resource_id=VALUES(resource_id)",
        (ven_id, resource_id)
    )

    # report_streams upsert（r_id / report_specifier_id は合成）
    r_id = synth_r_id(resource_id, measurement)
    report_specifier_id = f"auto::{resource_id}::{measurement}"

    await DB.execute(
        """
        INSERT INTO report_streams
          (ven_id, report_specifier_id, r_id, measurement, unit,
           min_sampling_interval, max_sampling_interval, requested_sampling_interval,
           resource_id, report_name, report_type, reading_type)
        VALUES
          (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          measurement=VALUES(measurement),
          unit=VALUES(unit),
          min_sampling_interval=VALUES(min_sampling_interval),
          max_sampling_interval=VALUES(max_sampling_interval),
          requested_sampling_interval=VALUES(requested_sampling_interval),
          resource_id=VALUES(resource_id),
          report_name=VALUES(report_name),
          report_type=VALUES(report_type),
          reading_type=VALUES(reading_type)
        """,
        (
            ven_id, report_specifier_id, r_id, measurement, unit,
            str(min_sampling_interval), str(max_sampling_interval), str(min_sampling_interval),
            resource_id, None, None, "Direct Read"
        )
    )

    await DB.execute(
        """
        INSERT INTO report_requests (ven_id, r_id, report_request_id, active)
        VALUES (%s, %s, %s, true)
        ON DUPLICATE KEY UPDATE active=true
        """,
        (ven_id, r_id, None)
    )

    callback = partial(on_update_report, ven_id=ven_id, r_id=r_id,
                       resource_id=resource_id, measurement=measurement)
    return callback, min_sampling_interval, DESIRED_REPORT

async def on_update_report(data, ven_id, r_id, resource_id, measurement):
    """
    レポート値を保存。data は (datetime, value) のイテラブル。
    report_id は簡易形式では見えないので NULL 保存。
    """
    # バルク insert（重複は PK (ven_id, r_id, ts) で自然排除）
    for ts, value in data:
        await DB.execute(
            """
            INSERT INTO report_values (ven_id, r_id, resource_id, measurement, report_id, ts, value)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE value=VALUES(value)
            """,
            (ven_id, r_id, resource_id, measurement, None, ts, float(value))
        )

async def event_response_callback(ven_id, event_id, opt_type):
    """
    VEN の opt 応答を保存。
    """
    await DB.execute(
        """
        INSERT INTO event_opt_responses (ven_id, event_id, opt_type)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE opt_type=VALUES(opt_type), responded_at=NOW()
        """,
        (ven_id, event_id, opt_type)
    )

def _normalize_intervals(intervals):
    out = []
    for it in intervals:
        dtstart = it["dtstart"]
        duration = it.get("duration")
        payload = it.get("signal_payload")
        out.append({
            "dtstart": dtstart.isoformat(),
            "duration_seconds": int(duration.total_seconds()) if duration else None,
            "signal_payload": payload
        })
    return out

async def add_event_and_persist(server: OpenADRServer, ven_id: str):
    """
    サンプルイベントをキューに追加し、DB にも保存。
    """
    intervals = [{
        "dtstart": now_utc() + timedelta(seconds=60),
        "duration": timedelta(minutes=10),
        "signal_payload": 1
    }]

    event_id = server.add_event(
        ven_id=ven_id,
        signal_name="LOAD_DISPATCH",
        signal_type="setpoint",      # ← ここを変更
        intervals=[{
            "dtstart": now_utc() + timedelta(seconds=60),
            "duration": timedelta(minutes=10),
            "signal_payload": 3000   # 例: 3000 W を指示（3 kW）
        }],
        callback=event_response_callback
    )

    # events 保存
    await DB.execute(
        """
        INSERT INTO events
          (event_id, ven_id, modification_number, event_status, market_context,
           created_datetime, priority, test_event, signals)
        VALUES
          (%s, %s, %s, %s, %s,
           %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          modification_number=VALUES(modification_number),
          event_status=VALUES(event_status),
          signals=VALUES(signals)
        """,
        (
            event_id, ven_id, 0, "far", "oadr://unknown.context",
            now_utc(), 0, False, json.dumps(_normalize_intervals(intervals))
        )
    )
    return event_id

async def main():
    enable_default_logging()
    await DB.init()

    server = OpenADRServer(
        vtn_id=VTN_ID,
        requested_poll_freq=REQUESTED_POLL_FREQ,
        ven_lookup=ven_lookup
    )

    # ハンドラ登録（名称はドキュメントの通り）
    # server.add_handler("on_query_registration", on_query_registration)
    server.add_handler("on_create_party_registration", on_create_party_registration)
    server.add_handler("on_register_report", on_register_report)

    # 動作確認: 既存 VEN があれば 1 件イベント投入
    row = await DB.fetchone("SELECT ven_id FROM vens ORDER BY created_at DESC LIMIT 1")
    if row:
        await add_event_and_persist(server, row["ven_id"])

    await server.run_async()
    # サーバは run_forever 相当で待機
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
