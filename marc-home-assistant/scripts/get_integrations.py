"""Get all config entries/integrations from Home Assistant."""
import asyncio
import json
import websockets

async def get_integrations():
    url = 'ws://192.168.0.111:8123/api/websocket'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmMzE4NmJjNDU4Yzk0YThkOTljNjJjZjNjYTI3MGYxZiIsImlhdCI6MTc3MDAyOTc0NCwiZXhwIjoyMDg1Mzg5NzQ0fQ.27vsNq4Q6tDQRsbofnTDCrrkJQPTw8V4IoEQc7Jmp04'
    
    async with websockets.connect(url, max_size=10*1024*1024) as ws:
        await ws.recv()
        await ws.send(json.dumps({'type': 'auth', 'access_token': token}))
        await ws.recv()
        
        # Get all config entries
        await ws.send(json.dumps({
            'id': 1,
            'type': 'config_entries/get'
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        entries = result.get('result', [])
        
        print(f"=== Config Entries ({len(entries)}) ===\n")
        
        # Group by domain
        by_domain = {}
        for entry in entries:
            domain = entry.get('domain', 'unknown')
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(entry)
        
        for domain in sorted(by_domain.keys()):
            items = by_domain[domain]
            print(f"\n{domain.upper()} ({len(items)}):")
            for item in items:
                state = item.get('state', 'unknown')
                title = item.get('title', 'Untitled')
                print(f"  - {title}: {state}")

if __name__ == '__main__':
    asyncio.run(get_integrations())
