from common import BlickCommon


class BlickImage():

    # Placeholder for persistent lazy objects
    _BLICK_OBJs = {}
    
    @staticmethod
    def get_pil(whatever, flatten=True, bg_fill=(255,255,255)):
        """
        Get a Pillow Image from various sources
        
        Args:
            whatever: Input which can be a URL, file path, numpy array, or base64 string
            flatten: Whether to convert image to RGB (3 channels)
            bg_color: Background color for flattening (default is black)
            
        Returns:
            PIL.Image.Image: Pillow Image object
            
        Raises:
            ValueError: If no valid input is provided or multiple inputs are provided
            ImportError: If required libraries are not installed
        """
        import os

        from PIL import Image as PIL_Image
        from PIL import ImageOps
        from io import BytesIO

        if BlickCommon.is_empty(whatever):
            return None
        
        pil_im = None

        if isinstance(whatever, PIL_Image.Image):
            pil_im = whatever

        elif str(whatever).startswith("http") or BlickCommon.get_urls(str(whatever)) is not None:
            # Load from URL
            import httpx # HTTPx is preferred over requests for async support and better performance

            httpx_client = BlickImage._BLICK_OBJs.setdefault('httpx_client', httpx.Client())

            try:
                if str(whatever).startswith("http"):
                    url = str(whatever).strip()
                else:
                    url = BlickImage.get_urls(str(whatever))[0] 
                    
                response = httpx_client.get(url)
                pil_im = PIL_Image.open(BytesIO(response.content))
            except Exception as e:
                #print(f"Warning: Unable to get image from URL: {e}")
                return None

        elif os.path.isfile(str(whatever).strip()):
            # Load from file path
            try:
                pil_im = PIL_Image.open(whatever) 
            except Exception as e:
                #print(f"Warning: Unable to load image from {whatever}: {e}")
                return None
                
        
        elif isinstance(whatever, (str)):
            # Assume base64 string
            import base64

            try:
                base64_str = str(whatever).strip()
                # Remove data URI prefix if present
                if "," in base64_str:
                    base64_str = base64_str.split(",")[1]
                image_data = base64.b64decode(base64_str)
                pil_im = PIL_Image.open(BytesIO(image_data))
            except Exception as e:
                #print(f"Warning: Unable to get image {str(whatever)[:25]}...: : {e}")
                return None
        
        else:
            # Assume numpy array
            array = whatever

            import numpy as np
            try:
                pil_im = PIL_Image.fromarray(whatever)
            except Exception as e:
                #print(f"Warning: Unable to convert numpy array to image {str(whatever)[:25]}...: {e}")
                return None

        try:
            if pil_im is not None:   
                # Fix EXIF orientation
                pil_im = ImageOps.exif_transpose(pil_im)     
                
                # Flatten to RGB if needed
                if flatten and pil_im.mode !=  'RGB':
                    # SAFE method to convert RGBA to RGB avoiding PIL bugs
                    # This composites the image onto a solid background
                    
                    pil_im = pil_im.convert('RGBA')
                    
                    # Create a new RGB background with the specified color
                    bg = PIL_Image.new('RGB', pil_im.size, bg_fill)
                    
                    # Paste the image onto the background using alpha channel as mask
                    # This properly handles semi-transparent pixels
                    bg.paste(pil_im, mask=pil_im.split()[3])  # split()[3] is the alpha channel
                    
                    pil_im = bg
            return pil_im
        
        except Exception as e:
            #print(f"Warning: Unable to process image: {str(whatever)[:25]}...: {e}")
            return None
    

    @staticmethod
    def autocrop(whatever, save_to=None, flatten=True, bg_fill=(255,255,255), strength=15):
        """
        Automatically crops uniform borders from a PIL image.
        The background color is taken from pixel (0, 0).
        A border is removed if the difference from the background is below a threshold.

        Args:
            whatever: whatever can be loaded as image (path, url, pil_image, numpy array, base64)
            save_to: If defined, saves the image on the save_to filename or on the save_to directory with same name as whatever
            flatten: if returns RGB or not
            bg_fill: color to fill transparency with
            strenth (int): [0-255] Tolerance threshold for color difference to consider as content.

        Returns:
            PIL Image.Image: Cropped image without uniform borders.
        """
        import os
        from PIL import Image as PIL_Image
        from PIL import ImageChops, ImageFilter
        
        im = BlickImage.get_pil(whatever, flatten=flatten, bg_fill=bg_fill)

        if not im:
            return None
        
        smoothed = im.filter(ImageFilter.SMOOTH)

        # Get background color from top-left pixel
        bg_color = smoothed.getpixel((0, 0))

        # Create a solid background image with the same color
        bg = PIL_Image.new(smoothed.mode, smoothed.size, bg_color)

        # Compute the difference between the image and the background
        diff = ImageChops.difference(smoothed, bg)

        # Enhance the difference to filter out small variations
        diff = ImageChops.add(diff, diff, 3.0, -strength)

        # Get bounding box of significant content
        bbox = diff.getbbox()

        # Crop the image if content is found
        if bbox:
            im = im.crop(bbox)

        if save_to:
            try:
                if BlickImage.get_ext(save_to):
                    # Save to is a filename
                    parent_dirs = BlickImage.get_fulldir(save_to)
                    if parent_dirs:
                        os.makedirs(parent_dirs, exist_ok=True)
                    im.save(save_to)
                elif len(str(save_to)) < 250:
                    # Consider save_to as a dir
                    os.makedirs(save_to, exist_ok=True)
                    if os.path.exists(str(whatever).strip()):
                        target_filename = BlickImage.get_filename(str(whatever))
                    else:
                        target_filename = "crop.jpg"
                    im.save(os.path.join(save_to, target_filename))                    
            except Exception as e:
                print(f"Error saving image with shape {im.size} to {save_to}")
                pass

        return im




    @staticmethod
    def get_base64(pil_image, image_format="webp", quality=75):
        """
        Convert a PIL Image to base64 string.
        
        Args:
            pil_image: PIL Image object
            image_format: Image format for encoding (default is "webp")
            quality: Quality for encoding (1-100, default is 75)
            
        Returns:
            str: Base64 encoded string of the image
        """
        import base64
        from io import BytesIO

        # Make sure it's a PIL image
        im = BlickImage.get_pil(pil_image, flatten=True)

        if im is None:
            return None

        buffered = BytesIO()
        try:
            im.save(buffered, format=image_format, quality=quality)
            img_bytes = buffered.getvalue()
            base64_str = base64.b64encode(img_bytes).decode('utf-8')

            mime_types = {
                'webp': 'image/webp',
                'png': 'image/png',
                'jpeg': 'image/jpeg',
                'jpg': 'image/jpeg',
                'gif': 'image/gif',
                'bmp': 'image/bmp'
            }
            if str(image_format).strip() not in mime_types.keys():
                return base64_str
            else:
                mime_type = mime_types.get(image_format.lower(), 'image/webp')
                return f"data:{mime_type};base64,{base64_str}"    
            
        except Exception as e:
            print(f"Warning: Unable to convert image to Base64: {e}")
            return None
                    
    