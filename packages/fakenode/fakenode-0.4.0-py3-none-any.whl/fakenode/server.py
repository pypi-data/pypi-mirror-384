"""
Flask server for simulated Autonomi node.
Provides /metadata and /metrics endpoints in OpenMetrics format.
"""

import argparse
import time
import os
import sys
import random
import string
from flask import Flask, jsonify, make_response


def generate_peer_id():
    """Generate a random 53-character alphanumeric peer ID."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=53))


class FakeNode:
    """Simulated Autonomi node server."""

    def __init__(self, ip, port, show_version, root_dir, log_output_dest,
                 create_files, log_format='default'):
        self.ip = ip
        self.port = port
        self.show_version = show_version
        self.root_dir = root_dir
        self.log_output_dest = log_output_dest
        self.create_files = create_files
        self.log_format = log_format
        self.start_time = time.time()
        self.peer_id = None

        self.app = Flask(__name__)
        self._setup_routes()

    def _load_or_generate_peer_id(self):
        """Load peer ID from file or generate a new one."""
        peer_id_path = os.path.join(self.root_dir, 'peer-id')

        if os.path.exists(peer_id_path):
            try:
                with open(peer_id_path, 'r') as f:
                    self.peer_id = f.read().strip()
                return
            except Exception as e:
                print(f"Warning: Could not read peer-id file: {e}")

        # Generate new peer ID
        self.peer_id = generate_peer_id()

        # Save if create_files is enabled
        if self.create_files:
            try:
                with open(peer_id_path, 'w') as f:
                    f.write(self.peer_id)
            except Exception as e:
                print(f"Error: Could not create peer-id file: {e}")
                sys.exit(-1)

    def _create_startup_files(self):
        """Create required startup files if --create-files is enabled."""
        if not self.create_files:
            return

        errors = []

        # Create antnode.pid file
        pid_path = os.path.join(self.root_dir, 'antnode.pid')
        try:
            with open(pid_path, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            errors.append(f"Could not create antnode.pid: {e}")

        # Create antnode.log file
        if self.log_output_dest != 'stdout':
            log_path = os.path.join(self.log_output_dest, 'antnode.log')
            try:
                os.makedirs(self.log_output_dest, exist_ok=True)
                with open(log_path, 'w') as f:
                    if self.log_format == 'json':
                        # JSON format log message
                        import datetime
                        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
                        log_message = f'{{"timestamp":"{timestamp}","level":"INFO","message":"Starting fakenode listening on TCP port {self.port}","target":"ant_bootstrap::bootstrap"}}\n'
                        f.write(log_message)
                    else:
                        # Default format log message
                        f.write(f"Starting fakenode listening on TCP port {self.port}\n")
            except Exception as e:
                errors.append(f"Could not create antnode.log: {e}")

        if errors:
            for error in errors:
                print(f"Error: {error}")
            sys.exit(-1)

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route('/metadata')
        def metadata():
            """Return node metadata in OpenMetrics format."""
            # Always return OpenMetrics format
            openmetrics_output = f"""# HELP ant_node_antnode_version The version of the ant node.
# TYPE ant_node_antnode_version info
ant_node_antnode_version_info{{antnode_version="{self.show_version}"}} 1
# HELP ant_node_antnode_branch The branch of the ant node.
# TYPE ant_node_antnode_branch info
ant_node_antnode_branch_info{{antnode_branch="fakenode"}} 1
# HELP ant_networking_peer_id Identifier of a peer of the network.
# TYPE ant_networking_peer_id info
ant_networking_peer_id_info{{peer_id="{self.peer_id}"}} 1
# HELP ant_networking_identify_protocol_str The protocol version string that is used to connect to the correct network.
# TYPE ant_networking_identify_protocol_str info
ant_networking_identify_protocol_str_info{{identify_protocol_str="ant/1.0/1"}} 1
# EOF
"""
            response = make_response(openmetrics_output, 200)
            response.headers['Content-Type'] = 'application/openmetrics-text;charset=utf-8;version=1.0.0'
            return response

        @self.app.route('/metrics')
        def metrics():
            """Return node metrics in OpenMetrics format."""
            uptime_seconds = int(time.time() - self.start_time)

            # Always return OpenMetrics format
            openmetrics_output = f"""# HELP ant_node_put_record_ok Number of successful record PUTs.
# TYPE ant_node_put_record_ok counter
ant_node_put_record_ok_total{{record_type="Chunk"}} 9
# HELP ant_node_put_record_err Number of errors during record PUTs.
# TYPE ant_node_put_record_err counter
ant_node_put_record_err_total 0
# HELP ant_node_put_record_err_v2 Number of errors during record PUTs.
# TYPE ant_node_put_record_err_v2 counter
# HELP ant_node_peer_added_to_routing_table Number of peers that have been added to the Routing Table.
# TYPE ant_node_peer_added_to_routing_table counter
ant_node_peer_added_to_routing_table_total 376
# HELP ant_node_peer_removed_from_routing_table Number of peers that have been removed from the Routing Table.
# TYPE ant_node_peer_removed_from_routing_table counter
ant_node_peer_removed_from_routing_table_total 19
# HELP ant_node_current_reward_wallet_balance The number of Nanos in the node reward wallet.
# TYPE ant_node_current_reward_wallet_balance gauge
ant_node_current_reward_wallet_balance 0
# HELP ant_node_uptime The uptime of the node in seconds.
# TYPE ant_node_uptime gauge
ant_node_uptime {uptime_seconds}
# HELP libp2p_bandwidth_bytes Bandwidth usage by direction and transport protocols.
# TYPE libp2p_bandwidth_bytes counter
# UNIT libp2p_bandwidth_bytes bytes
libp2p_bandwidth_bytes_total{{protocols="/ip4/udp/quic-v1/p2p",direction="Outbound"}} 1840522
libp2p_bandwidth_bytes_total{{protocols="/ip4/udp/quic-v1",direction="Outbound"}} 2641778
libp2p_bandwidth_bytes_total{{protocols="/ip4/udp/quic-v1",direction="Inbound"}} 7679130
libp2p_bandwidth_bytes_total{{protocols="/ip4/udp/quic-v1/p2p",direction="Inbound"}} 14180147
# HELP libp2p_identify_errors Number of errors while attempting to identify the remote.
# TYPE libp2p_identify_errors counter
libp2p_identify_errors_total 408
# HELP libp2p_identify_pushed Number of times identification information of the local node has been actively pushed to a peer..
# TYPE libp2p_identify_pushed counter
libp2p_identify_pushed_total 4
# HELP libp2p_identify_received Number of times identification information has been received from a peer.
# TYPE libp2p_identify_received counter
libp2p_identify_received_total 3139
# HELP libp2p_identify_sent Number of times identification information of the local node has been sent to a peer in response to an identification request.
# TYPE libp2p_identify_sent counter
libp2p_identify_sent_total 3396
# HELP libp2p_identify_remote_listen_addresses Number of connected nodes advertising a specific listen address
# TYPE libp2p_identify_remote_listen_addresses gauge
libp2p_identify_remote_listen_addresses{{listen_address="/ip4/udp/quic-v1/p2p"}} 3
# HELP libp2p_identify_local_observed_addresses Number of connected nodes observing the local node at a specific address
# TYPE libp2p_identify_local_observed_addresses gauge
libp2p_identify_local_observed_addresses{{observed_address="/ip4/udp/quic-v1"}} 3
# HELP libp2p_kad_query_result_get_record_ok Number of records returned by a successful Kademlia get record query.
# TYPE libp2p_kad_query_result_get_record_ok counter
libp2p_kad_query_result_get_record_ok_total 0
# HELP libp2p_kad_query_result_get_record_error Number of failed Kademlia get record queries.
# TYPE libp2p_kad_query_result_get_record_error counter
# HELP libp2p_kad_query_result_get_closest_peers_ok Number of closest peers returned by a successful Kademlia get closest peers query.
# TYPE libp2p_kad_query_result_get_closest_peers_ok histogram
libp2p_kad_query_result_get_closest_peers_ok_sum 699.0
libp2p_kad_query_result_get_closest_peers_ok_count 35
# HELP ant_networking_records_stored The number of records stored locally.
# TYPE ant_networking_records_stored gauge
ant_networking_records_stored 10
# HELP ant_networking_relay_reservation_health The average health of all the relay reservation connections. Value is between 0-1.
# TYPE ant_networking_relay_reservation_health gauge
ant_networking_relay_reservation_health 0.0
# HELP ant_networking_connected_peers The number of peers that we are currently connected to.
# TYPE ant_networking_connected_peers gauge
ant_networking_connected_peers 4
# HELP ant_networking_connected_relay_clients The number of relay clients that are currently connected to us.
# TYPE ant_networking_connected_relay_clients gauge
ant_networking_connected_relay_clients 0
# HELP ant_networking_estimated_network_size The estimated number of nodes in the network calculated by the peers in our RT.
# TYPE ant_networking_estimated_network_size gauge
ant_networking_estimated_network_size 2490368
# HELP ant_networking_relay_peers_percentage The percentage of relay peers in our routing table.
# TYPE ant_networking_relay_peers_percentage gauge
ant_networking_relay_peers_percentage 0.0
# HELP ant_networking_open_connections The number of active connections to other peers.
# TYPE ant_networking_open_connections gauge
ant_networking_open_connections 4
# HELP ant_networking_peers_in_routing_table The total number of peers in our routing table.
# TYPE ant_networking_peers_in_routing_table gauge
ant_networking_peers_in_routing_table 357
# HELP ant_networking_relay_peers_in_routing_table The total number of relay peers in our routing table.
# TYPE ant_networking_relay_peers_in_routing_table gauge
ant_networking_relay_peers_in_routing_table 0
# HELP ant_networking_shunned_count Number of peers that have shunned our node.
# TYPE ant_networking_shunned_count counter
ant_networking_shunned_count_total 0
# HELP ant_networking_bad_peers_count Number of bad peers that have been detected by us and been added to the blocklist.
# TYPE ant_networking_bad_peers_count counter
ant_networking_bad_peers_count_total 0
# HELP ant_networking_upnp_events Events emitted by the UPnP behaviour.
# TYPE ant_networking_upnp_events counter
# HELP ant_networking_relay_client_events Events emitted by the relay client.
# TYPE ant_networking_relay_client_events counter
ant_networking_relay_client_events_total{{event="OutboundCircuitEstablished"}} 8
# HELP ant_networking_node_versions Number of nodes running each version.
# TYPE ant_networking_node_versions gauge
ant_networking_node_versions{{version="2025.9.1.2"}} 15
ant_networking_node_versions{{version="old"}} 3
ant_networking_node_versions{{version="2025.7.1.3"}} 1
# HELP ant_networking_process_memory_used_mb Memory used by the process in MegaBytes.
# TYPE ant_networking_process_memory_used_mb gauge
ant_networking_process_memory_used_mb 24.3302
# HELP ant_networking_process_cpu_usage_percentage The percentage of CPU used by the process. Value is from 0-100.
# TYPE ant_networking_process_cpu_usage_percentage gauge
ant_networking_process_cpu_usage_percentage 0.0423
# HELP ant_networking_relevant_records The number of records that we're responsible for. This is used to calculate the store cost.
# TYPE ant_networking_relevant_records gauge
ant_networking_relevant_records 0
# HELP ant_networking_max_records The maximum number of records that we can store. This is used to calculate the store cost.
# TYPE ant_networking_max_records gauge
ant_networking_max_records 0
# HELP ant_networking_received_payment_count The number of payments received by our node. This is used to calculate the store cost.
# TYPE ant_networking_received_payment_count gauge
ant_networking_received_payment_count 0
# HELP ant_networking_live_time The time for which the node has been alive. This is used to calculate the store cost.
# TYPE ant_networking_live_time gauge
ant_networking_live_time 0
# HELP ant_networking_shunned_by_close_group The number of close group peers that have shunned our node.
# TYPE ant_networking_shunned_by_close_group gauge
ant_networking_shunned_by_close_group 0
# HELP ant_networking_shunned_by_old_close_group The number of close group peers that have shunned our node. This contains the peers that were once in our close group but have since been evicted..
# TYPE ant_networking_shunned_by_old_close_group gauge
ant_networking_shunned_by_old_close_group 0
# EOF
"""
            response = make_response(openmetrics_output, 200)
            response.headers['Content-Type'] = 'application/openmetrics-text;charset=utf-8;version=1.0.0'
            return response

        @self.app.errorhandler(404)
        def not_found(error):
            """Handle 404 errors with custom message."""
            response = make_response(f"Not found try localhost:{self.port}/metrics", 404)
            response.headers['Content-Type'] = 'text/plain'
            return response

    def initialize(self):
        """Initialize the node - load peer ID and create files."""
        self._load_or_generate_peer_id()
        self._create_startup_files()

    def run(self):
        """Start the Flask server."""
        self.app.run(host=self.ip, port=self.port)


def main():
    """Main entry point for the fakenode CLI."""
    parser = argparse.ArgumentParser(description='Simulated Autonomi node for testing')

    # Required and optional arguments
    parser.add_argument('--ip', type=str, default='0.0.0.0', help='IP address to bind to')
    parser.add_argument('--metrics-server-port', type=int, help='Port to listen on')
    parser.add_argument('--root-dir', type=str, default='.', help='Path to node environment')
    parser.add_argument('--log-output-dest', type=str, default='stdout',
                        help='Path for logs or "stdout"')
    parser.add_argument('--show-version', type=str, help='The antnode version number to simulate')
    parser.add_argument('--version', action='store_true',
                        help='Output version information and exit')
    parser.add_argument('--create-files', action='store_true',
                        help='Create antnode.pid, peer-id, and antnode.log files')
    parser.add_argument('--log-format', type=str, default='default',
                        choices=['default', 'json'],
                        help='Format for log file output (default: default)')

    args, unknown_args = parser.parse_known_args()

    # Log unknown arguments if any are provided
    if unknown_args:
        print(f"Note: Ignoring unknown arguments: {' '.join(unknown_args)}")

    # Handle --version flag
    if args.version:
        version_str = args.show_version if args.show_version else "0.4.6"
        print(f"""Autonomi Node v{version_str}
Network version: ant/1.0/1
Package version: 2025.9.1.2
Git info: fakenode / c3dbf09 / 2025-10-15""")
        sys.exit(0)

    # Validate required arguments for server mode
    if not args.show_version:
        parser.error('--show-version is required when not using --version flag')
    if not args.metrics_server_port:
        parser.error('--metrics-server-port is required when not using --version flag')

    # Create and initialize the node
    node = FakeNode(
        ip=args.ip,
        port=args.metrics_server_port,
        show_version=args.show_version,
        root_dir=args.root_dir,
        log_output_dest=args.log_output_dest,
        create_files=args.create_files,
        log_format=args.log_format
    )

    node.initialize()

    print(f"Starting fakenode on {args.ip}:{args.metrics_server_port}")
    print(f"Version: {args.show_version}")
    print(f"Peer ID: {node.peer_id}")
    print(f"Output format: {args.log_format}")

    node.run()


if __name__ == '__main__':
    main()
