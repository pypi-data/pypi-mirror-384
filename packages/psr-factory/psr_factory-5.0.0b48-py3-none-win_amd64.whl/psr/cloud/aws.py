import os
import tempfile
import zipfile
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from tqdm import tqdm


class AWS:
    def __init__(
        self,
        access: str,
        secret: str,
        session_token: str,
        url: str,
        Logger=None,
    ):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=access,
            aws_secret_access_key=secret,
            aws_session_token=session_token,
            region_name=AWS.get_region(url),
        )
        self.logger = Logger

    @staticmethod
    def get_region(url: Optional[str]) -> Optional[str]:
        """Extract the region from the S3 URL."""
        if url:
            parts = url.split(".")
            return parts[0]
        return None

    def upload_file(
        self,
        file_path: str,
        bucket_name: str,
        object_name: Optional[str] = None,
        extra_args: Optional[dict] = None,
        Callback=None,
    ) -> bool:
        """Upload a file to an S3 bucket using the AWS instance's S3 client."""
        if object_name is None:
            object_name = os.path.basename(file_path)
        try:
            self.s3_client.upload_file(
                file_path,
                bucket_name,
                object_name,
                ExtraArgs=extra_args,
                Callback=Callback,
            )
            return True
        except ClientError as e:
            self.logger.error(f"Error uploading file: {e}")
            return False

    def upload_case(
        self,
        files: List[str],
        repository_id: str,
        bucket_name: str,
        checksums: Optional[Dict[str, str]] = None,
        zip_compress: bool = False,
        compress_zip_name: str = None,
    ):
        """Upload files to an S3 bucket."""
        base_metadata: Dict[str, str] = {
            "upload": str(True).lower(),
            "user-agent": "aws-fsx-lustre",
            "file-owner": "537",
            "file-group": "500",
            "file-permissions": "100777",
        }

        if zip_compress and not compress_zip_name:
            compress_zip_name = str(repository_id)

        if zip_compress:
            # Create a temporary zip file
            with tempfile.NamedTemporaryFile(
                suffix=".zip", delete=False
            ) as tmp_zip_file:
                zip_path = tmp_zip_file.name
                tmp_zip_file.close()

            try:
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in files:
                        zipf.write(file_path, arcname=os.path.basename(file_path))

                object_name = f"{repository_id}/uploaded/{compress_zip_name}.zip"
                extra_args = {"Metadata": base_metadata.copy()}

                if not self.upload_file(
                    zip_path, bucket_name, object_name, extra_args=extra_args
                ):
                    raise ValueError(
                        f"Failed to upload zip file {zip_path} to S3 bucket {bucket_name}."
                    )
            finally:
                if os.path.exists(zip_path):
                    os.unlink(zip_path)
        else:
            for file_path in files:
                file_basename = os.path.basename(file_path)
                object_name = f"{repository_id}/uploaded/{file_basename}"

                current_file_metadata = base_metadata.copy()
                if checksums:
                    current_file_metadata["checksum"] = checksums.get(file_basename, "")

                extra_args = {"Metadata": current_file_metadata}

                if not self.upload_file(file_path, object_name, extra_args=extra_args):
                    raise ValueError(
                        f"Failed to upload file {file_path} to S3 bucket {bucket_name}."
                    )

        # Always upload .metadata files if the source 'files' list is provided
        if files:
            data_directory = os.path.dirname(files[0])
            metadata_dir_local_path = os.path.join(data_directory, ".metadata")

            if os.path.isdir(metadata_dir_local_path):
                for original_file_path in files:
                    original_file_basename = os.path.basename(original_file_path)
                    local_metadata_file_path = os.path.join(
                        metadata_dir_local_path, original_file_basename
                    )

                    if os.path.isfile(local_metadata_file_path):
                        s3_metadata_object_name = (
                            f"{repository_id}/.metadata/{original_file_basename}"
                        )
                        extra_args = {"Metadata": base_metadata.copy()}
                        if not self.upload_file(
                            local_metadata_file_path,
                            s3_metadata_object_name,
                            extra_args=extra_args,
                        ):
                            raise ValueError(
                                f"Failed to upload metadata file {local_metadata_file_path} to S3 bucket {bucket_name}."
                            )

    def upload_version(
        self,
        model_name: str,
        version_name: str,
        bucket_name: str,
        file_path: str,
    ):
        """
        Uploads a new version of the model to S3.
        """
        build = os.path.basename(file_path)
        object_name = f"{model_name}/{version_name}/linux/{build}"
        file_size = os.path.getsize(file_path)
        custom_format = (
            "{desc} [{percentage:3.0f}%] |{bar}| {n_fmt}/{total_fmt} @ {rate_fmt}"
        )
        with tqdm(
            bar_format=custom_format,
            total=file_size,
            unit="B",
            unit_scale=True,
            desc=f"Uploading {build}...",
        ) as pbar:
            if not self.upload_file(
                file_path,
                bucket_name,
                object_name,
                Callback=lambda bytes_transferred: pbar.update(bytes_transferred),
            ):
                raise ValueError(
                    f"Failed to upload file {file_path} to S3 bucket {bucket_name}."
                )

        # Delete all objects in the "latest" folder
        latest_prefix = f"{model_name}/{version_name}/linux/latest/"
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name, Prefix=latest_prefix
            )
            if "Contents" in response:
                for obj in response["Contents"]:
                    self.s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])
        except ClientError as e:
            self.logger.error(f"Error deleting objects in 'latest' folder: {e}")
            raise RuntimeError(f"Failed to clean 'latest' folder in S3: {e}")

        # Copy the uploaded version file to the "latest" folder
        latest_object_name = f"{model_name}/{version_name}/linux/latest/{build}"
        copy_source = {"Bucket": bucket_name, "Key": object_name}
        try:
            self.s3_client.copy_object(
                Bucket=bucket_name, CopySource=copy_source, Key=latest_object_name
            )
        except ClientError as e:
            self.logger.error(f"Error copying version file to 'latest' folder: {e}")
            raise RuntimeError(
                f"Failed to copy version file to 'latest' folder in S3: {e}"
            )

    def download_file(
        self, bucket_name: str, s3_object_key: str, local_file_path: str
    ) -> bool:
        """Downloads a single object from S3 to a local file path."""
        try:
            self.s3_client.download_file(bucket_name, s3_object_key, local_file_path)
            return True
        except ClientError as e:
            self.logger.error(f"ERROR: Failed to download {s3_object_key} from S3: {e}")
            return False

    def download_case(
        self,
        repository_id: str,
        cluster_name: str,
        bucket_name: str,
        output_path: str,
        file_list: List[str],
    ) -> List[str]:
        """
        Downloads files from an S3 bucket for a given case repository.
        """
        downloaded_files: List[str] = []

        try:
            for file_name in file_list:
                s3_object_key = f"{repository_id}/{file_name}"
                local_file_path = os.path.join(output_path, file_name)
                if self.logger:
                    self.logger.info(
                        f"Downloading {s3_object_key} to {local_file_path}"
                    )
                if self.download_file(bucket_name, s3_object_key, local_file_path):
                    downloaded_files.append(os.path.basename(local_file_path))
        except ClientError as e:
            self.logger.error(f"ERROR: S3 ClientError during download: {e}")
            raise RuntimeError(f"Failed to download files from S3: {e}")
        except Exception as e:
            self.logger.error(
                f"ERROR: An unexpected error occurred during download: {e}"
            )
            raise RuntimeError(f"An unexpected error occurred during S3 download: {e}")

        return downloaded_files

    def check_version_build_exists(
        self,
        bucket_name: str,
        model_name: str,
        version_name: str,
        build_id: str,
    ) -> bool:
        """
        Checks if a specific version build exists in the S3 bucket.
        """
        object_key = f"{model_name}/{version_name}/linux/{build_id}.zip"
        try:
            self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            self.logger.error(f"Error checking version build existence: {e}")
            raise RuntimeError(f"Failed to check version build existence in S3: {e}")
