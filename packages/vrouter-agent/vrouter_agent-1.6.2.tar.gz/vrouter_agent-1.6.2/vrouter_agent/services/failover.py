import os

from vpp_vrouter.client import ExtendedVPPAPIClient
from vpp_vrouter.common import models
from vrouter_agent.utils import load_env_variables

WG_TUNNELS_PER_CONNECTION = 1


def run_failover_notifier_loop():
    """Example of how to use the existing client API to detect link failover."""

    def get_links_health(c, link1_wgs, link2_wgs) -> (bool, bool):
        """Gets health state (True=Healthy, False=Unhealthy) for links"""
        config_items = c.get_configuration().items
        link1_health = (
            len(
                {
                    route_path.outgoing_interface
                    for detail in config_items
                    if detail.state == models.State.APPLIED
                    and isinstance(detail.config, models.RouteConfigurationItem)
                    and detail.config.multi_output_paths
                    for route_path in detail.config.multi_output_paths
                    if route_path.outgoing_interface in link1_wgs
                }
            )
            >= WG_TUNNELS_PER_CONNECTION
        )
        link2_health = (
            len(
                {
                    route_path.outgoing_interface
                    for detail in config_items
                    if detail.state == models.State.APPLIED
                    and isinstance(detail.config, models.RouteConfigurationItem)
                    and detail.config.multi_output_paths
                    for route_path in detail.config.multi_output_paths
                    if route_path.outgoing_interface in link2_wgs
                }
            )
            >= WG_TUNNELS_PER_CONNECTION
        )
        return link1_health, link2_health

    def wait_for_failover(c, link1_wgs, link2_wgs):
        """Waits for failover to happen. It is done by analyzing the configuration state from vrouter."""

        initial_link1_health, initial_link2_health = get_links_health(
            c, link1_wgs, link2_wgs
        )
        actual_link1_health, actual_link2_health = (
            initial_link1_health,
            initial_link2_health,
        )

        def check_for_failover(config_item_details) -> bool:
            nonlocal actual_link1_health, actual_link2_health
            actual_link1_health, actual_link2_health = get_links_health(
                c, link1_wgs, link2_wgs
            )
            return (
                initial_link1_health != actual_link1_health
                and initial_link2_health != actual_link2_health
            )

        client.wait_for_configuration(configuration_check=check_for_failover)
        return (
            1 if actual_link1_health else 2,
            2 if actual_link1_health else 1,
            link1_wgs if actual_link1_health else link2_wgs,
            link2_wgs if actual_link1_health else link1_wgs,
        )

    # load info from env file
    load_env_variables(silent=True)

    # compute wg names for each underlay link
    link1_wg_names = ["wg0"]
    link2_wg_names = ["wg1"]

    with ExtendedVPPAPIClient() as client:
        # print initial link state
        print("Detected initial state:")
        health_link1, health_link2 = get_links_health(
            client, link1_wg_names, link2_wg_names
        )
        print(f"link1 is {'used' if health_link1 else 'not used'}")
        print(f"link2 is {'used' if health_link2 else 'not used'}")

        # notification loop
        while True:
            active_link, failing_link, active_link_wg_names, failing_link_wg_names = (
                wait_for_failover(client, link1_wg_names, link2_wg_names)
            )
            print(
                f"detected link failover: {failing_link} -> {active_link}  "
                + f"({failing_link_wg_names} -> {active_link_wg_names})"
            )


def run():
    run_failover_notifier_loop()
