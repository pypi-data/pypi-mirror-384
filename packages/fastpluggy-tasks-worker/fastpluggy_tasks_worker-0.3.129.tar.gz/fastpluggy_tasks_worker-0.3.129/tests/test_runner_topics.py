
from fastpluggy_plugin.tasks_worker.core.events import TaskEventBus
from fastpluggy_plugin.tasks_worker.core.runner import TaskRunner


class FakeBrokerList:
    def __init__(self, topics):
        self._topics = topics

    def get_topics(self):
        return self._topics


class FakeBrokerError:
    def get_topics(self):
        raise RuntimeError("boom")


class ObjTopic:
    def __init__(self, topic):
        self.topic = topic


def make_runner():
    # TaskRunner only needs fp and bus stored; resolve_topics doesn't use them.
    fp = object()
    bus = TaskEventBus()
    return TaskRunner(fp=fp, bus=bus)


def test_resolve_topics_none_uses_broker_list_dicts():
    broker = FakeBrokerList([
        {"topic": "alpha", "queued": 1},
        {"topic": "beta", "queued": 0},
    ])
    r = make_runner()
    topics = r.resolve_topics(broker, topics=None)
    assert set(topics) == {"alpha", "beta"}


def test_resolve_topics_star_uses_broker_list_objects():
    broker = FakeBrokerList([
        ObjTopic("t1"),
        ObjTopic("t2"),
    ])
    r = make_runner()
    topics = r.resolve_topics(broker, topics=["*"])
    assert topics == ["t1", "t2"]


def test_resolve_topics_explicit_list_passthrough_and_casting():
    broker = FakeBrokerList([])  # should not be used when explicit topics provided
    r = make_runner()
    topics = r.resolve_topics(broker, topics=["A", "", 123, None, "B"])  # type: ignore[list-item]
    # empty/None filtered, non-str cast to str
    assert topics == ["A", "123", "B"]


def test_resolve_topics_broker_failure_returns_empty():
    broker = FakeBrokerError()
    r = make_runner()
    topics = r.resolve_topics(broker, topics=None)
    assert topics == []
