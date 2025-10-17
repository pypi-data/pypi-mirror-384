# broker/factory.py


def get_broker():
    from ..config import TasksRunnerSettings
    setting = TasksRunnerSettings()

    if setting.BROKER_TYPE == "local":
        from .local import LocalBroker
        return LocalBroker()

    else:
        raise ValueError(f"Unsupported broker scheme: {setting.BROKER_TYPE}")


# def setup_broker():
#     """
#     Construct the configured broker and run its startup hook.
#     Use this at application startup (e.g., before launching uvicorn) to ensure
#     broker-specific prerequisites are ready. Returns the broker instance.
#     """
#     broker = get_broker()
#     # All brokers inherit a default no-op setup(); specific backends can override
#     # to perform work (LocalBroker ensures BaseManager is running/connected).
#     try:
#         broker.setup()
#     except Exception:
#         # Be defensive: setup should not crash the app if a backend chooses no-op behavior
#         pass
#     return broker
