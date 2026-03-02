"""Get Thread network details from Home Assistant."""
import asyncio
import json
import websockets

async def get_thread_info():
    url = 'ws://192.168.0.111:8123/api/websocket'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmMzE4NmJjNDU4Yzk0YThkOTljNjJjZjNjYTI3MGYxZiIsImlhdCI6MTc3MDAyOTc0NCwiZXhwIjoyMDg1Mzg5NzQ0fQ.27vsNq4Q6tDQRsbofnTDCrrkJQPTw8V4IoEQc7Jmp04'
    
    async with websockets.connect(url, max_size=10*1024*1024) as ws:
        await ws.recv()
        await ws.send(json.dumps({'type': 'auth', 'access_token': token}))
        await ws.recv()
        
        # Get Thread dataset info
        print("=== Thread Network Information ===\n")
        
        # List Thread datasets
        await ws.send(json.dumps({
            'id': 1,
            'type': 'thread/list_datasets'
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        print("Thread Datasets:")
        print(json.dumps(result.get('result', result), indent=2))
        
        # Get Thread network diagnostics
        await ws.send(json.dumps({
            'id': 2,
            'type': 'thread/discover_routers'
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        print("\n\nThread Routers:")
        print(json.dumps(result.get('result', result), indent=2))
        
        # Check Matter entities (often use Thread)
        await ws.send(json.dumps({
            'id': 3,
            'type': 'config_entries/get',
            'domain': 'thread'
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        print("\n\nThread Config Entries:")
        print(json.dumps(result.get('result', result), indent=2))
        
        # Get all config entries to find Thread-related
        await ws.send(json.dumps({
            'id': 4,
            'type': 'config_entries/get'
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        entries = result.get('result', [])
        
        thread_entries = [e for e in entries if 'thread' in e.get('domain', '').lower() or 'thread' in e.get('title', '').lower()]
        matter_entries = [e for e in entries if 'matter' in e.get('domain', '').lower()]
        
        if thread_entries:
            print("\n\nThread-related config entries:")
            for e in thread_entries:
                print(f"  - {e.get('title')} ({e.get('domain')}): {e.get('state')}")
        
        if matter_entries:
            print("\n\nMatter config entries (may use Thread):")
            for e in matter_entries:
                print(f"  - {e.get('title')} ({e.get('domain')}): {e.get('state')}")

if __name__ == '__main__':
    asyncio.run(get_thread_info())
