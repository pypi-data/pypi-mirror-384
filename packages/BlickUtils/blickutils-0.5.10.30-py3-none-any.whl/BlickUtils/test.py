import os 
import time

from pathlib import Path
from glob import glob
import tempfile
import shutil

from core import BlickUtils as bkt


def run_tests():
    
    print(f"Running BlickUtils version {bkt.version()} tests...\n")

    bkt.get_methods()
    
    # Test get_gpu_info and get_device
    gpu_info = bkt.get_gpu_info()
    print(f"get_gpu_info(): {gpu_info}")
    assert gpu_info is not None, "get_gpu_info() should return a value"
    
    device = bkt.get_device()
    print(f"get_device(): {device}")
    assert device is not None, "get_device() should return a device"
    
    # Test get_urls
    urls = bkt.get_urls('bla bla bla https://google.com blabla http://test.de/test.png')
    print(f'get_urls(): {urls}')
    assert isinstance(urls, list), "get_urls() should return a list"
    assert len(urls) == 2, "get_urls() should find 2 URLs"
    assert 'https://google.com' in urls, "Should find https://google.com"
    assert 'http://test.de/test.png' in urls, "Should find http://test.de/test.png"

    # Test get_pil with invalid input
    invalid_pil = bkt.get_pil('jkjshkadf')
    print(f'get_pil(invalid): {invalid_pil}')
    assert invalid_pil is None, "get_pil() should return None for invalid input"
    
    # Test get_pil with URL
    url_pil = bkt.get_pil('http://archive.net.im/images/TV.png')
    print(f'get_pil(url): {url_pil.size}')
    assert url_pil is not None, "get_pil() should load image from URL"
    assert isinstance(url_pil.size, tuple), "PIL Image should have a size tuple"
    assert len(url_pil.size) == 2, "Image size should be (width, height)"
    
    # Test get_pil with base64
    base64_sample = 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==' 
    b64_im1 = bkt.get_pil(base64_sample)
    print(f'get_pil(base64): {b64_im1.size}')
    assert b64_im1 is not None, "get_pil() should decode base64 image"
    assert b64_im1.size == (1, 1), "Sample GIF should be 1x1 pixels"
    
    # Test get_base64
    base64_generated = bkt.get_base64(b64_im1)
    print(f'get_base64(): {base64_generated[:50]}...')
    assert isinstance(base64_generated, str), "get_base64() should return a string"
    assert base64_generated.startswith('data:image'), "Base64 should have proper data URI prefix"
    
    # Add tests for autocrop
        
    
    # Test round-trip: base64 -> PIL -> base64
    im2 = bkt.get_pil(base64_generated)
    print(f'get_pil(generated base64): {im2.size}')
    assert im2 is not None, "get_pil() should decode generated base64"
    assert im2.size == b64_im1.size, "Round-trip should preserve image dimensions"
    
    # Test get_files
    files = bkt.get_files()
    print(f'get_files(): {files}')
    assert isinstance(files, list), "get_files() should return a list"
    
    # Add test for get_parent, get_parents, get_filename
    
    # Test get_dirs
    dirs = bkt.get_dirs()
    print(f'get_dirs(): {dirs}')
    assert isinstance(dirs, list), "get_dirs() should return a list"
    
    # Test dir2df
    df = bkt.dir2df('.')
    print(f'dir2df(): {df.shape}')
    assert df is not None, "dir2df() should return a dataframe"
    assert len(df) > 0, "Dataframe should have rows"
    
    # Add test for split_df
    
    # Test execute_cmd
    cmd = "ls -lah"
    res_code, res_out = bkt.execute_cmd(cmd)
    print('execute_cmd():')
    print(f'  Command: {cmd}')
    print(f'  Exit Code: {res_code}')
    print(f'  Output: {res_out.strip().splitlines()[0]}...')
    assert res_code == 0, "ls command should succeed"
    assert isinstance(res_out, str), "Command output should be a string"
    assert len(res_out) > 0, "Command output should not be empty"
    
    # Test function 1: Single argument
    def square(x):
        time.sleep(0.1)
        return x * x
    
    # Test function 2: Multiple arguments
    def multiply(x, y):
        time.sleep(0.1)
        return x, y, x * y
    
    def test_cmd(cmd):
        time.sleep(0.05)
        return bkt.execute_cmd(cmd)
    
    # Test 1: Single argument function with simple list
    print("Generating multhreaded test data...")
    N = 1000
    cands = list(range(N))
    print("Test 1: Single argument function with simple list")
    results = bkt.run_parallel(square, cands, threads="16x")
    print(f"Results: {len(results)}")
    assert results == [x**2 for x in range(N)], "Parallel square should return correct values"
    
    # Test 2: Multiple argument function with list of lists
    N=1000
    print("Test 2: Multiple argument function with list of lists")
    pairs = [[n, n+1] for n in range(N)]
    exp_results = [(n, n+1, n*(n+1)) for n in range(N)]
    results = bkt.run_parallel(multiply, pairs, "max")
    print(f"Results: {len(results)}")
    assert results == exp_results, "Parallel multiply should return correct values"
    
    # Test 3: Using 8x threads
    print("Test 3: Using 8x threads")
    results = bkt.run_parallel(square, range(100), threads="8x")
    print(f"Results: {len(results)} items")
    assert len(results) == 100, "Should have 100 results"
    assert results[10] == 100, "square(10) should be 100"
    assert results[99] == 9801, "square(99) should be 9801"
    
    # Test 4: Command execution in parallel
    print("Test 4: Command execution in parallel")
    commands = ["echo Hello", "echo World", "echo Test"]
    results = bkt.run_parallel(test_cmd, commands, threads=3)
    assert len(results) == 3, "Should have 3 results"
    for i, (code, output) in enumerate(results):
        print(f"Command {i}: exit_code={code}, output={output.strip()}")
        assert code == 0, f"Command {i} should succeed"
        assert isinstance(output, str), f"Command {i} output should be a string"

    # Test get_hash
    hash_val = bkt.get_hash('Hello World!')
    print(f'get_hash(str): {hash_val}')
    assert isinstance(hash_val, str), "get_hash() should return a string"
    assert len(hash_val) > 0, "Hash should not be empty"
    
    print('Test zip')

    # Create temporary directory for testing
    temp_dir = Path(tempfile.mkdtemp())
        
    try:
        # Test 1: Zip a string
        print("Test 1: Zip a string")
        text = "Hello World! " * 100
        compressed = bkt.zip(text)
        print(f"Original length: {len(text)}")
        print(f"Compressed length: {len(compressed)}")
        print(f"Compressed (first 50 chars): {compressed[:50]}...\n")
        assert isinstance(compressed, str), "Compressed string should be string"
        assert len(compressed) < len(text), "Compressed should be smaller than original"
        
        # Test 2: Zip a single file
        print("Test 2: Zip a single file")
        test_file = temp_dir / "test.txt"
        test_file.write_text("This is a test file.")
        zip_path = bkt.zip(str(test_file))
        print(f"Created zip: {zip_path}\n")
        assert os.path.exists(zip_path), "Zip file should be created"
        assert zip_path.endswith('.zip'), "Output should be a zip file"
        
        # Test 3: Zip a single file with custom target
        print("Test 3: Zip a single file with custom target")
        zip_path = bkt.zip(str(test_file), target="custom_name")
        print(f"Created zip: {zip_path}\n")
        assert os.path.exists(zip_path), "Custom zip file should be created"
        assert "custom_name" in zip_path, "Custom name should be in zip path"
        
        # Test 4: Zip files matching a mask
        print("Test 4: Zip files matching a mask")
        for i in range(3):
            (temp_dir / f"video{i}.mp4").write_text(f"Video {i}")
        
        zip_path = bkt.zip(str(temp_dir / "*.mp4"))
        print(f"Created zip: {zip_path}\n")
        assert os.path.exists(zip_path), "Wildcard zip file should be created"
        
        # Test 5: Zip a directory
        print("Test 5: Zip a directory")
        test_dir = temp_dir / "my_folder"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("File 1")
        (test_dir / "file2.txt").write_text("File 2")
        
        zip_path = bkt.zip(str(test_dir))
        print(f"Created zip: {zip_path}\n")
        assert os.path.exists(zip_path), "Directory zip file should be created"
        
        # Test 6: Unzip a compressed string
        print("Test 6: Unzip a compressed string")
        original_text = "Hello World! " * 100
        compressed = bkt.zip(original_text)
        decompressed = bkt.unzip(compressed)
        print(f"Original == Decompressed: {original_text == decompressed}")
        print(f"Decompressed (first 50 chars): {decompressed[:50]}...\n")
        assert original_text == decompressed, "Decompressed text should match original"
        
        # Test 7: Unzip a file (auto-create directory)
        print("Test 7: Unzip a file (auto-create directory)")
        test_dir = temp_dir / "test_folder"
        test_dir.mkdir(exist_ok=True)
        (test_dir / "file1.txt").write_text("Content 1")
        (test_dir / "file2.txt").write_text("Content 2")
        (test_dir / "file3.txt").write_text("Content 3")
        
        zip_file = bkt.zip(str(test_dir), target=str(temp_dir / "archive.zip"))
        print(f"Created zip: {zip_file}")
        
        extract_dir = bkt.unzip(zip_file)
        print(f"Extracted to: {extract_dir}")
        assert os.path.exists(extract_dir), "Extract directory should be created"
        
        extracted_files = bkt.get_files(os.path.join(extract_dir, 'test_folder'))
        extracted_files = sorted([Path(f).name for f in extracted_files])
        original_files = sorted([f.name for f in test_dir.glob('*') if f.is_file()])
        print(f"Original files: {original_files}")
        print(f"Extracted files: {extracted_files}")
        assert original_files == extracted_files, "File names should match after extraction"
        
        all_contents_match = True
        for file_name in original_files:
            original_content = (test_dir / file_name).read_text()
            extracted_content = Path((os.path.join(extract_dir, 'test_folder', file_name))).read_text()
            if original_content != extracted_content:
                print(f"  Content mismatch in {file_name}")
                all_contents_match = False
            else:
                print(f"  {file_name}: content matches")
        
        assert all_contents_match, "All file contents should match after extraction"
        print(f"All contents match: {all_contents_match}\n")
        
        # Test 8: Unzip to custom directory
        print("Test 8: Unzip to custom directory")
        extract_dir = bkt.unzip(zip_file, target_dir=str(os.path.join(temp_dir,"custom_extract")))
        extract_dir = os.path.join(extract_dir, 'test_folder')
        read_files = bkt.get_files(extract_dir)
        print(f"Extracted to: {extract_dir} - Total files: {len(read_files)}")
        assert len(read_files) == 3, "Should have 3 extracted files"
        
        extracted_files = sorted([f.name for f in Path(extract_dir).glob('*') if f.is_file()])
        print(f"Extracted files: {extracted_files}")
        assert original_files == extracted_files, "File names should match in custom directory"
        
        all_contents_match = True
        for file_name in original_files:
            original_content = (test_dir / file_name).read_text()
            extracted_content = Path((os.path.join(extract_dir, file_name))).read_text()
            if original_content != extracted_content:
                print(f"  Content mismatch in {file_name}")
                all_contents_match = False
            else:
                print(f"  {file_name}: content matches")
        
        assert all_contents_match, "All file contents should match in custom directory"
        print(f"All contents match: {all_contents_match}\n")
        
        print("All tests completed successfully!")
                
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        for f in glob("*.zip"):
            try:
                os.remove(f)
            except:
                pass    
            

if __name__ == "__main__":    
    run_tests()