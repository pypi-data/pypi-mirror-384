class BlickCommon:

    # Placeholder for persistent lazy objects
    _BLICK_OBJs = {}


    @staticmethod
    def is_empty(obj):
        """
        Returns True if the object is considered empty (None, empty string, empty list, etc.)
        """
        import re
        
        if obj is None:
            return True

        if str(obj).strip() == '':
            return True
        
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
    def get_urls(text):
        """
        Extract URLs from a given text string.
        
        Args:
            text: Input text string
        Returns:
            List[str]: List of extracted URLs or None if none found
        """
        import re
        
        if BlickCommon.is_empty(text):
            return None
        
        # Lazy use of Regex pattern to match URLs
        url_pattern = BlickCommon._BLICK_OBJs.setdefault(
            'url_pattern', re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        )
        
        try:
            # Find all URLs in the text
            urls = re.findall(url_pattern, str(text))
        
            return urls if urls else None
        except Exception as e:
            return None


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

