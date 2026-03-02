"""Update CCTV2 dashboard to use WebRTC camera cards."""
import asyncio
import json
import websockets

async def update_cctv2_webrtc():
    url = 'ws://192.168.0.111:8123/api/websocket'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmMzE4NmJjNDU4Yzk0YThkOTljNjJjZjNjYTI3MGYxZiIsImlhdCI6MTc3MDAyOTc0NCwiZXhwIjoyMDg1Mzg5NzQ0fQ.27vsNq4Q6tDQRsbofnTDCrrkJQPTw8V4IoEQc7Jmp04'
    
    cameras = [
        {'entity': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_101', 'name': 'Camera 1'},
        {'entity': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_201', 'name': 'Camera 2'},
        {'entity': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_301', 'name': 'Camera 3'},
        {'entity': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_401', 'name': 'Camera 4'}
    ]
    
    async with websockets.connect(url, max_size=10*1024*1024) as ws:
        await ws.recv()
        await ws.send(json.dumps({'type': 'auth', 'access_token': token}))
        await ws.recv()
        
        # Create WebRTC camera cards with go2rtc streams
        camera_cards = []
        for cam in cameras:
            # WebRTC card with stream URL
            # go2rtc typically provides streams at http://ha-ip:1984/stream.html?src=camera_entity
            camera_cards.append({
                'type': 'custom:webrtc-camera',
                'entity': cam['entity'],
                'title': cam['name'],
                'style': 'width: 100%;'
            })
        
        # Build the dashboard with a grid layout
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
        
        print("Updating CCTV2 dashboard with WebRTC cards...")
        await ws.send(json.dumps({
            'id': 1,
            'type': 'lovelace/config/save',
            'url_path': 'dashboard-cctv2',
            'config': dashboard_config
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        print(f"Save result: {result}")
        
        if result.get('success'):
            print("\n✅ CCTV2 dashboard updated with WebRTC cards!")
            print("\n🔄 Please refresh your browser to load the WebRTC card")
            print("📺 Navigate to: http://192.168.0.111:8123/dashboard-cctv2")
        else:
            print(f"\n❌ Failed: {result.get('error')}")

if __name__ == '__main__':
    asyncio.run(update_cctv2_webrtc())
