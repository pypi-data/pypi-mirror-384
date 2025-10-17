from common import BlickCommon


class BlickFiles():
    

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
        
        if BlickCommon.is_empty(directory):
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
            extensions = ['*.' + str(e).strip().replace('*','').replace('.','') for e in ext if not BlickCommon.is_empty(e)]
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
        
        if BlickCommon.is_empty(directory):
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
        if BlickCommon.is_empty(parent):
            return None
        return parent 


    @staticmethod
    def get_parent_dir(filename):
        """Alias for get_parent_dir"""
        return BlickFiles.get_parent(filename)


    @staticmethod
    def get_parents(filename):
        """
        Returns the full parent directory path of the given file.

        Args:
            filename (str): The full file path.

        Returns:
            str: The full path to the parent directory.
        """
        import os 
        
        parents = os.path.dirname(str(filename))
        if BlickCommon.is_empty(parents):
            return None
        return parents 


    def get_fulldir(filename):
        """ Alias for get_parents """
        return BlickFiles.get_fulldir(filename=filename)
    

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
        
        if BlickCommon.is_empty(input):
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
                matched_files = BlickFiles.get_files(directory=masked_dir, ext=f'*.{masked_ext}', recursive=False)
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
        
        if BlickCommon.is_empty(input):
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

