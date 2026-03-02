"""Setup CCTV2 dashboard with WebRTC."""
import asyncio
import json
import websockets

async def setup_cctv2():
    url = 'ws://192.168.0.111:8123/api/websocket'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmMzE4NmJjNDU4Yzk0YThkOTljNjJjZjNjYTI3MGYxZiIsImlhdCI6MTc3MDAyOTc0NCwiZXhwIjoyMDg1Mzg5NzQ0fQ.27vsNq4Q6tDQRsbofnTDCrrkJQPTw8V4IoEQc7Jmp04'
    
    async with websockets.connect(url) as ws:
        await ws.recv()
        await ws.send(json.dumps({'type': 'auth', 'access_token': token}))
        await ws.recv()
        
        # Step 1: Create the new dashboard
        print("Creating CCTV2 dashboard...")
        await ws.send(json.dumps({
            'id': 1,
            'type': 'lovelace/dashboards/create',
            'url_path': 'dashboard-cctv2',
            'title': 'CCTV2',
            'icon': 'mdi:cctv',
            'require_admin': False,
            'show_in_sidebar': True
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        print(f"Dashboard create result: {result}")
        
        # Step 2: Configure the dashboard with picture-glance cards (better for cameras)
        # These will use go2rtc streaming when clicked
        cctv2_config = {
            'views': [{
                'title': 'CCTV2',
                'path': 'cctv2',
                'panel': True,
                'cards': [{
                    'type': 'vertical-stack',
                    'cards': [
                        {
                            'type': 'horizontal-stack',
                            'cards': [
                                {
                                    'type': 'picture-glance',
                                    'title': 'Front Garden',
                                    'camera_image': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_101',
                                    'camera_view': 'live',
                                    'entities': []
                                },
                                {
                                    'type': 'picture-glance',
                                    'title': 'Driveway',
                                    'camera_image': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_201',
                                    'camera_view': 'live',
                                    'entities': []
                                }
                            ]
                        },
                        {
                            'type': 'horizontal-stack',
                            'cards': [
                                {
                                    'type': 'picture-glance',
                                    'title': 'Extension Roof',
                                    'camera_image': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_301',
                                    'camera_view': 'live',
                                    'entities': []
                                },
                                {
                                    'type': 'picture-glance',
                                    'title': 'Back Garden',
                                    'camera_image': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_401',
                                    'camera_view': 'live',
                                    'entities': []
                                }
                            ]
                        }
                    ]
                }]
            }]
        }
        
        print("Configuring CCTV2 dashboard...")
        await ws.send(json.dumps({
            'id': 2,
            'type': 'lovelace/config/save',
            'url_path': 'dashboard-cctv2',
            'config': cctv2_config
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        print(f"Dashboard config result: {result}")
        
        print("\nCCTV2 dashboard created! Go to: http://192.168.0.111:8123/dashboard-cctv2")

if __name__ == '__main__':
    asyncio.run(setup_cctv2())
