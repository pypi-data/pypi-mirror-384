"""
Main utilities class for blickutils
"""


class BlickUtils:
    """
    A collection of static utility methods for Blick Technologies
    """
    # All imports are done on demand to avoid unnecessary dependencies
    # Placeholder for persistent lazy objects
    _BLICK_OBJs = {}


    @staticmethod
    def get_version():
        from importlib.metadata import version
        return version("blickutils")        
    
    @staticmethod
    def version():
        """Alias for get_version to maintain compatibility"""
        return BlickUtils.get_version()
    
    @staticmethod
    def is_empty(obj):
        """
        Returns True if the object is considered empty (None, empty string, empty list, etc.)
        """
        
        if obj is None:
            return True

        if str(obj).strip() == '':
            return True
        
        import re
        if re.sub(r'\s', '', str(obj)) == '':
            return True

        if isinstance(obj, list) and len(obj) == 0:
            return True

        try:
            if len(obj) == 0:
                return True
        except:
            pass

        return False

        
    @staticmethod
    def get_gpu_info():
        """
        Returns GPU information including device count, names, and memory
        
        Returns:
            dict: Dictionary containing GPU information or error message
        """
        try:
            import torch
        except ImportError:
            torch = None

        try:
            import GPUtil
        except ImportError:
            GPUtil = None

        gpu_info = {
            "gpu_available": False,
            "gpu_count": 0,
            "gpu_devices": None,
            "cuda_available": False,
            "cuda_count": 0,
            "cuda_devices": None,
        }   

        if GPUtil is not None:
            try:
                gpus = GPUtil.getGPUs()
                
                if not gpus:
                    return gpu_info
                
                gpu_info["gpu_available"] = True
                gpu_info["gpu_count"] = len(gpus)
                gpu_info["gpu_devices"] = []
                
                for gpu in gpus:
                    gpu_info["gpu_devices"].append({
                        "id": gpu.id,
                        "name": gpu.name,
                        "total_memory_gb": round(gpu.memoryTotal / 1024, 2),
                        "used_memory_gb": round(gpu.memoryUsed / 1024, 2),
                        "free_memory_gb": round(gpu.memoryFree / 1024, 2),
                        "memory_util_percent": round(gpu.memoryUtil * 100, 1),
                        "gpu_util_percent": round(gpu.load * 100, 1),
                        "temperature_c": gpu.temperature,
                        "uuid": gpu.uuid
                    })
                
                return gpu_info
            except Exception as e:
                print(f"Warning: install GPUtil for better GPU info: pip install GPUtil")
        else:
            print(f"Warning: install GPUtil for better GPU info: pip install GPUtil")

        if torch is None:
            print(f"Warning: install torch with CUDA for correct device detection: pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126     - Further info :https://pytorch.org/get-started/locally/")
            return gpu_info
        
        if torch.cuda.is_available():
            gpu_info["cuda_available"] = True
            gpu_info["cuda_count"] = torch.cuda.device_count()
            gpu_info["cuda_devices"] = []
        
            for i in range(torch.cuda.device_count()):
                device_props = torch.cuda.get_device_properties(i)
                gpu_info["cuda_devices"].append({
                    "id": i,
                    "name": device_props.name,
                    "total_memory_gb": round(device_props.total_memory / 1024**3, 2),
                    "compute_capability": f"{device_props.major}.{device_props.minor}"
                })
        
        return gpu_info
    
    
    @staticmethod
    def get_gpu(id=0):
        """
        Returns torch device (GPU if available, otherwise CPU)
        
        Args:
            id: The ID of the GPU to use (default is 0)

        Returns:
            torch.device: CUDA device if available, otherwise CPU device
        """
        try:
            import torch
            
            if torch.cuda.is_available():
                gpus = torch.cuda.device_count()
                print(f'Found GPUs: {gpus} \\o/') 
                if id < gpus:
                    return torch.device(f'cuda:{id}')
                else:
                    return torch.device(f'cuda:{gpus}')
        except:
            print(f"Warning: install torch with CUDA for correct device detection: pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126     - Further info :https://pytorch.org/get-started/locally/")

        return "cpu"


    @staticmethod
    def get_cuda(id=0):
        """Alias for get_gpu to maintain compatibility"""
        return BlickUtils.get_gpu(id)


    @staticmethod
    def get_device(id=0):
        """Alias for get_gpu to maintain compatibility"""
        return BlickUtils.get_gpu(id)


    @staticmethod
    def get_urls(text):
        """
        Extract URLs from a given text string.
        
        Args:
            text: Input text string
        Returns:
            List[str]: List of extracted URLs or None if none found
        """
        import re
        
        if BlickUtils.is_empty(text):
            return None
        
        # Lazy use of Regex pattern to match URLs
        url_pattern = BlickUtils._BLICK_OBJs.setdefault(
            'url_pattern', re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        )
        
        try:
            # Find all URLs in the text
            urls = re.findall(url_pattern, str(text))
        
            return urls if urls else None
        except Exception as e:
            return None

    
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

        if BlickUtils.is_empty(whatever):
            return None
        
        pil_im = None

        if isinstance(whatever, PIL_Image.Image):
            pil_im = whatever

        elif str(whatever).startswith("http") or BlickUtils.get_urls(str(whatever)) is not None:
            # Load from URL
            import httpx # HTTPx is preferred over requests for async support and better performance

            httpx_client = BlickUtils._BLICK_OBJs.setdefault('httpx_client', httpx.Client())

            try:
                if str(whatever).startswith("http"):
                    url = str(whatever).strip()
                else:
                    url = BlickUtils.get_urls(str(whatever))[0] 
                    
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
    def get_img(whatever, flatten=True, bg_fill=(255,255,255)):
        """
        Alias for get_pil to maintain compatibility
        """
        return BlickUtils.get_pil(whatever, flatten=flatten, bg_fill=bg_fill)


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
        
        im = BlickUtils.get_pil(whatever, flatten=flatten, bg_fill=bg_fill)

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
                if BlickUtils.get_ext(save_to):
                    # Save to is a filename
                    parent_dirs = BlickUtils.get_fulldir(save_to)
                    if parent_dirs:
                        os.makedirs(parent_dirs, exist_ok=True)
                    im.save(save_to)
                elif len(str(save_to)) < 250:
                    # Consider save_to as a dir
                    os.makedirs(save_to, exist_ok=True)
                    if os.path.exists(str(whatever).strip()):
                        target_filename = BlickUtils.get_filename(str(whatever))
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
        im = BlickUtils.get_pil(pil_image, flatten=True)

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
                    
    

    @staticmethod
    def get_files(directory='.', ext='*', recursive=False):
        """
        Retorns a list of files in a directory with specified extensions
        
        Args:
            directory: directory path to search
            ext: file extension(s) to filter by. Options:
                - '*' or None: all files
                - '.mp4': specific extension
                - ['.mp4', '.avi', '.mov']: extensions list
            recursive: if True, searches subdirectories recursively
        Returns:
            List[str]: full paths of matching files
        """
        from pathlib import Path
        
        if BlickUtils.is_empty(directory):
            return []
        
        ignore_list = ['.ipynb_checkpoints', '.DS_Store', '__MACOSX', '.Trash', '.localized', '.Spotlight-V100', '$RECYCLE.BIN', 'Thumbs.db', 'desktop.ini']
        
        # Ensure directory is a Path object
        path = Path(str(directory))
        
        if not path.exists():
            return []
        
        if not path.is_dir():
            return []
        
        files = []
        
        # Normalize the extensions input
        if ext is None or str(ext).strip() == '*':
            extensions = ['*']
        elif isinstance(ext, str):
            # cleans up *.ext or simply ext to -> .ext
            extensions = ['*.' + str(ext).strip().replace('*','').replace('.','')]
        elif isinstance(ext, list):
            # Extensions list
            extensions = ['*.' + str(e).strip().replace('*','').replace('.','') for e in ext if not BlickUtils.is_empty(e)]
        else:
            extensions = ['*']
        
        # Busca arquivos
        for extension in extensions:
            try:
                pattern = f'{extension}'
                
                if recursive:
                    files_list = path.rglob(pattern)
                else:
                    files_list = path.glob(pattern)
                    
                # Recursively searches in all subdirectories
                for file in files_list:
                    if file.is_file():
                        include_file = True
                        
                        # Skip unwanted files
                        for ignore_term in ignore_list:
                            if ignore_term in str(file):
                                include_file = False
                                break
                        
                        if include_file:
                            files.append(str(file.absolute()))
                            
            except PermissionError:
                print(f"No permission to access '{directory}'")
                continue
            except Exception as e:
                continue
            
        # Remove duplicates
        files = list(set(files))
        
        return files
            

    @staticmethod
    def get_dirs(directory='.', recursive = False):
        """
        Get all directories in a directory
        
        Args:
            dir: Directory path to search
            recursive: Whether to search subdirectories recursively
            
        Returns:
            List[str]: List of directory paths
        """
        from pathlib import Path
        ignore_list = ['.ipynb_checkpoints', '.DS_Store', '__MACOSX', '.Trash', '.localized', '.Spotlight-V100', '$RECYCLE.BIN', 'Thumbs.db', 'desktop.ini']
        
        if BlickUtils.is_empty(directory):
            return []
        
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return []
        
        if not dir_path.is_dir():
            return []
        
        dirs = []
        
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for item in dir_path.glob(pattern):
            # Skip .. and . entries
            if item.name in ('.', '..'):
                continue
            
            try:
                if item.is_dir():
                    include_dir = True
                    
                    # Skip unwanted directories
                    for ignore_term in ignore_list:
                        if ignore_term in str(item.absolute()):
                            include_dir = False
                            break
                    
                    if include_dir:
                        dirs.append(str(item.absolute()))
                    
            except PermissionError:
                print(f"No permission to access '{item}'")
                continue
            except Exception as e:
                continue
        
        return dirs
    


    @staticmethod
    def get_ext(filename):
        """
        Returns the file extension of the filename.

        Args:
            filename (str): The full filename or path.

        Returns:
            str: The file extension (without the dot).
        """
        import os
        
        trimmed = str(filename).strip()[-5:]         
        ext = "." + trimmed.split(".")[-1]
    
        if str(filename).strip().endswith(ext):
            return ext
        return None


    @staticmethod
    def get_parent(filename):
        """
        Returns the immediate parent directory of the given file path.

        Args:
            filename (str): The full file path.

        Returns:
            str: The name of the immediate parent directory.
        """
        import os 

        parent = os.path.basename(os.path.dirname(str(filename).strip()))
        if BlickUtils.is_empty(parent):
            return None
        return parent 


    @staticmethod
    def get_parent_dir(filename):
        """Alias for get_parent_dir"""
        return BlickUtils.get_parent(filename)


    @staticmethod
    def get_fulldir(filename):
        """
        Returns the full parent directory path of the given file.

        Args:
            filename (str): The full file path.

        Returns:
            str: The full path to the parent directory.
        """
        import os 
        
        parents = os.path.dirname(str(filename))
        if BlickUtils.is_empty(parents):
            return None
        return parents 


    @staticmethod
    def get_filename(filepath):
        """
        Returns the filename from a full file path.

        Args:
            filepath (str): The full path to the file.

        Returns:
            str: The filename with extension.
        """
        import os 
        return os.path.basename(str(filepath).strip())


        
    @staticmethod 
    def dir2df(directory='.', ext='*', recursive=False):
        """
        Returns a pandas DataFrame with files in 3 columns: file_path, file_name, dir
        
        Args:
            directory: Directory path to search
            ext: File extension(s) to filter by. Options:
                - '*' or None: all files
                - '.mp4': specific extension
                - ['.mp4', '.avi', '.mov']: extensions list
            recursive: Whether to search subdirectories recursively
            
        Returns:
            pd.DataFrame: DataFrame with file paths and names
        """
        import os
        import pandas as pd
        
        files = BlickUtils.get_files(directory=directory, ext=ext, recursive=recursive)
        
        if not files:
            return pd.DataFrame(columns=['fullpath', 'filename', 'dir'])
        
        data = {
            'fullpath': files,
            'filename': [os.path.basename(f) for f in files],
            'dir': [str(os.path.dirname(f)).split(os.path.sep)[-1] for f in files]            
        }
        
        df = pd.DataFrame(data)
        
        return df
            

    @staticmethod
    def execute_cmd(cmd, working_dir='.', timeout=30):
        """
        Execute a command on the system.
        
        Args:
            cmd: Command string to execute
            
        Returns:
            tuple: (exit_code, output_string)
                - exit_code: Integer return code (0 for success)
                - output_string: Combined stdout and stderr as string
        """
        import subprocess

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=working_dir,
                timeout=timeout
            )
            
            # Combine stdout and stderr
            output = result.stdout
            if result.stderr:
                output += result.stderr
                
            return (result.returncode, output)
            
        except Exception as e:
            return (1, f"Error executing command: {str(e)}")


    @staticmethod
    def run_parallel(function_name, args_list, threads="auto"):
        """
        Run a function in parallel for each set of arguments in args_list.
        
        Args:
            function_name: The function to execute
            args_list: List of arguments. Can be:
                - List of lists: [[arg1, arg2], [arg1, arg2], ...] for multi-arg functions
                - Simple list: [arg1, arg2, ...] for single-arg functions
            threads: Number of threads to use:
                - "auto" or "1x" or -1: number of CPU cores
                - "Nx": N times the number of cores (e.g., "4x" = 4 * cores)
                - integer: exact number of threads
        
        Returns:
            list: Results in the same order as args_list
        """
        import re
        import os
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        try:
            # Auto-detect if running in Jupyter and use appropriate tqdm
            try:
                get_ipython().__class__.__name__
                from tqdm.notebook import tqdm
            except (NameError, ImportError):
                from tqdm import tqdm
        except ImportError:
            print("Warning: install tqdm for progress bar: pip install tqdm")
            tqdm = None
        
        # Determine number of logical CPUs (threads)
        num_cores = os.cpu_count() or 1
        
        try:
            if threads is None:
                max_workers = 1
            elif str(threads).strip().lower() in ["-1", "auto", "1x"] :
                max_workers = num_cores
            elif str(threads).strip().lower() in ["max"] :
                max_workers = num_cores * 8
            elif isinstance(threads, str) and threads.lower().endswith('x'):
                multiplier = int(str(threads).replace('x', '').strip())
                max_workers = int(multiplier * num_cores)
            else:
                max_workers = int(re.sub(r'\D', '', str(threads)))
        except:
            print(f"Warning: invalid threads value '{threads}', defaulting to number of CPU cores ({num_cores})")
            max_workers = num_cores
        
        # Ensure at least 1 thread
        max_workers = max(1, max_workers)
        
        # Prepare arguments - handle both single args and multi-args
        normalized_args = [
            args if isinstance(args, (list, tuple)) else [args] 
            for args in args_list
        ]
        results = [None] * len(normalized_args)

        if len(normalized_args) > 1000000:
            print(f"Warning: This function is not optimized for so many arguments - it will work but may be slow. consider other approaches. ")

        # Execute in parallel with progress bar
        # ToDo - Fix tqdm on Windows Jupyter not updating properly
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks with their index
            future_to_index = {}
            idx_args = list([(idx, args) for idx, args in enumerate(normalized_args)])

            # Prepare futures objects
            iter_obj1 = idx_args if tqdm is None or len(normalized_args) < 50000 else tqdm(idx_args, desc="Preparing", total=len(idx_args))
            for item in iter_obj1:
                idx, args = item
                future_to_index[executor.submit(function_name, *args)] = idx

            # Process completed tasks with tqdm progress bar
            iter_obj2 = as_completed(future_to_index) if tqdm is None else tqdm(as_completed(future_to_index), desc="Processing", total=len(idx_args))
            for future in iter_obj2:
                idx = future_to_index[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    results[idx] = f"Error: {str(e)}"
            
        return results


    @staticmethod
    def run_parallels(function_name, args_list, threads="auto"):
        """Alias for run_parallel"""
        return BlickUtils.run_parallel(function_name, args_list, threads)


    @staticmethod
    def parallel(function_name, args_list, threads="auto"):
        """Alias for run_parallel"""
        return BlickUtils.run_parallel(function_name, args_list, threads)


    @staticmethod
    def parallels(function_name, args_list, threads="auto"):
        """Alias for run_parallel"""
        return BlickUtils.run_parallel(function_name, args_list, threads)


    @staticmethod
    def get_hash(object):
        """
        Get MD5 hash of an object.
        
        Args:
            object: Can be:
                    - File path (str or Path): returns MD5 hash of file contents
                    - Any other object: returns MD5 hash of string representation
                    
        Returns:
            str: MD5 hash as hexadecimal string
        """
        import hashlib
        from pathlib import Path

        md5_hash = hashlib.md5()
        
        # Check if object is a file path
        if isinstance(object, (str, Path)):
            path = Path(object)
            if path.exists() and path.is_file():
                # Read file in chunks for memory efficiency
                with open(path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b''):
                        md5_hash.update(chunk)
                return md5_hash.hexdigest()
        
        # For non-file objects, hash their string representation
        md5_hash.update(str(object).encode('utf-8'))
        return md5_hash.hexdigest()


    @staticmethod
    def zip(input, target=None):
        """
        Zip a string, file, files matching a mask, or directory.
        
        Args:
            input: Can be:
                - String: text to compress (returns compressed base64 string)
                - File path: path to file to zip
                - File mask: pattern like "*.mp4" to zip matching files
                - Directory: path to directory to zip
            target: Output zip file path (optional)
                    - For strings: ignored (returns compressed string)
                    - For files/dirs: if None, uses input name + .zip
                    - Automatically adds .zip extension if missing
                    
        Returns:
            str: For string input: base64 compressed string
                For file/dir input: path to created zip file
        """
        
        import re
        import os
        import zipfile
        import zlib
        import base64
        from pathlib import Path
        from glob import glob
        
        if BlickUtils.is_empty(input):
            print("Input is empty")
            return None
        
        str_in = str(input).strip()

        # Handle file/directory zipping
        is_path = False 
        is_mask = False
        try:
            # Check if input is a file mask
            is_mask = str_in.split(os.path.sep)[-1][0] in ['*', '?']

            input_path = Path(str_in)
            is_path = input_path.exists()
        except Exception as e:
            pass
        
        # Check if input is a string (not a file path nor a Mask)
        if not is_mask and not is_path:
            # Treat as string to compress
            text_bytes = input.encode('utf-8')
            compressed = zlib.compress(text_bytes)
            return base64.b64encode(compressed).decode('utf-8')
        
        # Determine target zip file path if not defined
        if target is None:
            if is_mask:
                # For file masks, use "files.zip" as default
                files_mask = re.sub(r'[\?\*\.]', '', str_in.split(os.path.sep)[-1])
                target = f"files_{files_mask}.zip"
            else:
                target = str(str_in)
        
        # Ensure .zip extension on target
        target_ends = str(target)[-5:]
        target_ends_no_ext = target_ends.split('.')[0]
        target = str(target)[:-5] + target_ends_no_ext + '.zip'
        
        target_path = Path(target)
        os.makedirs(target_path.parent, exist_ok=True)
        
        # Create zip file
        with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            
            # Handle file mask (e.g., "*.mp4")
            if is_mask:
                masked_dir = os.path.sep.join(str_in.split(os.path.sep)[:-1])
                masked_wildcard = '*' if '*' in str_in else '?'
                masked_ext = str(str_in.split(masked_wildcard)[-1]).replace('.', '').strip()
                matched_files = BlickUtils.get_files(directory=masked_dir, ext=f'*.{masked_ext}', recursive=False)
                if not matched_files:
                    print(f"No files match the pattern: {input}")
                    return None

                for file_path in matched_files:
                    file_path = Path(file_path)
                    if file_path.is_file():
                        zipf.write(file_path, file_path.name)
                return str(target_path)

            # Handle directory
            elif input_path.is_dir():
                for root, dirs, files in os.walk(input_path):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(input_path.parent)
                        zipf.write(file_path, arcname)
                return str(target_path)
                    
            # Handle single file
            elif input_path.is_file():
                matched_files = [str(input_path)]
                zipf.write(input_path, input_path.name)
                return str(target_path)
            # Input does not exist
            else:
                print(f"Input does not exist: {input} - Use a valid file, directory, or file mask (i.e.: *.png)")
                return None

        return None


    @staticmethod
    def unzip(input, target_dir=None):
        """
        Unzip a file or decompress a string.
        
        Args:
            input: Can be:
                - Zip file path: path to zip file to extract
                - Compressed string: base64 compressed string to decompress
            target_dir: Target directory for extraction (optional)
                        - For zip files: if None, creates directory with zip filename (without .zip)
                        - For strings: ignored (returns decompressed string)
                        
        Returns:
            str: For compressed string input: decompressed string
                For zip file input: path to target directory
        """
        
        import os
        import zipfile
        from pathlib import Path
        
        if BlickUtils.is_empty(input):
            print("Input is empty")
            return None
        
        str_in = str(input).strip()
        input_path = Path(str_in)
        
        # Check if input is a zip file
        if input_path.exists() and input_path.is_file() and str_in.lower().endswith('.zip'):
            # Determine target directory
            if target_dir is None:
                # Remove .zip extension for directory name
                target_dir = str_in[:-4]
            
            target_path = Path(str(target_dir))
            
            # Create target directory
            os.makedirs(target_path, exist_ok=True)
            
            # Extract zip file
            try:
                with zipfile.ZipFile(input_path, 'r') as zipf:
                    zipf.extractall(target_path)
                return str(target_path)
            except zipfile.BadZipFile:
                print(f"Error: {input} is not a valid zip file")
                return None
            except Exception as e:
                print(f"Error extracting zip file: {str(e)}")
                return None
        
        # Otherwise, treat as compressed string
        else:
            import zlib
            import base64
            try:
                # Decode from base64
                compressed_bytes = base64.b64decode(input)
                
                # Decompress
                decompressed = zlib.decompress(compressed_bytes)
                
                return decompressed.decode('utf-8')
            except Exception as e:
                print(f"Error decompressing string: {str(e)}")
                return None



if __name__ == "__main__":    
    from test import run_tests
    run_tests() 
    