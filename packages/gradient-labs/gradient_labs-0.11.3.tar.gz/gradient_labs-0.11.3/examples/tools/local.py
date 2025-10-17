import requests

rsp = requests.post(
    "https://1257-2a00-23c4-ca02-4601-4d6f-e46c-76bc-3167.ngrok-free.app/launch",
    json={"speed": "slow"},
)
print(rsp.json())
