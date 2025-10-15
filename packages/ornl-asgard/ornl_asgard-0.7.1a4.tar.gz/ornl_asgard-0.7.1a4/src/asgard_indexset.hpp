#pragma once

#include "asgard_grid_1d.hpp"

namespace asgard
{
/*!
 * \brief Helper wrapper for data that will be organized in two dimensional form
 *
 * See the vector2d and span2d that derive from this class,
 * the purpose here is to reduce retyping of the same code.
 */
template<typename T, typename data_container>
class organize2d
{
public:
  //! \brief Virtual destructor
  virtual ~organize2d() = default;

  //! \brief Returns the vector stride.
  int64_t stride() const { return stride_; }
  //! \brief Returns the vector stride.
  int64_t num_strips() const { return num_strips_; }
  //! \brief Returns the total number of entries.
  int64_t total_size() const { return stride_ * num_strips_; }
  //! \brief Returns true if empty.
  bool empty() const { return (num_strips_ == 0); }

  //! \brief Return pointer to the i-th strip.
  T *operator[](int64_t i) { return &data_[i * stride_]; }
  //! \brief Return const-pointer to the i-th strip.
  T const *operator[](int64_t i) const { return &data_[i * stride_]; }

protected:
  //! \brief Constructor, not intended for public use.
  organize2d(int64_t stride, int64_t num_strips)
      : stride_(stride), num_strips_(num_strips)
  {}

  int64_t stride_, num_strips_;
  data_container data_;
};

/*!
 * \brief Wrapper around std::vector, but providing 2d organization of the data.
 *
 * The data is divided into contiguous strips of fixed size.
 * The class provides easy access to individual strips, without the tedious
 * i * stride + j notation and with easy check for sizes.
 *
 * Note: while this is similar to a matrix, there is no notion of rows or column
 * and the data is not meant to represent a linear transformation.
 *
 * Allows access to the stride(), num_strips(), check for empty()
 * and access to alias to any strip with the [] operator.
 *
 * Since this container owns the data, we can also append more strips and/or
 * clear all the existing data.
 */
template<typename T>
class vector2d : public organize2d<T, std::vector<T>>
{
public:
  //! \brief Make an empty vector
  vector2d() : organize2d<T, std::vector<T>>::organize2d(0, 0) {}
  //! \brief Make a vector with the given dimensions, initialize to 0.
  vector2d(int64_t stride, int64_t num_strips)
      : organize2d<T, std::vector<T>>::organize2d(stride, num_strips)
  {
    this->data_ = std::vector<T>(stride * num_strips);
  }
  //! \brief Assume ownership of the data.
  vector2d(int64_t stride, std::vector<int> data)
      : organize2d<T, std::vector<T>>::organize2d(stride, 0)
  {
    expect(static_cast<int64_t>(data.size()) % this->stride_ == 0);
    this->num_strips_ = static_cast<int64_t>(data.size()) / this->stride_;
    this->data_       = std::move(data);
  }
  //! \brief Append to the end of the vector, assuming num_strips of data.
  void append(T const *p, int64_t num_strips = 1)
  {
    this->data_.insert(this->data_.end(), p, p + this->stride_ * num_strips);
    this->num_strips_ += num_strips;
  }
  //! \brief Append to the end of the vector.
  void append(std::vector<T> const &p)
  {
    expect(static_cast<int64_t>(p.size()) % this->stride_ == 0);
    this->data_.insert(this->data_.end(), p.begin(), p.end());
    this->num_strips_ += static_cast<int64_t>(p.size()) / this->stride_;
  }
  //! \brief Remove all data but keep the stride.
  void clear()
  {
    this->data_.clear();
    this->num_strips_ = 0;
  }
  //! \brief Resizes, avoids calling allocate
  void resize(int64_t stride, int64_t num_strips)
  {
    this->stride_     = stride;
    this->num_strips_ = num_strips;
    this->data_.resize(stride * num_strips);
  }
  //! \brief Resizes and sets all entries to zero (avoids calling allocate)
  void resize_and_zero(int64_t stride, int64_t num_strips)
  {
    resize(stride, num_strips);
    std::fill(this->data_.begin(), this->data_.end(), T{0});
  }
  //! \brief Copies the data into the provided vector
  void copy_out(std::vector<T> &out) const
  {
    out.resize(this->data_.size());
    std::copy(this->data_.begin(), this->data_.end(), out.begin());
  }
  //! \brief Debugging purposes, write to std::cout
  void print() const
  {
    for (auto i : indexof(this->num_strips_)) {
      for (auto j : indexof(this->stride_))
        std::cout << this->data_[i * this->stride_ + j] << "  ";
      std::cout << '\n';
    }
  }
  //! \brief Used to push data to the GPU
  std::vector<T> const &data_vector() const { return this->data_; }
  //! \brief (testing) fill the vector with a value
  void fill(T v) { std::fill(this->data_.begin(), this->data_.end(), v); }
};

//! \brief Non-owning version of vector2d.
template<typename T>
class span2d : public organize2d<T, T *>
{
public:
  //! \brief Make an empty data set
  span2d()
      : organize2d<T, T *>::organize2d(0, 0)
  {
    this->data_ = nullptr;
  }
  //! \brief Organize data with the given size
  span2d(int64_t stride, int64_t num_strips, T *data)
      : organize2d<T, T *>::organize2d(stride, num_strips)
  {
    this->data_ = data;
  }
  //! \brief Organize the data from a vector
  span2d(int64_t stride, std::vector<T> &vec)
      : organize2d<T, T *>::organize2d(stride, static_cast<int64_t>(vec.size() / stride))
  {
    expect(vec.size() == static_cast<size_t>(this->num_strips_ * this->stride_));
    this->data_ = vec.data();
  }
};

//!\brief Helper to convert from asg index format to tasmanian format.
inline int asg2tsg_convert(int asg_level, int asg_point)
{
  return (asg_level == 0) ? 0 : ((1 << (asg_level - 1)) + asg_point);
}
//!\brief Helper to convert from asg index format to tasmanian format.
inline void asg2tsg_convert(int num_dimensions, int const *asg, int *tsg)
{
  for (int d = 0; d < num_dimensions; d++)
    tsg[d] = asg2tsg_convert(asg[d], asg[d + num_dimensions]);
}
//!\brief Helper to convert from asg index format to tasmanian format.
inline vector2d<int> asg2tsg_convert(int num_dimensions, int64_t num_indexes,
                                     int const *asg)
{
  vector2d<int> tsg(num_dimensions, num_indexes);
  for (int64_t i = 0; i < num_indexes; i++)
    asg2tsg_convert(num_dimensions, asg + 2 * num_dimensions * i, tsg[i]);
  return tsg;
}

// forward declare so the indexes_ can be friends with the sparse grid
class sparse_grid;

/*!
 * \brief Contains a set of sorted multi-indexes
 *
 * For the given number of dimensions, the indexes are sorted
 * in lexicographical order with the last dimension changing the fastest.
 *
 * The purpose of this set is to establish an order between the multi-indexes
 * and the discretization cells that will be used to index the global degrees
 * of freedom.
 *
 * The structure is very similar to vector2d; however, the indexset always
 * keeps the indexes stored in lexicographical, which also facilitates
 * fast search to find the location of each index with the find() method.
 */
class indexset
{
public:
  //! \brief Creates an empty set.
  indexset() : num_dimensions_(0), num_indexes_(0) {}
  //! \brief Creates a new set from a vector of sorted indexes.
  indexset(int num_dimensions, std::vector<int> &&indexes)
      : num_dimensions_(num_dimensions), indexes_(std::move(indexes))
  {
    expect(indexes.size() % num_dimensions_ == 0);
    num_indexes_ = static_cast<int64_t>(indexes_.size() / num_dimensions_);
  }

  //! \brief Returns the number of stored multi-indexes.
  int64_t num_indexes() const { return num_indexes_; }
  //! \brief Returns the number of dimensions.
  int num_dimensions() const { return num_dimensions_; }
  //! \brief Total number of integer entries.
  size_t size() const { return indexes_.size(); }
  //! \brief Returns true if the number of indexes is zero.
  bool empty() const { return (num_indexes() == 0); }

  //! \brief Get the i-th index of the lexicographical order.
  const int *operator[](int64_t i) const
  {
    return &indexes_[i * num_dimensions_];
  }
  //! \brief Get the i-th index of the lexicographical order.
  const int *index(int i) const
  {
    return (*this)[i];
  }

  //! \brief Find the index in the sorted list, returns -1 if missing
  int64_t find(const int *idx) const
  {
    int64_t first = 0, last = num_indexes_ - 1;
    int64_t current = (first + last) / 2;
    while (first <= last)
    {
      match cmp = compare(current, idx);
      if (cmp == before_current)
      {
        last = current - 1;
      }
      else if (cmp == after_current)
      {
        first = current + 1;
      }
      else // match_found
      {
        return current;
      }
      current = (first + last) / 2;
    }
    return -1;
  }
  //! \brief Overload for std::vector
  int find(std::array<int, max_num_dimensions> const &idx) const { return find(idx.data()); }
  //! \brief Boolean check if an entry is there or not.
  bool missing(const int *idx) const { return (find(idx) == -1); }
  //! returns true if the index is not included in the set
  bool missing(std::array<int, max_num_dimensions> const &idx) const { return missing(idx.data()); }

  //! \brief Union this set with another
  indexset &operator+=(indexset const &iset)
  {
    expect(iset.num_dimensions_ == num_dimensions_);
    if (iset.num_indexes_ == 0)
      return *this;

    std::vector<int> union_set;
    union_set.reserve(iset.indexes_.size() + indexes_.size());

    int64_t ia = 0;
    int64_t ib = 0;
    while (ia < num_indexes_ and ib < iset.num_indexes_)
    {
      match cmp = compare(ia, iset[ib]);
      if (cmp == match::before_current)
      {
        union_set.insert(union_set.end(), iset[ib], iset[ib] + num_dimensions_);
        ib++;
      }
      else if (cmp == match::after_current)
      {
        union_set.insert(union_set.end(), index(ia),
                         index(ia) + num_dimensions_);
        ia++;
      }
      else
      {
        union_set.insert(union_set.end(), index(ia),
                         index(ia) + num_dimensions_);
        ia++;
        ib++;
      }
    }
    if (ia < num_indexes_)
      union_set.insert(union_set.end(), (*this)[ia],
                       (*this)[ia] + (num_indexes_ - ia) * num_dimensions_);
    else if (ib < iset.num_indexes_)
      union_set.insert(union_set.end(), iset[ib],
                       iset[ib] + (iset.num_indexes_ - ib) * num_dimensions_);

    indexes_     = std::move(union_set);
    num_indexes_ = static_cast<int64_t>(indexes_.size() / num_dimensions_);
    return *this;
  }

  //! \brief Print a single index, for debugging purposes.
  void print(int index, std::ostream &os = std::cout)
  {
    expect(index >= 0 and index < num_indexes_);
    os << std::setw(3) << indexes_[index * num_dimensions_];
    for (int j = 1; j < num_dimensions_; j++)
      os << " " << std::setw(3) << indexes_[index * num_dimensions_ + j];
  }
  //! \brief Print the entire set, one index per row.
  void print(std::ostream &os = std::cout)
  {
    for (int64_t i = 0; i < num_indexes_; i++)
    {
      print(i, os);
      os << '\n';
    }
  }
  //! \brief Returns the vector of indexes
  std::vector<int> const &indexes() const { return indexes_; }

  // I/O utilities
  template<typename P> friend class h5manager;
  // needed for MPI sync through the sparse-grid class
  friend class sparse_grid;

protected:
  //! \brief Result of a comparison
  enum match
  {
    before_current,
    match_found,
    after_current
  };
  //! \brief Compare the multi-index to the one at the position current.
  match compare(int64_t current, int const *b) const
  {
    int const *a = (*this)[current];
    for (int j = 0; j < num_dimensions_; j++)
    {
      if (a[j] < b[j])
        return after_current;
      if (a[j] > b[j])
        return before_current;
    }
    return match_found;
  }

private:
  int num_dimensions_;
  int64_t num_indexes_;
  std::vector<int> indexes_;
};

/*!
 * \brief Factory method for constructing a set from unsorted and non-unique indexes.
 *
 * The set list could have repeated indexes.
 *
 * Works with vector2d<int> and span2d<int>
 */
template<typename data_container>
indexset make_index_set(organize2d<int, data_container> const &indexes);

/*!
 * \brief Splits the multi-index set into 1D vectors
 *
 * Using several sort commands (for speed), we identify groups of indexes.
 * For each dimension dim, we have num_vecs(dim) 1d vectors,
 * where the multi-indexes of the 1d vector match in all dimensions but dim.
 * Each of the num_vecs(dim) vectors begins at sorted offset
 * vec_begin(dim, i) and ends at vec_end(dim, i) - 1 (following C++ conventions)
 * where i goes from 0 until num_vecs(dim)-1.
 * The entries of the vector are at global index dimension_sort(dim, j)
 *
 * \code
 *   dimension_sort sorted(iset);
 *   for(int dim=0; dim<iset.num_dimensions(); dim++)
 *     for(int i=0; i<sorted.num_vecs(dim); i++)
 *        for(int j=sorted.vec_begin(dim, i); j<sorted.vec_end(dim, i), j++)
 *          std::cout << " value = " << x[sorted(dim, j)]
 *                    << " at 1d index " << sorted.index1d(dim, j) << "\n";
 * \endcode
 * Note: if the polynomial order is linear or above, each x[] contains
 * (p+1)^num_dimensions entries.
 *
 * The iorder_ and pntr_ should be treated as "private" unless being copied to GPU memory.
 */
struct dimension_sort
{
  //! \brief Empty sort, used for an empty matrix.
  dimension_sort() {}
  //! \brief Sort the indexes dimension by dimension.
  dimension_sort(indexset const &iset);

  //! \brief Number of 1d vectors in dimensions dim
  int num_vecs(int dimension) const { return static_cast<int>(pntr_[dimension].size() - 1); }
  //! \brief Begin offset of the i-th vector
  int vec_begin(int dimension, int i) const { return pntr_[dimension][i]; }
  //! \brief End offset (one past the last entry) of the i-th vector
  int vec_end(int dimension, int i) const { return pntr_[dimension][i + 1]; }

  //! \brief Get the j-th global offset
  int map(int dimension, int j) const { return iorder_[dimension][j]; }
  //! \brief Get the 1d index of the j-th entry
  int operator()(indexset const &iset, int dimension, int j) const { return iset[iorder_[dimension][j]][dimension]; }

  //! \brief Holds the order of the indexes re-sorted for each dimension
  std::array<std::vector<int>, max_num_dimensions> iorder_;
  //! \brief Holds the offsets of each group of indexes that belong to a single "line" of the grid
  std::array<std::vector<int>, max_num_dimensions> pntr_;
};

/*!
 * \brief Finds the set of all missing ancestors.
 *
 * Returns the set, so that the union of the given set and the returned set
 * will be ancestry complete.
 *
 * \param iset is the set to be completed
 * \param hierarchy of 1D connections where the lower-triangular part is
 *        the ancestry list for each row, i.e., row i-th ancestors are
 *        listed between row_begin(i) and row_diag(i)
 * \param level_edges holds only the edge connections between elements
 *        one the same level of the hierarchy
 *
 * \returns a set of indexes so that the union of the original iset and
 *          the result will have the following properties:
 *
 * - the union will hold the hierarchy completion of iset
 * - the union will hold all edge neighbors of iset
 * - the union is not hierarchy complete (padded edge cell may be missing ancestors)
 * - the union is not complete with respect to the level_edges,
 *   i.e., only the immediate neighbors are considered
 *
 * Those properties guarantees correctness of the global generalized Kronecker
 * algorithm for the original indexes in iset.
 */
indexset compute_ancestry_completion(indexset const &iset,
                                     connect_1d const &hierarchy);

#ifdef ASGARD_USE_GPU
struct gpu_grid_data {
  //! number of 1d strips in each dimension
  std::array<int, max_num_dimensions> num_vecs;
  //! dsort pntr stored on the gpu
  std::array<gpu::vector<int>, max_num_dimensions> pntr;
  //! dsort order stored on the gpu
  std::array<gpu::vector<int>, max_num_dimensions> order;
  //! dsort sorted indexes stored on the gpu
  std::array<gpu::vector<int>, max_num_dimensions> sorted;
  //! level for each group of vecs
  std::array<gpu::vector<int>, max_num_dimensions> vec_levels;
};
#endif

/*!
 * \brief Manger for a sparse grid multi-index set
 *
 * \par Main components
 * The main components of the grid are an indexset and a corresponding dimension_sort.
 * Read access is provided for the multi-indexes and the grid can be refined using different
 * strategies.
 * After a refinement, the sparse grid can also remap a state vector from the old the grid
 * to the new, by removing the data corresponding to the removed cells and adding zeros for
 * the new cells.
 *
 * \par Generations
 * Many components of ASGarD need to prepare intermediate data-structures based on the current
 * set of indexes; therefore, there needs to be a mechanism that indicates when the grid
 * has changed and the intermediates have to be updated.
 * Simply counting the number of indexes is not sufficient, since refinement can both add and remove
 * indexes, e.g., adding one index and removing another will change the grid but not change
 * the number of indexes.
 * Thus, we introduce the generation index, every time a refinement operation updates the grid,
 * the generation index is incremented and that is the correct way to detect a change and update
 * the appropriate data-structures.
 * The generation index never decreases until we overflow the 32-bit signed int, thus the correct
 * way to compare generations is the != operator (equal or not equal),
 * as opposed to > (greater than or less than).
 */
class sparse_grid
{
public:
  //! indicates whether to refine, coarsen (compress) or do both
  enum class strategy {
    //! add indexes based on the tolerance, does not remove indexes
    refine,
    //! remove indexes only (compress the solution)
    coarsen,
    //! simultaneously add and remove indexes
    adapt
  };

  //! makes and empty grid, reinit before use
  sparse_grid() = default;
  //! number of dimensions and levels
  sparse_grid(prog_opts const &options);
  //! Returns the number of dimensions for the multi-index set
  int num_dims() const { return iset_.num_dimensions(); }
  //! Returns the number of indexes
  int64_t num_indexes() const { return iset_.num_indexes(); }

  //! returns pointer to the i-th index in the grid
  int const *operator[] (int64_t i) const { return iset_[i]; }

  //! access the internal indexset
  indexset const &iset() const { return iset_; }
  //! access the sort applied to the index set
  dimension_sort const &dsort() const { return dsort_; }
  //! calls the () operator on the sort
  int dsorted(int d, int j) const { return dsort_(iset_, d, j); }

  //! Testing purposes, returns the raw vector of indexes
  std::vector<int> const &indexes() const { return iset_.indexes(); }

  //! Returns the current level
  int current_level(int d) const { return level_[d]; }
  //! Returns the first index disallowed due to the max level
  int max_index(int d) const { return max_index_[d]; }
  //! Returns the current generation of the grid
  int generation() const { return generation_; }
  /*!
   * \brief Update the grid based on the strategy and current state
   *
   * \tparam P is float or double
   *
   * \param atolerance indicates the absolute tolerance for the refinement
   * \param rtolerance indicates the relative tolerance for the refinement
   * \param block_size is the number of degrees of freedom in a cell
   * \param hierarchy is the volume hierarchy build up to the max level
   * \param mode indicates whether we are coarsening, refining or both (adapt)
   * \param state the magnitude of the indexes in the cell will guide the refinement,
   *              the size of \b state should be block_size * num_indexes()
   */
  template<typename P>
  void refine(P atolerance, P rtolerance, int block_size, connect_1d const &hierarchy,
              strategy mode, std::vector<P> const &state);

  //! remaps the vector entries from an old grid to the new one, pads with zero
  template<typename P>
  void remap(int block_size, std::vector<P> &state) const;

  //! returns the internal set of cells
  std::vector<int> const &get_cells() const { return iset_.indexes(); }

  //! print summary of the grid
  void print_stats(std::ostream &os) const;

  #ifdef ASGARD_USE_MPI
  //! send the grid from the leader to all the sub-grids
  void mpi_sync(resource_set const &rcs, int last_gen);
  #endif

  #ifdef ASGARD_USE_GPU
  //! send the grid to all of the managed GPUs, check if needed
  void gpu_sync() {
    if (gpu_generation_ == generation_)
      return; // nothing to sync
    // this is split into two methods, so that the if statement can be inlined
    // while the load process uses OpenMP and more complex code
    gpu_generation_ = generation_;
    gpu_load();
  }
  //! send the grid to all of the managed GPUs, regardless if already loaded
  void gpu_load();
  //! return the data stored on the given gpu device
  gpu_grid_data const &gpu_grid(gpu::device device) const {
    return gpu_grid_[device.id];
  }
  #endif

  //! allows writer to save/load the grid
  template<typename P>
  friend class h5manager;

protected:
  //! marks the status of an entry
  enum class istatus {
    //! keep this index
    keep,
    //! refine this index, i.e., include the hierarchical descendants
    refine,
    //! mark index for removal
    clear
  };

  //! helper method, constructs a sparse grid given type and anisotropy
  template<grid_type gtype>
  indexset make_level_set(std::vector<int> const &levels);

private:
  int generation_ = 0;

  int mgroup = -1;
  indexset iset_;
  dimension_sort dsort_;

  std::array<int, max_num_dimensions> level_;
  std::array<int, max_num_dimensions> max_index_;

  std::vector<int64_t> map_;
  #ifdef ASGARD_USE_MPI
  std::vector<int> mpimeta;
  #endif
  #ifdef ASGARD_USE_GPU
  int gpu_generation_ = -2; // which is the last synced generation
  std::array<gpu_grid_data, max_num_gpus> gpu_grid_;
  #endif
};

//! overload for writing grid stats
inline std::ostream &operator<<(std::ostream &os, sparse_grid const &grid)
{
  grid.print_stats(os);
  return os;
}

} // namespace asgard
