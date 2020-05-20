import time
import os
import requests
import asyncio
import boto3
from asyncrcon import AsyncRCON

client = boto3.client("ssm", region="ap-southeast-1")
MC_SERVER_NAME = os.environ.get("MC_SERVER_NAME")
PORT_NUMBER = client.get_parameter(Name=f"{MC_SERVER_NAME}.config.rcon.pot")["Parameter"]["Value"]
PASSWORD = client.get_parameter(Name=f"{MC_SERVER_NAME}.config.rcon.password", WithDecryption=True)["Parameter"]["Value"]

rcon = AsyncRCON(f"localhost:{PORT_NUMBER}", PASSWORD)


async def check():
    token = None
    time_since_last_check = 0
    while True:
        if time.time() - (21600 - 100) > time_since_last_check:
            # fetch new token
            r = requests.put("http://169.254.169.254/latest/api/token",
                             headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"})
            token = r.text
        r = requests.get("http://169.254.169.254/latest/meta-data/spot/instance-action",
                         headers={"X-aws-ec2-metadata-token": token}
                         )
        if r.status_code == 404:
            await asyncio.sleep(10)
            continue
        else:
            # panic
            await rcon.open_connection()
            await rcon.command("say AWS is killing this instance! Stopping in 10 seconds!!")
            await asyncio.sleep(10)
            await rcon.command("say Goodbye!")
            await asyncio.sleep(1)
            await rcon.command("wb fill pause")
            await rcon.command("stop")
            return


asyncio.run(check())
