"""Install WebRTC Camera card from HACS - attempt 2."""
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
        print(f"Found {len(repos)} plugin repositories")
        
        # Find WebRTC
        webrtc = None
        for repo in repos:
            if 'webrtc' in repo.get('full_name', '').lower():
                webrtc = repo
                print(f"\nFound WebRTC: {json.dumps(repo, indent=2)}")
                break
        
        if webrtc:
            repo_id = webrtc.get('id')
            print(f"\nAttempting to download repository ID: {repo_id}")
            
            # Try download with repository ID
            await ws.send(json.dumps({
                'id': 2,
                'type': 'hacs/repository/download',
                'repository': repo_id
            }))
            resp = await ws.recv()
            result = json.loads(resp)
            print(f"Download result: {result}")
            
            if not result.get('success'):
                # Try with full_name
                print("\nTrying with full_name...")
                await ws.send(json.dumps({
                    'id': 3,
                    'type': 'hacs/repository/info',
                    'repository_id': repo_id
                }))
                resp = await ws.recv()
                info = json.loads(resp)
                print(f"Repository info: {json.dumps(info, indent=2)}")
        else:
            print("WebRTC repository not found")

if __name__ == '__main__':
    asyncio.run(install_webrtc())
