import { CheckCircle2, Circle, Clock } from 'lucide-react';

// Define types for Milestones
type Milestone = {
  title: string;
  description: string;
  status: 'completed' | 'inprogress' | 'default';
  date: string;
};

// Milestones Data
const milestones: Milestone[] = [
  {
    title: 'Foundation',
    description: 'System scanning, file hashing, and metadata extraction implementation',
    status: 'completed',
    date: 'Phase 1',
  },
  {
    title: 'Network Integration',
    description: 'ARP scanning and network information retrieval capabilities',
    status: 'completed',
    date: 'Phase 2',
  },
  {
    title: 'Memory Analysis',
    description: 'Process monitoring and module tracking implementation',
    status: 'completed',
    date: 'Phase 3',
  },
  {
    title: 'Advanced Features',
    description: 'YARA rule implementation and Plotly visualization integration',
    status: 'completed',
    date: 'Phase 4',
  },
  {
    title: 'Machine Learning Integration',
    description: 'Machine learning algorithms for pattern recognition to find anomalies',
    status: 'inprogress',
    date: 'Phase 5',
  },
];

// Get status icon based on status
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="h-6 w-6 text-green-500" />;
    case 'inprogress':
      return <Clock className="h-6 w-6 text-blue-500" />;
    default:
      return <Circle className="h-6 w-6 text-gray-400" />;
  }
};

export default function Roadmap() {
  return (
    <div id="roadmap" className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="lg:text-center mb-16">
          <h2 className="text-base text-blue-600 font-semibold tracking-wide uppercase">Development Roadmap</h2>
          <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
            Building the Future of Digital Forensics
          </p>
          <p className="mt-4 max-w-2xl text-xl text-gray-500 lg:mx-auto">
            Our phased approach to delivering comprehensive forensic capabilities
          </p>
        </div>

        <div className="relative">
          <div className="absolute inset-0 flex items-center" aria-hidden="true">
            <div className="w-full border-t border-gray-300" />
          </div>
          <div className="relative flex justify-between">
            {milestones.map((milestone, index) => (
              <div
                key={index}
                className={`relative bg-white px-4 ${index === 0 ? 'text-left' : index === milestones.length - 1 ? 'text-right' : 'text-center'} flex justify-center items-center`}
              >
                <span className="h-8 flex items-center">
                  {getStatusIcon(milestone.status)}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-8 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {milestones.map((milestone) => (
            <div key={milestone.title} className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-lg font-medium text-gray-900">{milestone.title}</h3>
              <p className="mt-2 text-sm text-gray-500">{milestone.description}</p>
              <p className="mt-4 text-sm font-medium text-blue-600">{milestone.date}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
