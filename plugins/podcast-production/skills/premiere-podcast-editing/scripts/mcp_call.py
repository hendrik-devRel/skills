#!/usr/bin/env python3
"""Explicit stdio MCP client for an installed server (tested on macOS).

Use callable host MCP tools first. This fallback does not install/configure a
server and never retries a request that might mutate Premiere.
"""
import argparse
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import tempfile
import time
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', required=True, type=Path,
                        help='Installed MCP server entrypoint, e.g. dist/index.js')
    parser.add_argument('--node', default='node', help='Node executable')
    parser.add_argument('--bridge-dir', type=Path, help='Existing CEP bridge directory')
    parser.add_argument('--timeout', type=float, default=90)
    parser.add_argument('--log-dir', type=Path, help='Optional request/result logs')
    parser.add_argument('--args-file', type=Path, help='JSON argument object file')
    parser.add_argument('tool', help='tools/list, search_tools, get_tool_schema, invoke_tool, etc.')
    parser.add_argument('arguments', nargs='?', help='JSON argument object')
    args = parser.parse_args()
    if not args.server.is_file():
        parser.error('Server entrypoint does not exist; locate the installed server first')
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    if args.args_file and args.arguments is not None:
        parser.error('Use --args-file or positional arguments, not both')
    try:
        params = json.loads(args.args_file.read_text() if args.args_file else (args.arguments or '{}'))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    if not isinstance(params, dict):
        parser.error('Arguments must be a JSON object')
    env = dict(os.environ, PREMIERE_MCP_TELEMETRY='0', PREMIERE_MCP_UPDATE_CHECK='0')
    if args.bridge_dir:
        env['PREMIERE_TEMP_DIR'] = str(args.bridge_dir.resolve())
    proc = None
    selector = selectors.DefaultSelector()
    log = {'tool': args.tool, 'arguments': params}
    try:
        with tempfile.TemporaryFile() as stderr:
            proc = subprocess.Popen([args.node, str(args.server.resolve())], stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=stderr, env=env)
            selector.register(proc.stdout, selectors.EVENT_READ)
            pending = bytearray()

            def send(value):
                proc.stdin.write((json.dumps(value) + '\n').encode())
                proc.stdin.flush()

            def receive(request_id):
                until = time.monotonic() + args.timeout
                while True:
                    while b'\n' in pending:
                        line, _, remainder = pending.partition(b'\n')
                        pending[:] = remainder
                        if not line.strip():
                            continue
                        response = json.loads(line)
                        if response.get('id') == request_id:
                            return response
                    remaining = until - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError('MCP response timed out; inspect Premiere state before retrying a mutation')
                    data = os.read(proc.stdout.fileno(), 65536)
                    if not data:
                        raise RuntimeError('MCP server exited before its response')
                    pending.extend(data)

            send({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
                'protocolVersion': '2025-06-18', 'capabilities': {},
                'clientInfo': {'name': 'podcast-edit-skill', 'version': '1.0'}}})
            initialized = receive(1)
            if 'error' in initialized:
                raise RuntimeError('MCP initialization failed: ' + json.dumps(initialized['error']))
            send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
            send({'jsonrpc': '2.0', 'id': 2,
                  'method': 'tools/list' if args.tool == 'tools/list' else 'tools/call',
                  'params': params if args.tool == 'tools/list' else {'name': args.tool, 'arguments': params}})
            response = receive(2)
            log['response'] = response
            payload = response.get('result', response)
            tool_error = isinstance(payload, dict) and bool(payload.get('isError'))
            if isinstance(payload, dict) and 'structuredContent' in payload:
                payload = payload['structuredContent']
            elif isinstance(payload, dict) and len(payload.get('content', [])) == 1:
                item = payload['content'][0]
                if item.get('type') == 'text':
                    try:
                        payload = json.loads(item['text'])
                    except ValueError:
                        pass
            print(json.dumps(payload, indent=2))
            return int('error' in response or tool_error or
                       (isinstance(payload, dict) and payload.get('success') is False))
    except (OSError, ValueError, RuntimeError, TimeoutError) as exc:
        log['clientError'] = str(exc)
        print(json.dumps({'success': False, 'clientError': str(exc)}), file=sys.stderr)
        return 1
    finally:
        selector.close()
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        if args.log_dir:
            args.log_dir.mkdir(parents=True, exist_ok=True)
            (args.log_dir / ('mcp-' + uuid.uuid4().hex + '.json')).write_text(json.dumps(log, indent=2))


if __name__ == '__main__':
    sys.exit(main())
