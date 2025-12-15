import json
import os
import subprocess

from blockchain import fabric_client as fc


def test_build_ctor_string_and_write_file(tmp_path):
    client = fc.BlockchainClient(network_path='fabric-samples/test-network', use_gateway=False)

    ev = {
        'EventID': 'EVT-unit-1',
        'DeviceID': 's0',
        'SwitchID': 's0',
        'EventType': 'unit_test',
        'TrustScore': 42,
        'RecordedTime': 1620000000,
    }

    # _build_ctor_string should return a JSON string where the second Arg is a JSON string
    ctor_str = client._build_ctor_string('RecordEvent', (ev,))
    parsed = json.loads(ctor_str)
    assert parsed['Args'][0] == 'RecordEvent'
    assert isinstance(parsed['Args'][1], str)
    inner = json.loads(parsed['Args'][1])
    assert inner['EventID'] == 'EVT-unit-1'

    # _write_ctor_file should write equivalent content to disk
    path = client._write_ctor_file('RecordEvent', (ev,))
    try:
        assert os.path.exists(path)
        on_disk = json.load(open(path))
        assert on_disk['Args'][0] == 'RecordEvent'
        assert isinstance(on_disk['Args'][1], str)
        inner_disk = json.loads(on_disk['Args'][1])
        assert inner_disk['EventID'] == 'EVT-unit-1'
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


def test_record_event_invokes_subprocess(monkeypatch):
    client = fc.BlockchainClient(network_path='fabric-samples/test-network', use_gateway=False)

    ev = {
        'EventID': 'EVT-unit-2',
        'DeviceID': 's0',
        'SwitchID': 's0',
        'EventType': 'unit_test',
        'TrustScore': 12,
        'RecordedTime': 1620000001,
    }

    captured = {}

    def fake_run(cmd, capture_output=True, text=True, timeout=None):
        # capture the command array
        captured['cmd'] = cmd
        class R:
            returncode = 0
            stdout = ''
            stderr = ''
        return R()

    monkeypatch.setattr(subprocess, 'run', fake_run)

    ok = client.record_event(ev)
    assert ok is True

    # ensure the peer CLI was invoked and -c argument contains JSON (not file://)
    cmd = captured.get('cmd')
    assert cmd is not None
    assert 'peer' in cmd[0]
    # find -c and its value
    if '-c' in cmd:
        idx = cmd.index('-c')
        ctor_val = cmd[idx + 1]
        assert isinstance(ctor_val, str)
        assert not ctor_val.startswith('file://')
        parsed = json.loads(ctor_val)
        assert parsed['Args'][0] == 'RecordEvent'
    else:
        # some environments may put -c later, just ensure some element is JSON with Args
        found = False
        for a in cmd:
            try:
                j = json.loads(a)
                if isinstance(j, dict) and 'Args' in j:
                    found = True
                    break
            except Exception:
                continue
        assert found
