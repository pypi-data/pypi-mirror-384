"""A module for image processing utilities, including encoding images to JPEG and PNG formats, and converting WebP images to JPEG."""

import base64
from collections.abc import Callable
from functools import partial
from io import BytesIO
from pathlib import Path
from typing import Any, Self

from PIL import Image
from PIL.Image import Image as PILImage
from PIL.ImageFile import ImageFile

ImageClass = PILImage | ImageFile


class ImageConverter:
    """A class to handle image conversions and resizing."""

    def __init__(self, image_path: Path, save_path: Path | None = None) -> None:
        """Create a new ImageConverter."""
        self.image_path: Path = image_path
        self.save_path: Path | None = save_path
        self.ops: list[Callable[..., Any]] = []
        self._target_format: str | None = None
        self._target_quality: int = -1

        self._output: str = ""

    def _add(self, func: Callable, kwargs: dict[str, Any]) -> None:
        """Add an operation to the chain."""
        self.ops.append(partial(func, **kwargs))

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        return

    def resize(self, max_size: int | None = None) -> Self:
        """Add a resize operation to the chain."""
        if max_size is None or max_size <= 0:
            # If you don't follow the rules, we just ignore you!
            return self
        self._add(func=self._resize, kwargs={"max_size": max_size})
        return self

    def to_jpeg(self, quality: int = 85) -> Self:
        """Add a JPEG conversion operation to the chain."""
        self._add(
            func=self._convert_mode,
            kwargs={"modes": ("RGB", "L"), "to_mode": "RGB", "fmt": "JPEG", "quality": quality},
        )
        return self

    def to_png(self) -> Self:
        """Add a PNG conversion operation to the chain."""
        self._add(
            func=self._convert_mode,
            kwargs={"modes": ("RGBA", "LA"), "to_mode": "RGBA", "fmt": "PNG"},
        )
        return self

    def to_base64(self) -> Self:
        """Add a base64 conversion operation to the chain."""
        self._add(func=self._to_base64, kwargs={})
        return self

    @staticmethod
    def _resize(image: ImageClass, max_size: int) -> ImageClass:
        """Return a new converter with resize applied."""
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        return image

    def _convert_mode(
        self,
        image: ImageClass,
        modes: tuple[str, ...],
        to_mode: str,
        fmt: str,
        quality: int = -1,
    ) -> ImageClass:
        """Convert image mode if not in mode_check."""
        if image.mode not in modes:
            image = image.convert(to_mode)
        self._target_format = fmt
        self._target_quality = quality
        return image

    def _to_base64(self, image: ImageClass) -> str:
        """Execute the chain and return base64.

        This should only be called as a last step since this returns a string.

        Args:
            image (ImageClass): The image to convert to base64.

        Returns:
            str: The base64 encoded string of the image.
        """
        buffer = BytesIO()
        image.save(
            buffer,
            format=self._target_format or image.format,
            quality=self._target_quality if self._target_quality > 0 else None,
        )
        output: bytes = buffer.getvalue()
        buffer.close()
        return base64.b64encode(output).decode("utf-8")

    def _save(self, image: ImageClass, output_path: Path | None = None) -> None:
        """Save the processed image to the specified path."""
        save_path: Path | None = self.save_path or output_path
        if save_path is None:
            raise ValueError("No save path specified.")
        image.save(
            save_path,
            format=self._target_format or image.format,
            quality=self._target_quality if self._target_quality > 0 else None,
        )

    def do(self, output_path: Path | None = None) -> Self:
        """Save the processed image to the specified path."""
        if len(self.ops) == 0:
            raise ValueError("No operations to execute.")
        with Image.open(self.image_path) as img:
            output: ImageClass = img
            for func in self.ops:
                output = func(image=output)
            if isinstance(output, str):
                self._output = output
                return self
            if not isinstance(output, (Image.Image | ImageFile)):
                raise TypeError(f"Unexpected output type: {type(output)}")
            self._save(output, output_path)
            return self

    def get(self) -> str:  # most likely only going to be used after to_base64
        """Get the output of the last operation."""
        return self._output


def encode_to_jpeg(image_path: Path, max_size: int = 1024, jpeg_quality: int = 75) -> str:
    """Resize image to optimize for token usage"""
    with ImageConverter(image_path) as converter:
        converter.resize(max_size)
        converter.to_jpeg(quality=jpeg_quality)
        converter.to_base64()
        converter.do()
        return converter.get()


def encode_to_png(image_path: Path, max_size: int = 1024) -> str:
    """Resize image to optimize for token usage"""
    return ImageConverter(image_path).resize(max_size).to_png().to_base64().do().get()


def to_jpeg_file(
    image_path: Path,
    save_path: Path | None = None,
    quality: int = 95,
    max_size: int | None = None,
) -> None:
    """Convert a WebP image to JPEG format and save to file."""
    ImageConverter(image_path, save_path).resize(max_size).to_jpeg(quality=quality).do()


def to_png_file(image_path: Path, save_path: Path | None = None, max_size: int | None = None) -> None:
    """Convert an image to PNG format and save to file."""
    ImageConverter(image_path, save_path).resize(max_size).to_png().do()
