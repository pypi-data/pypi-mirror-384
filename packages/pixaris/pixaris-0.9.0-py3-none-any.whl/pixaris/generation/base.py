from abc import abstractmethod
from PIL import Image


class ImageGenerator:
    """When implementing a new Image Generator, inherit from this one and implement all the abstract methods."""

    @abstractmethod
    def generate_single_image(self, args: dict[str, any]) -> tuple[Image.Image, str]:
        pass

    def validate_inputs_and_parameters(
        self, inputs: list[dict] = [], parameters: list[dict] = []
    ) -> bool:
        return True
