"""Check go2rtc streams and update CCTV2 dashboard with correct URLs."""
import asyncio
import json
import websockets

async def check_go2rtc_and_update():
    url = 'ws://192.168.0.111:8123/api/websocket'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmMzE4NmJjNDU4Yzk0YThkOTljNjJjZjNjYTI3MGYxZiIsImlhdCI6MTc3MDAyOTc0NCwiZXhwIjoyMDg1Mzg5NzQ0fQ.27vsNq4Q6tDQRsbofnTDCrrkJQPTw8V4IoEQc7Jmp04'
    
    # Check go2rtc API
    print("Checking go2rtc streams...")
    try:
        import urllib.request
        req = urllib.request.Request('http://192.168.0.111:1984/api/streams')
        with urllib.request.urlopen(req, timeout=5) as response:
            streams = json.loads(response.read().decode())
            print(f"go2rtc streams: {json.dumps(streams, indent=2)}")
    except Exception as e:
        print(f"Could not reach go2rtc API at port 1984: {e}")
        print("Trying HA's built-in go2rtc...")
    
    cameras = [
        {'entity': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_101', 'name': 'Camera 01'},
        {'entity': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_201', 'name': 'Camera 02'},
        {'entity': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_301', 'name': 'Camera 03'},
        {'entity': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_401', 'name': 'Camera 04'}
    ]
    
    async with websockets.connect(url, max_size=10*1024*1024) as ws:
        await ws.recv()
        await ws.send(json.dumps({'type': 'auth', 'access_token': token}))
        await ws.recv()
        
        # Check Lovelace resources
        print("\nChecking Lovelace resources...")
        await ws.send(json.dumps({
            'id': 1,
            'type': 'lovelace/resources'
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        resources = result.get('result', [])
        print(f"Resources: {json.dumps(resources, indent=2)}")
        
        # Try using picture-glance cards with camera_view: live for WebRTC
        # This uses HA's native WebRTC streaming
        print("\nUpdating dashboard to use native HA camera cards with WebRTC...")
        
        camera_cards = []
        for cam in cameras:
            camera_cards.append({
                'type': 'picture-entity',
                'entity': cam['entity'],
                'camera_view': 'live',  # This enables WebRTC streaming
                'show_state': False,
                'show_name': True
            })
        
        dashboard_config = {
            'views': [{
                'title': 'CCTV2 WebRTC',
                'path': 'cctv2',
                'panel': False,
                'cards': [
                    {
                        'type': 'grid',
                        'columns': 2,
                        'square': False,
                        'cards': camera_cards
                    }
                ]
            }]
        }
        
        await ws.send(json.dumps({
            'id': 2,
            'type': 'lovelace/config/save',
            'url_path': 'dashboard-cctv2',
            'config': dashboard_config
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        print(f"Dashboard update result: {result}")
        
        if result.get('success'):
            print("\n✅ Dashboard updated with camera_view: live")
            print("This uses Home Assistant's native WebRTC streaming via go2rtc")

if __name__ == '__main__':
    asyncio.run(check_go2rtc_and_update())
