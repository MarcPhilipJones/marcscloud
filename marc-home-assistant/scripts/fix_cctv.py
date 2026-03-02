"""Fix CCTV dashboard to display 16:9 properly."""
import asyncio
import json
import websockets

async def fix_cctv():
    url = 'ws://192.168.0.111:8123/api/websocket'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmMzE4NmJjNDU4Yzk0YThkOTljNjJjZjNjYTI3MGYxZiIsImlhdCI6MTc3MDAyOTc0NCwiZXhwIjoyMDg1Mzg5NzQ0fQ.27vsNq4Q6tDQRsbofnTDCrrkJQPTw8V4IoEQc7Jmp04'
    
    async with websockets.connect(url) as ws:
        await ws.recv()
        await ws.send(json.dumps({'type': 'auth', 'access_token': token}))
        await ws.recv()
        
        # Fix: Use iframe cards pointing to camera streams with proper sizing
        # Or use picture-entity without forced aspect ratio
        cctv_config = {
            'views': [{
                'title': 'CCTV',
                'path': 'cctv',
                'panel': True,
                'cards': [{
                    'type': 'vertical-stack',
                    'cards': [
                        {
                            'type': 'horizontal-stack',
                            'cards': [
                                {
                                    'type': 'picture-entity',
                                    'entity': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_101',
                                    'name': 'Front Garden',
                                    'camera_view': 'live',
                                    'show_state': False,
                                    'show_name': True,
                                    'image': '/api/camera_proxy_stream/camera.dvr_204q_m10420250308ccwrfx3431707wcvu_101'
                                },
                                {
                                    'type': 'picture-entity',
                                    'entity': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_201',
                                    'name': 'Driveway',
                                    'camera_view': 'live',
                                    'show_state': False,
                                    'show_name': True,
                                    'image': '/api/camera_proxy_stream/camera.dvr_204q_m10420250308ccwrfx3431707wcvu_201'
                                }
                            ]
                        },
                        {
                            'type': 'horizontal-stack',
                            'cards': [
                                {
                                    'type': 'picture-entity',
                                    'entity': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_301',
                                    'name': 'Extension Roof',
                                    'camera_view': 'live',
                                    'show_state': False,
                                    'show_name': True,
                                    'image': '/api/camera_proxy_stream/camera.dvr_204q_m10420250308ccwrfx3431707wcvu_301'
                                },
                                {
                                    'type': 'picture-entity',
                                    'entity': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_401',
                                    'name': 'Back Garden',
                                    'camera_view': 'live',
                                    'show_state': False,
                                    'show_name': True,
                                    'image': '/api/camera_proxy_stream/camera.dvr_204q_m10420250308ccwrfx3431707wcvu_401'
                                }
                            ]
                        }
                    ]
                }]
            }]
        }
        
        print("Updating CCTV dashboard...")
        await ws.send(json.dumps({
            'id': 1,
            'type': 'lovelace/config/save',
            'url_path': 'dashboard-cctv',
            'config': cctv_config
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        print(f"CCTV update result: {result}")
        
        # Also update CCTV2 with same fix
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
                                    'type': 'picture-entity',
                                    'entity': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_101',
                                    'name': 'Front Garden',
                                    'camera_view': 'live',
                                    'show_state': False,
                                    'show_name': True
                                },
                                {
                                    'type': 'picture-entity',
                                    'entity': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_201',
                                    'name': 'Driveway',
                                    'camera_view': 'live',
                                    'show_state': False,
                                    'show_name': True
                                }
                            ]
                        },
                        {
                            'type': 'horizontal-stack',
                            'cards': [
                                {
                                    'type': 'picture-entity',
                                    'entity': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_301',
                                    'name': 'Extension Roof',
                                    'camera_view': 'live',
                                    'show_state': False,
                                    'show_name': True
                                },
                                {
                                    'type': 'picture-entity',
                                    'entity': 'camera.dvr_204q_m10420250308ccwrfx3431707wcvu_401',
                                    'name': 'Back Garden',
                                    'camera_view': 'live',
                                    'show_state': False,
                                    'show_name': True
                                }
                            ]
                        }
                    ]
                }]
            }]
        }
        
        print("Updating CCTV2 dashboard...")
        await ws.send(json.dumps({
            'id': 2,
            'type': 'lovelace/config/save',
            'url_path': 'dashboard-cctv2',
            'config': cctv2_config
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        print(f"CCTV2 update result: {result}")

if __name__ == '__main__':
    asyncio.run(fix_cctv())
