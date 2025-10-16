import requests
from requests.auth import HTTPBasicAuth
import json

from ocpy.api.api_client import OpenCastBaseApiClient
import os


class User:
    def __init__(self, user, password, url, data):
        self.base_url = url
        self.user = user
        self.password = password
        self.data = data

    def __str__(self):
        return json.dumps(self.data, sort_keys=True, indent=4, separators=(",", ": "))

    def __repr__(self):
        return self.__str__()

    def get_email(self) -> str:
        return self.data["email"]

    def get_name(self) -> str:
        return self.data["name"]

    def get_provider(self) -> str:
        return self.data["provider"]

    def get_username(self) -> str:
        return self.data["username"]

    def get_user_role(self) -> str:
        return self.data["userRole"]


class UploadApi(OpenCastBaseApiClient):
    def __init__(self, user=None, password=None, server_url=None, **kwargs):
        super().__init__(user, password, server_url)
        self.base_url = self.server_url + "/upload"

    def get_job(self, job_id, **kwargs) -> dict:
        res = requests.get(
            self.base_url + "/" + job_id + ".json",
            auth=HTTPBasicAuth(self.user, self.password),
            **kwargs
        )
        if res.ok:
            return res.json()
        raise Exception("Could not get job info!")

    def create_new_job(
        self,
        file_name=None,
        file_size=None,
        chunk_size=None,
        flavor=None,
        mediapackage=None,
        **kwargs
    ):

        data = {
            "filename": file_name,
            "filesize": file_size,
            "chunksize": chunk_size,
            "flavor": flavor,
            "mediapackage": mediapackage,
        }

        res = requests.post(
            self.base_url + "/newjob",
            auth=HTTPBasicAuth(self.user, self.password),
            files=data,
            **kwargs
        )
        if res.ok:
            return res.text
        print(res.content)
        raise Exception("Could not create new upload!")

    def append_chunk_to_job(self, job_id, file_data, chunk_number=None, **kwargs):
        data = {"chunknumber": chunk_number, "filedata": file_data}

        res = requests.post(
            self.base_url + "/job/" + job_id,
            auth=HTTPBasicAuth(self.user, self.password),
            files=data,
            **kwargs
        )

        if res.ok:
            return res.text
        print(res.content)
        raise Exception("Could not append chunk to job!")


def read_in_chunks(file_object, chunk_size=1024):
    """Lazy function (generator) to read a file piece by piece.
    Default chunk size: 1k."""
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


def test_file_upload():
    api = UploadApi()
    file = "/home/tobias/Downloads/lot_small_files.zip"
    print(os.path.getsize(file))
    job_id = api.create_new_job(
        file_name=os.path.basename(file), file_size=os.path.getsize(file)
    )
    f = open(file, "rb")
    count = 0
    for piece in read_in_chunks(f):
        print(count)
        api.append_chunk_to_job(job_id, piece)
        count += 1


def main():
    test_file_upload()
    return
    api = UploadApi()
    job_id = api.create_new_job()
    print(api.append_chunk_to_job(job_id, "file_data"))


if __name__ == "__main__":
    main()
