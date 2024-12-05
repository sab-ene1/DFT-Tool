import Navbar from './components/Navbar';
import Hero from './components/Hero';
import Features from './components/Features';
import Documentation from './components/Documentation';
import Roadmap from './components/Roadmap';

import DownloadSection from './components/Download';

function App() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <div className="pt-16">
        <Hero />
        <Features />
        <Documentation />
         
        <Roadmap />
        <DownloadSection />
      </div>
    </div>
  );
}

export default App;