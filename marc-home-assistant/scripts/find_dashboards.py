"""Try different WebSocket commands to find dashboards."""
import asyncio
import json
import websockets

async def try_commands():
    url = 'ws://192.168.0.111:8123/api/websocket'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmMzE4NmJjNDU4Yzk0YThkOTljNjJjZjNjYTI3MGYxZiIsImlhdCI6MTc3MDAyOTc0NCwiZXhwIjoyMDg1Mzg5NzQ0fQ.27vsNq4Q6tDQRsbofnTDCrrkJQPTw8V4IoEQc7Jmp04'
    
    async with websockets.connect(url) as ws:
        await ws.recv()
        await ws.send(json.dumps({'type': 'auth', 'access_token': token}))
        await ws.recv()
        
        # Get panels - this shows sidebar items including custom dashboards
        commands = [
            {'id': 1, 'type': 'get_panels'},
            {'id': 2, 'type': 'get_config'},
            {'id': 3, 'type': 'lovelace/config'},
            {'id': 4, 'type': 'supported_features'},
        ]
        
        for cmd in commands:
            cmd_type = cmd['type']
            print(f'\n=== Trying: {cmd_type} ===')
            await ws.send(json.dumps(cmd))
            resp = await ws.recv()
            result = json.loads(resp)
            if result.get('success'):
                print(json.dumps(result.get('result'), indent=2)[:3000])
            else:
                err = result.get('error', {}).get('message', 'unknown')
                print(f'FAILED: {err}')

if __name__ == '__main__':
    asyncio.run(try_commands())
