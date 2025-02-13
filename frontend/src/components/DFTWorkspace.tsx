import React, { useState, useCallback, useRef, useEffect } from 'react';
import PlotComponent from './Visualization/PlotComponent';
import FileUploader from './FileManagement/FileUploader';
import ClusterAnalysis from './Analysis/ClusterAnalysis';

interface ProcessedData {
  timeData: number[];
  freqData: number[];
  phaseData: number[];
  timeLabels: string[];
  freqLabels: string[];
}

interface ClusterStats {
  center_frequency: number;
  mean_magnitude: number;
  std_magnitude: number;
  median_magnitude: number;
  iqr: number;
  size: number;
  frequency_range: {
    min: number;
    max: number;
  };
}

interface ClusterData {
  dominant_frequencies: number[];
  clusters: ClusterStats[];
  silhouette_score: number;
}

class DFTError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DFTError';
  }
}

const DFTWorkspace: React.FC = () => {
  const [processedData, setProcessedData] = useState<ProcessedData | null>(null);
  const [clusterData, setClusterData] = useState<ClusterData | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isClustering, setIsClustering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const workerRef = useRef<Worker | null>(null);

  // Initialize Web Worker
  const initWorker = useCallback(() => {
    if (!workerRef.current) {
      try {
        workerRef.current = new Worker(
          new URL('../workers/dft.worker.ts', import.meta.url),
          { type: 'module' }
        );

        workerRef.current.onmessage = (e: MessageEvent) => {
          const { result, phase, error, processingTime } = e.data;
          setIsProcessing(false);

          if (error) {
            setError(error);
            return;
          }

          if (result) {
            console.log(`DFT processing time: ${processingTime}ms`);
            const freqLabels = result.map((_: any, i: number) => 
              ((i * (1 / result.length))).toFixed(2)
            );
            
            setProcessedData(prevData => ({
              ...prevData!,
              freqData: result,
              phaseData: phase,
              freqLabels
            }));

            // After DFT is complete, perform clustering
            analyzeFrequencyPatterns(result, freqLabels.map(Number));
          }
        };

        workerRef.current.onerror = (error) => {
          console.error('Worker error:', error);
          setError('Error in DFT calculation');
          setIsProcessing(false);
        };
      } catch (err) {
        console.error('Error creating worker:', err);
        setError('Failed to initialize DFT processor');
        setIsProcessing(false);
      }
    }
  }, []);

  const analyzeFrequencyPatterns = async (dftOutput: number[], frequencies: number[]) => {
    try {
      setIsClustering(true);
      setError(null);
      
      const response = await fetch('http://localhost:8000/analyze-patterns', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          dft_output: dftOutput,
          frequencies: frequencies,
          n_clusters: 3
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Failed to analyze frequency patterns');
      }

      const data = await response.json();
      setClusterData(data.data);
    } catch (err) {
      console.error('Clustering error:', err);
      setError(err instanceof Error ? err.message : 'Error analyzing patterns');
    } finally {
      setIsClustering(false);
    }
  };

  // Cleanup worker on unmount
  useEffect(() => {
    return () => {
      if (workerRef.current) {
        workerRef.current.terminate();
        workerRef.current = null;
      }
    };
  }, []);

  const readFileContent = useCallback((file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target?.result as string);
      reader.onerror = (e) => reject(new DFTError('Error reading file'));
      reader.readAsText(file);
    });
  }, []);

  const parseFileContent = useCallback((content: string): number[] => {
    return content
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0)
      .map(line => {
        const num = parseFloat(line);
        if (isNaN(num)) {
          throw new DFTError('Invalid number in data');
        }
        return num;
      });
  }, []);

  const handleFileUpload = useCallback(async (files: File[]) => {
    const file = files[0];
    if (!file) return;

    try {
      setError(null);
      setIsProcessing(true);
      setClusterData(null);
      initWorker();

      const content = await readFileContent(file);
      const timeData = parseFileContent(content);
      
      if (timeData.length === 0) {
        throw new DFTError('File contains no valid data');
      }
      
      if (timeData.length > 1000000) {
        throw new DFTError('File too large: maximum 1,000,000 points allowed');
      }

      const timeLabels = timeData.map((_, i) => i.toString());

      setProcessedData({
        timeData,
        freqData: [],
        phaseData: [],
        timeLabels,
        freqLabels: []
      });

      // Process DFT in Web Worker
      workerRef.current?.postMessage({ signal: timeData });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      setIsProcessing(false);
      setProcessedData(null);
    }
  }, [initWorker, readFileContent, parseFileContent]);

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Upload Signal Data</h2>
        <FileUploader 
          onFileUpload={handleFileUpload}
          acceptedFileTypes={['.txt', '.csv', '.dat']}
          maxFileSize={10 * 1024 * 1024} // 10MB
        />
        {error && (
          <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-md">
            {error}
          </div>
        )}
        {isProcessing && (
          <div className="mt-4 p-4 bg-blue-50 text-blue-700 rounded-md">
            Processing data...
          </div>
        )}
      </div>

      {processedData && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Time Domain</h3>
              <PlotComponent
                data={processedData.timeData}
                labels={processedData.timeLabels}
                title="Time Domain Signal"
                xLabel="Time"
                yLabel="Amplitude"
              />
            </div>
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Frequency Domain</h3>
              <PlotComponent
                data={processedData.freqData}
                labels={processedData.freqLabels}
                title="Frequency Spectrum"
                xLabel="Frequency (Hz)"
                yLabel="Magnitude"
                clusterCenters={clusterData?.clusters.map(c => c.center_frequency)}
                dominantFrequencies={clusterData?.dominant_frequencies}
              />
            </div>
            {processedData.phaseData.length > 0 && (
              <div className="bg-white shadow rounded-lg p-6 lg:col-span-2">
                <h3 className="text-lg font-semibold mb-4">Phase Spectrum</h3>
                <PlotComponent
                  data={processedData.phaseData}
                  labels={processedData.freqLabels}
                  title="Phase Spectrum"
                  xLabel="Frequency (Hz)"
                  yLabel="Phase (radians)"
                />
              </div>
            )}
          </div>

          <ClusterAnalysis 
            clusterData={clusterData} 
            isLoading={isClustering} 
          />
        </>
      )}
    </div>
  );
};

export default React.memo(DFTWorkspace);
