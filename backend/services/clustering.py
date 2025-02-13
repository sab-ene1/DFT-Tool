from sklearn.cluster import KMeans, MiniBatchKMeans, DBSCAN, SpectralClustering
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from sklearn.decomposition import PCA
from scipy import signal, stats
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
import json
from services.advanced_analysis import (
    AdvancedSpectralAnalyzer,
    WaveletAnalysis,
    HarmonicAnalysis,
    AnomalyDetection
)

@dataclass
class SignalFeatures:
    """Features extracted from frequency data."""
    peak_frequencies: List[float]
    peak_magnitudes: List[float]
    bandwidth: float
    spectral_centroid: float
    spectral_spread: float
    spectral_skewness: float
    spectral_kurtosis: float
    spectral_flatness: float
    spectral_rolloff: float
    wavelet_analysis: Optional[WaveletAnalysis] = None
    harmonic_analysis: Optional[HarmonicAnalysis] = None
    anomaly_detection: Optional[AnomalyDetection] = None

@dataclass
class ClusterResult:
    cluster_centers: List[float]
    labels: List[int]
    dominant_frequencies: List[float]
    silhouette_score: float
    calinski_score: float
    cluster_features: List[SignalFeatures]
    trend_analysis: Optional[Dict[str, Any]] = None

class FrequencyClusteringService:
    def __init__(self, n_clusters: int = 3, batch_size: int = 1024):
        self.n_clusters = n_clusters
        self.batch_size = batch_size
        self.scaler = RobustScaler()
        self.advanced_analyzer = AdvancedSpectralAnalyzer()
        
        # Clustering algorithms
        self.kmeans = MiniBatchKMeans(
            n_clusters=n_clusters,
            batch_size=batch_size,
            init='k-means++',
            n_init=3,
            random_state=42
        )
        
        self.dbscan = DBSCAN(
            eps=0.3,
            min_samples=5,
            n_jobs=-1
        )
        
        self.spectral = SpectralClustering(
            n_clusters=n_clusters,
            random_state=42,
            n_jobs=-1
        )
        
        # Store historical data for trend analysis
        self.historical_data = {
            'frequencies': [],
            'magnitudes': [],
            'timestamps': []
        }
        
    def _preprocess_data(
        self,
        dft_output: List[float],
        frequencies: List[float],
        sampling_rate: Optional[float] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Enhanced preprocessing with additional cleaning steps."""
        frequencies = np.array(frequencies)
        dft_output = np.array(dft_output)
        X = np.column_stack((frequencies, dft_output))
        
        # Create mask for filtering
        mask = np.ones(len(frequencies), dtype=bool)
        
        # Remove DC component and very high frequencies
        if sampling_rate:
            nyquist = sampling_rate / 2
            mask = (frequencies != 0) & (frequencies < nyquist * 0.95)
        
        # Scale the features
        scaler = RobustScaler()
        X_filtered = X[mask]
        X_scaled = scaler.fit_transform(X_filtered)
        
        return X_scaled, X_filtered, mask
    
    def _calculate_spectral_features(
        self,
        frequencies: np.ndarray,
        magnitudes: np.ndarray
    ) -> SignalFeatures:
        """Calculate various spectral features."""
        total_power = np.sum(magnitudes)
        if total_power == 0:
            return SignalFeatures([], [], 0, 0, 0, 0, 0, 0, 0)
            
        # Normalize magnitudes
        norm_magnitudes = magnitudes / total_power
        
        # Spectral centroid (weighted mean of frequencies)
        centroid = np.sum(frequencies * norm_magnitudes)
        
        # Spectral spread (variance around centroid)
        spread = np.sqrt(np.sum(((frequencies - centroid) ** 2) * norm_magnitudes))
        
        # Spectral skewness
        skewness = stats.skew(norm_magnitudes)
        
        # Spectral kurtosis
        kurtosis = stats.kurtosis(norm_magnitudes)
        
        # Spectral flatness
        flatness = stats.gmean(magnitudes + 1e-10) / (np.mean(magnitudes) + 1e-10)
        
        # Spectral rolloff (frequency below which 85% of power is concentrated)
        cumsum = np.cumsum(norm_magnitudes)
        rolloff = frequencies[np.searchsorted(cumsum, 0.85)]
        
        # Find peaks
        peak_freqs, peak_mags = self.advanced_analyzer.find_peaks(frequencies, magnitudes)
        
        # Calculate bandwidth
        bandwidth = self.advanced_analyzer.calculate_bandwidth(frequencies, magnitudes)
        
        return SignalFeatures(
            peak_frequencies=peak_freqs.tolist(),
            peak_magnitudes=peak_mags.tolist(),
            bandwidth=float(bandwidth),
            spectral_centroid=float(centroid),
            spectral_spread=float(spread),
            spectral_skewness=float(skewness),
            spectral_kurtosis=float(kurtosis),
            spectral_flatness=float(flatness),
            spectral_rolloff=float(rolloff)
        )
    
    def _select_best_clustering(self, X_scaled: np.ndarray) -> Tuple[np.ndarray, str]:
        """Select best clustering method based on validation scores."""
        results = []
        
        # Try different clustering methods
        try:
            # K-means
            kmeans_labels = self.kmeans.fit_predict(X_scaled)
            kmeans_score = silhouette_score(X_scaled, kmeans_labels)
            results.append(('kmeans', kmeans_labels, kmeans_score))
        except:
            pass
            
        try:
            # DBSCAN
            dbscan_labels = self.dbscan.fit_predict(X_scaled)
            if len(set(dbscan_labels)) > 1:  # Only if multiple clusters found
                dbscan_score = silhouette_score(X_scaled, dbscan_labels)
                results.append(('dbscan', dbscan_labels, dbscan_score))
        except:
            pass
            
        try:
            # Spectral Clustering
            spectral_labels = self.spectral.fit_predict(X_scaled)
            spectral_score = silhouette_score(X_scaled, spectral_labels)
            results.append(('spectral', spectral_labels, spectral_score))
        except:
            pass
            
        if not results:
            return self.kmeans.fit_predict(X_scaled), 'kmeans'
            
        # Select best method
        best_method = max(results, key=lambda x: x[2])
        return best_method[1], best_method[0]
    
    def analyze_frequency_patterns(
        self,
        dft_output: List[float],
        frequencies: List[float],
        sampling_rate: Optional[float] = None,
        timestamp: Optional[float] = None,
        use_cache: bool = True
    ) -> ClusterResult:
        """Enhanced frequency pattern analysis with advanced features."""
        # Convert inputs to numpy arrays
        dft_output = np.array(dft_output)
        frequencies = np.array(frequencies)
        
        # Preprocess data
        X_scaled, X_filtered, mask = self._preprocess_data(
            dft_output, frequencies, sampling_rate
        )
        
        # Store data for trend analysis
        if timestamp is not None:
            self.historical_data['frequencies'].append(X_filtered[:, 0])
            self.historical_data['magnitudes'].append(X_filtered[:, 1])
            self.historical_data['timestamps'].append(timestamp)
        
        # Perform clustering on filtered data
        filtered_labels, method = self._select_best_clustering(X_scaled)
        
        # Map labels back to original size
        full_labels = np.zeros(len(frequencies), dtype=int)
        full_labels[mask] = filtered_labels
        full_labels[~mask] = -1  # Mark filtered out points as noise
        
        # Calculate quality scores
        silhouette = silhouette_score(X_scaled, filtered_labels)
        calinski = calinski_harabasz_score(X_scaled, filtered_labels)
        
        # Analyze each cluster
        cluster_features = []
        dominant_frequencies = []
        
        # Perform wavelet and harmonic analysis on full signal once
        if sampling_rate:
            full_wavelet_results = self.advanced_analyzer.perform_wavelet_analysis(
                dft_output, sampling_rate
            )
            full_harmonic_results = self.advanced_analyzer.detect_harmonics(
                frequencies, dft_output
            )
        
        for i in range(len(set(filtered_labels))):
            cluster_mask = filtered_labels == i
            if np.any(cluster_mask):
                cluster_freqs = X_filtered[cluster_mask, 0]
                cluster_mags = X_filtered[cluster_mask, 1]
                
                # Basic spectral features
                features = self._calculate_spectral_features(
                    cluster_freqs, cluster_mags
                )
                
                # Advanced analysis
                if sampling_rate:
                    # Use the full wavelet and harmonic analysis results
                    features.wavelet_analysis = full_wavelet_results
                    features.harmonic_analysis = full_harmonic_results
                    
                    # Anomaly detection
                    anomaly_results = self.advanced_analyzer.detect_anomalies(
                        cluster_freqs, cluster_mags
                    )
                    features.anomaly_detection = anomaly_results
                
                cluster_features.append(features)
                
                # Find dominant frequency
                max_idx = np.argmax(cluster_mags)
                dominant_frequencies.append(float(cluster_freqs[max_idx]))
        
        # Perform trend analysis if we have historical data
        trend_analysis = None
        if len(self.historical_data['timestamps']) > 1:
            trend_analysis = self.advanced_analyzer.analyze_trends(
                self.historical_data['frequencies'],
                self.historical_data['magnitudes'],
                self.historical_data['timestamps']
            )
        
        return ClusterResult(
            cluster_centers=self.kmeans.cluster_centers_.tolist(),
            labels=full_labels.tolist(),  # Use full labels
            dominant_frequencies=dominant_frequencies,
            silhouette_score=float(silhouette),
            calinski_score=float(calinski),
            cluster_features=cluster_features,
            trend_analysis=trend_analysis
        )
    
    def get_cluster_statistics(
        self,
        dft_output: List[float],
        frequencies: List[float],
        sampling_rate: Optional[float] = None,
        timestamp: Optional[float] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive statistical information with advanced analysis."""
        result = self.analyze_frequency_patterns(
            dft_output, frequencies, sampling_rate, timestamp, use_cache
        )
        
        stats = {
            "dominant_frequencies": result.dominant_frequencies,
            "clustering_quality": {
                "silhouette_score": result.silhouette_score,
                "calinski_harabasz_score": result.calinski_score
            },
            "clusters": []
        }
        
        for features in result.cluster_features:
            cluster_stats = {
                "spectral_features": {
                    "peak_frequencies": features.peak_frequencies,
                    "peak_magnitudes": features.peak_magnitudes,
                    "bandwidth": features.bandwidth,
                    "spectral_centroid": features.spectral_centroid,
                    "spectral_spread": features.spectral_spread,
                    "spectral_skewness": features.spectral_skewness,
                    "spectral_kurtosis": features.spectral_kurtosis,
                    "spectral_flatness": features.spectral_flatness,
                    "spectral_rolloff": features.spectral_rolloff
                }
            }
            
            if features.wavelet_analysis:
                cluster_stats["wavelet_analysis"] = {
                    "power_spectrum": features.wavelet_analysis.power.tolist(),
                    "frequencies": features.wavelet_analysis.frequencies.tolist(),
                    "times": features.wavelet_analysis.times.tolist()
                }
            
            if features.harmonic_analysis:
                cluster_stats["harmonic_analysis"] = {
                    "fundamental_frequency": features.harmonic_analysis.fundamental_freq,
                    "harmonics": features.harmonic_analysis.harmonics,
                    "harmonic_magnitudes": features.harmonic_analysis.harmonic_magnitudes,
                    "harmonic_ratios": features.harmonic_analysis.harmonic_ratios,
                    "total_harmonic_distortion": features.harmonic_analysis.thd
                }
            
            if features.anomaly_detection:
                cluster_stats["anomalies"] = {
                    "indices": features.anomaly_detection.anomalies,
                    "scores": features.anomaly_detection.scores,
                    "threshold": features.anomaly_detection.threshold
                }
                
            stats["clusters"].append(cluster_stats)
        
        if result.trend_analysis:
            stats["trend_analysis"] = result.trend_analysis
        
        return stats
