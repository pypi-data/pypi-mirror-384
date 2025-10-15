import subprocess
import sys
import platform
import os
import time
from typing import List, Optional 
from dataclasses import dataclass
from enum import Enum


class CheckStatus(Enum):
    """Status levels for checks."""
    PASS = "✅"
    WARNING = "⚠️ "
    FAIL = "❌"
    INFO = "ℹ️ "


@dataclass
class CheckResult:
    """Result of a single check."""
    name: str
    status: CheckStatus
    message: str
    details: Optional[str] = None
    suggestions: Optional[List[str]] = None
    is_critical: bool = False


class DependencyChecker:
    """Enhanced dependency checker with comprehensive system validation."""

    def __init__(self):
        self.results: List[CheckResult] = []
        self.start_time = time.time()

    def _add_result(self, result: CheckResult) -> None:
        """Add a check result to the collection."""
        self.results.append(result)

    def check_python_version(self) -> None:
        """Check Python version compatibility."""
        version = sys.version_info
        required_major, required_minor = 3, 8
        
        version_str = f"Python {version.major}.{version.minor}.{version.micro}"
        
        if version.major >= required_major and version.minor >= required_minor:
            details = f"Running {version_str} on {platform.platform()}"
            if version.minor >= 10:
                message = f"Excellent! {version_str} (Latest features supported)"
            else:
                message = f"Good! {version_str} (Compatible)"
        else:
            message = f"Incompatible {version_str}"
            details = f"Requires Python >= {required_major}.{required_minor}"
            suggestions = [
                f"Upgrade to Python {required_major}.{required_minor}+ using your system package manager",
                "Consider using pyenv or conda for Python version management"
            ]
            
            self._add_result(CheckResult(
                name="Python Version",
                status=CheckStatus.FAIL,
                message=message,
                details=details,
                suggestions=suggestions,
                is_critical=True
            ))
            return
        
        self._add_result(CheckResult(
            name="Python Version",
            status=CheckStatus.PASS,
            message=message,
            details=details
        ))

    def check_system_info(self) -> None:
        """Comprehensive system information check."""
        system = platform.system()
        architecture = platform.machine()
        processor = platform.processor() or "Unknown"
        
        # Get detailed system info
        details = []
        suggestions = []
        
        # Check for specific platforms
        platform_info = self._detect_platform()
        if platform_info:
            details.append(platform_info)
        
        # CPU and memory information
        try:
            import psutil
            cpu_count = psutil.cpu_count(logical=False)  # Physical cores
            logical_count = psutil.cpu_count(logical=True)  # Logical cores
            memory_gb = psutil.virtual_memory().total / (1024**3)
            
            details.append(f"{cpu_count} physical cores, {logical_count} logical cores")
            details.append(f"{memory_gb:.1f}GB RAM")
            
            # Memory recommendations
            if memory_gb < 8:
                suggestions.append("Consider upgrading RAM for better training performance (16GB+ recommended)")
            elif memory_gb >= 32:
                details.append("Excellent RAM for large model training")
        except ImportError:
            suggestions.append("Install psutil for detailed system information")
        
        message = f"{system} {architecture}"
        if processor != "Unknown":
            message += f" ({processor})"
        
        status = CheckStatus.PASS
        if suggestions:
            status = CheckStatus.WARNING if memory_gb < 8 else CheckStatus.INFO
        
        self._add_result(CheckResult(
            name="System Information",
            status=status,
            message=message,
            details="\n".join(details) if details else None,
            suggestions=suggestions if suggestions else None
        ))

    def _detect_platform(self) -> Optional[str]:
        """Detect specific hardware platforms."""
        if platform.system() == "Linux":
            # Check for Jetson devices
            jetson_files = [
                "/sys/firmware/devicetree/base/model",
                "/proc/device-tree/model"
            ]
            for jetson_file in jetson_files:
                try:
                    if os.path.exists(jetson_file):
                        with open(jetson_file, 'r') as f:
                            model = f.read().strip()
                            if "jetson" in model.lower():
                                return f"NVIDIA Jetson Platform: {model}"
                except (OSError, IOError):
                    continue
            
            # Check for Raspberry Pi
            try:
                if os.path.exists("/proc/device-tree/model"):
                    with open("/proc/device-tree/model", 'r') as f:
                        model = f.read().strip()
                        if "raspberry pi" in model.lower():
                            return f"Raspberry Pi: {model}"
            except (OSError, IOError):
                pass
        
        return None

    def check_gpu_availability(self) -> None:
        """Enhanced GPU detection and analysis."""
        gpu_details = []
        suggestions = []
        
        # Primary check: PyTorch CUDA
        torch_gpu_info = self._check_pytorch_gpu()
        if torch_gpu_info:
            gpu_details.extend(torch_gpu_info)
        
        # Secondary check: System-level GPU detection
        system_gpu_info = self._check_system_gpu()
        if system_gpu_info and not torch_gpu_info:
            gpu_details.extend(system_gpu_info)
            suggestions.append("GPU detected but not accessible via PyTorch - check CUDA installation")
        
        if not gpu_details:
            # No GPU detected
            suggestions.extend([
                "Training will run on CPU (much slower)",
                "Consider using a system with NVIDIA GPU for optimal performance",
                "For cloud training, try Google Colab, AWS EC2, or similar services"
            ])
            
            self._add_result(CheckResult(
                name="GPU Hardware",
                status=CheckStatus.WARNING,
                message="No GPU detected - CPU training only",
                suggestions=suggestions
            ))
        else:
            # GPU(s) detected
            message = f"Found {len(gpu_details)} GPU(s)"
            self._add_result(CheckResult(
                name="GPU Hardware",
                status=CheckStatus.PASS,
                message=message,
                details="\n".join(gpu_details)
            ))

    def _check_pytorch_gpu(self) -> List[str]:
        """Check GPU availability through PyTorch."""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_info = []
                for i in range(torch.cuda.device_count()):
                    try:
                        device_name = torch.cuda.get_device_name(i)
                        props = torch.cuda.get_device_properties(i)
                        memory_gb = props.total_memory / (1024**3)
                        compute_capability = f"{props.major}.{props.minor}"
                        
                        info = f"GPU {i}: {device_name}"
                        info += f" ({memory_gb:.1f}GB VRAM, Compute {compute_capability})"
                        
                        # Add performance hints
                        if memory_gb >= 24:
                            info += " [Excellent for large models]"
                        elif memory_gb >= 8:
                            info += " [Good for most models]"
                        elif memory_gb < 4:
                            info += " [Limited VRAM - consider smaller models]"
                        
                        gpu_info.append(info)
                    except Exception:
                        gpu_info.append(f"GPU {i}: Available but details unavailable")
                return gpu_info
        except ImportError:
            pass
        return []

    def _check_system_gpu(self) -> List[str]:
        """Check for GPU at system level."""
        gpu_info = []
        
        if platform.system() == "Linux":
            # Check NVIDIA
            if os.path.exists("/proc/driver/nvidia/version"):
                try:
                    with open("/proc/driver/nvidia/version", 'r') as f:
                        driver_info = f.read().strip().split('\n')[0]
                        gpu_info.append(f"NVIDIA Driver: {driver_info}")
                except (OSError, IOError):
                    pass
            
            # Check for GPU devices
            try:
                result = subprocess.run(["lspci", "-nn"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    gpu_lines = [line for line in lines if 'VGA' in line or 'Display' in line or '3D' in line]
                    for line in gpu_lines:
                        if 'NVIDIA' in line or 'AMD' in line or 'Intel' in line:
                            gpu_info.append(f"System GPU: {line.split(':')[-1].strip()}")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        return gpu_info

    def check_cuda_installation(self) -> None:
        """Comprehensive CUDA installation check."""
        cuda_info = []
        suggestions = []
        status = CheckStatus.FAIL
        
        # Check PyTorch CUDA
        try:
            import torch
            if torch.cuda.is_available():
                cuda_version = getattr(torch.version, 'cuda', 'Unknown')
                cuda_info.append(f"PyTorch CUDA: {cuda_version}")
                status = CheckStatus.PASS
            elif hasattr(torch.version, 'cuda') and torch.version.cuda:
                cuda_info.append(f"PyTorch compiled with CUDA {torch.version.cuda} but runtime unavailable")
                suggestions.append("Check NVIDIA driver installation and GPU compatibility")
                status = CheckStatus.WARNING
        except ImportError:
            suggestions.append("Install PyTorch with CUDA support")
        
        # Check system CUDA installation
        cuda_paths = self._find_cuda_installations()
        if cuda_paths:
            cuda_info.extend(cuda_paths)
            if status == CheckStatus.FAIL:
                status = CheckStatus.WARNING
        
        # Check CUDA runtime libraries
        runtime_info = self._check_cuda_runtime()
        if runtime_info:
            cuda_info.append(runtime_info)
        
        if status == CheckStatus.FAIL:
            suggestions.extend([
                "Install NVIDIA CUDA Toolkit from https://developer.nvidia.com/cuda-downloads",
                "Ensure NVIDIA drivers are properly installed",
                "Verify GPU compatibility with CUDA"
            ])
            message = "CUDA not available - GPU training disabled"
        elif status == CheckStatus.WARNING:
            message = "CUDA partially available - may have issues"
        else:
            message = "CUDA properly configured"
        
        self._add_result(CheckResult(
            name="CUDA Support",
            status=status,
            message=message,
            details="\n".join(cuda_info) if cuda_info else None,
            suggestions=suggestions if suggestions else None,
            is_critical=(status == CheckStatus.FAIL and cuda_info)  # Critical if GPU present but CUDA broken
        ))

    def _find_cuda_installations(self) -> List[str]:
        """Find CUDA installations on the system."""
        cuda_info = []
        
        if platform.system() == "Windows":
            cuda_paths = [
                "C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA",
                "C:\\Program Files (x86)\\NVIDIA GPU Computing Toolkit\\CUDA"
            ]
        else:
            cuda_paths = ["/usr/local/cuda", "/opt/cuda", "/usr/cuda"]
        
        for base_path in cuda_paths:
            if os.path.exists(base_path):
                # Find version directories
                try:
                    versions = []
                    if os.path.isdir(base_path):
                        for item in os.listdir(base_path):
                            item_path = os.path.join(base_path, item)
                            if os.path.isdir(item_path) and item.startswith('v'):
                                versions.append(item)
                    
                    if versions:
                        cuda_info.append(f"CUDA Toolkit: {', '.join(sorted(versions))} at {base_path}")
                    else:
                        # Check version file
                        version_file = os.path.join(base_path, "version.txt")
                        if os.path.exists(version_file):
                            with open(version_file, 'r') as f:
                                version = f.read().strip()
                                cuda_info.append(f"CUDA Toolkit: {version}")
                        else:
                            cuda_info.append(f"CUDA Toolkit found at {base_path}")
                except (OSError, IOError):
                    continue
        
        return cuda_info

    def _check_cuda_runtime(self) -> Optional[str]:
        """Check CUDA runtime libraries."""
        if platform.system() != "Windows":
            try:
                result = subprocess.run(
                    ["ldconfig", "-p"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if result.returncode == 0:
                    if "libcudart" in result.stdout:
                        # Extract version if possible
                        lines = result.stdout.split('\n')
                        cudart_lines = [line for line in lines if "libcudart" in line]
                        if cudart_lines:
                            return f"CUDA Runtime: Libraries found ({len(cudart_lines)} entries)"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        return None

    def check_required_packages(self) -> None:
        """Enhanced package checking with version information."""
        packages = {
            # Core ML packages
            'torch': {'import': 'torch', 'critical': True, 'description': 'PyTorch deep learning framework'},
            'torchvision': {'import': 'torchvision', 'critical': True, 'description': 'PyTorch computer vision'},
            'numpy': {'import': 'numpy', 'critical': True, 'description': 'Numerical computing'},
            
            # Computer Vision
            'opencv-python': {'import': 'cv2', 'critical': True, 'description': 'OpenCV computer vision'},
            'pillow': {'import': 'PIL', 'critical': True, 'description': 'Image processing'},
            
            # Communication & Networking
            'grpcio': {'import': 'grpc', 'critical': True, 'description': 'gRPC communication'},
            'protobuf': {'import': 'google.protobuf', 'critical': True, 'description': 'Protocol buffers'},
            'pika': {'import': 'pika', 'critical': False, 'description': 'RabbitMQ client'},
            'requests': {'import': 'requests', 'critical': True, 'description': 'HTTP library'},
            
            # Cloud & Storage
            'boto3': {'import': 'boto3', 'critical': False, 'description': 'AWS SDK'},
            
            # System & Utilities
            'psutil': {'import': 'psutil', 'critical': False, 'description': 'System monitoring'},
            'tqdm': {'import': 'tqdm', 'critical': False, 'description': 'Progress bars'},
        }
        
        installed = []
        missing_critical = []
        missing_optional = []
        package_details = []
        
        for pkg_name, pkg_info in packages.items():
            try:
                module = __import__(pkg_info['import'])
                version = getattr(module, '__version__', 'Unknown')
                installed.append(pkg_name)
                package_details.append(f"{pkg_name} v{version}")
            except ImportError:
                if pkg_info['critical']:
                    missing_critical.append(f"{pkg_name} - {pkg_info['description']}")
                else:
                    missing_optional.append(f"{pkg_name} - {pkg_info['description']}")
        
        # Determine status
        if missing_critical:
            status = CheckStatus.FAIL
            message = f"Missing {len(missing_critical)} critical packages"
            suggestions = [
                "Install missing packages using: pip install " + " ".join([pkg.split(' -')[0] for pkg in missing_critical]),
                "Consider using a virtual environment to manage dependencies"
            ]
        elif missing_optional:
            status = CheckStatus.WARNING
            message = f"All critical packages installed ({len(installed)}/{len(packages)})"
            suggestions = [
                "Install optional packages for full functionality: pip install " + " ".join([pkg.split(' -')[0] for pkg in missing_optional])
            ]
        else:
            status = CheckStatus.PASS
            message = f"All packages installed ({len(packages)}/{len(packages)})"
        
        details = []
        if package_details:
            details.append("Installed packages:")
            details.extend([f"  • {pkg}" for pkg in package_details])
        
        if missing_critical:
            details.append("Missing critical packages:")
            details.extend([f"  • {pkg}" for pkg in missing_critical])
        
        if missing_optional:
            details.append("Missing optional packages:")
            details.extend([f"  • {pkg}" for pkg in missing_optional])
        
        self._add_result(CheckResult(
            name="Python Packages",
            status=status,
            message=message,
            details="\n".join(details) if details else None,
            suggestions=suggestions if missing_critical or missing_optional else None,
            is_critical=bool(missing_critical)
        ))

    def check_disk_space(self) -> None:
        """Enhanced disk space checking."""
        try:
            import psutil
            current_dir = os.getcwd()
            disk_usage = psutil.disk_usage(current_dir)
            
            total_gb = disk_usage.total / (1024**3)
            free_gb = disk_usage.free / (1024**3)
            free_percent = (free_gb / total_gb) * 100
            
            details = f"Total: {total_gb:.1f}GB, Free: {free_gb:.1f}GB ({free_percent:.1f}%)"
            
            # Enhanced status determination
            if free_gb < 2:
                status = CheckStatus.FAIL
                message = "Critical: Very low disk space"
                suggestions = [
                    "Free up disk space immediately",
                    "Training may fail due to insufficient storage",
                    "Consider moving to a system with more storage"
                ]
            elif free_gb < 10:
                status = CheckStatus.WARNING
                message = "Warning: Low disk space"
                suggestions = [
                    "Consider freeing up space before training",
                    "Monitor disk usage during training",
                    "Large models may require 20-50GB+ free space"
                ]
            elif free_gb < 50:
                status = CheckStatus.INFO
                message = "Adequate disk space available"
                suggestions = [
                    "Good for small to medium models",
                    "Large models may need additional space"
                ]
            else:
                status = CheckStatus.PASS
                message = "Excellent disk space available"
            
        except ImportError:
            # Fallback to shutil
            try:
                import shutil
                total, used, free = shutil.disk_usage(os.getcwd())
                free_gb = free / (1024**3)
                total_gb = total / (1024**3)
                
                details = f"Total: {total_gb:.1f}GB, Free: {free_gb:.1f}GB"
                
                if free_gb < 5:
                    status = CheckStatus.WARNING
                    message = "Low disk space detected"
                    suggestions = ["Free up disk space before training"]
                else:
                    status = CheckStatus.PASS
                    message = "Sufficient disk space"
            except Exception as e:
                status = CheckStatus.INFO
                message = "Unable to check disk space"
                details = f"Error: {str(e)}"
                suggestions = ["Manually verify available disk space"]
        
        self._add_result(CheckResult(
            name="Disk Space",
            status=status,
            message=message,
            details=details,
            suggestions=suggestions if status != CheckStatus.PASS else None,
            is_critical=(status == CheckStatus.FAIL)
        ))

    def run_all_checks(self) -> List[CheckResult]:
        """Execute all system checks."""
        print("🔍 Running comprehensive system checks...\n")
        
        checks = [
            ("Python Version", self.check_python_version),
            ("System Info", self.check_system_info),
            ("Disk Space", self.check_disk_space),
            ("GPU Hardware", self.check_gpu_availability),
            ("CUDA Support", self.check_cuda_installation),
            ("Python Packages", self.check_required_packages),
        ]
        
        for i, (name, check_func) in enumerate(checks, 1):
            print(f"[{i}/{len(checks)}] Checking {name}...", end=" ")
            try:
                check_func()
                print("Done")
            except Exception as e:
                print(f"Error: {e}")
                self._add_result(CheckResult(
                    name=name,
                    status=CheckStatus.FAIL,
                    message=f"Check failed: {str(e)}",
                    is_critical=True
                ))
            time.sleep(0.1)  # Brief pause for better UX
        
        return self.results

    def print_detailed_report(self) -> bool:
        """Print a comprehensive, well-formatted report."""
        elapsed = time.time() - self.start_time
        
        print("\n" + "="*70)
        print("🏥 NEDO VISION TRAINING SERVICE - SYSTEM HEALTH REPORT")
        print("="*70)
        print(f"📅 Scan completed in {elapsed:.1f} seconds")
        print(f"🖥️  Platform: {platform.platform()}")
        print("="*70)
        
        # Categorize results
        passed = [r for r in self.results if r.status == CheckStatus.PASS]
        warnings = [r for r in self.results if r.status in [CheckStatus.WARNING, CheckStatus.INFO]]
        failed = [r for r in self.results if r.status == CheckStatus.FAIL]
        critical_failed = [r for r in failed if r.is_critical]
        
        # Print results by category
        for result in self.results:
            print(f"\n{result.status.value} {result.name}")
            print(f"   {result.message}")
            
            if result.details:
                print(f"   Details: {result.details}")
            
            if result.suggestions:
                print("   💡 Suggestions:")
                for suggestion in result.suggestions:
                    print(f"      • {suggestion}")
        
        # Summary
        print("\n" + "="*70)
        print("📊 SUMMARY")
        print("="*70)
        
        print(f"✅ Passed: {len(passed)}")
        print(f"⚠️  Warnings: {len(warnings)}")
        print(f"❌ Failed: {len(failed)}")
        
        if critical_failed:
            print(f"\n🚨 CRITICAL ISSUES: {len(critical_failed)}")
            print("   Service may not function properly!")
            print("   Please address critical issues before proceeding.")
        elif failed:
            print(f"\n⚠️  NON-CRITICAL ISSUES: {len(failed)}")
            print("   Service should work but with limitations.")
        elif warnings:
            print(f"\n💡 RECOMMENDATIONS: {len(warnings)}")
            print("   System ready with minor optimizations possible.")
        else:
            print("\n🎉 SYSTEM READY!")
            print("   All checks passed - optimal configuration detected.")
        
        print("="*70)
        
        return len(critical_failed) == 0


def run_doctor() -> int:
    """Run the dependency doctor and return appropriate exit code."""
    try:
        checker = DependencyChecker()
        results = checker.run_all_checks()
        success = checker.print_detailed_report()
        
        return 0 if success else 1
    
    except KeyboardInterrupt:
        print("\n\n🛑 Health check interrupted by user.")
        return 130
    except Exception as e:
        print(f"\n\n💥 Unexpected error during health check: {e}")
        import traceback
        traceback.print_exc()
        return 1