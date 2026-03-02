"""Install WebRTC Camera card from HACS - search properly."""
import asyncio
import json
import websockets

async def install_webrtc():
    url = 'ws://192.168.0.111:8123/api/websocket'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmMzE4NmJjNDU4Yzk0YThkOTljNjJjZjNjYTI3MGYxZiIsImlhdCI6MTc3MDAyOTc0NCwiZXhwIjoyMDg1Mzg5NzQ0fQ.27vsNq4Q6tDQRsbofnTDCrrkJQPTw8V4IoEQc7Jmp04'
    
    async with websockets.connect(url) as ws:
        await ws.recv()
        await ws.send(json.dumps({'type': 'auth', 'access_token': token}))
        await ws.recv()
        
        # List all repositories to find WebRTC
        print("Listing all HACS plugin repositories...")
        await ws.send(json.dumps({
            'id': 1,
            'type': 'hacs/repositories/list',
            'categories': ['plugin']
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        
        repos = result.get('result', [])
        
        # Search for rtc, webrtc, or alexx
        print("\nSearching for WebRTC or Alexx repositories:")
        found = []
        for repo in repos:
            name = (repo.get('name') or '').lower()
            full_name = (repo.get('full_name') or '').lower()
            description = (repo.get('description') or '').lower()
            
            if 'rtc' in name or 'rtc' in full_name or 'alexx' in full_name or 'rtc' in description:
                found.append(repo)
                print(f"  - {repo.get('full_name')}: {repo.get('name')} (installed: {repo.get('installed', False)})")
        
        if not found:
            print("\nNo WebRTC found. Let's search for 'camera' cards:")
            for repo in repos:
                name = repo.get('name', '').lower()
                if 'camera' in name:
                    print(f"  - {repo.get('full_name')}: {repo.get('name')} (installed: {repo.get('installed', False)})")
        
        # Try to add WebRTC Camera manually
        print("\n\nAdding AlexxIT/WebRTC repository to HACS...")
        await ws.send(json.dumps({
            'id': 2,
            'type': 'hacs/repositories/add',
            'repository': 'AlexxIT/WebRTC',
            'category': 'plugin'
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        print(f"Add result: {result}")
        
        # Now list again and find it
        await ws.send(json.dumps({
            'id': 3,
            'type': 'hacs/repositories/list',
            'categories': ['plugin']
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        repos = result.get('result', [])
        
        for repo in repos:
            if 'alexx' in repo.get('full_name', '').lower():
                print(f"\nFound after add: {json.dumps(repo, indent=2)}")
                
                # Try to download
                print("\nDownloading...")
                await ws.send(json.dumps({
                    'id': 4,
                    'type': 'hacs/repository/download',
                    'repository': repo.get('id')
                }))
                resp = await ws.recv()
                dl_result = json.loads(resp)
                print(f"Download result: {dl_result}")
                break

if __name__ == '__main__':
    asyncio.run(install_webrtc())
