/*
 * Simple TEN VAD Python bindings
 */
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>

extern "C" {
#include "ten_vad.h"
}

namespace py = pybind11;

class VAD {
private:
    ten_vad_handle_t handle;
    size_t hop_size;

public:
    VAD(size_t hop_size = 256, float threshold = 0.5f) : hop_size(hop_size) {
        if (ten_vad_create(&handle, hop_size, threshold) != 0) {
            throw std::runtime_error("Failed to create VAD");
        }
    }

    ~VAD() {
        ten_vad_destroy(&handle);
    }

        std::pair<float, bool> process(py::array_t<int16_t> audio) {
        py::buffer_info buf = audio.request();

        // Validate input size matches hop_size
        if (buf.size != hop_size) {
            throw std::invalid_argument(
                "Audio data size (" + std::to_string(buf.size) +
                ") must match hop_size (" + std::to_string(hop_size) + ")"
            );
        }

        float prob;
        int flag;

        int result = ten_vad_process(handle,
            static_cast<int16_t*>(buf.ptr),
            buf.size, &prob, &flag);

        if (result != 0) {
            throw std::runtime_error("VAD processing failed");
        }

        return {prob, flag != 0};
    }

    const char* version() const {
        return ten_vad_get_version();
    }
};

PYBIND11_MODULE(ten_vad_python, m) {
    m.doc() = "TEN Voice Activity Detection";

    py::class_<VAD>(m, "VAD")
        .def(py::init<size_t, float>(),
             py::arg("hop_size") = 256, py::arg("threshold") = 0.5f)
        .def("process", &VAD::process, "Process audio frame")
        .def("version", &VAD::version, "Get version");
}
