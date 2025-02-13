"""Benchmarking script for the Digital Forensics Triage Tool."""

import numpy as np
import time
import matplotlib.pyplot as plt
from typing import List, Tuple
import json
import os
import logging
from utils.exceptions import DFTError

logger = logging.getLogger(__name__)

def generate_test_signal(size: int, frequencies: List[float]) -> np.ndarray:
    """Generate a test signal with given frequencies."""
    t = np.linspace(0, 1, size)
    signal = np.zeros_like(t)
    for f, amp in frequencies:
        signal += amp * np.sin(2 * np.pi * f * t)
    return signal

def benchmark_dft(sizes: List[int], frequencies: List[Tuple[float, float]]) -> dict:
    """Benchmark DFT performance for different input sizes."""
    try:
        results = {
            'sizes': sizes,
            'wasm_times': [],
            'js_times': [],
            'numpy_times': []
        }
        
        for size in sizes:
            signal = generate_test_signal(size, frequencies)
            
            # Benchmark NumPy FFT (as baseline)
            start_time = time.time()
            _ = np.fft.fft(signal)
            numpy_time = time.time() - start_time
            results['numpy_times'].append(numpy_time)
            
            # Save signal for JS/WASM benchmarking
            np.savetxt(f'test_signal_{size}.txt', signal)
        
        return results
    except Exception as e:
        logger.error(f"Error during DFT benchmarking: {e}")
        raise DFTError(f"DFT benchmarking failed: {e}")

def plot_results(results: dict, output_dir: str):
    """Plot benchmark results."""
    try:
        plt.figure(figsize=(10, 6))
        plt.plot(results['sizes'], results['wasm_times'], 'b-', label='WebAssembly')
        plt.plot(results['sizes'], results['js_times'], 'r-', label='JavaScript')
        plt.plot(results['sizes'], results['numpy_times'], 'g-', label='NumPy FFT')
        plt.xlabel('Signal Size')
        plt.ylabel('Time (seconds)')
        plt.title('DFT Performance Comparison')
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(output_dir, 'dft_benchmark.png'))
        plt.close()
    except Exception as e:
        logger.error(f"Error during plotting results: {e}")
        raise DFTError(f"Plotting results failed: {e}")

def main():
    """Run benchmarks and plot results."""
    try:
        # Test parameters
        sizes = [128, 256, 512, 1024, 2048, 4096, 8192]
        frequencies = [
            (10, 1.0),   # 10 Hz with amplitude 1.0
            (20, 0.5),   # 20 Hz with amplitude 0.5
            (30, 0.25)   # 30 Hz with amplitude 0.25
        ]
        
        # Create output directory
        output_dir = 'benchmark_results'
        os.makedirs(output_dir, exist_ok=True)
        
        # Run benchmarks
        results = benchmark_dft(sizes, frequencies)
        
        # Save results
        with open(os.path.join(output_dir, 'benchmark_results.json'), 'w') as f:
            json.dump(results, f, indent=2)
        
        # Plot results
        plot_results(results, output_dir)
        
        print("Benchmark completed. Results saved in 'benchmark_results' directory.")
    except Exception as e:
        logger.error(f"Error during benchmarking: {e}")
        raise DFTError(f"Benchmarking failed: {e}")

if __name__ == '__main__':
    main()
