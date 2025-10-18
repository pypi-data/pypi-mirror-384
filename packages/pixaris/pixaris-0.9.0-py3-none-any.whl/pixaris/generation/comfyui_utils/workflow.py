from PIL import Image
import json
import io
import urllib.request
import urllib.parse
import requests
import time
from pixaris.utils.retry import retry


class ComfyWorkflow:
    """
    ComfyWorkflow is a class that handles the execution of a workflow in ComfyUI.
    It provides methods to manipulate the workflow, set parameters, upload images, and execute the workflow.
    It also provides methods to check the status of the workflow and download images.
    It is designed to work with the ComfyUI API and requires the API host and workflow in JSON format.
    """

    api_host = ""
    workflow_apiformat_json = {}
    last_history = {}

    def __init__(self, api_host: str, workflow_apiformat_json: dict):
        self.api_host = api_host
        cleaned_workflow_apiformat_json = self._remove_preview_images(
            workflow_apiformat_json
        )
        self.workflow_apiformat_json = cleaned_workflow_apiformat_json

    def _remove_preview_images(self, workflow_apiformat_json: dict) -> dict:
        """
        Remove all nodes of class type "PreviewImage" from the workflow.

        :parm workflow_apiformat_json: The workflow file in JSON format.
        :type workflow_apiformat_json: dict
        :return: The workflow file with all nodes of class type "PreviewImage" removed.
        :rtype: dict
        """
        ids_to_remove = [
            id
            for id in workflow_apiformat_json
            if workflow_apiformat_json[id]["class_type"] == "PreviewImage"
        ]
        for id in ids_to_remove:
            del workflow_apiformat_json[id]
        return workflow_apiformat_json

    def node_id_for_name(self, node_name: str) -> str:
        """
        Get the id of a node by its name.
        """
        for id in self.workflow_apiformat_json:
            if self.workflow_apiformat_json[id]["_meta"]["title"] == node_name:
                return id

    def check_if_node_exists(self, node_name: str) -> bool:
        """Check if a node exists in the workflow."""
        for id in self.workflow_apiformat_json:
            if self.workflow_apiformat_json[id]["_meta"]["title"] == node_name:
                return True
        return False

    def count_node_class_occurances(self, node_class: str) -> int:
        """Count the number of occurances of a node class in the workflow."""
        count = 0
        for id in self.workflow_apiformat_json:
            if self.workflow_apiformat_json[id]["class_type"] == node_class:
                count += 1
        return count

    def check_if_parameter_exists(self, node_name: str, parameter: str) -> bool:
        """Check if a parameter exists for a node."""
        node_id = self.node_id_for_name(node_name)
        return parameter in self.workflow_apiformat_json[node_id]["inputs"].keys()

    def check_if_parameter_has_correct_type(
        self, node_name: str, parameter: str, expected_type: type
    ) -> bool:
        """Check if a parameter has the correct type for a node."""
        node_id = self.node_id_for_name(node_name)
        return isinstance(
            self.workflow_apiformat_json[node_id]["inputs"][parameter], expected_type
        )

    def set_value(self, node_name: str, parameter: str, value: any):
        """Set the value of a parameter for a node."""
        node_id = self.node_id_for_name(node_name)
        if node_id is None:
            raise ValueError(f"Node {node_name} does not exist in the workflow.")

        if parameter not in self.workflow_apiformat_json[node_id]["inputs"]:
            raise ValueError(f"Node {node_name} does not have input {parameter}")

        self.workflow_apiformat_json[node_id]["inputs"][parameter] = value

    def check_if_parameters_are_valid(self, generation_params: list[dict]):
        """
        Validates a list of generation_params for the workflow.
        This method performs several checks on each generation_param in the provided list:
        1. Verifies that the node specified by 'node_name' exists in the workflow.
        2. Checks that the specified input parameter exists for the given node.
        3. Ensures that the input parameter has the correct type.
        4. Attempts to set the value of the input parameter for the node.
        If any of these checks fail, a ValueError is raised with an appropriate error message.
        Args:
            generation_params (list[dict]): A list of dictionaries, each containing:
            - 'node_name' (str): The name of the node.
            - 'input' (str): The name of the input parameter.
            - 'value' (any): The value to set for the input parameter.
        Raises:
            ValueError: If any of the validation checks fail.
        """
        # assert each existing element of generation_params has the keys "node_name", "input", "value"
        for value_info in generation_params:
            if not all(key in value_info for key in ["node_name", "input", "value"]):
                raise ValueError(
                    "Each generation_param dictionary should contain the keys 'node_name', 'input', and 'value'."
                )

        for generation_param in generation_params:
            # check if node exists
            if not self.check_if_node_exists(generation_param["node_name"]):
                raise ValueError(
                    f"Node {generation_param['node_name']} does not exist in the workflow."
                )
            # check if input exists
            if not self.check_if_parameter_exists(
                generation_param["node_name"], generation_param["input"]
            ):
                raise ValueError(
                    f"Node {generation_param['node_name']} does not have input {generation_param['input']}"
                )
            # check if input has correct type
            if not self.check_if_parameter_has_correct_type(
                generation_param["node_name"],
                generation_param["input"],
                type(generation_param["value"]),
            ):
                raise ValueError(
                    f"Node {generation_param['node_name']} input {generation_param['input']} has the wrong type"
                )
            try:
                self.set_value(
                    generation_param["node_name"],
                    generation_param["input"],
                    generation_param["value"],
                )
            except ValueError:
                raise ValueError(
                    f"Node {generation_param['node_name']} can't set input {generation_param['input']} to value {generation_param['value']}"
                )

    def set_generation_params(self, generation_params: list[dict]):
        """Set the generation_params for the workflow."""
        for generation_param in generation_params:
            self.set_value(
                generation_param["node_name"],
                generation_param["input"],
                generation_param["value"],
            )

    def get_value(self, node_name: str, parameter: str):
        """Get the value of a parameter for a node."""
        node_id = self.node_id_for_name(node_name)
        return self.workflow_apiformat_json[node_id]["inputs"][parameter]

    def set_image(self, node_name: str, image: Image.Image):
        """Set the image input for a node."""
        node_id = self.node_id_for_name(node_name)
        if node_id is None:
            raise ValueError(f"Node '{node_name}' does not exist in the workflow.")

        metadata = self.upload_image(image, "input")
        self.workflow_apiformat_json[node_id]["inputs"]["image"] = (
            metadata["subfolder"] + "/" + metadata["name"]
        )

    def upload_image(self, image: Image.Image, name: str) -> object:
        """Upload an image to the server."""
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)
        files = {
            "image": (f"{name}.png", img_byte_arr),
        }
        data = {"overwrite": "false", "subfolder": "uploaded_images"}
        return requests.post(
            "http://{}/upload/image".format(self.api_host),
            files=files,
            data=data,
            timeout=20,
        ).json()

    def get_history(self, prompt_id: str):
        """Get the history of a prompt."""
        with urllib.request.urlopen(
            "http://{}/history/{}".format(self.api_host, prompt_id),
            timeout=15,
        ) as response:
            return json.loads(response.read())

    @retry(tries=3, delay=5, max_delay=30)
    def queue_prompt(self, prompt: str):
        """Queue a prompt. This is the crucial step to start a workflow."""
        print(f"Start workflow on {self.api_host}")
        p = {"prompt": prompt, "client_id": "paws-frontend"}
        data = json.dumps(p).encode("utf-8")
        req = urllib.request.Request(
            "http://{}/prompt".format(self.api_host), data=data
        )
        return json.loads(urllib.request.urlopen(req, timeout=10).read())

    @retry(tries=3, delay=5, max_delay=30)
    def wait_for_done(self, prompt_id: str):
        """Wait for a prompt to be completed."""
        while True:
            history = self.get_history(prompt_id)
            if prompt_id in history and (
                history[prompt_id]["status"]["completed"]
                or history[prompt_id]["status"]["status_str"] == "error"
            ):
                return history
            else:
                time.sleep(1)

    @retry(tries=3, delay=5, max_delay=30)
    def check_for_error(self, history):
        status = history.get(list(history.keys())[0])["status"]["status_str"]
        if status == "error":
            details = history.get(list(history.keys())[0])["status"]["messages"]
            for info in details:
                if "error" in info[0]:
                    # raise exception and display info
                    raise Exception(info)

    def execute(self):
        """Execute the workflow and wait for it to be done."""
        prompt_id = self.queue_prompt(self.workflow_apiformat_json)["prompt_id"]

        history = self.wait_for_done(prompt_id)
        self.check_for_error(history)
        self.last_history = history[prompt_id]

    def download_image(
        self, filename: str, subfolder: str, folder_type: str
    ) -> Image.Image:
        """Download an image from the server."""
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(
            "http://{}/view?{}".format(self.api_host, url_values)
        ) as response:
            return Image.open(io.BytesIO(response.read()))

    def get_image(self, node_name: str) -> list[Image.Image]:
        """Get the output image of a node."""
        node_id = self.node_id_for_name(node_name)

        return [
            self.download_image(img["filename"], img["subfolder"], img["type"])
            for img in self.last_history["outputs"][node_id]["images"]
        ]

    def delete_complete_node(self, node_name: str):
        """Delete a node from the workflow."""
        node_id = self.node_id_for_name(node_name)
        self.workflow_apiformat_json.pop(node_id)

    def adjust_workflow_to_generate_one_image_only(self):
        """Remove all nodes that generate multiple images and their connection to the sampler node via script input."""
        try:
            # Only if there is some sort of XY plot, it is necessary to adjust the image. Otherwise no action needed.
            if self.check_if_node_exists("XY Plot"):
                nodes_to_remove = [
                    "XY Input: Sampler/Scheduler",
                    "XY Input: Seeds++ Batch",
                    "XY Plot",
                ]

                for node in nodes_to_remove:
                    if self.check_if_node_exists(node):
                        self.delete_complete_node(node)

                # the sampler node's connection via script to the removed nodes needs to be removed as well
                sampler_node_id = self.node_id_for_name(
                    "KSampler (Efficient) - Generation"
                )
                if "script" in self.workflow_apiformat_json[sampler_node_id]["inputs"]:
                    self.workflow_apiformat_json[sampler_node_id]["inputs"].pop(
                        "script"
                    )
        except Exception as e:
            print(f"Error adjusting workflow to one image only.: {e} . CONTINUING ...")
