"""
Supabase client for image storage
"""
import os
import logging
from supabase import create_client, Client
from typing import Optional

logger = logging.getLogger(__name__)

class SupabaseStorage:
    """Handle image uploads to Supabase storage"""
    
    def __init__(self):
        # Get Supabase credentials from environment
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment")
        
        self.client: Client = create_client(supabase_url, supabase_key)
        self.bucket_name = "question-images"  # You can change this to your bucket name
        
        logger.info(f"Initialized Supabase client for {supabase_url}")
    
    def upload_image(self, file_path: str, file_name: str) -> Optional[str]:
        """
        Upload an image to Supabase storage and return the public URL
        
        Parameters:
        -----------
        file_path : str
            Local path to the image file
        file_name : str
            Name to save the file as in Supabase
            
        Returns:
        --------
        str
            Public URL of the uploaded image, or None if upload failed
        """
        try:
            # Read the file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Upload to Supabase storage
            response = self.client.storage.from_(self.bucket_name).upload(
                path=file_name,
                file=file_data,
                file_options={"content-type": "image/png"}
            )
            
            # Get public URL
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_name)
            
            logger.info(f"Successfully uploaded image to Supabase: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload image to Supabase: {e}")
            # Try to handle duplicate file error
            if "already exists" in str(e):
                try:
                    # Get existing file URL
                    public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_name)
                    logger.info(f"File already exists, returning existing URL: {public_url}")
                    return public_url
                except Exception as e2:
                    logger.error(f"Failed to get existing file URL: {e2}")
            return None