import { Book, Terminal, FileText, HelpCircle } from 'lucide-react';

const docs = [
  {
    title: 'Getting Started',
    description: 'Quick setup guide and basic usage instructions',
    icon: Book,
    link: '#',
  },
  {
    title: 'CLI Reference',
    description: 'Complete command line interface documentation',
    icon: Terminal,
    link: '#',
  },
  {
    title: 'User Manual',
    description: 'Detailed documentation of all features and capabilities',
    icon: FileText,
    link: '#',
  },
  {
    title: 'FAQs',
    description: 'Common questions and troubleshooting guides',
    icon: HelpCircle,
    link: '#',
  },
];

export default function Documentation() {
  return (
    <div id="documentation" className="py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="lg:text-center">
          <h2 className="text-base text-blue-600 font-semibold tracking-wide uppercase">Documentation</h2>
          <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
            Learn how to use Forensics Triage
          </p>
          <p className="mt-4 max-w-2xl text-xl text-gray-500 lg:mx-auto">
            Comprehensive documentation to help you get the most out of our tools
          </p>
        </div>

        <div className="mt-16">
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {docs.map((doc) => (
              <div
                key={doc.title}
                className="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-blue-500 rounded-lg shadow-sm hover:shadow-md transition-shadow"
              >
                <div>
                  <span className="rounded-lg inline-flex p-3 bg-blue-50 text-blue-600 ring-4 ring-white">
                    <doc.icon className="h-6 w-6" aria-hidden="true" />
                  </span>
                </div>
                <div className="mt-8">
                  <h3 className="text-lg font-medium">
                    <a href={doc.link} className="focus:outline-none">
                      <span className="absolute inset-0" aria-hidden="true" />
                      {doc.title}
                    </a>
                  </h3>
                  <p className="mt-2 text-sm text-gray-500">
                    {doc.description}
                  </p>
                </div>
                <span
                  className="pointer-events-none absolute top-6 right-6 text-gray-300 group-hover:text-gray-400"
                  aria-hidden="true"
                >
                  <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20 4h1a1 1 0 00-1-1v1zm-1 12a1 1 0 102 0h-2zM8 3a1 1 0 000 2V3zM3.293 19.293a1 1 0 101.414 1.414l-1.414-1.414zM19 4v12h2V4h-2zm1-1H8v2h12V3zm-.707.293l-16 16 1.414 1.414 16-16-1.414-1.414z" />
                  </svg>
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}