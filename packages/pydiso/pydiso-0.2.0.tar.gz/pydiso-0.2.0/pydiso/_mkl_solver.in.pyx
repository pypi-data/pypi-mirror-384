# cython: language_level=3
# cython: embedsignature=True, language_level=3
# cython: freethreading_compatible=True
cimport numpy as np
import cython

import numpy as np
import os

# We use np.PyArray_DATA to grab the pointer
# to a numpy array.
np.import_array()

cdef extern from 'mkl.h':
    ctypedef long long MKL_INT64
    ctypedef int MKL_INT

ctypedef MKL_INT int_t
ctypedef MKL_INT64 long_t

cdef extern from 'mkl.h':
    int MKL_DOMAIN_PARDISO

    ctypedef struct MKLVersion:
        int MajorVersion
        int MinorVersion
        int UpdateVersion
        char * ProductStatus
        char * Build
        char * Processor
        char * Platform

    void mkl_get_version(MKLVersion* pv)

    void mkl_set_num_threads(int nth)
    int mkl_domain_set_num_threads(int nt, int domain)
    int mkl_get_max_threads()
    int mkl_domain_get_max_threads(int domain)

    ctypedef int (*ProgressEntry)(int* thread, int* step, char* stage, int stage_len) except? -1;
    ProgressEntry mkl_set_progress(ProgressEntry progress);

    ctypedef void * _MKL_DSS_HANDLE_t

    void pardiso(_MKL_DSS_HANDLE_t, const int_t*, const int_t*, const int_t*,
                 const int_t *, const int_t *, const void *, const int_t *,
                 const int_t *, int_t *, const int_t *, int_t *,
                 const int_t *, void *, void *, int_t *) nogil

    void pardiso_64(_MKL_DSS_HANDLE_t, const long_t *, const long_t *, const long_t *,
                    const long_t *, const long_t *, const void *, const long_t *,
                    const long_t *, long_t *, const long_t *, long_t *,
                    const long_t *, void *, void *, long_t *) nogil


_err_messages = {0:"no error",
                -1:'input inconsistent',
                -2:'not enough memory',
                -3:'reordering problem',
                -4:'zero pivot, numerical factorization or iterative refinement problem',
                -5:'unclassified (internal) error',
                -6:'reordering failed',
                -7:'diagonal matrix is singular',
                -8:'32-bit integer overflow problem',
                -9:'not enough memory for OOC',
                -10:'error opening OOC files',
                -11:'read/write error with OOC files',
                -12:'pardiso_64 called from 32-bit library',
                }

class PardisoError(Exception):
    pass

class PardisoWarning(UserWarning):
    pass

#call pardiso (pt, maxfct, mnum, mtype, phase, n, a, ia, ja, perm, nrhs, iparm, msglvl, b, x, error)
cdef int mkl_progress(int *thread, int* step, char* stage, int stage_len) nogil:
    # must be a nogil process to pass to mkl pardiso progress reporting
    with gil:
        # must reacquire the gil to print out back to python.
        print(thread[0], step[0], stage, stage_len)
    return 0

cdef int mkl_no_progress(int *thread, int* step, char* stage, int stage_len) nogil:
    return 0


def get_mkl_max_threads():
    """
    Returns the current number of openMP threads available to the MKL Library
    """
    return mkl_get_max_threads()

def get_mkl_pardiso_max_threads():
    """
    Returns the current number of openMP threads available to the Pardiso functions
    """
    return mkl_domain_get_max_threads(MKL_DOMAIN_PARDISO)

def set_mkl_threads(num_threads=None):
    """
    Sets the number of openMP threads available to the MKL library.

    Parameters
    ----------
    num_threads : None or int
        number of threads to use for the MKL library.
        None will set the number of threads to that returned by `os.cpu_count()`.
    """
    if num_threads is None:
        num_threads = os.cpu_count()
    elif num_threads<=0:
        raise ValueError('Number of threads must be greater than 0')
    mkl_set_num_threads(num_threads)

def set_mkl_pardiso_threads(num_threads=None):
    """
    Sets the number of openMP threads available to the Pardiso functions

    Parameters
    ----------
    num_threads : None or int
        Number of threads to use for the MKL Pardiso routines.
        None (or 0) will set the number of threads to `get_mkl_max_threads`
    """
    if num_threads is None:
        num_threads = 0
    elif num_threads<0:
        raise ValueError('Number of threads must be greater than 0')
    mkl_domain_set_num_threads(num_threads, MKL_DOMAIN_PARDISO)

def get_mkl_version():
    """
    Returns a dictionary describing the version of Intel Math Kernel Library used
    """
    cdef MKLVersion vers
    mkl_get_version(&vers)
    return vers

def get_mkl_int_size():
    """Return the size of the MKL_INT at compile time in bytes.

    Returns
    -------
    int
    """
    return sizeof(MKL_INT)


def get_mkl_int64_size():
    """Return the size of the MKL_INT64 at compile time in bytes.

    Returns
    -------
    int
    """
    return sizeof(MKL_INT64)



ctypedef fused real_or_complex:
    np.float32_t
    np.float64_t
    np.complex64_t
    np.complex128_t


{{for int_type in ["int_t", "long_t"]}}
cdef class _PardisoHandle_{{int_type}}:
    cdef _MKL_DSS_HANDLE_t handle[64]
    cdef cython.pymutex lock

    cdef {{int_type}} n, maxfct, mnum, msglvl
    cdef public {{int_type}} matrix_type
    cdef public {{int_type}}[64] iparm
    cdef public {{int_type}}[:] perm

    @cython.boundscheck(False)
    def __cinit__(self, A_dat_dtype, n, matrix_type, maxfct, mnum, msglvl):

        np_int_dtype = np.dtype(f"i{sizeof({{int_type}})}")

        for i in range(64):
            self.handle[i] = NULL

        self.n = n
        self.matrix_type = matrix_type
        self.maxfct = maxfct
        self.mnum = mnum
        self.msglvl = msglvl


        with self.lock:
            if self.msglvl:
                #for reporting factorization progress via python's `print`
                mkl_set_progress(mkl_progress)
            else:
                mkl_set_progress(mkl_no_progress)

        is_single_precision = np.issubdtype(A_dat_dtype, np.single) or np.issubdtype(A_dat_dtype, np.csingle)

        self.perm = np.empty(self.n, dtype=np_int_dtype)

        for i in range(64):
            self.iparm[i] = 0  # ensure these all start at 0

        # set default parameters
        self.iparm[0] = 1  # tell pardiso to not reset these values on the first call
        self.iparm[1] = 2  # The nested dissection algorithm from the METIS
        self.iparm[3] = 0  # The factorization is always computed as required by phase.
        self.iparm[4] = 2  # fill perm with computed permutation vector
        self.iparm[5] = 0  # The array x contains the solution; right-hand side vector b is kept unchanged.
        self.iparm[7] = 0  # The solver automatically performs two steps of iterative refinement when perterbed pivots are obtained
        self.iparm[9] = 13 if matrix_type in [11, 13] else 8
        self.iparm[10] = 1 if matrix_type in [11, 13] else 0
        self.iparm[11] = 0  # Solve a linear system AX = B (as opposed to A.T or A.H)
        self.iparm[12] = 1 if matrix_type in [11, 13] else 0
        self.iparm[17] = -1  # Return the number of non-zeros in this value after first call
        self.iparm[18] = 0  # do not report flop count
        self.iparm[20] = 1 if matrix_type in [-2, -4, 6] else 0
        self.iparm[23] = 0  # classic (not parallel) factorization
        self.iparm[24] = 0  # default behavoir of parallel solving
        self.iparm[26] = 1  # Do not check the input matrix
        self.iparm[27] = is_single_precision  # 1 if single, 0 if double
        self.iparm[30] = 0  # this would be used to enable sparse input/output for solves
        self.iparm[33] = 0  # optimal number of thread for CNR mode
        self.iparm[34] = 1  # zero based indexing
        self.iparm[35] = 0  # Do not compute schur complement
        self.iparm[36] = 0  # use CSR storage format
        self.iparm[38] = 0  # Do not use low rank update
        self.iparm[42] = 0  # Do not compute the diagonal of the inverse
        self.iparm[55] = 0  # Internal function used to work with pivot and calculation of diagonal arrays turned off.
        self.iparm[59] = 0  # operate in-core mode

    def initialized(self):
        return self._initialized()

    cdef int _initialized(self) noexcept nogil:
        # If any of the handle pointers are not null, return 1
        cdef int i
        for i in range(64):
            if self.handle[i]:
                return 1
        return 0

    def set_iparm(self, {{int_type}} i, {{int_type}} val):
        self.iparm[i] = val

    @cython.boundscheck(False)
    cpdef {{int_type}} call_pardiso(self,
            {{int_type}} phase,
            real_or_complex[::1] a_data,
            {{int_type}}[::1] a_indptr,
            {{int_type}}[::1] a_indices,
            real_or_complex[::1, :] rhs,
            real_or_complex[::1, :] out
    ):
        cdef {{int_type}} error, nrhs
        with nogil:
            nrhs = rhs.shape[1]
            with self.lock:
                pardiso{{if int_type == "long_t"}}_64{{endif}}(
                        self.handle, &self.maxfct, &self.mnum, &self.matrix_type, &phase, &self.n,
                        &a_data[0], &a_indptr[0], &a_indices[0], &self.perm[0],
                        &nrhs, self.iparm, &self.msglvl,
                        &rhs[0, 0], &out[0, 0], &error
                    )
        return error

    @cython.boundscheck(False)
    def __dealloc__(self):
        # Need to call pardiso with phase=-1 to release memory (if it was initialized)
        cdef {{int_type}} phase = -1, nrhs = 0, error = 0

        with nogil:
            with self.lock:
                if self._initialized():
                    pardiso{{if int_type == "long_t"}}_64{{endif}}(
                                self.handle, &self.maxfct, &self.mnum, &self.matrix_type,
                                &phase, &self.n, NULL, NULL, NULL, NULL, &nrhs, self.iparm,
                                &self.msglvl, NULL, NULL, &error)
                    if error == 0:
                        for i in range(64):
                            self.handle[i] = NULL
        if error != 0:
            raise MemoryError("Pardiso Memory release error: " + _err_messages[error])
{{endfor}}