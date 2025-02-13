import pytest
import numpy as np
from services.clustering import FrequencyClusteringService
from models.clustering import FrequencyData
from services.advanced_analysis import AdvancedSpectralAnalyzer

@pytest.fixture
def clustering_service():
    return FrequencyClusteringService(n_clusters=3)

@pytest.fixture
def sample_data():
    # Generate sample signal with three distinct frequency components
    sampling_rate = 1000  # Hz
    t = np.linspace(0, 1, sampling_rate)
    signal = (
        np.sin(2 * np.pi * 10 * t) +  # 10 Hz
        0.5 * np.sin(2 * np.pi * 20 * t) +  # 20 Hz
        0.25 * np.sin(2 * np.pi * 30 * t)   # 30 Hz
    )
    
    # Compute DFT
    dft = np.fft.fft(signal)
    freqs = np.fft.fftfreq(len(t), 1/sampling_rate)
    magnitudes = np.abs(dft)
    
    return (
        freqs[:len(freqs)//2].tolist(),
        magnitudes[:len(magnitudes)//2].tolist(),
        sampling_rate
    )

def test_clustering_initialization(clustering_service):
    assert clustering_service.n_clusters == 3
    assert clustering_service.batch_size == 1024
    assert clustering_service.kmeans is not None
    assert clustering_service.scaler is not None
    assert clustering_service.advanced_analyzer is not None

def test_frequency_pattern_analysis(clustering_service, sample_data):
    frequencies, magnitudes, sampling_rate = sample_data
    result = clustering_service.analyze_frequency_patterns(
        magnitudes,
        frequencies,
        sampling_rate=sampling_rate
    )
    
    assert result.cluster_centers is not None
    assert len(result.labels) == len(frequencies)
    assert len(result.dominant_frequencies) == 3
    assert result.silhouette_score >= -1 and result.silhouette_score <= 1
    
    # Test new features
    assert result.trend_analysis is None  # No history yet
    assert len(result.cluster_features) == 3
    
    for features in result.cluster_features:
        # Test spectral features
        assert features.spectral_centroid > 0
        assert features.spectral_spread > 0
        assert isinstance(features.spectral_skewness, float)
        assert isinstance(features.spectral_kurtosis, float)
        assert 0 <= features.spectral_flatness <= 1
        assert features.spectral_rolloff > 0
        
        # Test wavelet analysis
        assert features.wavelet_analysis is not None
        assert features.wavelet_analysis.coefficients.shape[1] == len(magnitudes)
        
        # Test harmonic analysis
        assert features.harmonic_analysis is not None
        assert features.harmonic_analysis.fundamental_freq > 0
        assert len(features.harmonic_analysis.harmonics) >= 0
        
        # Test anomaly detection
        assert features.anomaly_detection is not None
        assert isinstance(features.anomaly_detection.anomalies, list)
        assert isinstance(features.anomaly_detection.scores, list)
        assert features.anomaly_detection.threshold > 0

def test_cluster_statistics(clustering_service, sample_data):
    frequencies, magnitudes, sampling_rate = sample_data
    stats = clustering_service.get_cluster_statistics(
        magnitudes,
        frequencies,
        sampling_rate=sampling_rate
    )
    
    assert 'dominant_frequencies' in stats
    assert 'clusters' in stats
    assert len(stats['clusters']) == 3
    
    for cluster in stats['clusters']:
        # Test spectral features
        assert 'spectral_features' in cluster
        spec = cluster['spectral_features']
        assert 'peak_frequencies' in spec
        assert 'peak_magnitudes' in spec
        assert 'bandwidth' in spec
        assert 'spectral_centroid' in spec
        assert 'spectral_spread' in spec
        assert 'spectral_skewness' in spec
        assert 'spectral_kurtosis' in spec
        assert 'spectral_flatness' in spec
        assert 'spectral_rolloff' in spec
        
        # Test wavelet analysis
        assert 'wavelet_analysis' in cluster
        wave = cluster['wavelet_analysis']
        assert 'power_spectrum' in wave
        assert 'frequencies' in wave
        assert 'times' in wave
        
        # Test harmonic analysis
        assert 'harmonic_analysis' in cluster
        harm = cluster['harmonic_analysis']
        assert 'fundamental_frequency' in harm
        assert 'harmonics' in harm
        assert 'harmonic_magnitudes' in harm
        assert 'harmonic_ratios' in harm
        assert 'total_harmonic_distortion' in harm
        
        # Test anomaly detection
        assert 'anomalies' in cluster
        anom = cluster['anomalies']
        assert 'indices' in anom
        assert 'scores' in anom
        assert 'threshold' in anom

def test_trend_analysis(clustering_service, sample_data):
    frequencies, magnitudes, sampling_rate = sample_data
    
    # Analyze multiple times with slightly different data
    for i in range(5):
        # Add some time-varying noise
        noisy_magnitudes = [m * (1 + 0.1 * i * np.random.rand()) for m in magnitudes]
        result = clustering_service.analyze_frequency_patterns(
            noisy_magnitudes,
            frequencies,
            sampling_rate=sampling_rate,
            timestamp=float(i)
        )
        
        if i >= 1:  # Should have trend analysis after first point
            assert result.trend_analysis is not None
            assert 'band_trends' in result.trend_analysis
            assert 'timestamps' in result.trend_analysis
            assert 'total_samples' in result.trend_analysis
            assert result.trend_analysis['total_samples'] == i + 1

def test_input_validation():
    with pytest.raises(ValueError):
        FrequencyData(
            dft_output=[],
            frequencies=[],
            n_clusters=3
        )
    
    with pytest.raises(ValueError):
        FrequencyData(
            dft_output=[1.0, 2.0],
            frequencies=[1.0],
            n_clusters=3
        )
    
    with pytest.raises(ValueError):
        FrequencyData(
            dft_output=[1.0],
            frequencies=[1.0],
            n_clusters=1  # Less than minimum
        )

def test_large_dataset(clustering_service):
    # Generate large dataset
    size = 100000
    sampling_rate = 1000
    frequencies = np.linspace(0, sampling_rate/2, size).tolist()
    magnitudes = np.random.rand(size).tolist()
    
    result = clustering_service.analyze_frequency_patterns(
        magnitudes,
        frequencies,
        sampling_rate=sampling_rate,
        use_cache=False
    )
    
    assert len(result.labels) == size
    assert len(result.cluster_centers) == 3
    assert result.cluster_features is not None
    assert len(result.cluster_features) == 3
