import { jest } from '@jest/globals';

describe('DFT Worker', () => {
  let worker: Worker;

  beforeEach(() => {
    worker = new Worker(new URL('../workers/dft.worker.ts', import.meta.url));
  });

  afterEach(() => {
    worker.terminate();
  });

  test('should process valid signal data', (done) => {
    const signal = Array.from({ length: 1024 }, (_, i) => 
      Math.sin(2 * Math.PI * i / 1024) + 
      0.5 * Math.sin(4 * Math.PI * i / 1024)
    );

    worker.onmessage = (e) => {
      const { result, phase, processingTime } = e.data;
      expect(result).toBeDefined();
      expect(result.length).toBe(signal.length);
      expect(phase).toBeDefined();
      expect(phase.length).toBe(signal.length);
      expect(processingTime).toBeGreaterThan(0);
      
      // Check for expected frequency peaks
      const maxMagnitudes = result
        .map((mag: number, i: number) => ({ mag, i }))
        .sort((a: any, b: any) => b.mag - a.mag)
        .slice(0, 2);
      
      // First peak should be at frequency index 1 (fundamental)
      expect(maxMagnitudes[0].i).toBe(1);
      // Second peak should be at frequency index 2 (first harmonic)
      expect(maxMagnitudes[1].i).toBe(2);
      
      done();
    };

    worker.postMessage({ signal });
  });

  test('should handle invalid input', (done) => {
    worker.onmessage = (e) => {
      expect(e.data.error).toBeDefined();
      expect(e.data.error).toContain('Invalid input');
      done();
    };

    worker.postMessage({ signal: null });
  });

  test('should handle empty signal', (done) => {
    worker.onmessage = (e) => {
      expect(e.data.error).toBeDefined();
      expect(e.data.error).toContain('Invalid input');
      done();
    };

    worker.postMessage({ signal: [] });
  });

  test('should handle large signals', (done) => {
    const signal = Array.from({ length: 1000000 }, (_, i) => 
      Math.sin(2 * Math.PI * i / 1000000)
    );

    worker.onmessage = (e) => {
      const { result, phase, processingTime } = e.data;
      expect(result).toBeDefined();
      expect(result.length).toBe(signal.length);
      expect(phase).toBeDefined();
      expect(phase.length).toBe(signal.length);
      expect(processingTime).toBeGreaterThan(0);
      done();
    };

    worker.postMessage({ signal });
  });
});
