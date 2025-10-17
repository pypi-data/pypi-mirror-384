
class BlickProcess():
    
    @staticmethod
    def execute_cmd(cmd, working_dir='.', timeout=120):
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
        return BlickProcess.run_parallel(function_name, args_list, threads)



