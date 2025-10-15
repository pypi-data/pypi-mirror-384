"""GPU Manager - CUDA device management and optimization utilities."""

try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    cp = None
    CUPY_AVAILABLE = False

class GPUManager:
    """Manage CUDA devices and provide optimization utilities."""
    
    def __init__(self):
        self.devices = []
        self.best_device = 0
        
        if CUPY_AVAILABLE:
            try:
                if cp.cuda.is_available():
                    self._detect_devices()
            except Exception as e:
                print(f"CUDA not available: {e}")
                # CUDA not available, use CPU-only mode
    
    def _detect_devices(self):
        """Detect available CUDA devices."""
        device_count = cp.cuda.runtime.getDeviceCount()
        for i in range(device_count):
            props = cp.cuda.runtime.getDeviceProperties(i)
            device_info = {
                'id': i,
                'name': props['name'].decode(),
                'compute_capability': f"{props['computeCapabilityMajor']}.{props['computeCapabilityMinor']}",
                'total_memory': props['totalGlobalMem'],
                'multiprocessors': props['multiProcessorCount']
            }
            self.devices.append(device_info)
        
        # Select best device (most multiprocessors)
        if self.devices:
            self.best_device = max(self.devices, key=lambda x: x['multiprocessors'])['id']
    
    def get_device_count(self) -> int:
        """Get number of available CUDA devices."""
        return len(self.devices)
    
    def get_best_device(self) -> int:
        """Get ID of best CUDA device."""
        return self.best_device
    
    def set_device(self, device_id: int):
        """Set active CUDA device."""
        if CUPY_AVAILABLE and 0 <= device_id < len(self.devices):
            cp.cuda.Device(device_id).use()
    
    def get_memory_info(self, device_id: int = 0):
        """Get memory information for device."""
        if CUPY_AVAILABLE and self.devices:
            free, total = cp.cuda.runtime.memGetInfo()
            return {'free': free, 'total': total, 'used': total - free}
        return None
    
    def optimize_for_size(self, data_size: int) -> int:
        """Select optimal device based on data size and available memory."""
        if not self.devices:
            return 0
        
        # Simple heuristic: choose device with most free memory
        best_device = 0
        max_free_memory = 0
        
        for device in self.devices:
            mem_info = self.get_memory_info(device['id'])
            if mem_info and mem_info['free'] > max_free_memory:
                max_free_memory = mem_info['free']
                best_device = device['id']
        
        return best_device

# Global GPU manager instance
_gpu_manager = None

def get_gpu_manager():
    """Get singleton GPU manager instance."""
    global _gpu_manager
    if _gpu_manager is None:
        _gpu_manager = GPUManager()
    return _gpu_manager