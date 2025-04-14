
import requests

def upload_to_ipfs(file_path):
    with open(file_path, "rb") as f:
        response = requests.post("https://ipfs.io/api/v0/add", files={"file": f})
        if response.status_code == 200:
            ipfs_hash = response.json()["Hash"]
            return f"https://ipfs.io/ipfs/{ipfs_hash}"
        else:
            raise Exception("IPFS upload failed")
