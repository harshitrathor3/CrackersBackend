import os
import random
import traceback

import cloudinary
import cloudinary.api
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from fastapi import UploadFile, status

from config import CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET, CLOUDINARY_CLOUD_NAME


cloudinary.config( 
    cloud_name = CLOUDINARY_CLOUD_NAME, 
    api_key = CLOUDINARY_API_KEY, 
    api_secret = CLOUDINARY_API_SECRET,
    secure=True
)


class ImageUtils:
    def __init__(self, image: UploadFile) -> None:    
        self.image = image
        self.image_path = ""


    def save_image_locally(self):
        """
        Save image locally

        Args:
            image (UploadFile): image file

        Returns:
            image_path (str): path of image
            status_code (int): status of the operation
        """
        try:
            image_filename = self.image.filename
            image_filename_without_ext, ext = os.path.splitext(image_filename)
            image_filename_final = f"{image_filename_without_ext}_{random.randint(1, 9999)}{ext}"
            with open(image_filename_final, "wb") as buffer:
                buffer.write(self.image.file.read())
            self.image_path = os.path.abspath(image_filename_final)

            return {"status": "success"}, status.HTTP_201_CREATED
        except Exception as e:
            return {"error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR


    def upload_image(self, public_id: str):
        """
        Upload an image to cloudinary

        Args:
            public_id (str): image unique id

        Returns:
            _type_: 
        """
        try:
            upload_result = cloudinary.uploader.upload(self.image_path, secure=True, public_id=public_id)
            return upload_result, status.HTTP_201_CREATED
        except Exception as e:
            return {"error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR


    def optimize_image(self, public_id: str):
        """
        Optimize delivery by resizing and applying auto-format and auto-quality

        Args:
            public_id (str): image unique id

        Returns:
            _type_: 
        """
        try:
            optimize_url, _ = cloudinary_url(public_id, fetch_format="auto", quality="auto")
            return optimize_url
        except Exception as e:
            return {"error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR


    def transform_image(self, public_id: str, width: int, height: int):
        """
        Transform the image: auto-crop to square aspect_ratio

        Args:
            public_id (str): image unique id
            width (int): image width
            height (int): image height

        Returns:
            _type_: 
        """
        try:
            auto_crop_url, _ = cloudinary_url(public_id, width=width, height=height, crop="auto", gravity="auto")
            return auto_crop_url
        except Exception as e:
            return {"error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR


    def get_image_info(self, public_id: str):
        """
        Get image info from cloudinary

        Args:
            public_id (str): image unique id

        Returns:
            _type_: 
        """
        try:
            image_info=cloudinary.api.resource(public_id)
            return image_info
        except Exception as e:
            return {"error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR


    def delete_image(self, public_id: str):
        """
        Delete image from cloudinary

        Args:
            public_id (str): image unique id

        Returns:
            _type_: 
        """
        try:
            image_info=cloudinary.api.delete_resources(public_id)
            return image_info
        except Exception as e:
            return {"error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR


    def delete_local_saved_image(self):
        """
        Delete local saved image

        Args:
            image_path (str): image path

        Returns:
            _type_: 
        """
        try:
            if os.path.exists(self.image_path):
                os.remove(self.image_path)
                print("locally saved image deleted")
        except Exception as e:
            return {"error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR



