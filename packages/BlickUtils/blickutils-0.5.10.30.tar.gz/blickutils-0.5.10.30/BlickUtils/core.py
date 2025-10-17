try:
    # Try relative imports (for package use)
    from .common import BlickCommon
    from .utils_infra import BlickInfra
    from .utils_files import BlickFiles
    from .utils_image import BlickImage
    from .utils_df import BlickDF
    from .utils_process import BlickProcess
except ImportError:
    # Local Tests
    from common import BlickCommon
    from utils_infra import BlickInfra
    from utils_files import BlickFiles
    from utils_image import BlickImage
    from utils_df import BlickDF
    from utils_process import BlickProcess


class BlickUtils(BlickCommon, BlickFiles, BlickInfra, BlickImage, BlickDF, BlickProcess):
    """
    A collection of static utility methods for Blick Technologies
    """
    # All imports are done on demand to avoid unnecessary dependencies
    # Placeholder for persistent lazy objects
    _BLICK_OBJs = {}
    

    @staticmethod
    def version():
        """ Returns lib version """
        from importlib.metadata import version
        return version("blickutils")        
    
    @staticmethod
    def get_version():
        """Alias for version() """
        return BlickUtils.version       
    
    
    @staticmethod
    def get_methods():
        """ Prints all class methods and their arguments """
        import inspect
        import sys
        current_module = sys.modules[__name__]
        
        print("Available methods:")
        for name, obj in inspect.getmembers(current_module, inspect.isclass):
            if obj.__module__ != __name__:
                continue
                
            for method_name, method in inspect.getmembers(obj):
                if isinstance(inspect.getattr_static(obj, method_name), staticmethod):
                    sig = inspect.signature(method)

                    # Get the first line of docstring
                    doc = inspect.getdoc(method)
                    doc_first_line = doc.split('\n')[0] if doc else ""
                                    
                    print(f"  {method_name}{sig} -> {doc_first_line}")
            return None

    
    @staticmethod
    def get_info():
        """ Prints Lib and System info """
        
        import json

        print('')
        import pprint 
        print(f'BlickUtils v{BlickUtils.version()} - Data Science Swiss Knife')
        print('Version:', BlickUtils.version())
        print('CPU:    ', json.dumps(BlickUtils.get_cpu()))
        print('Mem:    ', json.dumps(BlickUtils.get_mem()))
        print('GPU:    ', json.dumps(BlickUtils.get_gpu_info()))
        return None

    @staticmethod
    def methods():
        """ Alias for get_methods"""
        BlickUtils.get_methods()

    @staticmethod
    def info():
        """ Alias for get_info"""
        BlickUtils.get_info()



if __name__ == "__main__":    
    from test import run_tests
    run_tests() 
    