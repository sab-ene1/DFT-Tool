// Data Types
export interface ProcessedData {
  timeData: number[];
  freqData: number[];
  phaseData: number[];
  timeLabels: string[];
  freqLabels: string[];
}

export interface ClusterStats {
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

export interface ClusterData {
  dominant_frequencies: number[];
  clusters: ClusterStats[];
  silhouette_score: number;
}

// Error Types
export class DFTError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DFTError';
  }
}

// Component Props Types
export interface PlotComponentProps {
  data: number[];
  labels: string[];
  title: string;
  xLabel: string;
  yLabel: string;
  clusterCenters?: number[];
  dominantFrequencies?: number[];
}

export interface FileUploaderProps {
  onFileUpload: (files: File[]) => void;
  acceptedFileTypes?: string[];
  maxFileSize?: number;
}

export interface ClusterAnalysisProps {
  clusterData: ClusterData | null;
  isLoading: boolean;
}
