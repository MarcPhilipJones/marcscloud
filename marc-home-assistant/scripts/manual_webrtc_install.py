"""Manually install WebRTC card by downloading from GitHub and adding as Lovelace resource."""
import asyncio
import json
import websockets

WEBRTC_JS_URL = "https://github.com/AlexxIT/WebRTC/releases/latest/download/webrtc-camera.js"

async def install_webrtc_manual():
    url = 'ws://192.168.0.111:8123/api/websocket'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmMzE4NmJjNDU4Yzk0YThkOTljNjJjZjNjYTI3MGYxZiIsImlhdCI6MTc3MDAyOTc0NCwiZXhwIjoyMDg1Mzg5NzQ0fQ.27vsNq4Q6tDQRsbofnTDCrrkJQPTw8V4IoEQc7Jmp04'
    
    # First check what Lovelace resources we have
    async with websockets.connect(url, max_size=10*1024*1024) as ws:
        await ws.recv()
        await ws.send(json.dumps({'type': 'auth', 'access_token': token}))
        await ws.recv()
        
        # Check existing resources
        print("Checking existing Lovelace resources...")
        await ws.send(json.dumps({
            'id': 1,
            'type': 'lovelace/resources'
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        resources = result.get('result', [])
        print(f"Found {len(resources)} resources:")
        for r in resources:
            print(f"  - {r.get('url')}")
        
        # Check if WebRTC is already added
        webrtc_exists = any('webrtc' in (r.get('url') or '').lower() for r in resources)
        
        if webrtc_exists:
            print("\n✅ WebRTC resource already exists!")
        else:
            print("\nWebRTC not found. Need to add it manually.")
            print("\nTo add WebRTC manually:")
            print("1. Download webrtc-camera.js from GitHub releases")
            print("2. Upload to /config/www/ folder on HA")
            print("3. Add resource /local/webrtc-camera.js")
            
            # Let's try adding a resource pointing to GitHub CDN
            print("\nTrying to add as CDN resource (jsdelivr)...")
            await ws.send(json.dumps({
                'id': 2,
                'type': 'lovelace/resources/create',
                'res_type': 'module',
                'url': 'https://cdn.jsdelivr.net/gh/AlexxIT/WebRTC@master/custom_components/webrtc/www/webrtc-camera.js'
            }))
            resp = await ws.recv()
            result = json.loads(resp)
            print(f"Add resource result: {result}")
            
            if result.get('success'):
                print("\n✅ WebRTC resource added from CDN!")
                print("⚠️  You may need to refresh your browser or restart HA")
            else:
                print(f"\n❌ Failed: {result.get('error')}")
                
        # Also check if go2rtc is running
        print("\n\nChecking go2rtc status...")
        await ws.send(json.dumps({
            'id': 10,
            'type': 'get_states'
        }))
        resp = await ws.recv()
        states = json.loads(resp).get('result', [])
        
        go2rtc_entities = [s for s in states if 'go2rtc' in s.get('entity_id', '').lower()]
        if go2rtc_entities:
            print(f"Found go2rtc entities: {[e['entity_id'] for e in go2rtc_entities]}")
        else:
            print("No go2rtc entities found in states")
        
        # Look for camera entities that might use go2rtc
        camera_entities = [s for s in states if s.get('entity_id', '').startswith('camera.')]
        print(f"\nCamera entities ({len(camera_entities)}):")
        for cam in camera_entities:
            print(f"  - {cam['entity_id']}: {cam.get('state')}")
            attrs = cam.get('attributes', {})
            if 'stream_source' in attrs:
                print(f"    stream_source: {attrs['stream_source']}")

if __name__ == '__main__':
    asyncio.run(install_webrtc_manual())
