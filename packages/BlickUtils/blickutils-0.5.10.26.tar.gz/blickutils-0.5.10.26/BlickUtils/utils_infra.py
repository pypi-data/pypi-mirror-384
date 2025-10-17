
class BlickInfra:
    """ Infrastructure utils"""
    
    @staticmethod
    def get_cpu():
        """" 
            Gets CPU usage percentage for each core and calculate average 
            
            Returns:
                dict: Dictionary containing GPU information or error message        
        """
        import psutil 
        import platform
        import numpy as np
        
        per_cpu_usage = psutil.cpu_percent(interval=0.5, percpu=True)
        cpu_vals = np.array(per_cpu_usage)
        
        cpu_name = platform.processor()
        if "AMD64" in cpu_name:
            n=1
            top_n = np.partition(cpu_vals, -1*n)[(-1*n):]
            max_usage = int(top_n.mean())/100
        else:
            max_usage = int(cpu_vals.mean())/100
        
        # Calculate average of top 3 cores
        # avg_usage = int(top3.mean())/100
        #max_usage = int(cpu_vals.max())/100

        return {
            "cpu_name": platform.processor(),
            "cores": psutil.cpu_count(logical=True),
            "cpu_usage_perc": max_usage
        }

    @staticmethod
    def get_mem():
        """" 
            Gets Memory usage percentage for each core and calculate average 
            
            Returns:
                dict: Dictionary containing GPU information or error message        
        """

        import psutil 

        mem = psutil.virtual_memory()
        mem_perc = int(mem.percent) /100
        mem_use = int(mem.used / (1024 * 1024))
        total_mb = int(mem.total / (1024 * 1024))
        return mem_perc, mem_use, total_mb
        
        
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
            print(f"Warning: install GPUtil for better GPU info: pip install GPUtil")
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
                pass

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
        return BlickInfra.get_gpu(id)


    @staticmethod
    def get_device(id=0):
        """Alias for get_gpu to maintain compatibility"""
        return BlickInfra.get_gpu(id)

    