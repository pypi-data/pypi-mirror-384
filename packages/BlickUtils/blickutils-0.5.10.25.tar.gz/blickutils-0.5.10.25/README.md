# blick_utils
Blick Technologies Python Utilities

## 1 - Installation

```bash
pip install git+https://github.com/horstao/blick_utils.git
```

## 2 - Usage

```python
from blick_utils import BlickUtils as bkt

# Returns GPU info 
gpu_info = bkt.get_gpu_info()

# Returns torch device GPU or CPU
device = bkt.get_gpu()

# Get a Pillow image from anything (URL, path, array, or base64)
pil_im = bkt.get_pil(url="https://example.com/image.jpg")
pil_im = bkt.get_pil(path="/path/to/image.jpg")
pil_im = bkt.get_pil(array=numpy_array)
pil_im = bkt.get_pil(base64=base64_string)

# Get all files in a Directory
files = bkt.get_files(dir="/path/to/dir", extensions=[".py", ".txt"], recursive=True)

# Get all directories in a Directory
dirs = bkt.get_dirs(dir="/path/to/dir", recursive=True)
```

## Requirements

- Python >= 3.7
- torch (for GPU utilities)
- Pillow (for image utilities)
- numpy (for image array handling)
- requests (for URL image loading)

## License

MIT License