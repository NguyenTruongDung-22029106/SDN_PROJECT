"""Hyperledger Fabric Client for SDN Controller
Provides Python interface to interact with a real Hyperledger Fabric network.
This file no longer contains the MockBlockchainClient - the project is
configured to require a real Fabric environment.
"""
import json
import time
import os
import subprocess
import shutil
import tempfile
from datetime import datetime


class BlockchainClient:
    """
    Client for interacting with Hyperledger Fabric blockchain
    Used by SDN controller to record security events
    """
    
    def __init__(self, 
                 network_path=None,
                 channel_name='sdnchannel',
                 chaincode_name='trustlog',
                 org_name='Org1',
                 use_gateway=False):
        """
        Initialize blockchain client
        
        Args:
            network_path: Path to Fabric network directory
            channel_name: Blockchain channel name
            chaincode_name: Name of deployed chaincode
            org_name: Organization name
            use_gateway: Use REST gateway instead of direct CLI
        """
        self.channel_name = channel_name
        self.chaincode_name = chaincode_name
        self.org_name = org_name
        self.use_gateway = use_gateway
        
        # Set network path (resolve to absolute path). If a relative path is
        # provided, treat it as relative to the repository root (one level up
        # from this file). This prevents the peer CLI from interpreting the
        # path relative to FABRIC_CFG_PATH which can cause missing-file errors.
        if network_path is None:
            default_rel = os.path.join(os.path.dirname(__file__), '..', 'fabric-samples', 'test-network')
            self.network_path = os.path.abspath(default_rel)
        else:
            if os.path.isabs(network_path):
                self.network_path = network_path
            else:
                repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                self.network_path = os.path.abspath(os.path.join(repo_root, network_path))
        
        # Gateway URL if using REST API
        self.gateway_url = "http://localhost:3001"
        
        print(f"Blockchain Client initialized")
        print(f"  Channel: {self.channel_name}")
        print(f"  Chaincode: {self.chaincode_name}")
        print(f"  Mode: {'Gateway' if use_gateway else 'CLI'}")
        # Quick environment checks for CLI mode
        if not self.use_gateway:
            peer_path = shutil.which('peer')
            if peer_path is None:
                raise EnvironmentError(
                    "`peer` CLI not found on PATH. Install Fabric binaries or set use_gateway=True.\n"
                    "See docs/FABRIC_SETUP_NOTE.md for setup instructions."
                )

    def record_event(self, event_data):
        """
        Record a security event to blockchain
        
        Args:
            event_data: Dictionary containing event information
                {
                    'event_type': 'attack_detected',
                    'switch_id': 's1',
                    'timestamp': 1234567890,
                    'trust_score': 0.5,
                    'action': 'block',
                    'details': {...}
                }
        
        Returns:
            bool: Success status
        """
        try:
            # Accept either a JSON string or a dict-like event_data
            if isinstance(event_data, str):
                try:
                    event = json.loads(event_data)
                except Exception:
                    print("record_event: provided string is not valid JSON")
                    return False
            elif isinstance(event_data, (dict,)):
                event = dict(event_data)
            else:
                print("record_event: unsupported event_data type")
                return False

            # Normalize common key names to the chaincode expected snake_case
            event = self._normalize_event(event)

            if self.use_gateway:
                return self._invoke_via_gateway('RecordEvent', event)
            else:
                return self._invoke_via_cli('RecordEvent', event)

        except Exception as e:
            print(f"Error recording event to blockchain: {e}")
            return False

    def _normalize_event(self, event):
        """
        Normalize event dict keys to the chaincode expected snake_case fields.
        Known output keys: event_id, event_type, switch_id, timestamp, trust_score,
        action, details, recorded_by, recorded_time
        """
        def pick(keys, d, default=None):
            for k in keys:
                if k in d:
                    return d[k]
            return default

        normalized = {}
        normalized['event_id'] = pick(['event_id', 'EventID', 'eventID', 'id'], event, '')
        normalized['event_type'] = pick(['event_type', 'EventType', 'type'], event, '')
        normalized['switch_id'] = pick(['switch_id', 'SwitchID', 'switchId', 'switch'], event, '')
        # timestamp / time
        ts = pick(['timestamp', 'Timestamp', 'time'], event, None)
        if ts is None:
            ts = int(time.time())
        try:
            normalized['timestamp'] = int(ts)
        except Exception:
            normalized['timestamp'] = int(time.time())

        # trust score could be float or int
        tscr = pick(['trust_score', 'TrustScore', 'trust'], event, None)
        try:
            normalized['trust_score'] = float(tscr) if tscr is not None else 0.0
        except Exception:
            normalized['trust_score'] = 0.0

        normalized['action'] = pick(['action', 'Action'], event, '')
        normalized['details'] = pick(['details', 'Details'], event, {}) or {}
        # recorded_time - prefer provided, else use timestamp
        rt = pick(['recorded_time', 'RecordedTime', 'recordedTime'], event, None)
        if rt is None:
            rt = normalized['timestamp']
        try:
            normalized['recorded_time'] = int(rt)
        except Exception:
            normalized['recorded_time'] = normalized['timestamp']

        # recorded_by left blank; chaincode will fill identity when invoked
        normalized['recorded_by'] = pick(['recorded_by', 'RecordedBy'], event, '')

        return normalized

    def query_event(self, event_id):
        """
        Query a specific event from blockchain
        
        Args:
            event_id: Event identifier
            
        Returns:
            dict: Event data or None
        """
        try:
            if self.use_gateway:
                return self._query_via_gateway('QueryEvent', event_id)
            else:
                return self._query_via_cli('QueryEvent', event_id)
        except Exception as e:
            print(f"Error querying event: {e}")
            return None

    def query_trust_log(self, device_id):
        """
        Query trust log for a device
        
        Args:
            device_id: Device identifier (e.g., switch ID)
            
        Returns:
            dict: Trust log data or None
        """
        try:
            if self.use_gateway:
                return self._query_via_gateway('QueryTrustLog', device_id)
            else:
                return self._query_via_cli('QueryTrustLog', device_id)
        except Exception as e:
            print(f"Error querying trust log: {e}")
            return None

    def query_events_by_switch(self, switch_id):
        """Query all events for a specific switch"""
        try:
            if self.use_gateway:
                return self._query_via_gateway('QueryEventsBySwitch', switch_id)
            else:
                return self._query_via_cli('QueryEventsBySwitch', switch_id)
        except Exception as e:
            print(f"Error querying events by switch: {e}")
            return None

    def query_events_by_type(self, event_type):
        """Query all events of a specific type"""
        try:
            if self.use_gateway:
                return self._query_via_gateway('QueryEventsByType', event_type)
            else:
                return self._query_via_cli('QueryEventsByType', event_type)
        except Exception as e:
            print(f"Error querying events by type: {e}")
            return None

    def _invoke_via_cli(self, function_name, *args):
        """
        Invoke chaincode function via Fabric CLI
        
        Args:
            function_name: Name of chaincode function
            *args: Function arguments
            
        Returns:
            bool: Success status
        """
        try:
            # Build ctor JSON string. We pass it directly to subprocess.run (no shell)
            ctor_json = self._build_ctor_string(function_name, args)

            cmd = [
                'peer', 'chaincode', 'invoke',
                '-o', 'localhost:7050',
                '--ordererTLSHostnameOverride', 'orderer.example.com',
                '--tls',
                # orderer tls CA is stored under the ordererOrganizations msp/tlscacerts
                '--cafile', f'{self.network_path}/organizations/ordererOrganizations/example.com/msp/tlscacerts/tlsca.example.com-cert.pem',
                '-C', self.channel_name,
                '-n', self.chaincode_name,
                '--peerAddresses', 'localhost:7051',
                '--tlsRootCertFiles', f'{self.network_path}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt',
                '--peerAddresses', 'localhost:9051',
                '--tlsRootCertFiles', f'{self.network_path}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt',
                '-c', ctor_json
            ]

            # Prepare environment variables
            env = os.environ.copy()
            env['FABRIC_CFG_PATH'] = os.path.abspath(os.path.join(self.network_path, '../config'))
            env['CORE_PEER_TLS_ENABLED'] = 'true'
            env['CORE_PEER_LOCALMSPID'] = 'Org1MSP'
            env['CORE_PEER_MSPCONFIGPATH'] = f'{self.network_path}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp'
            env['CORE_PEER_ADDRESS'] = 'localhost:7051'
            env['CORE_PEER_TLS_ROOTCERT_FILE'] = f'{self.network_path}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt'

            # Execute command
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=60
            )

            # no temp file to clean up when passing JSON directly

            if result.returncode == 0:
                print(f"✓ Blockchain invoke successful: {function_name}")
                return True
            else:
                print(f"✗ Blockchain invoke failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("Blockchain invoke timeout")
            return False
        except Exception as e:
            print(f"Error invoking chaincode: {e}")
            return False

    def _query_via_cli(self, function_name, *args):
        """
        Query chaincode function via Fabric CLI
        
        Args:
            function_name: Name of chaincode function
            *args: Function arguments
            
        Returns:
            dict: Query result or None
        """
        try:
            # Build ctor JSON string and pass directly
            ctor_json = self._build_ctor_string(function_name, args)

            cmd = [
                'peer', 'chaincode', 'query',
                '-C', self.channel_name,
                '-n', self.chaincode_name,
                '-c', ctor_json
            ]

            # Prepare environment variables
            env = os.environ.copy()
            env['FABRIC_CFG_PATH'] = os.path.abspath(os.path.join(self.network_path, '../config'))
            env['CORE_PEER_TLS_ENABLED'] = 'true'
            env['CORE_PEER_LOCALMSPID'] = 'Org1MSP'
            env['CORE_PEER_MSPCONFIGPATH'] = f'{self.network_path}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp'
            env['CORE_PEER_ADDRESS'] = 'localhost:7051'
            env['CORE_PEER_TLS_ROOTCERT_FILE'] = f'{self.network_path}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt'

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # peer query prints the returned payload to stdout
                try:
                    return json.loads(result.stdout)
                except Exception:
                    return result.stdout
            else:
                print(f"Query failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print("Blockchain query timeout")
            return None
        except Exception as e:
            print(f"Error querying chaincode: {e}")
            return None

    def _write_ctor_file(self, function_name, args):
        """
        Write a temporary constructor JSON file for the peer CLI to avoid quoting/escaping issues.
        Returns the path to the temporary file.
        """
        # Prepare args: if an arg is a dict or list, JSON-dump it so it's passed as a string
        processed_args = []
        for a in args:
            if isinstance(a, (dict, list)):
                processed_args.append(json.dumps(a))
            else:
                # ensure it's a string
                processed_args.append(str(a))

        ctor = {"Args": [function_name] + processed_args}
        tf = tempfile.NamedTemporaryFile(mode='w', delete=False, prefix='ctor_', suffix='.json')
        json.dump(ctor, tf)
        tf.close()
        return tf.name

    def _build_ctor_string(self, function_name, args):
        """
        Build the constructor JSON string to pass to peer CLI directly.
        Returns a JSON string (not a file:// path).
        """
        processed_args = []
        for a in args:
            if isinstance(a, (dict, list)):
                processed_args.append(json.dumps(a))
            else:
                processed_args.append(str(a))

        ctor = {"Args": [function_name] + processed_args}
        return json.dumps(ctor)

    def _invoke_via_gateway(self, function_name, *args):
        """Invoke via REST gateway (requires separate gateway service)"""
        try:
            import requests
            url = f"{self.gateway_url}/invoke"
            payload = {
                'channelName': self.channel_name,
                'chaincodeName': self.chaincode_name,
                'function': function_name,
                'args': list(args)
            }
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Gateway invoke error: {e}")
            return False

    def _query_via_gateway(self, function_name, *args):
        """Query via REST gateway"""
        try:
            import requests
            url = f"{self.gateway_url}/query"
            payload = {
                'channelName': self.channel_name,
                'chaincodeName': self.chaincode_name,
                'function': function_name,
                'args': list(args)
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            print(f"Gateway query error: {e}")
            return None


# Utility functions
def create_event_data(event_type, switch_id, trust_score=1.0, action='', **details):
    """
    Helper function to create event data structure.

    Returns a dict ready to be passed to BlockchainClient.record_event
    """
    return {
        'event_type': event_type,
        'switch_id': switch_id,
        'timestamp': int(time.time()),
        'trust_score': trust_score,
        'action': action,
        'details': details
    }
