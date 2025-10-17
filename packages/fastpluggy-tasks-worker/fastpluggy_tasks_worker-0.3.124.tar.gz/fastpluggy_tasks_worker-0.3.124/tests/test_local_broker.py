import os
import sys

# ensure plugin src is importable
PLUGIN_SRC = "/Users/jerome/Dev/test-fast-pluggy/src"
if PLUGIN_SRC not in sys.path:
    sys.path.insert(0, PLUGIN_SRC)

os.environ["BROKER_TYPE"] = "local"

from fastpluggy_plugin.tasks_worker.src_v2.broker.factory import get_broker
from fastpluggy_plugin.tasks_worker.src_v2.broker.local import LocalBroker
from fastpluggy_plugin.tasks_worker.src_v2.broker.contracts import BrokerMessage


def test_publish_and_claim_ack():
    broker = get_broker()
    assert isinstance(broker, LocalBroker)

    msg_id = broker.publish("test", {"x": 1})
    assert msg_id.startswith("local:")

    msg = broker.claim("test", worker_id="w1")
    assert isinstance(msg, BrokerMessage)
    assert msg.id == msg_id
    assert msg.payload == {"x": 1}
    assert msg.topic == "test"

    broker.ack(msg.id)
    stats = broker.stats("test")
    assert stats["queued"] == 0
    assert stats["inflight"] == 0


def test_claim_none_when_empty():
    broker = get_broker()
    msg = broker.claim("empty", worker_id="w1")
    assert msg is None


def test_nack_requeue():
    broker = get_broker()
    mid = broker.publish("requeue", {"n": 7})
    msg = broker.claim("requeue", worker_id="w1")
    assert msg and msg.id == mid

    broker.nack(mid, requeue=True)
    # should be available again immediately
    msg2 = broker.claim("requeue", worker_id="w2")
    assert msg2 and msg2.id == mid
