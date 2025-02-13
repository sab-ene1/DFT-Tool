import React, { useMemo, useCallback, useRef, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import zoomPlugin from 'chartjs-plugin-zoom';
import debounce from 'lodash/debounce';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  zoomPlugin
);

interface PlotComponentProps {
  data: number[];
  labels: string[];
  title: string;
  xLabel: string;
  yLabel: string;
  clusterCenters?: number[];
  dominantFrequencies?: number[];
}

const DEBOUNCE_DELAY = 150; // ms
const MAX_VISIBLE_POINTS = 1000;

const PlotComponent: React.FC<PlotComponentProps> = React.memo(({
  data,
  labels,
  title,
  xLabel,
  yLabel,
  clusterCenters,
  dominantFrequencies
}) => {
  const chartRef = useRef<any>(null);

  // Optimize data for visualization
  const optimizedData = useMemo(() => {
    if (data.length <= MAX_VISIBLE_POINTS) return data;

    const stride = Math.ceil(data.length / MAX_VISIBLE_POINTS);
    return data.filter((_, i) => i % stride === 0);
  }, [data]);

  const optimizedLabels = useMemo(() => {
    if (labels.length <= MAX_VISIBLE_POINTS) return labels;

    const stride = Math.ceil(labels.length / MAX_VISIBLE_POINTS);
    return labels.filter((_, i) => i % stride === 0);
  }, [labels]);

  const chartData = useMemo(() => {
    const datasets = [
      {
        label: 'Signal',
        data: optimizedData,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
        pointRadius: optimizedData.length > 500 ? 0 : 1,
        borderWidth: 1.5,
        tension: 0.1,
      }
    ];

    // Add vertical lines for cluster centers if provided
    if (clusterCenters) {
      clusterCenters.forEach((center, index) => {
        const centerIndex = optimizedLabels.findIndex(label => parseFloat(label) >= center);
        if (centerIndex !== -1) {
          datasets.push({
            label: `Cluster ${index + 1} Center`,
            data: Array(optimizedLabels.length).fill(null),
            borderColor: `rgba(255, 99, ${99 + index * 50}, 0.5)`,
            backgroundColor: `rgba(255, 99, ${99 + index * 50}, 0.5)`,
            pointRadius: 0,
            borderWidth: 2,
            borderDash: [5, 5],
            segment: {
              borderColor: ctx => ctx.p0.skip || ctx.p1.skip ? undefined : `rgba(255, 99, ${99 + index * 50}, 0.5)`,
            },
          });
          datasets[datasets.length - 1].data[centerIndex] = Math.max(...optimizedData);
          datasets[datasets.length - 1].data[centerIndex + 1] = 0;
        }
      });
    }

    // Add markers for dominant frequencies if provided
    if (dominantFrequencies) {
      datasets.push({
        label: 'Dominant Frequencies',
        data: dominantFrequencies.map(freq => {
          const index = optimizedLabels.findIndex(label => parseFloat(label) >= freq);
          return index !== -1 ? optimizedData[index] : null;
        }),
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.5)',
        pointRadius: 5,
        pointStyle: 'star',
        showLine: false,
      });
    }

    return {
      labels: optimizedLabels,
      datasets,
    };
  }, [optimizedData, optimizedLabels, clusterCenters, dominantFrequencies]);

  // Debounced zoom handler
  const handleZoom = useCallback(debounce(() => {
    if (chartRef.current) {
      const chart = chartRef.current;
      const zoomLevel = chart.getZoomLevel();
      const newPointRadius = zoomLevel > 1.5 ? 1 : 0;
      
      chart.data.datasets[0].pointRadius = newPointRadius;
      chart.update('none'); // Update without animation
    }
  }, DEBOUNCE_DELAY), []);

  useEffect(() => {
    const chart = chartRef.current;
    if (chart) {
      chart.options.plugins.zoom.zoom.onZoom = handleZoom;
    }
    return () => {
      handleZoom.cancel();
    };
  }, [handleZoom]);

  const options = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    animation: false, // Disable animations for better performance
    spanGaps: true,
    parsing: false, // Disable parsing for better performance
    normalized: true, // Enable normalized data for better performance
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          boxWidth: 6,
          generateLabels: (chart: any) => {
            const datasets = chart.data.datasets;
            return datasets.map((dataset: any, i: number) => ({
              text: dataset.label,
              fillStyle: dataset.backgroundColor,
              hidden: !chart.isDatasetVisible(i),
              lineCap: dataset.borderCapStyle,
              lineDash: dataset.borderDash,
              lineDashOffset: dataset.borderDashOffset,
              lineJoin: dataset.borderJoinStyle,
              lineWidth: dataset.borderWidth,
              strokeStyle: dataset.borderColor,
              pointStyle: dataset.pointStyle || 'circle',
              datasetIndex: i
            }));
          }
        }
      },
      tooltip: {
        enabled: true,
        mode: 'nearest',
        intersect: false,
        animation: false,
      },
      title: {
        display: true,
        text: title
      },
      zoom: {
        pan: {
          enabled: true,
          mode: 'xy' as const,
          modifierKey: 'ctrl',
        },
        zoom: {
          wheel: {
            enabled: true,
            modifierKey: 'ctrl',
          },
          pinch: {
            enabled: true
          },
          mode: 'xy' as const,
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: xLabel
        },
        ticks: {
          maxTicksLimit: 20,
          callback: (value: any) => {
            const label = optimizedLabels[value];
            return label ? parseFloat(label).toFixed(2) : '';
          }
        }
      },
      y: {
        title: {
          display: true,
          text: yLabel
        },
        ticks: {
          maxTicksLimit: 10
        }
      }
    }
  }), [title, xLabel, yLabel, optimizedLabels]);

  return (
    <div style={{ height: '400px' }}>
      <Line ref={chartRef} data={chartData} options={options} />
    </div>
  );
});

PlotComponent.displayName = 'PlotComponent';

export default PlotComponent;
