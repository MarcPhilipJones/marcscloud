"""Fix CCTV2 dashboard - full width cameras with correct aspect ratio."""
import asyncio
import json
import websockets

async def fix_cctv2_layout():
    url = 'ws://192.168.0.111:8123/api/websocket'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmMzE4NmJjNDU4Yzk0YThkOTljNjJjZjNjYTI3MGYxZiIsImlhdCI6MTc3MDAyOTc0NCwiZXhwIjoyMDg1Mzg5NzQ0fQ.27vsNq4Q6tDQRsbofnTDCrrkJQPTw8V4IoEQc7Jmp04'
    
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
        
        # Use vertical-stack with horizontal-stack for 2x2 layout
        # Each camera uses picture-entity with proper sizing
        row1 = []
        row2 = []
        
        for i, cam in enumerate(cameras):
            card = {
                'type': 'picture-entity',
                'entity': cam['entity'],
                'camera_view': 'live',
                'show_state': False,
                'show_name': True,
                'aspect_ratio': '16:9'
            }
            if i < 2:
                row1.append(card)
            else:
                row2.append(card)
        
        dashboard_config = {
            'views': [{
                'title': 'CCTV2 WebRTC',
                'path': 'cctv2',
                'panel': True,  # Panel mode = full width
                'cards': [
                    {
                        'type': 'vertical-stack',
                        'cards': [
                            {
                                'type': 'horizontal-stack',
                                'cards': row1
                            },
                            {
                                'type': 'horizontal-stack',
                                'cards': row2
                            }
                        ]
                    }
                ]
            }]
        }
        
        print("Updating CCTV2 dashboard with full-width panel layout...")
        await ws.send(json.dumps({
            'id': 1,
            'type': 'lovelace/config/save',
            'url_path': 'dashboard-cctv2',
            'config': dashboard_config
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        print(f"Result: {result}")
        
        if result.get('success'):
            print("\n✅ Dashboard updated!")
            print("Panel mode enabled - cameras should now fill the screen")

if __name__ == '__main__':
    asyncio.run(fix_cctv2_layout())
