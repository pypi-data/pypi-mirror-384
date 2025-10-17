import os
import sys

PLUGIN_SRC = "/Users/jerome/Dev/test-fast-pluggy/src"
if PLUGIN_SRC not in sys.path:
    sys.path.insert(0, PLUGIN_SRC)

os.environ["BROKER_TYPE"] = "local"

from fastpluggy_plugin.tasks_worker.src_v2.broker.factory import get_broker
from fastpluggy_plugin.tasks_worker.src_v2.broker.contracts import BrokerMessage


def test_claim_sets_worker_id_header():
    broker = get_broker()
    mid = broker.publish("wtopic", {"a": 1})
    msg = broker.claim("wtopic", worker_id="worker-123")
    assert isinstance(msg, BrokerMessage)
    assert msg.id == mid
    assert msg.headers.get("worker_id") == "worker-123"
    assert "claimed_at" in msg.headers
    broker.ack(mid)
