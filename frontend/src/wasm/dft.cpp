#include <emscripten/bind.h>
#include <emscripten/val.h>
#include <vector>
#include <cmath>
#include <complex>

using namespace emscripten;

class DFTProcessor {
private:
    std::vector<std::complex<double>> twiddle_factors;
    
    void precompute_twiddle_factors(size_t N) {
        twiddle_factors.resize(N);
        const double theta = -2.0 * M_PI / N;
        for (size_t k = 0; k < N; k++) {
            twiddle_factors[k] = std::polar(1.0, theta * k);
        }
    }

public:
    val compute_dft(const std::vector<double>& signal) {
        const size_t N = signal.size();
        precompute_twiddle_factors(N);
        
        std::vector<double> magnitudes(N);
        std::vector<double> phases(N);
        std::vector<std::complex<double>> X(N);

        #pragma omp parallel for
        for (size_t k = 0; k < N; k++) {
            std::complex<double> sum(0.0, 0.0);
            for (size_t n = 0; n < N; n++) {
                sum += signal[n] * twiddle_factors[(k * n) % N];
            }
            X[k] = sum / static_cast<double>(N);
            magnitudes[k] = std::abs(X[k]);
            phases[k] = std::arg(X[k]);
        }

        val result = val::object();
        result.set("magnitudes", val::array(magnitudes));
        result.set("phases", val::array(phases));
        return result;
    }
};

EMSCRIPTEN_BINDINGS(dft_module) {
    class_<DFTProcessor>("DFTProcessor")
        .constructor<>()
        .function("computeDFT", &DFTProcessor::compute_dft);
        
    register_vector<double>("Vector");
}
