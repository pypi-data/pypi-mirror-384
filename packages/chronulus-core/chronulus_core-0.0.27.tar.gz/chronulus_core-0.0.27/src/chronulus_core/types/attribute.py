import os
from typing import Any, Union

from pydantic import BaseModel, Field
from PIL import Image as PILImage
import io
import base64
import requests


def get_pillow_image_type(ext: str):
    ext = "." + ext.lower().replace('.','')
    if ext in PILImage.registered_extensions():
        return PILImage.registered_extensions()[ext]
    else:
        return None


def get_mime_type_from_headers(url: str):
    response = requests.head(url, allow_redirects=True)  # HEAD request is lighter than GET
    try:
        content_type = response.headers['content-type']
        if type(content_type) is str:
            return content_type
        else:
            raise KeyError(f'Content type not found in header for {url}')
    except Exception as e:
        return False


def get_image_type_from_url(url: str):
    parts = url.split(".")
    if len(parts) == 1:
        raise ValueError(f"""Image type could not be determined for {url}. 
                    Please add it in the `type` argument.""")
    else:
        ext = parts[-1]
        pillow_format = get_pillow_image_type(ext)
        if pillow_format is None:
            raise ValueError(
                f"""Image type was detected as '.{ext}' but this type is not supported.
                                If this is incorrect, please provide the correct type in the `type` argument.
                            """)
        else:
            return pillow_format


class ImageFromUrl(BaseModel):
    """Attribute to fetch an image from a specified remote URL

    The remote URL should be publicly accessible otherwise our systems will fail to retrieve it.

    Parameters
    ----------
    url : str
        URL of the remote image
    type : Optional[str]
        The PIL image type, e.g., PNG, JPEG, etc.

    Attributes
    ----------
    url : str
        URL of the remote image
    type : Optional[str]
        The PIL image type, e.g., PNG, JPEG, etc.

    """
    url: str
    type: Union[str, None] = Field(default=None, description='PIL image type')

    def model_post_init(self, __context: Any) -> None:

        if self.type is None:
            mime_type = get_mime_type_from_headers(self.url)
            if mime_type:
                image_type = mime_type.split('/')[-1]
                self.type = image_type
            else:
                raise ValueError(f'No image type could be detected for {self.url}. Please provide the correct type in the `type` argument')

        pillow_format = get_pillow_image_type(self.type)
        if pillow_format is None:
            raise ValueError(
                f"""Image type '{self.type}' was specified but this type is not supported.
                    If this is incorrect, please provide the correct type in the `type` argument.
                """)
        else:
            self.type = pillow_format


class ImageFromFile(BaseModel):
    """Attribute to upload an image from a local file

    The image should be accessible in your local file system by the client

    Parameters
    ----------
    file_path : str
        Path to image file, e.g., '/path/to/image.jpg'
    type : Optional[str]
        The PIL image type, e.g., PNG, JPEG, etc.

    Attributes
    ----------
    file_path : str
        Path to image file, e.g., '/path/to/image.jpg'
    type : Optional[str]
        The PIL image type, e.g., PNG, JPEG, etc.
    data : Optional[str]
        The base64 encoded image string

    """
    file_path: str = Field(exclude=True, description='path to the image file')
    type: Union[str, None] = Field(default=None, description='PIL image type')
    data: Union[str, None] = Field(default=None, description='base64 encoded image string')

    def model_post_init(self, __context: Any) -> None:
        if self.data is None:
            # Open the image with PIL
            try:
                img = PILImage.open(self.file_path)

            except FileNotFoundError as e:
                # trying handling case there macOS gives us screenshots with abnormal spacing before AM/PM
                if self.file_path.endswith(" AM.png"):
                    new_file = self.file_path.replace(" AM.png", "\u202fAM.png")
                    img = PILImage.open(new_file)
                    self.file_path = new_file

                elif self.file_path.endswith(" PM.png"):
                    new_file = self.file_path.replace(" PM.png", "\u202fPM.png")
                    img = PILImage.open(new_file)
                    self.file_path = new_file

                else:
                    raise e

            # Convert to bytes using an in-memory bytes buffer
            buffer = io.BytesIO()
            img.save(buffer, format=img.format)
            image_bytes = buffer.getvalue()

            if self.type is None or self.type != img.format:
                self.type = img.format
            self.data = base64.b64encode(image_bytes).decode('utf-8')

        if self.type is None and self.data is not None:
            raise ValueError(f"""Image data was provided without a type""")


class ImageFromBytes(BaseModel):
    """Attribute to upload an image from bytes

    The image should be provided in raw bytes and the PIL image type specified

    Parameters
    ----------
    image_bytes : bytes
        raw bytes of the image
    type : str
        The PIL image type, e.g., PNG, JPEG, etc.

    Attributes
    ----------
    image_bytes : bytes
        raw bytes of the image
    type : str
        The PIL image type, e.g., PNG, JPEG, etc.
    data : Optional[str]
        The base64 encoded image string

    """
    image_bytes: bytes = Field(exclude=True, description='image bytes')
    type: str = Field(description='PIL image type')
    data: Union[str, None] = Field(default=None, description='base64 encoded image string')

    def model_post_init(self, __context: Any) -> None:
        if self.data is None:
            self.data = base64.b64encode(self.image_bytes).decode('utf-8')


class Image(BaseModel):
    """Attribute to upload an image from base64 encoded string

    The image should be provided as a base64 encoded string and the PIL image type specified

    Parameters
    ----------
    type : str
        The PIL image type, e.g., PNG, JPEG, etc.
    data : str
        The base64 encoded image string

    Attributes
    ----------
    type : str
        The PIL image type, e.g., PNG, JPEG, etc.
    data : str
        The base64 encoded image string
    """
    type: str = Field(description='PIL image type')
    data: str = Field(description='base64 encoded image string')

    @staticmethod
    def from_bytes(_bytes: bytes, _type: str):
        data = base64.b64encode(_bytes).decode('utf-8')
        return Image(type=_type, data=data)

    @staticmethod
    def from_file(file_path: str, _type: Union[str, None] = None):
        img = PILImage.open(file_path)

        # Convert to bytes using an in-memory bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format=img.format)
        image_bytes = buffer.getvalue()
        if _type is None or _type != img.format:
            _type = img.format
        data = base64.b64encode(image_bytes).decode('utf-8')
        return Image(type=_type, data=data)


class Text(BaseModel):
    """Attribute to upload a large text document

    Parameters
    ----------
    data : str
        The content of the large text document

    Attributes
    ----------
    data : str
        The content of the large text document
    """
    data: str = Field(description='the contents of the text file')


class TextFromFile(BaseModel):
    """Attribute to upload a text document from a local file

    The text should be accessible in your local file system by the client

    Parameters
    ----------
    file_path : str
        Path to text file, e.g., '/path/to/text.txt'

    Attributes
    ----------
    file_path : str
        Path to text file, e.g., '/path/to/text.txt'
    data : Optional[str]
        The content of the large text document

    """
    file_path: str = Field(exclude=True, description='path to the text file')
    data: Union[str, None] = Field(default=None, description='the contents of the text file')

    def model_post_init(self, __context: Any) -> None:
        if self.data is None:

            try:
                # Try UTF-8 first
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
            except UnicodeDecodeError:
                # Fallback if UTF-8 fails
                print("Warning: UTF-8 decoding failed, trying system default encoding")
                with open(self.file_path, 'r') as f:
                    text_content = f.read()
            file_name = os.path.basename(self.file_path)
            text_content = f"file: {file_name}\n\n" + text_content

            self.data = text_content


class Pdf(BaseModel):
    """Attribute to upload a PDF from a base64 encoded string

    The PDF should be provided as a base64 encoded string

    Parameters
    ----------
    data : str
        The base64 encoded PDF

    Attributes
    ----------
    data : str
        The base64 encoded PDF

    """
    data: str = Field(description='the contents of the PDF file as a base64 encoded string')


class PdfFromFile(BaseModel):
    """Attribute to upload PDF from a local file

    The PDF should be accessible in your local file system by the client

    Parameters
    ----------
    file_path : str
        Path to PDF file, e.g., '/path/to/doc.pdf'

    Attributes
    ----------
    file_path : str
        Path to PDF file, e.g., '/path/to/doc.pdf'
    data : Optional[str]
        The base64 encoded PDF

    """

    file_path: str = Field(exclude=True, description='path to the PDF file')
    data: Union[str, None] = Field(default=None,
                                   description='the contents of the PDF file as a base64 encoded string')

    def model_post_init(self, __context: Any) -> None:
        if self.data is None:
            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"PDF file not found at {self.file_path}")

            if not self.file_path.lower().endswith('.pdf'):
                raise ValueError(f"File {self.file_path} does not appear to be a PDF")

            # If text reading fails or binary signature found, read as binary
            with open(self.file_path, 'rb') as f:
                pdf_bytes = f.read()
            self.data = base64.b64encode(pdf_bytes).decode('utf-8')
