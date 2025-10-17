import os
import sys
import subprocess
import time
import pytest

# ensure plugin src is importable (same as other tests)
PLUGIN_SRC = "/Users/jerome/Dev/test-fast-pluggy/src"
if PLUGIN_SRC not in sys.path:
    sys.path.insert(0, PLUGIN_SRC)

os.environ["BROKER_TYPE"] = "local"

from fastpluggy_plugin.tasks_worker.src_v2.broker.local import LocalBroker


@pytest.mark.timeout(10)
def test_multi_process_shared_queue():
    # Parent starts broker to become leader and start manager
    os.environ['PYTHONPATH'] = PLUGIN_SRC + ':' + os.environ.get('PYTHONPATH','')
    broker = LocalBroker()

    # Child process code: publish three messages to topic 'mp'
    child_code = (
        "import os, sys\n"
        f"PLUGIN_SRC = {PLUGIN_SRC!r}\n"
        "if PLUGIN_SRC not in sys.path:\n"
        "    sys.path.insert(0, PLUGIN_SRC)\n"
        "os.environ['PYTHONPATH'] = PLUGIN_SRC + ':' + os.environ.get('PYTHONPATH','')\n\n"
        "os.environ['BROKER_TYPE'] = 'local'\n"
        "from fastpluggy_plugin.tasks_worker.src_v2.broker.factory import get_broker\n\n"
        "broker = get_broker()\n"
        "for i in range(3):\n"
        "    broker.publish('mp', {'i': i})\n"
        "print('CHILD_DONE')\n"
    )

    # Run child to publish messages
    proc = subprocess.Popen([sys.executable, "-c", child_code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate(timeout=5)
    assert proc.returncode == 0, f"Child failed: {err}"
    assert "CHILD_DONE" in out

    # small delay to ensure manager is fully up and state is visible
    time.sleep(0.2)

    # Parent claims the messages using a new broker instance
    # Ensure PYTHONPATH is set so manager process can import modules on spawn
    os.environ['PYTHONPATH'] = PLUGIN_SRC + ':' + os.environ.get('PYTHONPATH','')
    # Use LocalBroker directly in parent to ensure we attempt manager connection with defaults
    broker = LocalBroker()

    # Attempt to claim three messages
    msgs = []
    for _ in range(3):
        got = None
        for __ in range(10):
            m = broker.claim('mp', worker_id='parent')
            if m is not None:
                got = m
                break
            time.sleep(0.05)
        assert got is not None, 'Expected a message but got None'
        msgs.append(got)
    ids = {m.id for m in msgs}
    assert len(ids) == 3

    # ack them
    for m in msgs:
        broker.ack(m.id)
