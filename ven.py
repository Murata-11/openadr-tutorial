# ven.py
import asyncio
from datetime import timedelta
from openleadr import OpenADRClient, enable_default_logging

enable_default_logging()

async def collect_value():
    return 1.23   # ダミーの計測値

async def handle_event(event):
    print("[EVENT] received:", event["event_signals"][0]["intervals"])
    return "optIn"

client = OpenADRClient(
    ven_name="ven123",
    vtn_url="http://localhost:8080/OpenADR2/Simple/2.0b"
)

client.add_report(
    callback=collect_value,
    resource_id="device001",
    measurement="powerReal",
    sampling_rate=timedelta(seconds=10),
    report_duration=timedelta(seconds=30)
)

client.add_handler("on_event", handle_event)

loop = asyncio.get_event_loop()
loop.create_task(client.run())
loop.run_forever()
