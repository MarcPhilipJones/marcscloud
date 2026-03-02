"""Find and install WebRTC from HACS using proper API."""
import asyncio
import json
import websockets

async def find_and_install_webrtc():
    url = 'ws://192.168.0.111:8123/api/websocket'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmMzE4NmJjNDU4Yzk0YThkOTljNjJjZjNjYTI3MGYxZiIsImlhdCI6MTc3MDAyOTc0NCwiZXhwIjoyMDg1Mzg5NzQ0fQ.27vsNq4Q6tDQRsbofnTDCrrkJQPTw8V4IoEQc7Jmp04'
    
    async with websockets.connect(url, max_size=10*1024*1024) as ws:
        await ws.recv()
        await ws.send(json.dumps({'type': 'auth', 'access_token': token}))
        await ws.recv()
        
        # List only plugin repos
        print("Listing plugin repositories...")
        await ws.send(json.dumps({
            'id': 1,
            'type': 'hacs/repositories/list',
            'categories': ['plugin']
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        repos = result.get('result', [])
        print(f"Total plugin repos: {len(repos)}")
        
        # Search for anything with webrtc, camera, or stream
        webrtc_repos = []
        for repo in repos:
            full_name = (repo.get('full_name') or '').lower()
            name = (repo.get('name') or '').lower()
            if 'webrtc' in full_name or 'webrtc' in name:
                webrtc_repos.append(repo)
            elif 'alexx' in full_name:
                webrtc_repos.append(repo)
        
        if webrtc_repos:
            print(f"\nFound {len(webrtc_repos)} WebRTC-related repos:")
            for repo in webrtc_repos:
                print(f"  - {repo.get('full_name')} (ID: {repo.get('id')}, installed: {repo.get('installed')})")
        else:
            print("\nNo WebRTC found yet. Let me add it...")
            
            # Add the repo
            await ws.send(json.dumps({
                'id': 2,
                'type': 'hacs/repositories/add',
                'repository': 'AlexxIT/WebRTC',
                'category': 'plugin'
            }))
            resp = await ws.recv()
            add_result = json.loads(resp)
            print(f"Add result: {add_result}")
            
            if add_result.get('success'):
                # The result should contain the repository data
                repo_data = add_result.get('result', {})
                if repo_data:
                    print(f"\nRepository added: {repo_data}")
                    repo_id = repo_data.get('id')
                    
                    if repo_id:
                        print(f"\nDownloading WebRTC (ID: {repo_id})...")
                        await ws.send(json.dumps({
                            'id': 3,
                            'type': 'hacs/repository/download',
                            'repository': repo_id
                        }))
                        resp = await ws.recv()
                        dl_result = json.loads(resp)
                        print(f"Download result: {dl_result}")
                else:
                    # Re-list to find it
                    print("\nRe-listing to find the new repo...")
                    await ws.send(json.dumps({
                        'id': 4,
                        'type': 'hacs/repositories/list',
                        'categories': ['plugin']
                    }))
                    resp = await ws.recv()
                    repos = json.loads(resp).get('result', [])
                    
                    for repo in repos:
                        full_name = (repo.get('full_name') or '').lower()
                        if 'alexx' in full_name and 'webrtc' in full_name:
                            print(f"\nFound: {repo}")
                            
                            # Download it
                            print(f"\nDownloading...")
                            await ws.send(json.dumps({
                                'id': 5,
                                'type': 'hacs/repository/download',
                                'repository': repo.get('id')
                            }))
                            resp = await ws.recv()
                            print(f"Download result: {json.loads(resp)}")
                            break

if __name__ == '__main__':
    asyncio.run(find_and_install_webrtc())
