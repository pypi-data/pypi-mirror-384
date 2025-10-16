// -*- c++ -*-

#include <cuComplex.h>
#include <cuda.h>
#include <cuda_fp16.h>
#include <cuda_runtime.h>
#include <stdexcept>
#include <stdio.h>

#ifndef KSMM
#define KSMM

struct __align__(2) half3
{
  __half x, y, z;
};

struct __align__(8) half4
{
  __half x, y, z, w;
};

struct __align__(32) float8
{
  float x, y, z, w, r, s, t, u;
};

struct __align__(64) double8
{
  double x, y, z, w, r, s, t, u;
};

#if defined(V1)
#define VSIZE 1
#elif defined(V2)
#define VSIZE 2
#elif defined(V3)
#define VSIZE 3
#elif defined(V4)
#define VSIZE 4
#endif

#ifdef USE_FLOAT16
#define SUPPORT_FLOAT16
#endif

#ifdef USE_FLOAT32
#define SUPPORT_FLOAT32
#endif

#ifdef USE_COMPLEX64
#define SUPPORT_COMPLEX64
#define SUPPORT_COMPLEX
#endif

#ifdef USE_FLOAT64
#define SUPPORT_FLOAT64
#endif

#ifdef USE_COMPLEX128
#define SUPPORT_COMPLEX128
#define SUPPORT_COMPLEX
#endif

#ifdef SUPPORT_FLOAT16
typedef __half dtype;
#if defined(V1)
typedef __half dtypex;
#endif
#if defined(V2)
typedef __half2 dtypex;
#endif
#if defined(V3)
typedef half3 dtypex;
#endif
#if defined(V4)
typedef half4 dtypex;
#endif
#endif

#ifdef SUPPORT_FLOAT32
typedef float dtype;
#if defined(V1)
typedef float dtypex;
#endif
#if defined(V2)
typedef float2 dtypex;
#endif
#if defined(V3)
typedef float3 dtypex;
#endif
#if defined(V4)
typedef float4 dtypex;
#endif
#endif

#ifdef SUPPORT_FLOAT64
typedef double dtype;
#if defined(V1)
typedef double dtypex;
#endif
#if defined(V2)
typedef double2 dtypex;
#endif
#if defined(V3)
typedef double3 dtypex;
#endif
#if defined(V4)
typedef double4 dtypex;
#endif
#endif

#ifdef SUPPORT_COMPLEX64
typedef cuFloatComplex dtype;
typedef float elt_t;
#if defined(V1)
typedef cuFloatComplex dtypex;
#endif
#if defined(V2)
typedef float4 dtypex;
#endif
#if defined(V3)
typedef float4 dtypex;
#endif
#if defined(V4)
typedef float8 dtypex;
#endif
#endif

#ifdef SUPPORT_COMPLEX128
typedef cuDoubleComplex dtype;
typedef double elt_t;
#if defined(V1)
typedef cuDoubleComplex dtypex;
#endif
#if defined(V2)
typedef double4 dtypex;
#endif
#if defined(V3)
typedef double4 dtypex;
#endif
#if defined(V4)
typedef double8 dtypex;
#endif
#endif

#define loadx(a, b)                                                            \
  reinterpret_cast<dtypex *>(&a)[0] = reinterpret_cast<dtypex *>(&b)[0]

__device__ inline void rload(dtype *a, dtype *b, int idx1, int idx2) {
#if defined(V1)
  a[idx1] = b[idx2];
#else
#if defined(SUPPORT_COMPLEX) && defined(V3)
  // No float6 and double6 structures.
  loadx(a[idx1], b[idx2]);
  a[idx1 + 2] = b[idx2 + 2];
#else
  loadx(a[idx1], b[idx2]);
#endif
#endif
}  

#ifdef SUPPORT_COMPLEX
__device__ inline void make_cuXComplex(dtype &dst, elt_t r, elt_t i) {
#if defined(SUPPORT_COMPLEX64)
  dst = make_cuFloatComplex(r, i);
#else
  dst = make_cuDoubleComplex(r, i);
#endif
}
#endif

__device__ inline void kload(dtype *gmem, dtype *smem, int c, int row, int s,
                             int col, dtypex src) {
#if defined(SUPPORT_COMPLEX)
#if defined(V1)
  smem[(col * VSIZE + 0) * xTILEYx + row + s] = gmem[0];
#else
#if defined(V2)
  loadx(src, gmem[0]);
  make_cuXComplex(smem[(col * VSIZE + 0) * xTILEYx + row + s], src.x, src.y);
  make_cuXComplex(smem[(col * VSIZE + 1) * xTILEYx + row + s], src.z, src.w);
#else
#if defined(V3)
  loadx(src, gmem[0]);
  make_cuXComplex(smem[(col * VSIZE + 0) * xTILEYx + row + s], src.x, src.y);
  make_cuXComplex(smem[(col * VSIZE + 1) * xTILEYx + row + s], src.z, src.w);
  smem[(col * VSIZE + 2) * xTILEYx + row + s] = gmem[2];
#else
#if defined(V4)
  loadx(src, gmem[0]);
  make_cuXComplex(smem[(col * VSIZE + 0) * xTILEYx + row + s], src.x, src.y);
  make_cuXComplex(smem[(col * VSIZE + 1) * xTILEYx + row + s], src.z, src.w);
  make_cuXComplex(smem[(col * VSIZE + 2) * xTILEYx + row + s], src.r, src.s);
  make_cuXComplex(smem[(col * VSIZE + 3) * xTILEYx + row + s], src.t, src.u);
#endif
#endif
#endif
#endif
#else
#if defined(V1)
 smem[col * VSIZE * xTILEYx + row + s] = gmem[0];
#else
  loadx(src, gmem[0]);
  smem[(col * VSIZE + 0) * xTILEYx + row + s] = src.x;
  smem[(col * VSIZE + 1) * xTILEYx + row + s] = src.y;
#if defined(V3)
  smem[(col * VSIZE + 2) * xTILEYx + row + s] = src.z;
#elif defined(V4)
  smem[(col * VSIZE + 2) * xTILEYx + row + s] = src.z;
  smem[(col * VSIZE + 3) * xTILEYx + row + s] = src.w;
#endif
#endif
#endif
}

__device__ inline void iload(dtype *gmem, dtype *smem, int batch_size,
                             int row, int s, int col) {
#if defined(V1)
  smem[(row + s) * xTILEXx + col * VSIZE] = gmem[0];
#elif defined(V3)
  loadx(smem[(row + s) * xTILEXx + col * VSIZE], gmem[0]);
  smem[(row + s) * xTILEXx + col * VSIZE + 2] = gmem[2];
#else
  loadx(smem[(row + s) * xTILEXx + col * VSIZE], gmem[0]);
#endif
}

extern "C" {
__global__ void ksmm(dtype *values, dtype *input, dtype *output, const uint a,
                     const uint b, const uint c, const uint d, uint batch_size) {
  int bx = blockIdx.x;
  int by = blockIdx.y;
  int t_id = threadIdx.x * blockDim.y + threadIdx.y;
  // Kronecker-sparse pattern (a, b, c, d)
  // K = kron(Id_{a,a}, kron(1_{b,c}, Id_{d,d}))
  // There is 'a' super-blocks of shape (b * d, c * d).
  // Number of non-zero per super-block is
  // b per column and c per row.
  // We would like to compute K @ X.
  // K (row-major format) shape is (a * b * d, a * c * d).
  // X (row-major format) shape is (a * c * d, batch).
  // TILEX / TX threads per column
  // Get the current thread
  int threadx = t_id % (xTILEXx / xTXx);
  int thready = t_id / (xTILEXx / xTXx);
  // To store input in shared memory
  __shared__ dtype shared_input[2][xTILEKx * xTILEXx];
  // To store sparse matrix in shared memory
  __shared__ dtype shared_values[2][xTILEYx * xTILEKx];
  // To store output in shared memory
  // __shared__ dtype shared_output[xTILEYx * xTILEXx];
  dtype tmp_acc[xTYx * xTXx] = {0.0};
  dtype regY[xTYx] = {0.0};
  dtype regX[xTXx] = {0.0};

  dtypex src;

  // Current super-block.
  int sb_id = (by * xTILEYx) / (b * d);
  // Group and id inside the super-block.
  int grp_id = (by * xTILEYx - sb_id * b * d) / b;
  int off = ((by * xTILEYx - sb_id * b * d) % b) / xTILEYx;
  // Move to the current super-block, group and id.
  values = &values[(sb_id * b * d + grp_id + off * d * xTILEYx) * c];
  input = &input[(c * d * sb_id + grp_id % d) * batch_size];
  output = &output[(sb_id * b * d + grp_id + off * d * xTILEYx) * batch_size];
  // Move bx * TILEX columns.
  input += bx * xTILEXx;
  output += bx * xTILEXx;

  // Indices to load (Kronecker-sparse factor) in smem.
  int ValuesSubRow = t_id / (xTILEKx / VSIZE);
  int ValuesSubCol = t_id % (xTILEKx / VSIZE);
  // Indices to load (input matrix) in smem.
  int InputSubRow = t_id / (xTILEXx / VSIZE);
  int InputSubCol = t_id % (xTILEXx / VSIZE);

  // Use stride to load from GMEM to SMEM
  const int StrideValues = VSIZE * xNTHREADSx / xTILEKx;
  const int StrideInput = VSIZE * xNTHREADSx / xTILEXx;

  // Load (dtypex) the first batch of Kronecker-sparse factor from global to
  // shared memory TILEY * TILEK.
#pragma unroll
  for (int s = 0; s < xTILEYx; s += StrideValues)
    kload(&values[d * (ValuesSubRow + s) * c + (ValuesSubCol * VSIZE) % c],
          &shared_values[0][0], c, ValuesSubRow, s, ValuesSubCol, src);

  // Load the first batch of input from global to shared memory TILEK * TILEX.
#pragma unroll
  for (int s = 0; s < xTILEKx; s += StrideInput)
    iload(&input[d * (InputSubRow + s) * batch_size + InputSubCol * VSIZE],
          &shared_input[0][0], batch_size, InputSubRow, s, InputSubCol);

  int load = 0;
  int write = 1;

  // Loop over non-zero entries by TILEK
  for (int k = 0; k < xTILEKx * (c / xTILEKx); k += xTILEKx) {
    __syncthreads();
    // Load smem to register and compute accumulation.
#pragma unroll
    for (int i = 0; i < xTILEKx; i++) {
      // Kronecker-sparse factor.
#pragma unroll
      for (int y = 0; y < xTYx; y += VSIZE)
	rload(regY, shared_values[load], y, i * xTILEYx + thready * xTYx + y);
      // Input.
#pragma unroll
      for (int x = 0; x < xTXx; x += VSIZE)
        rload(regX, shared_input[load], x, i * xTILEXx + threadx * xTXx + x);

      // Compute accumulation.
#pragma unroll
      for (int y = 0; y < xTYx; y++) {
#pragma unroll
        for (int x = 0; x < xTXx; x++) {
#if defined(SUPPORT_COMPLEX64)
          tmp_acc[y * xTXx + x] =
              cuCaddf(tmp_acc[y * xTXx + x], cuCmulf(regY[y], regX[x]));
#elif defined(SUPPORT_COMPLEX128)
          tmp_acc[y * xTXx + x] =
              cuCadd(tmp_acc[y * xTXx + x], cuCmul(regY[y], regX[x]));
#else
          tmp_acc[y * xTXx + x] += regY[y] * regX[x];
#endif
        }
      }
    }

    load = load ^ 1;
    // Move xTILEKx columns (values is in row-major).
    values += xTILEKx;
    // Move d * xTILEKx rows (input is in row-major).
    input += d * xTILEKx * batch_size;

    // Condition on columns of values.
    if ((k + xTILEKx) < (xTILEKx * (c / xTILEKx))) {
      // Load the Kronecker-sparse factor in shared memory TILEY x TILEK.
#pragma unroll
      for (int s = 0; s < xTILEYx; s += StrideValues)
        kload(&values[d * (ValuesSubRow + s) * c + (ValuesSubCol * VSIZE) % c],
              &shared_values[write][0], c, ValuesSubRow, s, ValuesSubCol, src);
        // Load next batch from global to shared memory TILEK x TILEX
#pragma unroll
      for (int s = 0; s < xTILEKx; s += StrideInput)
        iload(&input[d * (InputSubRow + s) * batch_size + InputSubCol * VSIZE],
              &shared_input[write][0], batch_size, InputSubRow, s, InputSubCol);
      write = write ^ 1;
    }
  }

//   // Store accumulation to shared memory
// #pragma unroll
//   for (int y = 0; y < xTYx; y++) {
// #pragma unroll
//     for (int x = 0; x < xTXx; x += VSIZE) {
// #pragma unroll
//       for (int v = 0; v < VSIZE; v++)
// 	shared_output[(thready * xTYx + y) * xTILEXx + threadx * xTXx + x + v] =
// 	  tmp_acc[y * xTXx + x + v];
// // #if defined(V1)
// //       shared_output[(thready * xTYx + y) * xTILEXx + threadx * xTXx + x] =
// // 	tmp_acc[y * xTXx + x];
// // #else
// //       loadx(shared_output[(thready * xTYx + y) * xTILEXx + threadx * xTXx + x],
// // 	    tmp_acc[y * xTXx + x]);
// // #endif
//     }
//   }

#pragma unroll
  for (int y = 0; y < xTYx; y++) {
#pragma unroll
    for (int x = 0; x < xTXx; x += VSIZE)
      rload(output, tmp_acc,
	    d * (thready * xTYx + y) * batch_size + threadx * xTXx + x, y * xTXx + x);
  }
}
}

#endif
