import numpy as np
from scipy import signal, stats
import pywt
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import IsolationForest
import pandas as pd
import logging
from utils.exceptions import DFTError

logger = logging.getLogger(__name__)

@dataclass
class WaveletAnalysis:
    """Results of wavelet analysis."""
    coefficients: np.ndarray
    frequencies: np.ndarray
    times: np.ndarray
    power: np.ndarray
    
@dataclass
class HarmonicAnalysis:
    """Results of harmonic analysis."""
    fundamental_freq: float
    harmonics: List[float]
    harmonic_magnitudes: List[float]
    harmonic_ratios: List[float]
    thd: float  # Total Harmonic Distortion

@dataclass
class AnomalyDetection:
    """Results of anomaly detection."""
    anomalies: List[int]  # Indices of anomalous frequencies
    scores: List[float]   # Anomaly scores
    threshold: float      # Threshold used for detection

class AdvancedSpectralAnalyzer:
    def __init__(self):
        self.scaler = RobustScaler()
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        
    def perform_wavelet_analysis(
        self,
        signal_data: np.ndarray,
        sampling_rate: float,
        wavelet: str = 'cmor1.5-1.0'
    ) -> WaveletAnalysis:
        """
        Perform continuous wavelet transform analysis.
        """
        try:
            # Ensure signal data is numpy array
            signal_data = np.asarray(signal_data)
            
            # Calculate scales for desired frequency range
            # Use more conservative frequency ranges to avoid scale issues
            min_freq = max(1, sampling_rate/100)  # Minimum frequency of 1 Hz or sampling_rate/100
            max_freq = sampling_rate/4  # Up to Nyquist/2 to avoid aliasing
            num_freqs = min(32, int(sampling_rate/50))  # Limit number of frequencies
            
            # Use linear spacing for more stable results
            freq_range = np.linspace(
                min_freq,
                max_freq,
                num_freqs
            )
            
            # Calculate scales and ensure they're within valid range
            scales = pywt.frequency2scale(wavelet, freq_range)
            min_scale = 1.0  # Minimum allowed scale
            scales = np.clip(scales, min_scale, None)  # Clip scales to minimum value
            
            # Sort scales in ascending order (required by cwt)
            scales = np.sort(scales)
            
            # Perform CWT
            coefficients, frequencies = pywt.cwt(
                signal_data,
                scales,
                wavelet,
                sampling_period=1/sampling_rate,
                method='conv'  # Use convolution method for better stability
            )
            
            # Calculate time points
            times = np.arange(len(signal_data)) / sampling_rate
            
            # Calculate power spectrum
            power = np.abs(coefficients) ** 2
            
            return WaveletAnalysis(
                coefficients=coefficients,
                frequencies=frequencies,
                times=times,
                power=power
            )
        except Exception as e:
            logger.error(f"Error during wavelet analysis: {e}")
            raise DFTError(f"Wavelet analysis failed: {e}")
    
    def find_peaks(
        self,
        frequencies: np.ndarray,
        magnitudes: np.ndarray,
        height: Optional[float] = None,
        threshold: Optional[float] = None,
        distance: Optional[int] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Find peaks in the frequency spectrum.
        
        Args:
            frequencies: Array of frequency values
            magnitudes: Array of magnitude values
            height: Required height of peaks (default: 10% of max magnitude)
            threshold: Required threshold between peaks (default: None)
            distance: Required distance between peaks in samples (default: None)
            
        Returns:
            Tuple of (peak_frequencies, peak_magnitudes)
        """
        try:
            if height is None:
                height = np.max(magnitudes) * 0.1
                
            # Find peaks
            peak_indices, properties = signal.find_peaks(
                magnitudes,
                height=height,
                threshold=threshold,
                distance=distance
            )
            
            peak_freqs = frequencies[peak_indices]
            peak_mags = magnitudes[peak_indices]
            
            return peak_freqs, peak_mags
        except Exception as e:
            logger.error(f"Error finding peaks: {e}")
            raise DFTError(f"Peak finding failed: {e}")
    
    def detect_harmonics(
        self,
        frequencies: np.ndarray,
        magnitudes: np.ndarray,
        tolerance: float = 0.05
    ) -> HarmonicAnalysis:
        """
        Detect harmonic relationships in frequency components.
        """
        try:
            # Find fundamental frequency (strongest peak)
            peak_indices, _ = signal.find_peaks(magnitudes, height=np.max(magnitudes)*0.1)
            if len(peak_indices) == 0:
                return HarmonicAnalysis(0, [], [], [], 0.0)
                
            fundamental_idx = peak_indices[np.argmax(magnitudes[peak_indices])]
            fundamental_freq = frequencies[fundamental_idx]
            
            # Look for harmonics
            harmonics = []
            harmonic_magnitudes = []
            harmonic_ratios = []
            
            for n in range(2, 11):  # Look for up to 10th harmonic
                expected_freq = n * fundamental_freq
                # Find closest peak to expected frequency
                nearby_peaks = peak_indices[
                    np.abs(frequencies[peak_indices] - expected_freq) < 
                    expected_freq * tolerance
                ]
                
                if len(nearby_peaks) > 0:
                    harmonic_idx = nearby_peaks[
                        np.argmax(magnitudes[nearby_peaks])
                    ]
                    harmonics.append(frequencies[harmonic_idx])
                    harmonic_magnitudes.append(magnitudes[harmonic_idx])
                    harmonic_ratios.append(
                        frequencies[harmonic_idx] / fundamental_freq
                    )
            
            # Calculate Total Harmonic Distortion
            if harmonic_magnitudes:
                thd = np.sqrt(np.sum(np.array(harmonic_magnitudes)**2)) / magnitudes[fundamental_idx]
            else:
                thd = 0.0
                
            return HarmonicAnalysis(
                fundamental_freq=fundamental_freq,
                harmonics=harmonics,
                harmonic_magnitudes=harmonic_magnitudes,
                harmonic_ratios=harmonic_ratios,
                thd=thd
            )
        except Exception as e:
            logger.error(f"Error detecting harmonics: {e}")
            raise DFTError(f"Harmonic detection failed: {e}")
    
    def detect_anomalies(
        self,
        frequencies: np.ndarray,
        magnitudes: np.ndarray,
        threshold_percentile: float = 90.0
    ) -> AnomalyDetection:
        """
        Detect anomalous frequency components using Isolation Forest.

        Parameters:
            frequencies (np.ndarray): Array of frequency values.
            magnitudes (np.ndarray): Array of magnitude values.
            threshold_percentile (float): Percentile used to compute anomaly threshold (default: 90.0).

        Returns:
            AnomalyDetection: Contains anomaly indices, raw scores, and the computed threshold.
        """
        try:
            # Input validation
            if frequencies.size == 0 or magnitudes.size == 0:
                raise ValueError("Input arrays must not be empty.")
            if frequencies.shape[0] != magnitudes.shape[0]:
                raise ValueError("Frequencies and magnitudes must have the same number of elements.")
            
            logger.info(f"Detecting anomalies for {frequencies.size} data points with threshold percentile {threshold_percentile}.")
            
            # Prepare data and scale
            X = np.column_stack([frequencies, magnitudes])
            X_scaled = self.scaler.fit_transform(X)
            
            # Use Isolation Forest for anomaly detection
            preds = self.isolation_forest.fit_predict(X_scaled)
            anomaly_indices = np.where(preds == -1)[0]
            
            # Calculate raw anomaly scores
            scores = self.isolation_forest.score_samples(X_scaled)
            
            # Ensure threshold is non-negative
            threshold = max(np.percentile(scores, threshold_percentile), 0)
            
            logger.info(f"Anomaly detection complete: {len(anomaly_indices)} anomalies found with threshold {threshold:.2f}.")
            
            return AnomalyDetection(
                anomalies=anomaly_indices.tolist(),
                scores=scores.tolist(),
                threshold=threshold
            )
        except Exception as e:
            logger.error(f"Error in detect_anomalies: {e}")
            raise DFTError(f"Anomaly detection failed: {e}")
    
    def calculate_bandwidth(
        self,
        frequencies: np.ndarray,
        magnitudes: np.ndarray,
        threshold: float = 0.707  # -3dB point
    ) -> float:
        """
        Calculate the bandwidth of the signal.
        
        Args:
            frequencies: Array of frequency values
            magnitudes: Array of magnitude values
            threshold: Power threshold for bandwidth calculation (default: 0.707 for -3dB)
            
        Returns:
            Bandwidth in Hz
        """
        try:
            if len(frequencies) < 2:
                return 0.0
                
            # Normalize magnitudes
            max_mag = np.max(magnitudes)
            if max_mag == 0:
                return 0.0
                
            norm_magnitudes = magnitudes / max_mag
            
            # Find points above threshold
            mask = norm_magnitudes >= threshold
            if not np.any(mask):
                return 0.0
                
            # Get frequency range
            freq_range = frequencies[mask]
            if len(freq_range) < 2:
                return 0.0
                
            return freq_range[-1] - freq_range[0]
        except Exception as e:
            logger.error(f"Error calculating bandwidth: {e}")
            raise DFTError(f"Bandwidth calculation failed: {e}")
    
    def analyze_trends(
        self,
        frequency_series: List[np.ndarray],
        magnitude_series: List[np.ndarray],
        timestamps: List[float]
    ) -> Dict[str, Any]:
        """
        Analyze trends in frequency content over time.
        """
        try:
            # Convert to DataFrame for easier analysis
            data = []
            for i, (freqs, mags, ts) in enumerate(zip(frequency_series, magnitude_series, timestamps)):
                for f, m in zip(freqs, mags):
                    data.append({
                        'timestamp': ts,
                        'frequency': f,
                        'magnitude': m,
                        'sample_index': i
                    })
            
            df = pd.DataFrame(data)
            
            # Group by frequency bands
            freq_bands = [(0, 10), (10, 100), (100, 1000), (1000, np.inf)]
            band_trends = {}
            
            for low, high in freq_bands:
                mask = (df['frequency'] >= low) & (df['frequency'] < high)
                band_df = df[mask]
                
                if not band_df.empty:
                    # Calculate trend statistics
                    mean_magnitude = band_df.groupby('sample_index')['magnitude'].mean()
                    peak_magnitude = band_df.groupby('sample_index')['magnitude'].max()
                    total_power = band_df.groupby('sample_index')['magnitude'].apply(
                        lambda x: np.sum(x**2)
                    )
                    
                    trend_stats = {}
                    
                    # Calculate trend direction and strength for each metric
                    for name, values in [
                        ('mean_magnitude', mean_magnitude),
                        ('peak_magnitude', peak_magnitude),
                        ('total_power', total_power)
                    ]:
                        values = values.values
                        if len(values) > 1:
                            slope, intercept = np.polyfit(range(len(values)), values, 1)
                            r_squared = np.corrcoef(range(len(values)), values)[0, 1]**2
                        else:
                            slope, intercept, r_squared = 0, 0, 0
                            
                        trend_stats[name] = values
                        trend_stats[f'{name}_trend'] = {
                            'slope': float(slope),
                            'intercept': float(intercept),
                            'r_squared': float(r_squared)
                        }
                    
                    band_trends[f'{low}-{high}Hz'] = trend_stats
            
            return {
                'band_trends': band_trends,
                'timestamps': timestamps,
                'total_samples': len(frequency_series)
            }
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            raise DFTError(f"Trend analysis failed: {e}")
