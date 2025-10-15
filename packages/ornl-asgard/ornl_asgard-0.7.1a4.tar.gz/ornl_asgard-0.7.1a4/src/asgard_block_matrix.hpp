#pragma once
#include "asgard_indexset.hpp"

namespace asgard
{
/*!
 * \internal
 * \brief holds the points and values of a variable rhs function
 *
 * Used a both workspace/scratch-space and a way to avoid double-evals
 * of the rhs, e.g., once for the operator matrix and once for
 * the separable boundary condition.
 * \endinternal
 */
template<typename P>
struct rhs_raw_data {
  //! points in the domain, where rhs was evaluated
  std::vector<P> pnts;
  //! the values of the rhs
  std::vector<P> vals;
};

/*!
 * \internal
 * \brief Stores a matrix in regular (non-block) column major format
 *
 * Stores a regular matrix and possibly the PLU factors.
 * \endinternal
 */
template<typename P>
class dense_matrix
{
public:
  //! creates an empty matrix
  dense_matrix() = default;
  //! create a matrix with the given number of rows and columns
  dense_matrix(int64_t rows, int64_t cols)
      : nrows_(rows), ncols_(cols), data_(nrows_ * ncols_)
  {}

  //! number of rows
  int64_t nrows() const { return nrows_; }
  //! number of columns
  int64_t ncols() const { return ncols_; }

  //! returns a ref to the entry
  P &operator() (int64_t r, int64_t c) { return data_[c * nrows_ + r]; }
  //! returns a const-ref to the entry
  P const &operator() (int64_t r, int64_t c) const { return data_[c * nrows_ + r]; }
  //! returns pointer to the internal data
  P *data() { return data_.data(); }
  //! returns pointer to the internal data
  P const *data() const { return data_.data(); }

  //! returns pointer to the internal data at the given row-column
  P *data(int64_t r, int64_t c) { return &data_[c * nrows_ + r]; }
  //! returns pointer to the internal data at the given row-column
  P const *data(int64_t r, int64_t c) const { return &data_[c * nrows_ + r]; }

  //! shows if the matrix has been factorized
  #ifdef ASGARD_USE_GPU
  bool is_factorized() const { return (not ipiv.empty() or not gpu_ipiv.empty()); }
  #else
  bool is_factorized() const { return (not ipiv.empty()); }
  #endif
  //! factorize the matrix using plu
  void factorize();

  //! check whether the matrix has been set
  operator bool () const { return (nrows_ > 0); }

  //! applies the inverse of the matrix to the provided vector
  void solve(std::vector<P> &b) const;
  #ifdef ASGARD_USE_GPU
  //! applies the inverse of the matrix to the provided vector
  void solve(gpu::vector<P> &b) const;
  #endif

  //! (testing) writes the the matric to the scream
  void print(std::ostream &os = std::cout) {
    for (int64_t r = 0; r < nrows_; r++) {
      for (int64_t c = 0; c < ncols_; c++)
        os << std::setw(16) << data_[c * nrows_ + r];
      os << '\n';
    }
  }

private:
  int64_t nrows_ = 0;
  int64_t ncols_ = 0;
  std::vector<P> data_;
  std::vector<int> ipiv;
  #ifdef ASGARD_USE_GPU
  gpu::vector<P> gpu_factor;
  gpu::vector<gpu::direct_int> gpu_ipiv;
  #endif
};

/*!
 * \internal
 * \brief Stores a matrix in block format
 *
 * The entries of each block are stored contiguously in memory and logically
 * organized into an matrix with column major format.
 *
 * This is for testing and cross-reference purposes, i.e., the sparse block types
 * can be converted to this full-block format for easier introspection.
 * \endinternal
 */
template<typename P>
class block_matrix
{
public:
  //! make an empty matrix
  block_matrix() : nrows_(0), ncols_(0), data_(0, 0) {}
  //! initialize matrix with given block-size and number of rows/cols
  block_matrix(int block_size, int64_t num_rows, int64_t num_cols)
      : nrows_(num_rows), ncols_(num_cols), data_(block_size, num_rows * num_cols)
  {}

  //! block size
  int nblock() const { return data_.stride(); }
  //! number of rows
  int64_t nrows() const { return nrows_; }
  //! number of columns
  int64_t ncols() const { return ncols_; }

  //! gives the i,j-th block
  P *operator() (int64_t i, int64_t j) { return data_[j * nrows_ + i]; }
  //! gives the i,j-th block, const-overload
  P const *operator() (int64_t i, int64_t j) const { return data_[j * nrows_ + i]; }

  //! returns the raw internal data
  P *data() { return data_[0]; }
  //! returns the raw internal data, const-overload
  P const *data() const { return data_[0]; }

  //! fill with single entry
  void fill(P v) { std::fill_n(data_[0], data_.total_size(), v); }

  //! prints the block-matrix with given block row/cols, or assume block is square
  void print(std::ostream &os = std::cout, int br = -1, int bc = -1, int oswidth = 16)
  {
    if (br == -1)
    {
      int const nb = data_.stride();
      br = 0;
      while (br < nb and br * br != nb)
        ++br;
      expect(br * br == nb);
      bc = br;
    }
    expect(br * bc == data_.stride());
    for (auto r : indexof(nrows_))
    {
      for (int i = 0; i < br; i++)
      {
        for (auto c : indexof(ncols_))
        {
          for (int j = 0; j < bc; j++)
            os << std::setw(oswidth) << data_[c * nrows_ + r][j * br + i];
          os << std::setw(oswidth / 2) << "  ";
        }
        os << '\n';
      }
      os << '\n';
    }
  }

  //! prints one column
  void printc(std::ostream &os, int c = 0, int oswidth = 12)
  {
    int const nb = data_.stride();
    int br = 0;
    while (br < nb and br * br != nb)
      ++br;
    expect(br * br == nb);
    int bc = br;
    expect(br * bc == data_.stride());
    for (auto r : indexof(nrows_))
    {
      for (int i = 0; i < br; i++)
      {

        for (int j = 0; j < bc; j++)
          os << std::setw(oswidth) << data_[c * nrows_ + r][j * br + i];
        os << std::setw(oswidth / 2) << "  ";

        os << '\n';
      }
      os << '\n';
    }
  }

  //! prints the block-matrix with given block row/cols, or assume block is square
  void printr(std::ostream &os, int r = 0, int oswidth = 12)
  {
    int const nb = data_.stride();
    int br = 0;
    while (br < nb and br * br != nb)
      ++br;
    expect(br * br == nb);
    int bc = br;
    expect(br * bc == data_.stride());
    for (int i = 0; i < br; i++)
    {
      for (auto c : indexof(ncols_))
      {
        for (int j = 0; j < bc; j++)
          os << std::setw(oswidth) << data_[c * nrows_ + r][j * br + i];
        os << std::setw(oswidth / 2) << "  ";
      }
      os << '\n';
    }
    os << '\n';
  }

  //! returns the l-inf max norm between the two matrices
  P max_diff(block_matrix<P> const &other) {
    expect(nrows_ == other.nrows_);
    expect(ncols_ == other.ncols_);
    expect(nblock() == other.nblock());
    int64_t const size = nrows_ * ncols_ * nblock();
    P const *v1 = data_[0];
    P const *v2 = other.data_[0];
    P err = 0;
    for (auto i : indexof(size))
      err = std::max(err, std::abs(v1[i] - v2[i]));
    return err;
  }

  //! convert the matrix to dense matrix
  dense_matrix<P> to_dense_matrix(int const n) const
  {
    expect(n * n == data_.stride());
    dense_matrix<P> mat(n * nrows_, n * ncols_);
    for (int r = 0; r < nrows_; r++)
      for (int c = 0; c < ncols_; c++)
        for (int k = 0; k < n; k++)
          std::copy_n(data_[c * nrows_ + r] + n * k , n, mat.data(n * r, n * c + k));
    return mat;
  }

private:
  int64_t nrows_, ncols_;
  vector2d<P> data_;
};

//! C += A * B
template<typename P>
void gemm1(int const n, block_matrix<P> const &A, block_matrix<P> const &B, block_matrix<P> &C);

/*!
 * \internal
 * \brief Block-diagonal matrix, stores the factorized mass matrix
 *
 * The idea is almost the same as the diagonal matrix, the difference being
 * that we store the factorized form of the diagonal blocks so we can
 * quickly apply the inverse onto another matrix.
 * \endinternal
 */
template<typename P>
class mass_matrix
{
public:
  //! create an empty matrix
  mass_matrix() {}
  //! get the mass matrix for the given level
  mass_matrix(int const nblock, int const num_rows) : data_(nblock, num_rows)
  {
    expect(nblock > 0);
    expect(num_rows > 0);
  }
  //! size of the block
  int nblock() const { return data_.stride(); }
  //! number of rows
  int64_t nrows() const { return data_.num_strips(); }

  //! gives the diagonal block
  P *operator() (int64_t row) { return data_[row]; }
  //! gives the diagonal block, const-overload
  P const *operator() (int64_t row) const { return data_[row]; }

  //! gives the diagonal block
  P *operator[] (int64_t row) { return data_[row]; }
  //! gives the diagonal block, const-overload
  P const *operator[] (int64_t row) const { return data_[row]; }

  //! returns the raw internal data
  P *data() { return data_.data(); }
  //! returns the raw internal data, const-overload
  P const *data() const { return data_.data(); }

  //! returns true of the matrix is empty
  bool empty() const { return data_.empty(); }

  //! converts the matrix to a full one, mostly for testing/plotting
  block_matrix<P> to_full() const
  {
    int const n = nblock();
    block_matrix<P> full(n, nrows(), nrows());
    for (auto r : indexof(nrows()))
      std::copy_n(data_[r], n, full(r, r));
    return full;
  }

private:
  vector2d<P> data_;
};

// forward declaration so we can do the inverse in the diag-matrix
template<typename P>
class block_tri_matrix;

/*!
 * \internal
 * \brief Stores a square block diagonal matrix
 *
 * \endinternal
 */
template<typename P>
class block_diag_matrix
{
public:
  //! make an empty matrix
  block_diag_matrix() : nrows_(0), data_(0, 0) {}
  //! initialize matrix with given block-size and number of rows/cols
  block_diag_matrix(int block_size, int64_t num_rows)
      : nrows_(num_rows), data_(block_size, num_rows)
  {}

  //! block size
  int nblock() const { return data_.stride(); }
  //! number of rows
  int64_t nrows() const { return nrows_; }

  //! gives the main diagonal block
  P *operator() (int64_t r) { return data_[r]; }
  //! gives the i,j-th block, const-overload
  P const *operator() (int64_t r) const { return data_[r]; }

  //! gives the main diagonal block
  P *operator[] (int64_t r) { return data_[r]; }
  //! gives the i,j-th block, const-overload
  P const *operator[] (int64_t r) const { return data_[r]; }

  //! returns the raw internal data
  P *data() { return data_[0]; }
  //! returns the raw internal data, const-overload
  P const *data() const { return data_[0]; }
  //! indicates whether the matrix is empty
  operator bool () const { return (nrows_ > 0); }
  //! indicates whether the matrix is empty
  bool empty() const { return (nrows_ == 0); }

  //! converts the matrix to a full one, mostly for testing/plotting
  block_matrix<P> to_full() const
  {
    int const n = nblock();
    block_matrix<P> full(n, nrows_, nrows_);
    for (auto r : indexof(nrows_))
      std::copy_n(data_[r], n, full(r, r));
    return full;
  }

  //! resizes the matrix and sets all entries to zero
  void resize_and_zero(int block_size, int64_t nrows)
  {
    nrows_ = nrows;
    data_.resize_and_zero(block_size, nrows);
  }
  //! resize to match the other matrix size
  void resize_and_zero(block_diag_matrix<P> const &other)
  {
    resize_and_zero(other.nblock(), other.nrows());
  }
  //! check size, resizes only if the size is different
  void check_resize(block_diag_matrix<P> const &other) {
    if (nblock() != other.nblock() or nrows_ != other.nrows())
      resize_and_zero(other);
  }

  //! assuming the blocks are s.p.d., factorize the matrix
  void spd_factorize(int const n);
  //! solves against a vector
  void solve(int const n, std::vector<P> &rhs) const {
    expect(rhs.size() == static_cast<size_t>(n * nrows_));
    solve(n, rhs.data());
  }
  //! solves against a raw-array
  void solve(int const n, P rhs[]) const;
  //! solves against a diag-matrix
  void solve(int const n, block_diag_matrix<P> &rhs) const;
  //! solves against a tri-matrix
  void solve(int const n, block_tri_matrix<P> &rhs) const;

  void inplace_gemv(int n, std::vector<P> &x, std::vector<P> &work) const;

private:
  int64_t nrows_;
  vector2d<P> data_;
};

/*!
 * \internal
 * \brief Stores a matrix in block tri-diagonal format
 *
 * The entries of each block are stored contiguously in memory and logically
 * organized into an tri-diagonal matrix (using row-major format).
 * The three diagonals have the names lower, diag, upper.
 * The entry for lower(0) is actually the top-right entry (0, n-1) corresponding
 * to periodic boundary condition. Similarly upper(n-1) is the bottom left entry.
 * Both entries are included in the pattern but could be numerically zero.
 * \endinternal
 */
template<typename P>
class block_tri_matrix
{
public:
  //! make an empty matrix
  block_tri_matrix() : nrows_(0), data_(0, 0) {}
  //! initialize matrix with given block-size and number of rows/cols
  block_tri_matrix(int block_size, int64_t num_rows)
      : nrows_(num_rows), data_(block_size, 3 * num_rows)
  {}

  //! copy diagonal to tri-diagonal matrix
  block_tri_matrix& operator = (block_diag_matrix<P> const &other)
  {
    resize_and_zero(other.nblock(), other.nrows());
    for (auto i : indexof(nrows_))
      std::copy_n(other[i], data_.stride(), diag(i));
    return *this;
  }

  //! block size
  int nblock() const { return data_.stride(); }
  //! number of rows
  int64_t nrows() const { return nrows_; }

  //! gives the main diagonal block
  P *operator() (int64_t r) { return data_[3 * r + 1]; }
  //! gives the i,j-th block, const-overload
  P const *operator() (int64_t r) const { return data_[3 * r + 1]; }

  //! gives the lower diagonal block
  P *lower(int64_t r) { return data_[3 * r]; }
  //! gives the lower diagonal block, const-overload
  P const *lower(int64_t r) const { return data_[3 * r]; }
  //! gives the main diagonal block
  P *diag(int64_t r) { return data_[3 * r + 1]; }
  //! gives the main diagonal block, const-overload
  P const *diag(int64_t r) const { return data_[3 * r + 1]; }
  //! gives the upper diagonal block
  P *upper(int64_t r) { return data_[3 * r + 2]; }
  //! gives the upper diagonal block, const-overload
  P const *upper(int64_t r) const { return data_[3 * r + 2]; }

  //! returns the raw internal data
  P *data() { return data_[0]; }
  //! returns the raw internal data, const-overload
  P const *data() const { return data_[0]; }

  //! fill with single entry
  void fill(P v) { std::fill_n(data_[0], data_.total_size(), v); }
  //! resizes the matrix and sets all entries to zero
  void resize_and_zero(int block_size, int64_t nrows)
  {
    nrows_ = nrows;
    data_.resize_and_zero(block_size, 3 * nrows);
  }
  //! resize to match the other matrix size
  void resize_and_zero(block_tri_matrix<P> const &other)
  {
    resize_and_zero(other.nblock(), other.nrows());
  }
  //! check size, resizes only if the size is different
  void check_resize(block_tri_matrix<P> const &other) {
    if (nblock() != other.nblock() or nrows_ != other.nrows())
      resize_and_zero(other);
  }
  //! check size, resizes only if the size is different
  void check_resize(block_diag_matrix<P> const &other) {
    if (nblock() != other.nblock() or nrows_ != other.nrows())
      resize_and_zero(other.nblock(), other.nrows());
  }

  //! add another matrix to this one, used to merge with the penalty term
  block_tri_matrix<P> &operator += (block_tri_matrix<P> const &other);

  //! converts the matrix to a full one, mostly for testing/plotting
  block_matrix<P> to_full() const
  {
    int const n = nblock();
    block_matrix<P> full(n, nrows_, nrows_);
    std::copy_n(diag(0), n, full(0, 0));
    if (nrows_ == 1)
      return full;
    std::copy_n(lower(0), n, full(0, nrows_ - 1));
    std::copy_n(upper(0), n, full(0, 1));
    for (int64_t r = 1; r < nrows_ - 1; r++)
    {
      std::copy_n(lower(r), n, full(r, r - 1));
      std::copy_n(diag(r), n, full(r, r));
      std::copy_n(upper(r), n, full(r, r + 1));
    }
    std::copy_n(lower(nrows_ - 1), n, full(nrows_ - 1, nrows_ - 2));
    std::copy_n(diag(nrows_ - 1), n, full(nrows_ - 1, nrows_ - 1));
    std::copy_n(upper(nrows_ - 1), n, full(nrows_ - 1, 0));
    if (nrows_ == 2)
    {
      for (int i : indexof<int>(data_.stride()))
        full(0, 1)[i] += lower(0)[i];
      for (int i : indexof<int>(data_.stride()))
        full(1, 0)[i] += lower(nrows_ - 1)[i];
    }
    return full;
  };

  void inplace_gemv(int n, std::vector<P> &x, std::vector<P> &work) const;

private:
  int64_t nrows_;
  vector2d<P> data_;
};

/*!
 * \internal
 * \brief Block sparse matrix and holds the type-pattern (volume or edge)
 *
 * \endinternal
 */
template<typename P>
struct block_sparse_matrix
{
public:
  //! make an empty matrix
  block_sparse_matrix() : data_(0, 0) {}
  //! initialize matrix with given block-size and number of rows/cols
  block_sparse_matrix(int block_size, int64_t nnz, connect_1d::hierarchy htype)
      : htype_(htype), data_(block_size, nnz)
  {}
  //! block size
  int nblock() const { return data_.stride(); }
  //! num non-zero blocks
  int64_t nnz() const { return data_.num_strips(); }
  //! returns the type of the sparsity pattern
  operator connect_1d::hierarchy() const { return htype_; }
  //! returns the block at the given index
  P *operator[] (int64_t i) { return data_[i]; }
  //! returns the block at the given index
  P const *operator[] (int64_t i) const { return data_[i]; }
  //! returns the internal data
  P *data() { return data_[0]; }
  //! returns the internal data (const overload)
  P const *data() const { return data_[0]; }
  //! returns true if the matrix is empty, i.e., uninitialized
  bool empty() const { return (data_.stride() == 0); }

  //! converts the matrix to a full one, mostly for testing/plotting
  block_matrix<P> to_full(connection_patterns const &conns) const
  {
    connect_1d const &conn = conns(htype_);
    int const n     = nblock();
    int const nrows = conn.num_rows();
    int mcol = 0;
    for (int j = 0; j < conn.num_connections(); j++)
      mcol = std::max(mcol, conn[j]);
    block_matrix<P> full(n, nrows, mcol + 1);

    for (int r = 0; r < nrows; r++)
      for (int j = conn.row_begin(r); j < conn.row_end(r); j++)
        std::copy_n(data_[j], n, full(r, conn[j]));

    return full;
  }
  //! compute matrix vector product
  void gemv(int const n, int const level, connection_patterns const &conns, P const x[], P y[]) const;
  //! copy into external vector
  void copy_out(std::vector<P> &out) const
  {
    data_.copy_out(out);
  }
  //! returns the internal raw-data so it can be loaded to the GPU
  std::vector<P> const &data_vector() const { return data_.data_vector(); }
  //! scales the matrix by a value
  void scal(P v);
  //! (testing) fill the matrix with a value
  void fill(P v) { data_.fill(v); }

  #ifdef ASGARD_USE_GPU
  block_sparse_matrix get_subpattern(int level, connection_patterns const &conns) const {
    expect(htype_ == connect_1d::hierarchy::volume or htype_ == connect_1d::hierarchy::full);

    connect_1d const &conn = conns(htype_);
    connect_1d const &low  = conns.get(level, htype_);
    expect(level < conn.max_loaded_level()); // special case, either just copy or avoid this

    int const n = nblock();

    block_sparse_matrix res(n, low.num_connections(), htype_);
    for (int row = 0; row < low.num_rows(); row++) {
      int const nz = low.row_end(row) - low.row_begin(row);
      std::copy_n(data_[conn.row_begin(row)], nz * n, res[low.row_begin(row)]);
    }

    return res;
  }
  #endif

private:
  connect_1d::hierarchy htype_ = connect_1d::hierarchy::volume;
  vector2d<P> data_;
};

/*!
 * \internal
 * \brief Fill the blocks of A with identical pattern pattern
 *
 * The block size for A is n by n, and the pattern must have n * n entries.
 *
 * \endinternal
 */
template<typename P>
void fill_pattern(P const pattern[], block_diag_matrix<P> &A);

/*!
 * \internal
 * \brief Multiply block-tri-diagonal matrices
 *
 * The product of general tri-diagonal matrices is penta-diagonal matrix
 * and chaining multiple matrices together increases the bandwidth of the result.
 * However, if the matrices are logically tri-diagonal but numerically
 * lower/upper, then the result will be a general tridiagonal matrix.
 *
 * This is the upper times lower case, or upwind-downwind for terms 0 and 1
 * \endinternal
 */
template<typename P>
void gemm_block_tri_ul(int const n, block_tri_matrix<P> const &A, block_tri_matrix<P> const &B,
                       block_tri_matrix<P> &C);

/*!
 * \internal
 * \brief Multiply block-tri-diagonal matrices
 *
 * The product of general tri-diagonal matrices is penta-diagonal matrix
 * and chaining multiple matrices together increases the bandwidth of the result.
 * However, if the matrices are logically tri-diagonal but numerically
 * lower/upper, then the result will be a general tridiagonal matrix.
 *
 * This is the lower times upper case, or downwind-upwind for terms 0 and 1
 * \endinternal
 */
template<typename P>
void gemm_block_tri_lu(int const n, block_tri_matrix<P> const &A, block_tri_matrix<P> const &B,
                       block_tri_matrix<P> &C);

/*!
 * \internal
 * \brief Multiply block-tri-diagonal matrices
 *
 * The assumption is that the matrices are upper and lower tri-diagonal but it is unclear
 * which is which. Thus, the algorithm multiplies the matrices but ignores the entries
 * outside of the three diagonals.
 * \endinternal
 */
template<typename P>
void gemm_block_tri(int const n, block_tri_matrix<P> const &A, block_tri_matrix<P> const &B,
                    block_tri_matrix<P> &C);

/*!
 * \internal
 * \brief Multiply block-diagonal by block-tri-triagonal matrix
 *
 * \endinternal
 */
template<typename P>
void gemm_diag_tri(int const n, block_diag_matrix<P> const &A,
                   block_tri_matrix<P> const &B, block_tri_matrix<P> &C);
/*!
 * \internal
 * \brief Multiply block-tri-diagonal by block-diagonal matrix
 *
 * \endinternal
 */
template<typename P>
void gemm_tri_diag(int const n, block_tri_matrix<P> const &A,
                   block_diag_matrix<P> const &B, block_tri_matrix<P> &C);

/*!
 * \internal
 * \brief Multiply block-diagonal matrices
 *
 * \endinternal
 */
template<typename P>
void gemm_block_diag(int const n, block_diag_matrix<P> const &A, block_diag_matrix<P> const &B,
                     block_diag_matrix<P> &C);

/*!
 * \internal
 * \brief Applies the inverse of a mass matrix times block tri-diagonal matrix
 *
 * \endinternal
 */
template<typename P>
void invert_mass(int const n, mass_matrix<P> const &mass, block_tri_matrix<P> &op);

/*!
 * \internal
 * \brief Applies the inverse of a mass matrix times block diagonal matrix
 *
 * \endinternal
 */
template<typename P>
void invert_mass(int const n, mass_matrix<P> const &mass, block_diag_matrix<P> &op);

/*!
 * \internal
 * \brief Applies the inverse of a mass matrix times vector
 *
 * \endinternal
 */
template<typename P>
void invert_mass(int const n, mass_matrix<P> const &mass, P x[]);

/*!
 * \internal
 * \brief Overwrites A with (I + alpha * A)
 *
 * \endinternal
 */
template<typename P>
void to_euler(int const n, P alpha, block_diag_matrix<P> &A);

/*!
 * \internal
 * \brief Overwrites A with (I + alpha * A)
 *
 * \endinternal
 */
template<typename P>
void to_euler(int const n, P alpha, block_tri_matrix<P> &A);

/*!
 * \internal
 * \brief Destroys the content in A and forms approximate inverse of A, similar to ILU
 *
 * \endinternal
 */
template<typename P>
void psedoinvert(int const n, block_tri_matrix<P> &A,
                 block_tri_matrix<P> &iA);
/*!
 * \internal
 * \brief Destroys the content in A and forms the inverse of A
 *
 * \endinternal
 */
template<typename P>
void psedoinvert(int const n, block_diag_matrix<P> &A,
                 block_diag_matrix<P> &iA);

} // namespace asgard
