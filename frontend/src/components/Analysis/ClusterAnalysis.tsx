import React from 'react';

interface ClusterStats {
  center_frequency: number;
  mean_magnitude: number;
  std_magnitude: number;
  size: number;
}

interface ClusterData {
  dominant_frequencies: number[];
  clusters: ClusterStats[];
}

interface ClusterAnalysisProps {
  clusterData: ClusterData | null;
  isLoading: boolean;
}

const ClusterAnalysis: React.FC<ClusterAnalysisProps> = ({ clusterData, isLoading }) => {
  if (isLoading) {
    return (
      <div className="p-4 bg-white rounded-lg shadow">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (!clusterData) {
    return null;
  }

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">Frequency Cluster Analysis</h3>
      
      <div className="mb-4">
        <h4 className="text-md font-medium mb-2">Dominant Frequencies</h4>
        <div className="flex flex-wrap gap-2">
          {clusterData.dominant_frequencies.map((freq, idx) => (
            <span
              key={idx}
              className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
            >
              {freq.toFixed(2)} Hz
            </span>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <h4 className="text-md font-medium">Cluster Statistics</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {clusterData.clusters.map((cluster, idx) => (
            <div
              key={idx}
              className="p-3 border rounded-lg bg-gray-50"
            >
              <h5 className="font-medium mb-2">Cluster {idx + 1}</h5>
              <div className="space-y-1 text-sm">
                <p>Center Frequency: {cluster.center_frequency.toFixed(2)} Hz</p>
                <p>Mean Magnitude: {cluster.mean_magnitude.toFixed(4)}</p>
                <p>Std Deviation: {cluster.std_magnitude.toFixed(4)}</p>
                <p>Size: {cluster.size} points</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default React.memo(ClusterAnalysis);
