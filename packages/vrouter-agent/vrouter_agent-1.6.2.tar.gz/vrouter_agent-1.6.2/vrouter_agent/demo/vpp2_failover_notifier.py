from vrouter_agent.failover.failover_notifier import run_failover_notifier_loop


def run():
    run_failover_notifier_loop(2, 1)
