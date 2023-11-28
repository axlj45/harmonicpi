from azure.storage.blob import BlobServiceClient
from config import get_config
import os


cfg = get_config()
blob_service_client = BlobServiceClient(account_url=cfg["az_blob_sas_url"])


def upload_file_to_blob(container_name, file_path, blob_name):
    """
    Uploads a file to Azure Blob Storage
    :param container_name: Name of the Azure Blob Storage container
    :param file_path: Local path to the file
    :param blob_name: Name of the blob (file name in storage)
    """
    try:
        # Create a blob client using the local file name as the name for the blob
        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=blob_name
        )

        # Upload the file
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        chart_url = blob_client.url.split("?")[0]
        # print(f"File {file_path} uploaded to {chart_url}")

        return chart_url

    except Exception as e:
        print(e)


def upload_chart(chart_path):
    blob_name = os.path.basename(chart_path).split("/")[-1]
    chart_url = upload_file_to_blob(cfg["az_blob_container"], chart_path, blob_name)
    return chart_url
