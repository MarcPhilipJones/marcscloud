"""Download WebRTC Camera card after adding to HACS."""
import asyncio
import json
import websockets

async def download_webrtc():
    url = 'ws://192.168.0.111:8123/api/websocket'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmMzE4NmJjNDU4Yzk0YThkOTljNjJjZjNjYTI3MGYxZiIsImlhdCI6MTc3MDAyOTc0NCwiZXhwIjoyMDg1Mzg5NzQ0fQ.27vsNq4Q6tDQRsbofnTDCrrkJQPTw8V4IoEQc7Jmp04'
    
    async with websockets.connect(url) as ws:
        await ws.recv()
        await ws.send(json.dumps({'type': 'auth', 'access_token': token}))
        await ws.recv()
        
        # List repos to find WebRTC
        print("Searching for WebRTC repository...")
        await ws.send(json.dumps({
            'id': 1,
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
        
        if webrtc:
            if webrtc.get('installed'):
                print("WebRTC is already installed!")
            else:
                print(f"\nDownloading WebRTC (ID: {webrtc.get('id')})...")
                await ws.send(json.dumps({
                    'id': 2,
                    'type': 'hacs/repository/download',
                    'repository': webrtc.get('id')
                }))
                resp = await ws.recv()
                result = json.loads(resp)
                print(f"Download result: {result}")
                
                if result.get('success'):
                    print("\n✅ WebRTC Camera card installed!")
                    print("⚠️  You need to restart Home Assistant for the card to become available.")
                    print("\nAfter restart, add this to your Lovelace resources:")
                    print("  /hacsfiles/WebRTC/webrtc-camera.js")
        else:
            print("WebRTC not found. Available repos with 'alexx' or 'rtc':")
            for repo in repos:
                full_name = (repo.get('full_name') or '').lower()
                name = (repo.get('name') or '').lower()
                if 'alexx' in full_name or 'rtc' in name:
                    print(f"  - {repo.get('full_name')}: {repo.get('name')}")

if __name__ == '__main__':
    asyncio.run(download_webrtc())
