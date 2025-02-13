import unittest
import numpy as np
from scipy import signal
from services.advanced_analysis import (
    AdvancedSpectralAnalyzer,
    WaveletAnalysis,
    HarmonicAnalysis,
    AnomalyDetection
)

class TestAdvancedSpectralAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = AdvancedSpectralAnalyzer()
        self.sampling_rate = 1000  # 1 kHz
        self.duration = 1.0  # 1 second
        self.t = np.linspace(0, self.duration, int(self.sampling_rate * self.duration))
        
        # Create test signal with known components
        f1, f2, f3 = 10, 50, 100  # Hz
        self.test_signal = (
            np.sin(2 * np.pi * f1 * self.t) +  # Fundamental
            0.5 * np.sin(2 * np.pi * f2 * self.t) +  # First harmonic
            0.25 * np.sin(2 * np.pi * f3 * self.t)  # Second harmonic
        )
        
        # Add some noise
        self.test_signal += np.random.normal(0, 0.1, len(self.test_signal))
        
        # Calculate frequency spectrum
        self.freqs = np.fft.fftfreq(len(self.t), 1/self.sampling_rate)
        self.fft = np.abs(np.fft.fft(self.test_signal))
        self.freqs = self.freqs[:len(self.freqs)//2]
        self.fft = self.fft[:len(self.fft)//2]
        
    def test_wavelet_analysis(self):
        result = self.analyzer.perform_wavelet_analysis(
            self.test_signal,
            self.sampling_rate
        )
        
        self.assertIsInstance(result, WaveletAnalysis)
        self.assertTrue(hasattr(result, 'coefficients'))
        self.assertTrue(hasattr(result, 'frequencies'))
        self.assertTrue(hasattr(result, 'times'))
        self.assertTrue(hasattr(result, 'power'))
        
        # Check dimensions
        self.assertEqual(len(result.times), len(self.test_signal))
        self.assertTrue(result.power.shape[1] == len(self.test_signal))
        
    def test_harmonic_analysis(self):
        result = self.analyzer.detect_harmonics(
            self.freqs,
            self.fft,
            tolerance=0.1
        )
        
        self.assertIsInstance(result, HarmonicAnalysis)
        self.assertTrue(hasattr(result, 'fundamental_freq'))
        self.assertTrue(hasattr(result, 'harmonics'))
        self.assertTrue(hasattr(result, 'harmonic_magnitudes'))
        self.assertTrue(hasattr(result, 'harmonic_ratios'))
        self.assertTrue(hasattr(result, 'thd'))
        
        # Check fundamental frequency detection (should be close to 10 Hz)
        self.assertAlmostEqual(result.fundamental_freq, 10.0, delta=1.0)
        
        # Check harmonics detection
        self.assertTrue(len(result.harmonics) > 0)
        
    def test_anomaly_detection(self):
        # Add an anomaly to the signal
        anomaly_idx = len(self.fft) // 2
        self.fft[anomaly_idx] *= 10
        
        result = self.analyzer.detect_anomalies(
            self.freqs,
            self.fft
        )
        
        self.assertIsInstance(result, AnomalyDetection)
        self.assertTrue(hasattr(result, 'anomalies'))
        self.assertTrue(hasattr(result, 'scores'))
        self.assertTrue(hasattr(result, 'threshold'))
        
        # Check if anomaly was detected
        self.assertTrue(len(result.anomalies) > 0)
        
    def test_trend_analysis(self):
        # Create multiple signals with varying characteristics
        signals = []
        timestamps = []
        for i in range(5):
            # Vary amplitude and frequency over time
            amp = 1.0 + 0.1 * i
            freq = 10.0 + i
            t = self.t
            signal = amp * np.sin(2 * np.pi * freq * t)
            freqs = np.fft.fftfreq(len(t), 1/self.sampling_rate)[:len(t)//2]
            fft = np.abs(np.fft.fft(signal))[:len(t)//2]
            signals.append(freqs)
            timestamps.append(i)
            
        result = self.analyzer.analyze_trends(
            signals,
            [np.abs(s) for s in signals],
            timestamps
        )
        
        self.assertIsInstance(result, dict)
        self.assertTrue('band_trends' in result)
        self.assertTrue('timestamps' in result)
        self.assertTrue('total_samples' in result)
        
        # Check band trends
        for band, trends in result['band_trends'].items():
            self.assertTrue('mean_magnitude' in trends)
            self.assertTrue('peak_magnitude' in trends)
            self.assertTrue('total_power' in trends)
            
if __name__ == '__main__':
    unittest.main()
