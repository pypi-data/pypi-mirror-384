import subprocess
import sys

DEBUG = False

def get_cuda_version():
    """Detect CUDA version on system, return as comparable tuple"""
    try:
        result = subprocess.run(['nvcc', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'release' in line:
                    version = line.split('release')[1].strip().split(',')[0]
                    major, minor = version.split('.')
                    return (int(major), int(minor))
    except FileNotFoundError:
        pass
    return None

def get_best_cuda_version(user_cuda_version):
    """Get the best available PyTorch CUDA version for user's system"""
    # Available PyTorch CUDA versions (update this list as needed)
    available_versions = [
        (9, 0, "cu90"),
        (9, 1, "cu91"),
        (9, 2, "cu92"),
        (10, 0, "cu100"),
        (10, 1, "cu101"),
        (10, 2, "cu102"),
        (11, 0, "cu110"),
        (11, 1, "cu111"),
        (11, 3, "cu113"),
        (11, 5, "cu115"),
        (11, 6, "cu116"),
        (11, 7, "cu117"),
        (11, 8, "cu118"),
        (12, 1, "cu121"),
        (12, 4, "cu124"),
        (12, 6, "cu126"), 
        (12, 8, "cu128"),
        (12, 9, "cu129")
    ]
    
    # Find the highest available version that's <= user's version
    compatible_versions = [
        (major, minor, tag) for major, minor, tag in available_versions
        if (major, minor) <= user_cuda_version
    ]
    
    if compatible_versions:
        # Return the highest compatible version
        return max(compatible_versions)[2]
    return None

def install_torch():
    user_cuda = get_cuda_version()
    
    if user_cuda:
        cuda_tag = get_best_cuda_version(user_cuda)
        if cuda_tag:
            print(f"Detected CUDA {user_cuda[0]}.{user_cuda[1]}, installing PyTorch with {cuda_tag}...")
            cmd = [
                sys.executable, "-m", "uv", "pip", "install", 
                "torch", "torchaudio", "--index-url",
                f"https://download.pytorch.org/whl/{cuda_tag}", "--force-reinstall"
            ]
            if DEBUG:
                print(' '.join(cmd))
            else:
                subprocess.check_call(cmd)
            return
    
    print("No compatible CUDA detected, installing CPU-only PyTorch...")
    cmd = [
        sys.executable, "-m", "uv", "pip", "install",
        "torch", "torchaudio"
    ]
    if DEBUG:
        print(' '.join(cmd))
    else:
        subprocess.check_call(cmd)

if __name__ == "__main__":
    install_torch()