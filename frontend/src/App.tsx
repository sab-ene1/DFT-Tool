import React, { Suspense, lazy } from 'react';
import Navbar from './components/Navbar';

// Lazy load components
const Hero = lazy(() => import('./components/Hero'));
const Features = lazy(() => import('./components/Features'));
const Documentation = lazy(() => import('./components/Documentation'));
const Roadmap = lazy(() => import('./components/Roadmap'));
const DownloadSection = lazy(() => import('./components/Download'));
const DFTWorkspace = lazy(() => import('./components/DFTWorkspace'));

// Loading fallback component
const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-[200px]">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
  </div>
);

const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">DFT Analysis Tool</h1>
        </div>
      </header>
      
      <Navbar />
      
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Suspense fallback={<LoadingFallback />}>
          <div className="space-y-12">
            <Hero />
            <Features />
            <Documentation />
            <Roadmap />
            <DownloadSection />
            <DFTWorkspace />
          </div>
        </Suspense>
      </main>
    </div>
  );
};

export default React.memo(App);