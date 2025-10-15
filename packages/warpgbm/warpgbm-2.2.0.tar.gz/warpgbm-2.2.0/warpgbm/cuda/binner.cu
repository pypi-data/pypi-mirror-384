#include <torch/extension.h>
#include <cuda.h>
#include <cuda_runtime.h>

__global__ void bin_column_kernel(
    const float *__restrict__ X,         // [N]
    const float *__restrict__ bin_edges, // [B - 1]
    int8_t *__restrict__ bin_indices,    // [N]
    int N,
    int B_minus1)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= N)
        return;

    float val = X[idx];
    int bin = 0;

    // Linear scan over edges: bin_edges is sorted
    while (bin < B_minus1 && val >= bin_edges[bin])
    {
        ++bin;
    }

    bin_indices[idx] = static_cast<int8_t>(bin);
}

// C++ launcher for calling from Python
void launch_bin_column_kernel(
    at::Tensor X,          // [N]
    at::Tensor bin_edges,  // [B - 1]
    at::Tensor bin_indices // [N]
)
{
    const int N = X.size(0);
    const int B = bin_edges.size(0);

    const int threads = 256;
    const int blocks = (N + threads - 1) / threads;

    bin_column_kernel<<<blocks, threads>>>(
        X.data_ptr<float>(),
        bin_edges.data_ptr<float>(),
        bin_indices.data_ptr<int8_t>(),
        N,
        B);

    // Optional: sync and error check
    cudaError_t err = cudaGetLastError();
    if (err != cudaSuccess)
        printf("CUDA error: %s\n", cudaGetErrorString(err));
}
