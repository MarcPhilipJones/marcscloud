"""Install WebRTC Camera card from HACS."""
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
        
        # Search for WebRTC in HACS repositories
        print("Searching for WebRTC Camera in HACS...")
        await ws.send(json.dumps({
            'id': 1,
            'type': 'hacs/repositories/list',
            'categories': ['plugin']
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        
        if not result.get('success'):
            print(f"HACS query failed: {result.get('error')}")
            return
        
        # Find WebRTC camera
        repos = result.get('result', [])
        webrtc_repo = None
        for repo in repos:
            name = repo.get('name', '').lower()
            full_name = repo.get('full_name', '').lower()
            if 'webrtc' in name or 'webrtc' in full_name:
                print(f"Found: {repo.get('name')} - {repo.get('full_name')} (installed: {repo.get('installed')})")
                if 'camera' in name or 'camera' in full_name:
                    webrtc_repo = repo
        
        if not webrtc_repo:
            # Try to add the repository first
            print("\nWebRTC Camera not found in HACS. Adding repository...")
            await ws.send(json.dumps({
                'id': 2,
                'type': 'hacs/repositories/add',
                'repository': 'AlexxIT/WebRTC',
                'category': 'plugin'
            }))
            resp = await ws.recv()
            result = json.loads(resp)
            print(f"Add repository result: {result}")
            
            if result.get('success'):
                # Now download/install it
                print("\nDownloading WebRTC Camera...")
                await ws.send(json.dumps({
                    'id': 3,
                    'type': 'hacs/repository/download',
                    'repository': 'AlexxIT/WebRTC'
                }))
                resp = await ws.recv()
                result = json.loads(resp)
                print(f"Download result: {result}")
        else:
            if webrtc_repo.get('installed'):
                print(f"\nWebRTC Camera is already installed!")
            else:
                print(f"\nInstalling WebRTC Camera...")
                await ws.send(json.dumps({
                    'id': 2,
                    'type': 'hacs/repository/download',
                    'repository': webrtc_repo.get('full_name')
                }))
                resp = await ws.recv()
                result = json.loads(resp)
                print(f"Install result: {result}")

if __name__ == '__main__':
    asyncio.run(install_webrtc())
