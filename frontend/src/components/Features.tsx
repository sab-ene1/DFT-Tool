
import { 
  Search, Shield, Database, Network, 
  Clock, Lock, Terminal, FileSearch,
  BarChart, FileText
} from 'lucide-react';

const features = [
  {
    name: 'Automated Analysis',
    description: 'Comprehensive system scanning, network monitoring, and memory analysis with advanced automation.',
    icon: Search,
  },
  {
    name: 'Machine Learning Integration',
    description: 'Advanced threat detection using machine learning algorithms for pattern recognition.',
    icon: Database,
  },
  {
    name: 'YARA-based Detection',
    description: 'Powerful malware detection using customizable YARA rules for precise identification.',
    icon: Shield,
  },
  {
    name: 'Network Analysis',
    description: 'Deep network traffic inspection with ARP scanning and comprehensive information retrieval.',
    icon: Network,
  },
  {
    name: 'Real-time Processing',
    description: 'Optimized for large-scale data processing with maintained performance.',
    icon: Clock,
  },
  {
    name: 'Evidence Protection',
    description: 'Secure file hashing and metadata extraction for maintaining evidence integrity.',
    icon: Lock,
  },
  {
    name: 'Interactive Visualization',
    description: 'Advanced data visualization using Plotly for comprehensive analysis insights.',
    icon: BarChart,
  },
 
  {
    name: 'Command Line Interface',
    description: 'Powerful CLI for automation and integration with existing security workflows.',
    icon: Terminal,
  },
  {
    name: 'File Analysis',
    description: 'Deep file inspection and metadata analysis for comprehensive investigation.',
    icon: FileSearch,
  },
  {
    name: 'Detailed Reporting',
    description: 'Generate comprehensive reports with interactive visualizations and findings.',
    icon: FileText,
  },
];

export default function Features() {
  return (
    <div id="features" className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="lg:text-center">
          <h2 className="text-base text-blue-600 font-semibold tracking-wide uppercase">Features</h2>
          <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
            Advanced Digital Forensics Capabilities
          </p>
          <p className="mt-4 max-w-2xl text-xl text-gray-500 lg:mx-auto">
            Comprehensive suite of tools designed for modern cyber incident response and investigation.
          </p>
        </div>

        <div className="mt-20">
          <div className="grid grid-cols-1 gap-12 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <div key={feature.name} className="relative group">
                <div className="absolute h-12 w-12 text-blue-600 group-hover:scale-110 transition-transform">
                  <feature.icon className="h-8 w-8" />
                </div>
                <div className="ml-16">
                  <h3 className="text-lg font-medium text-gray-900">{feature.name}</h3>
                  <p className="mt-2 text-base text-gray-500">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}