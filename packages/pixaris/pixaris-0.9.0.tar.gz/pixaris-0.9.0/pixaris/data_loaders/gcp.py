import os
from pathlib import Path
import shutil
from google.cloud import storage
from google.cloud.storage import transfer_manager
from pixaris.data_loaders.base import DatasetLoader
from typing import List
from PIL import Image


class GCPDatasetLoader(DatasetLoader):
    """
    GCPDatasetLoader is a class for loading datasets from a Google Cloud Storage bucket. Upon initialisation, the dataset is downloaded to a local directory.

    :param gcp_project_id: The Google Cloud Platform project ID.
    :type gcp_project_id: str
    :param gcp_pixaris_bucket_name: The name of the Google Cloud Storage bucket.
    :type gcp_pixaris_bucket_name: str
    :param project: The name of the project containing the evaluation set.
    :type project: str
    :param dataset: The name of the evaluation set to download images for.
    :type dataset: str
    :param eval_dir_local: The local directory where evaluation images will be saved. Defaults to "local_experiment_inputs".
    :type eval_dir_local: str
    :param force_download: Whether to force download the images even if they already exist locally. Defaults to True.
    :type force_download: bool
    """

    def __init__(
        self,
        gcp_project_id: str,
        gcp_pixaris_bucket_name: str,
        project: str,
        dataset: str,
        eval_dir_local: str = "local_experiment_inputs",
        force_download: bool = True,
    ):
        self.gcp_project_id = gcp_project_id
        self.bucket_name = gcp_pixaris_bucket_name
        self.project = project
        self.dataset = dataset
        self.eval_dir_local = eval_dir_local
        os.makedirs(self.eval_dir_local, exist_ok=True)
        self.force_download = force_download
        self.bucket = None
        self.image_dirs = None

    def _download_dataset(self):
        """
        Downloads evaluation images for a given evaluation set.
        """
        storage_client = storage.Client(project=self.gcp_project_id)
        self.bucket = storage_client.get_bucket(self.bucket_name)
        if self.force_download:
            self._verify_bucket_folder_exists()

        # only download if the local directory does not exist or is empty
        if self._decide_if_download_needed():
            self._download_bucket_dir()

        self.image_dirs = [
            name
            for name in os.listdir(
                os.path.join(self.eval_dir_local, self.project, self.dataset)
            )
            if os.path.isdir(
                os.path.join(self.eval_dir_local, self.project, self.dataset, name)
            )
        ]

    def _verify_bucket_folder_exists(self):
        """
        Verifies that the bucket exists and is not empty.

        :raises: ValueError: If no files are found in the specified directory in the bucket.
        """
        # List the blobs in the bucket. If no blobs are found, raise an error.
        blobs = list(
            self.bucket.list_blobs(
                prefix=f"experiment_inputs/{self.project}/{self.dataset}/"
            )
        )
        if not blobs:
            raise ValueError(
                f"No images found in bucket or bucket does not exist. Please double-check gs://{self.bucket_name}/experiment_inputs/{self.project}/{self.dataset}/."
            )

    def _decide_if_download_needed(self):
        """
        Decides if the download is necessary based on the force_download attribute and existence of the local directory.
        """
        # delete the local directory if force_download is True
        if self.force_download:
            if os.path.exists(
                os.path.join(self.eval_dir_local, self.project, self.dataset)
            ):
                shutil.rmtree(
                    os.path.join(self.eval_dir_local, self.project, self.dataset)
                )

        # Create the local directory if it does not exist
        local_dir = os.path.join(self.eval_dir_local, self.project, self.dataset)
        if os.path.exists(local_dir) and len(os.listdir(local_dir)) > 0:
            return False
        else:
            os.makedirs(local_dir, exist_ok=True)
            return True

    def _download_bucket_dir(self):
        """
        Downloads all files from a specified directory in a Google Cloud Storage bucket to a local directory.
        """
        # Download the blobs to the local directory
        blobs = self.bucket.list_blobs(
            prefix=f"experiment_inputs/{self.project}/{self.dataset}/"
        )
        blob_names = [
            blob.name for blob in blobs if not blob.name.endswith("/")
        ]  # exclude directories

        # remove experiment_inputs/ from the blob names
        blob_names = [name.replace("experiment_inputs/", "") for name in blob_names]

        results = transfer_manager.download_many_to_path(
            self.bucket,
            blob_names,
            blob_name_prefix="experiment_inputs/",
            destination_directory=os.path.join(self.eval_dir_local),
            worker_type=transfer_manager.THREAD,
        )
        # The results list is either `None` or an exception for each blob.
        for name, result in zip(blob_names, results):
            if isinstance(result, Exception):
                print("Failed to download {} due to exception: {}".format(name, result))
            else:
                print(
                    "Downloaded {} to {}.".format(
                        name, os.path.join(self.eval_dir_local, *name.split("/"))
                    )
                )

    def _retrieve_and_check_dataset_image_names(self):
        """
        Retrieves the names of the images in the evaluation set and checks if they are the same in each image directory.

        :return: The names of the images in the evaluation set.
        :rtype: List[str]
        :raises: ValueError: If the names of the images in each image directory are not the same.
        """
        self.image_dirs = [
            file
            for file in os.listdir(
                os.path.join(self.eval_dir_local, self.project, self.dataset)
            )
            if file != ".DS_Store"
        ]
        basis_names = os.listdir(
            os.path.join(
                self.eval_dir_local, self.project, self.dataset, self.image_dirs[0]
            )
        )
        basis_names = [name for name in basis_names if name != ".DS_Store"]
        for image_dir in self.image_dirs:
            image_names = os.listdir(
                os.path.join(self.eval_dir_local, self.project, self.dataset, image_dir)
            )
            image_names = [name for name in image_names if name != ".DS_Store"]

            if basis_names != image_names:
                raise ValueError(
                    "The names of the images in each image directory should be the same. {} does not match {}.".format(
                        self.image_dirs[0], image_dir
                    )
                )
        return basis_names

    def load_dataset(
        self,
    ) -> List[dict[str, List[dict[str, Image.Image]]]]:
        """
        Returns all images in the evaluation set as an iterator of dictionaries containing PIL Images.

        :return: list of dicts containing data loaded from the bucket.
            The key will always be "pillow_images".
            The value is a dict mapping node names to PIL Image objects.
            This dict has a key for each directory in the image_dirs list representing a Node Name.
        :rtype: List[dict[str, List[dict[str, Image.Image]]]]:
        """
        self._download_dataset()
        image_names = self._retrieve_and_check_dataset_image_names()

        dataset = []
        for image_name in image_names:
            pillow_images = []
            for image_dir in self.image_dirs:
                image_path = os.path.join(
                    self.eval_dir_local,
                    self.project,
                    self.dataset,
                    image_dir,
                    image_name,
                )
                # Load the image using PIL
                pillow_image = Image.open(image_path)
                pillow_images.append(
                    {
                        "node_name": f"Load {image_dir.capitalize()} Image",
                        "pillow_image": pillow_image,
                    }
                )
            dataset.append({"pillow_images": pillow_images})
        return dataset

    def _upload_dir_to_bucket(self, bucket_prefix: str, workers=8):
        """takes a project and uploads its contents to a GCP bucket.
        project and bucket are set in the constructor.

        :param bucket_prefix: The prefix under which the files will be uploaded in the bucket.
        :type bucket_prefix: str
        :param workers: The number of worker threads to use for the upload. Defaults to 8.
        :type workers: int, optional
        """
        storage_client = storage.Client(project=self.gcp_project_id)
        bucket = storage_client.get_bucket(self.bucket_name)

        # this follows https://cloud.google.com/storage/docs/uploading-objects?hl=de
        # First, recursively get all files in `directory` as Path objects.
        source_dir = os.path.join(self.eval_dir_local, self.project, self.dataset)
        directory_as_path_obj = Path(source_dir)
        paths = directory_as_path_obj.rglob("*")

        # Filter so the list only includes files, not directories themselves.
        file_paths = [path for path in paths if path.is_file()]

        # only upload if a path does not end with .DS_Store
        file_paths = [
            path for path in file_paths if not str(path).endswith(".DS_Store")
        ]

        # These paths are relative to the current working directory. Next, make them
        # relative to `directory`
        relative_paths = [path.relative_to(source_dir) for path in file_paths]

        # Finally, convert them all to strings.
        string_paths = [str(path) for path in relative_paths]

        # Start the upload.
        results = transfer_manager.upload_many_from_filenames(
            bucket,
            string_paths,
            source_directory=source_dir,
            blob_name_prefix=bucket_prefix,
            max_workers=workers,
        )

        for name, result in zip(string_paths, results):
            # The results list is either `None` or an exception for each filename in
            # the input list, in order.

            if isinstance(result, Exception):
                print("Failed to upload {} due to exception: {}".format(name, result))
            else:
                print("Uploaded {} to {}.".format(name, bucket.name))

    def create_dataset(
        self,
        project: str,
        dataset: str,
    ):
        """
        Creates a gcp dataset based on an existing local directory structure and uploads it to gcp.

        :param project: The name of the project containing the dataset.
        :type project: str
        :param dataset: The name of the dataset to upload.
        :type dataset: str
        """
        self.project = project
        self.dataset = dataset

        self._retrieve_and_check_dataset_image_names()

        self._upload_dir_to_bucket(
            bucket_prefix=f"experiment_inputs/{self.project}/{self.dataset}/",
        )
