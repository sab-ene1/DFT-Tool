
import { Download, Monitor } from 'lucide-react';

const platforms = [
  {
    name: 'Windows',
    icon: Monitor,
    version: '2.1.0',
    requirements: 'Windows 10 or later',
    link: 'https://www.dropbox.com/scl/fi/a23haa2003eg737cb3st1/VMware-player-full-17.0.2-21581411.exe?rlkey=qfys4feco7f84stj9sbm91l43&st=32f6zl5t&dl=0',
  },

];

export default function DownloadSection() {
  return (
    <div id="download" className="bg-gray-900 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="lg:text-center mb-16">
          <h2 className="text-base text-blue-400 font-semibold tracking-wide uppercase">Download</h2>
          <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-white sm:text-4xl">
            Get Started with Forensics Triage
          </p>
          <p className="mt-4 max-w-2xl text-xl text-gray-400 lg:mx-auto">
            Choose your platform and download the latest version
          </p>
        </div>

        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {platforms.map((platform) => (
            <div
              key={platform.name}
              className="bg-gray-800 rounded-lg p-8 hover:bg-gray-700 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <platform.icon className="h-8 w-8 text-blue-400" />
                  <h3 className="ml-3 text-xl font-medium text-white">{platform.name}</h3>
                </div>
                <span className="text-sm text-gray-400">v{platform.version}</span>
              </div>
              <p className="mt-4 text-gray-400 text-sm">{platform.requirements}</p>
              <a
                href={platform.link}
                className="mt-6 w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                <Download className="h-5 w-5 mr-2" />
                Download
              </a>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <p className="text-gray-400">
            By downloading, you agree to our{' '}
            <a href="#" className="text-blue-400 hover:text-blue-300">
              Terms of Service
            </a>{' '}
            and{' '}
            <a href="#" className="text-blue-400 hover:text-blue-300">
              Privacy Policy
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}