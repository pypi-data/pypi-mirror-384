import os 
import time

from pathlib import Path
from glob import glob
import tempfile
import shutil

from core import BlickUtils as bkt



def run_tests():
    
    print("Running BlickUtils tests...\n")
    print('get_gpu_info(): ', bkt.get_gpu_info())
    print('get_device(): ', bkt.get_device())
    print('get_pil(invalid): ', bkt.get_pil('jkjshkadf'))
    print('get_pil(url): ', bkt.get_pil('http://archive.net.im/images/TV.png').size)
    print('get_pil(base64): ', bkt.get_pil('data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==').size)
    print('get_files(): ', bkt.get_files())
    print('get_dirs(): ', bkt.get_dirs())
    print('dir2df(): \n', bkt.dir2df('.'))

    # Execute command
    cmd = "ls -lah"
    res_code, res_out = bkt.execute_cmd(cmd)
    print('execute_cmd():')
    print(f'  Command: {cmd}')
    print(f'  Exit Code: {res_code}')
    print(f'  Output: {'\n'.join(res_out.strip().splitlines()) }')
    
    # Parallel execution tests:
    
    # Test function 1: Single argument
    def square(x):
        time.sleep(0.5)  # Simulate some work
        return x * x
    
    # Test function 2: Multiple arguments
    def multiply(x, y):
        time.sleep(0.5)  # Simulate some work
        return x, y, x * y
    
    def test_cmd(cmd):
        time.sleep(0.2)
        return bkt.execute_cmd(cmd)
        
    print("Test 1: Single argument function with simple list")
    results = bkt.run_parallel(square, [1, 2, 3, 4, 5], threads="auto")
    print(f"Results: {results}\n")
    
    print("Test 2: Multiple argument function with list of lists")
    results = bkt.run_parallel(multiply, [[2, 3], [4, 5], [6, 7]], threads=2)
    print(f"Results: {results}\n")
    
    print("Test 3: Using 8x threads")
    results = bkt.run_parallel(square, range(100), threads="8x")
    print(f"Results: {results}\n")
    
    print("Test 4: Command execution in parallel")
    commands = ["echo Hello", "echo World", "echo Test"]
    results = bkt.run_parallel(test_cmd, commands, threads=3)
    for i, (code, output) in enumerate(results):
        print(f"Command {i}: exit_code={code}, output={output.strip()}")

    print('get_hash(str): ', bkt.get_hash('Hello World!'))
    
    print('Test zip')


    # Create temporary directory for testing

    temp_dir = Path(tempfile.mkdtemp())
        
    try:
        print("Test 1: Zip a string")
        text = "Hello World! " * 100
        compressed = bkt.zip(text)
        print(f"Original length: {len(text)}")
        print(f"Compressed length: {len(compressed)}")
        print(f"Compressed (first 50 chars): {compressed[:50]}...\n")
        
        print("Test 2: Zip a single file")
        test_file = temp_dir / "test.txt"
        test_file.write_text("This is a test file.")
        zip_path = bkt.zip(str(test_file))
        print(f"Created zip: {zip_path}\n")
        
        print("Test 3: Zip a single file with custom target")
        zip_path = bkt.zip(str(test_file), target="custom_name")
        print(f"Created zip: {zip_path}\n")
        
        print("Test 4: Zip files matching a mask")
        # Create multiple test files
        for i in range(3):
            (temp_dir / f"video{i}.mp4").write_text(f"Video {i}")
        
        zip_path = bkt.zip(str(temp_dir / "*.mp4"))
        print(f"Created zip: {zip_path}\n")
        
        print("Test 5: Zip a directory")
        test_dir = temp_dir / "my_folder"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("File 1")
        (test_dir / "file2.txt").write_text("File 2")
        
        zip_path = bkt.zip(str(test_dir))
        print(f"Created zip: {zip_path}\n")
        
        print("Test 6: Unzip a compressed string")
        original_text = "Hello World! " * 100
        compressed = bkt.zip(original_text)
        decompressed = BlickUtils.unzip(compressed)
        print(f"Original == Decompressed: {original_text == decompressed}")
        print(f"Decompressed (first 50 chars): {decompressed[:50]}...\n")
        
        print("Test 7: Unzip a file (auto-create directory)")
        # Create test files and zip them
        test_dir = temp_dir / "test_folder"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("Content 1")
        (test_dir / "file2.txt").write_text("Content 2")
        (test_dir / "file3.txt").write_text("Content 3")
        
        zip_file = bkt.zip(str(test_dir), target=str(temp_dir / "archive.zip"))
        print(f"Created zip: {zip_file}")
        
        # Unzip with auto directory name
        extract_dir = bkt.unzip(zip_file)
        print(f"Extracted to: {extract_dir}")
        
        # Verify extracted files
        extracted_files = bkt.get_files(os.path.join(extract_dir, 'test_folder'))
        extracted_files = sorted([Path(f).name for f in extracted_files])
        original_files = sorted([f.name for f in test_dir.glob('*') if f.is_file()])
        print(f"Original files: {original_files}")
        print(f"Extracted files: {extracted_files}")
        print(f"File names match: {original_files == extracted_files}")
        
        # Verify file contents
        all_contents_match = True
        for file_name in original_files:
            original_content = (test_dir / file_name).read_text()
            extracted_content = Path((os.path.join(extract_dir, 'test_folder', file_name))).read_text()
            if original_content != extracted_content:
                print(f"  Content mismatch in {file_name}")
                all_contents_match = False
            else:
                print(f"  {file_name}: content matches")
        
        print(f"All contents match: {all_contents_match}\n")
        
        print("Test 8: Unzip to custom directory")
        extract_dir = bkt.unzip(zip_file, target_dir=str(os.path.join(temp_dir,"custom_extract")))
        extract_dir = os.path.join(extract_dir, 'test_folder')
        read_files = bkt.get_files(extract_dir)
        print(f"Extracted to: {extract_dir} - Total files: {len(read_files)}")
        
        # Verify extracted files in custom directory
        extracted_files = sorted([f.name for f in Path(extract_dir).glob('*') if f.is_file()])
        print(f"Extracted files: {extracted_files}")
        print(f"File names match: {original_files == extracted_files}")
        
        # Verify file contents in custom directory
        all_contents_match = True
        for file_name in original_files:
            original_content = (test_dir / file_name).read_text()
            extracted_content = Path((os.path.join(extract_dir, file_name))).read_text()
            if original_content != extracted_content:
                print(f"  Content mismatch in {file_name}")
                all_contents_match = False
            else:
                print(f"  {file_name}: content matches")
        
        print(f"All contents match: {all_contents_match}\n")
        
        print("All tests completed successfully!")
                
    finally:
        pass
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        # Clean up created zip files
        for f in glob("*.zip"):
            try:
                os.remove(f)
            except:
                pass    