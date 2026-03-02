"""Get Home Assistant dashboards via WebSocket."""
import asyncio
import json
import websockets

async def get_dashboards():
    url = 'ws://192.168.0.111:8123/api/websocket'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmMzE4NmJjNDU4Yzk0YThkOTljNjJjZjNjYTI3MGYxZiIsImlhdCI6MTc3MDAyOTc0NCwiZXhwIjoyMDg1Mzg5NzQ0fQ.27vsNq4Q6tDQRsbofnTDCrrkJQPTw8V4IoEQc7Jmp04'
    
    async with websockets.connect(url) as ws:
        # Auth required
        await ws.recv()
        # Send auth
        await ws.send(json.dumps({'type': 'auth', 'access_token': token}))
        auth_resp = await ws.recv()
        print('Auth:', json.loads(auth_resp).get('type'))
        
        # Get dashboards list
        await ws.send(json.dumps({'id': 1, 'type': 'lovelace/dashboards'}))
        resp = await ws.recv()
        dashboards = json.loads(resp)
        print('\nDashboards:')
        for d in dashboards.get('result', []):
            title = d.get('title') or d.get('url_path') or 'unnamed'
            url_path = d.get('url_path')
            print(f"  - {title} (url: {url_path})")
        
        # Find CCTV dashboard
        cctv_dashboard = None
        for d in dashboards.get('result', []):
            if 'cctv' in (d.get('title') or '').lower() or 'cctv' in (d.get('url_path') or '').lower():
                cctv_dashboard = d.get('url_path')
                break
        
        # Get default lovelace config
        print("\nGetting default lovelace config...")
        await ws.send(json.dumps({'id': 2, 'type': 'lovelace/config'}))
        resp = await ws.recv()
        config = json.loads(resp)
        print(f"Default config result: {config}")
        
        # Try lovelace/resources
        print("\nGetting lovelace resources...")
        await ws.send(json.dumps({'id': 3, 'type': 'lovelace/resources'}))
        resp = await ws.recv()
        resources = json.loads(resp)
        print(f"Resources: {resources}")
        
        # Try different dashboard URL paths with incrementing IDs
        msg_id = 10
        for dash_name in ['lovelace-cctv', 'cctv', 'lovelace_cctv', 'cameras', 'security', 'lovelace-cameras']:
            print(f"\nTrying dashboard: {dash_name}")
            msg_id += 1
            await ws.send(json.dumps({'id': msg_id, 'type': 'lovelace/config', 'url_path': dash_name}))
            resp = await ws.recv()
            dash_config = json.loads(resp)
            if dash_config.get('success'):
                print(f"  FOUND: {dash_name}")
                views = dash_config.get('result', {}).get('views', [])
                print(f"  Views: {len(views)}")
                for v in views:
                    print(f"    - {v.get('title', 'untitled')}")
            else:
                print(f"  Not found: {dash_config.get('error', {}).get('message', 'unknown')}")

if __name__ == '__main__':
    asyncio.run(get_dashboards())
