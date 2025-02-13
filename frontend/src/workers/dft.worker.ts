// DFT Worker with WebAssembly support
import DFTModule from '../wasm/dft';

interface DFTResult {
  magnitude: number[];
  phase: number[];
}

let wasmModule: any = null;
let dftProcessor: any = null;

// Initialize WebAssembly module
const initWasm = async () => {
  try {
    wasmModule = await DFTModule();
    dftProcessor = new wasmModule.DFTProcessor();
  } catch (err) {
    console.error('Failed to initialize WebAssembly module:', err);
    throw new Error('WebAssembly initialization failed');
  }
};

// Fallback DFT implementation using TypeScript
const performDFTFallback = (signal: Float64Array): DFTResult => {
  const N = signal.length;
  const magnitude = new Float64Array(N);
  const phase = new Float64Array(N);
  const twoPiDivN = (2 * Math.PI) / N;

  for (let k = 0; k < N; k++) {
    let realPart = 0;
    let imagPart = 0;
    for (let n = 0; n < N; n++) {
      const angle = twoPiDivN * k * n;
      realPart += signal[n] * Math.cos(angle);
      imagPart -= signal[n] * Math.sin(angle);
    }
    magnitude[k] = Math.sqrt(realPart * realPart + imagPart * imagPart) / N;
    phase[k] = Math.atan2(-imagPart, realPart);
  }

  return {
    magnitude: Array.from(magnitude),
    phase: Array.from(phase)
  };
};

// Message handler with error boundary and memory cleanup
self.addEventListener('message', async (e: MessageEvent) => {
  const { signal } = e.data;
  
  if (!signal || !Array.isArray(signal)) {
    self.postMessage({ error: 'Invalid input: signal must be an array' });
    return;
  }

  try {
    const startTime = performance.now();
    let result: DFTResult;

    // Try WebAssembly first, fallback to TypeScript implementation
    try {
      if (!wasmModule) {
        await initWasm();
      }
      const wasmResult = dftProcessor.computeDFT(signal);
      result = {
        magnitude: Array.from(wasmResult.magnitudes),
        phase: Array.from(wasmResult.phases)
      };
    } catch (err) {
      console.warn('WebAssembly failed, using fallback:', err);
      result = performDFTFallback(new Float64Array(signal));
    }

    const endTime = performance.now();
    
    self.postMessage({ 
      result: result.magnitude,
      phase: result.phase,
      processingTime: endTime - startTime
    });

  } catch (err) {
    console.error('DFT calculation error:', err);
    self.postMessage({ 
      error: err instanceof Error ? err.message : 'Unknown error in DFT calculation'
    });
  } finally {
    // Clean up memory
    if (globalThis.gc) {
      globalThis.gc();
    }
  }
});
