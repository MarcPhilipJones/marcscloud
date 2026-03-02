"""Add and download WebRTC Camera card from HACS."""
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
        
        # Step 1: Add the repository
        print("Step 1: Adding AlexxIT/WebRTC repository to HACS...")
        await ws.send(json.dumps({
            'id': 1,
            'type': 'hacs/repositories/add',
            'repository': 'AlexxIT/WebRTC',
            'category': 'plugin'
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        print(f"Add result: {result}")
        
        if not result.get('success'):
            print(f"Failed to add repository: {result.get('error')}")
            return
        
        # Wait a moment for HACS to process
        print("Waiting for HACS to process...")
        await asyncio.sleep(2)
        
        # Step 2: List repos again to find the ID
        print("\nStep 2: Finding repository ID...")
        await ws.send(json.dumps({
            'id': 2,
            'type': 'hacs/repositories/list',
            'categories': ['plugin']
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        repos = result.get('result', [])
        
        webrtc = None
        for repo in repos:
            full_name = (repo.get('full_name') or '').lower()
            if 'alexx' in full_name and 'webrtc' in full_name:
                webrtc = repo
                print(f"Found: {repo.get('full_name')} (ID: {repo.get('id')}, installed: {repo.get('installed')})")
                break
        
        if not webrtc:
            print("Could not find WebRTC after adding. Dumping all repos with 'webrtc' in name:")
            for repo in repos[:20]:
                print(f"  {repo.get('id')}: {repo.get('full_name')} - {repo.get('name')}")
            return
        
        # Step 3: Download/install the repository
        if webrtc.get('installed'):
            print("\n✅ WebRTC is already installed!")
        else:
            print(f"\nStep 3: Downloading WebRTC (ID: {webrtc.get('id')})...")
            await ws.send(json.dumps({
                'id': 3,
                'type': 'hacs/repository/download',
                'repository': webrtc.get('id')
            }))
            resp = await ws.recv()
            result = json.loads(resp)
            print(f"Download result: {result}")
            
            if result.get('success'):
                print("\n✅ WebRTC Camera card installed successfully!")
                print("\n⚠️  IMPORTANT: Restart Home Assistant for the card to work!")
                print("\nCard type to use: custom:webrtc-camera")
                print("Resource path: /hacsfiles/webrtc/webrtc-camera.js")
            else:
                print(f"\n❌ Download failed: {result.get('error')}")

if __name__ == '__main__':
    asyncio.run(install_webrtc())
