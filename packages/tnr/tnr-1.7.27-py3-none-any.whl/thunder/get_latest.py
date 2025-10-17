import os
import requests
import urllib.request  # download into memory
import hashlib  # for hashing
import platform  # which OS

# Pulling latest binary from gcs
def get_latest(version: str, path: str) -> str:
    if version != "host" and version != "client":
        return None

    # Validate the platform we're trying to run on
    operating_system = platform.system().lower()
    if version == "client" and operating_system != "linux":
        print("Only Linux supported")
        exit(1)

    architecture = platform.machine().lower()

    metadata_url = f"https://storage.googleapis.com/storage/v1/b/client-binary/o/{version}_{operating_system}_{architecture}?alt=json"
    latest_metadata = requests.get(metadata_url).json().get("metadata")
    if latest_metadata == None:
        print(f"Cannot find latest binary for system {operating_system}/{architecture}")
        return None

    latest_hash = latest_metadata.get("hash")
    if latest_hash == None:
        print(f"Cannot find latest binary for system {operating_system}/{architecture}")
        return None

    # Check if we already have latest binary

    path = os.path.expanduser(path)

    if os.path.isfile(path):
        current_hash = hashlib.md5(open(path, "rb").read()).hexdigest()
        if current_hash == latest_hash:
            return str(path)


    download_url = f"https://storage.googleapis.com/client-binary/{version}_{operating_system}_{architecture}"
    data = urllib.request.urlopen(download_url).read()
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    
    with open(path, "wb") as f:
        f.write(data)

    return str(path)
