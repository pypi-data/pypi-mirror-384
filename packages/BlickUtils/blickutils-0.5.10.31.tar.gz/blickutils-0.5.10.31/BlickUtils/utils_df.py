try:
    from .utils_files import BlickFiles
except:
    from utils_files import BlickFiles

class BlickDF():
    
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
        
        files = BlickFiles.get_files(directory=directory, ext=ext, recursive=recursive)
        
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
    def split_df(pd_dataframe, parts):
        """
        Splits a Pandas Datafrane into parts and returns a list of dataframes  
        Args:
            pd_dataframe (Dataframe): Pandas Dataframe
            parts (int): N parts to split the DataFrame into

        Returns:
            list: list of Dataframes
        """
        import numpy as np
        
        # Split the dataframe into roughly equal parts
        return np.array_split(pd_dataframe, parts)              
