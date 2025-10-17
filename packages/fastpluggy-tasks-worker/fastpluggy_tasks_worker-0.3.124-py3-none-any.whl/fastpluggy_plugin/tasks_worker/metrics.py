import logging

try:
    from prometheus_client import REGISTRY  # type: ignore
    from prometheus_client.core import GaugeMetricFamily  # type: ignore
    PROM_AVAILABLE = True
except Exception as e:  # pragma: no cover - optional dependency
    logging.warning(f"prometheus_client not available for broker metrics: {e}")
    PROM_AVAILABLE = False

# Ensure idempotent registration within a single process
_BROKER_COLLECTOR_REGISTERED = False


def register_broker_collector_once() -> None:
    """
    Register a Prometheus custom collector that scrapes TaskWorker broker stats
    at collection time. The registration is idempotent and will be silently
    skipped if prometheus_client is not installed or TaskWorker/broker is
    unavailable.
    """
    global _BROKER_COLLECTOR_REGISTERED

    if not PROM_AVAILABLE or _BROKER_COLLECTOR_REGISTERED:
        return

    try:
        # Local import to avoid hard dependency on init/import time
        from . import TaskWorker  # type: ignore
    except Exception as e:
        logging.info(f"Broker collector not registered (TaskWorker unavailable): {e}")
        return

    class BrokerCollector:
        """
        Prometheus collector that scrapes broker stats at collection time.
        This avoids maintaining state and ensures fresh values per scrape.
        """

        def collect(self):  # pragma: no cover - runtime integration
            try:
                broker = TaskWorker._get_broker()
            except Exception as e:
                logging.debug(f"No broker available for metrics: {e}")
                return
            if not broker:
                return

            # Topics metrics
            try:
                topics = broker.get_topics() or []
            except Exception as e:
                logging.warning(f"broker.get_topics() failed: {e}")
                topics = []

            g_queued = GaugeMetricFamily(
                'fastpluggy_broker_topic_queued',
                'Number of queued messages per topic',
                labels=['topic']
            )
            g_inflight = GaugeMetricFamily(
                'fastpluggy_broker_topic_inflight',
                'Number of in-flight messages per topic',
                labels=['topic']
            )
            g_dead = GaugeMetricFamily(
                'fastpluggy_broker_topic_dead_letter',
                'Number of dead-letter messages per topic',
                labels=['topic']
            )
            g_sub = GaugeMetricFamily(
                'fastpluggy_broker_topic_subscribers',
                'Number of subscribers per topic',
                labels=['topic']
            )

            topics_count = 0
            total_queued = 0
            total_inflight = 0
            for t in topics:
                # t may be a dataclass TopicInfo or a dict
                topic = getattr(t, 'topic', None) or (t.get('topic') if isinstance(t, dict) else None)
                queued = getattr(t, 'queued', None)
                inflight = getattr(t, 'inflight', None)
                dead_letter = getattr(t, 'dead_letter', None)
                subscribers = getattr(t, 'subscribers', None)
                if isinstance(t, dict):
                    queued = queued if queued is not None else t.get('queued', 0)
                    inflight = inflight if inflight is not None else t.get('inflight', 0)
                    dead_letter = dead_letter if dead_letter is not None else t.get('dead_letter', 0)
                    subscribers = subscribers if subscribers is not None else t.get('subscribers', 0)

                if topic is None:
                    continue
                topics_count += 1
                try:
                    qv = int(queued or 0)
                    iv = int(inflight or 0)
                    dv = int(dead_letter or 0)
                    sv = int(subscribers or 0)
                except Exception:
                    qv = iv = dv = sv = 0

                total_queued += qv
                total_inflight += iv

                g_queued.add_metric([topic], qv)
                g_inflight.add_metric([topic], iv)
                g_dead.add_metric([topic], dv)
                g_sub.add_metric([topic], sv)

            # Yield topic metrics
            yield g_queued
            yield g_inflight
            yield g_dead
            yield g_sub

            # Cluster/aggregate metrics
            try:
                workers = broker.get_workers(include_tasks=False) or []
            except Exception as e:
                logging.warning(f"broker.get_workers() failed: {e}")
                workers = []

            g_workers = GaugeMetricFamily(
                'fastpluggy_broker_workers',
                'Number of workers registered in broker'
            )
            g_topics_total = GaugeMetricFamily(
                'fastpluggy_broker_topics',
                'Number of topics registered in broker'
            )
            g_total_queued = GaugeMetricFamily(
                'fastpluggy_broker_messages_queued_total',
                'Total queued messages across all topics'
            )
            g_total_inflight = GaugeMetricFamily(
                'fastpluggy_broker_messages_inflight_total',
                'Total in-flight messages across all topics'
            )

            g_workers.add_metric([], len(workers))
            g_topics_total.add_metric([], topics_count)
            g_total_queued.add_metric([], total_queued)
            g_total_inflight.add_metric([], total_inflight)

            yield g_workers
            yield g_topics_total
            yield g_total_queued
            yield g_total_inflight

            # Locks metric if available
            try:
                locks = broker.get_locks() or []
                g_locks = GaugeMetricFamily(
                    'fastpluggy_broker_locks',
                    'Number of active task locks'
                )
                g_locks.add_metric([], len(locks))
                yield g_locks
            except Exception:
                pass

    try:
        REGISTRY.register(BrokerCollector())
        logging.info("Registered FastPluggy broker metrics collector")
        _BROKER_COLLECTOR_REGISTERED = True
    except Exception as e:
        logging.warning(f"Failed to register broker metrics collector: {e}")


