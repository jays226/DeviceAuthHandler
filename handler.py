import aiohttp
import json
import time
import asyncio
import webbrowser

switch_token = "NTIyOWRjZDNhYzM4NDUyMDhiNDk2NjQ5MDkyZjI1MWI6ZTNiZDJkM2UtYmY4Yy00ODU3LTllN2QtZjNkOTQ3ZDIyMGM3"
dauntless_token = "YjA3MGYyMDcyOWY4NDY5M2I1ZDYyMWM5MDRmYzViYzI6SEdAWEUmVEdDeEVKc2dUIyZfcDJdPWFSbyN+Pj0+K2M2UGhSKXpYUA=="

class Handler:
    
    def __init__(self) -> None:
        self.device_auths = {}
        self.session = None

    async def get_access_token(self):
        headers = {
            'content-type': "application/x-www-form-urlencoded",
            'authorization': f"basic {dauntless_token}",
        }
        async with await self.session.request("POST","https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token", data="grant_type=client_credentials", headers=headers) as r:
            response = await r.json()
        access_token = response['access_token']
        await self.session.close()
        return access_token

    async def get_url(self) -> None:
        access_token = await self.get_access_token()
        
        url = "https://account-public-service-prod03.ol.epicgames.com/account/api/oauth/deviceAuthorization"

        querystring = {"prompt":"login"}

        payload = "prompt=promptType"
        headers = {
            'content-type': "application/x-www-form-urlencoded",
            'authorization': f"bearer {access_token}",
            }

        async with aiohttp.request("POST", url, data=payload, headers=headers, params=querystring) as r:
            response = await r.json()

        verification_uri = response['verification_uri_complete']
        device_code = response['device_code']

        return [verification_uri,device_code]
    
    async def generate_device_auths(self, data) -> None:
        try:
            deviceCode = data
            
            url = "https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token"
            payload = f"grant_type=device_code&device_code={deviceCode}"
            headers = {
                'content-type': "application/x-www-form-urlencoded",
                'authorization': f"basic {switch_token}",
                }
            status = 0
            time_start = time.time()
            while(status != 200):
                async with aiohttp.request("POST", url, data=payload, headers=headers) as r:
                    data = await r.json()
                    status = r.status
                time_now = time.time()
                if(time_now-time_start >= 600):
                    return {}
                await asyncio.sleep(1)
            
            self.device_auths['display_name'] = data['displayName']

            account_id = data['account_id']
            access_token = data['access_token']

            url = f"https://account-public-service-prod.ol.epicgames.com/account/api/public/account/{account_id}/deviceAuth"
            headers = {
                'content-type': "application/json",
                'authorization': f"bearer {access_token}",
                }
            async with aiohttp.request("POST", url, data=payload, headers=headers) as r:
                device_details = await r.json()

            self.device_auths['device_id'] = device_details['deviceId']
            self.device_auths['account_id'] = device_details['accountId']
            self.device_auths['secret'] = device_details['secret']
            self.device_auths['refresh_token'] = data['refresh_token']
            self.device_auths['refresh_expire'] = data['refresh_expires_at']
            self.device_auths['created_at'] = device_details['created']['dateTime']

            return self.device_auths
        except:
            return {}
    
    async def run(self):
        self.session = aiohttp.ClientSession()
        print("Device Auth Handler by AtomicXYZ")
        data = await self.get_url()
        url = data[0]
        print("Login Url: " + url)
        print("The url will open in a new window." + "\n")
        await asyncio.sleep(2)
        webbrowser.open(url, new=2)
        await asyncio.sleep(1)
        auths = await self.generate_device_auths(data[1])
        print("Generating Device Auths..." + "\n")
        device_auths = json.dumps(auths, indent=4)
        with open("device_auths.json", 'w') as fp:
            json.dump(auths, fp)
        print('Generated Device Auths:')
        print(device_auths)
        print("\nDevice Auths stored in device_auths.json")

    
    def loop(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.run())
        loop.run_forever()

handler = Handler()
handler.loop()
