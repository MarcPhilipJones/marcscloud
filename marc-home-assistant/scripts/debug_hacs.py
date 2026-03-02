"""Debug HACS custom repositories and WebRTC."""
import asyncio
import json
import websockets

async def debug_hacs():
    url = 'ws://192.168.0.111:8123/api/websocket'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmMzE4NmJjNDU4Yzk0YThkOTljNjJjZjNjYTI3MGYxZiIsImlhdCI6MTc3MDAyOTc0NCwiZXhwIjoyMDg1Mzg5NzQ0fQ.27vsNq4Q6tDQRsbofnTDCrrkJQPTw8V4IoEQc7Jmp04'
    
    async with websockets.connect(url) as ws:
        await ws.recv()
        await ws.send(json.dumps({'type': 'auth', 'access_token': token}))
        await ws.recv()
        
        # Get HACS info
        print("Getting HACS info...")
        await ws.send(json.dumps({
            'id': 1,
            'type': 'hacs/info'
        }))
        resp = await ws.recv()
        print(f"HACS info: {json.loads(resp)}")
        
        # Try to get custom repositories
        print("\nGetting repositories list (all categories)...")
        await ws.send(json.dumps({
            'id': 2,
            'type': 'hacs/repositories/list',
            'categories': ['plugin', 'integration', 'theme', 'python_script', 'appdaemon', 'netdaemon']
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        repos = result.get('result', [])
        print(f"Total repos: {len(repos)}")
        
        # Search for webrtc, alexx, or custom repos
        for repo in repos:
            full_name = (repo.get('full_name') or '').lower()
            name = (repo.get('name') or '').lower()
            if 'webrtc' in full_name or 'webrtc' in name or 'alexx' in full_name:
                print(f"\nFOUND: {repo}")
        
        # Also try to get the repository info directly
        print("\nTrying to get WebRTC repo info directly...")
        await ws.send(json.dumps({
            'id': 3,
            'type': 'hacs/repository/info',
            'repository_id': 'AlexxIT/WebRTC'
        }))
        resp = await ws.recv()
        print(f"Repo info result: {json.loads(resp)}")
        
        # Try refresh
        print("\nTriggering HACS data refresh...")
        await ws.send(json.dumps({
            'id': 4,
            'type': 'hacs/repositories/reload',
            'force': True
        }))
        resp = await ws.recv()
        print(f"Refresh result: {json.loads(resp)}")

if __name__ == '__main__':
    asyncio.run(debug_hacs())
