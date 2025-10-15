#include "asgard_indexset.hpp"

namespace asgard
{

// the signature of callable is
// std::function<bool(std::array<int, max_num_dimensions> const &index)>
template<typename callable>
inline std::vector<int> generate_lower_index_set(
    size_t num_dims, callable inside)
{
  size_t c   = 0;
  bool is_in = true;
  std::array<int, max_num_dimensions> root;
  std::fill_n(root.begin(), num_dims, 0);
  std::vector<int> indexes;
  // reserve 1-4 pages to save on the first few relocations
  indexes.reserve( (16 * 1024) / (num_dims * sizeof(int)) );
  while (is_in or c > 0)
  {
    if (is_in)
    {
      indexes.insert(indexes.end(), root.begin(), root.begin() + num_dims);
      c = num_dims - 1;
      root[c]++;
    }
    else
    {
      std::fill(root.begin() + c, root.begin() + num_dims, 0);
      root[--c]++;
    }
    is_in = inside(root);
  }
  return indexes;
}

template<typename data_container>
indexset make_index_set(organize2d<int, data_container> const &indexes)
{
  int64_t num_indexes    = indexes.num_strips();
  int64_t num_dimensions = indexes.stride();

  // compute a map that gives the sorted order of the indexes
  std::vector<int64_t> map(num_indexes);
  std::iota(map.begin(), map.end(), 0);

  std::sort(map.begin(), map.end(),
            [&](int64_t a, int64_t b) -> bool {
              for (int64_t d = 0; d < num_dimensions; d++)
              {
                if (indexes[a][d] < indexes[b][d])
                  return true;
                if (indexes[a][d] > indexes[b][d])
                  return false;
              }
              return false; // equal should be false, as in < operator
            });

  // in the sorted order, it's easy to find repeated entries
  int64_t repeated_indexes = 0;
  for (int64_t i = 0; i < num_indexes - 1; i++)
  {
    bool is_repeated = [&]() -> bool {
      for (int64_t d = 0; d < num_dimensions; d++)
        if (indexes[map[i]][d] != indexes[map[i + 1]][d])
          return false;
      return true;
    }();
    if (is_repeated)
    {
      map[i] = -1;
      repeated_indexes += 1;
    }
  }

  // map the unique entries into a vector and load into an indexset
  std::vector<int> sorted_indexes;
  sorted_indexes.reserve(num_dimensions * (num_indexes - repeated_indexes));
  for (int64_t i = 0; i < num_indexes; i++)
  {
    if (map[i] != -1)
      sorted_indexes.insert(sorted_indexes.end(), indexes[map[i]],
                            indexes[map[i]] + num_dimensions);
  }

  return indexset(num_dimensions, std::move(sorted_indexes));
}

template indexset
make_index_set(organize2d<int, std::vector<int>> const &indexes);
template indexset
make_index_set(organize2d<int, int *> const &indexes);
template indexset
make_index_set(organize2d<int, int const *> const &indexes);

dimension_sort::dimension_sort(indexset const &iset)
{
  int num_dimensions = iset.num_dimensions();
  int num_indexes    = iset.num_indexes();

  for (int d : iindexof(num_dimensions))
    iorder_[d] = std::vector<int>(num_indexes);

#pragma omp parallel for
  for (int d = 0; d < num_dimensions - 1; d++)
  {
    // for each dimension, use the map to group points together
    std::iota(iorder_[d].begin(), iorder_[d].end(), 0);
    std::sort(iorder_[d].begin(), iorder_[d].end(), [&](int a, int b) -> bool {
      const int *idxa = iset[a];
      const int *idxb = iset[b];
      for (int j = 0; j < num_dimensions; j++)
      {
        if (j != d)
        {
          if (idxa[j] < idxb[j])
            return true;
          if (idxa[j] > idxb[j])
            return false;
        }
      }
      // lexigographical order, dimension d is the fastest moving one
      if (idxa[d] < idxb[d])
        return true;
      if (idxa[d] > idxb[d])
        return false;
      return false;
    });
  }
  // no sort needed for the last dimenison
  std::iota(iorder_[num_dimensions - 1].begin(), iorder_[num_dimensions - 1].end(), 0);

  // check if multi-indexes match in all but one dimension
  auto match_outside_dim = [&](int d, int const *a, int const *b) -> bool {
    for (int j = 0; j < d; j++)
      if (a[j] != b[j])
        return false;
    for (int j = d + 1; j < num_dimensions; j++)
      if (a[j] != b[j])
        return false;
    return true;
  };

  // split the map into vectors of identical coefficients in all but 1d
  if (num_dimensions == 1)
  {
    pntr_[0].push_back(0);
    pntr_[0].push_back(num_indexes);
  }
  else
  {
#pragma omp parallel for
    for (int d = 0; d < num_dimensions; d++)
    {
      int const *c_index = iset[iorder_[d][0]];
      pntr_[d].push_back(0);
      for (int i = 1; i < num_indexes; i++)
      {
        if (not match_outside_dim(d, c_index, iset[iorder_[d][i]]))
        {
          pntr_[d].push_back(i);
          c_index = iset[iorder_[d][i]];
        }
      }
      pntr_[d].push_back(num_indexes);
    }
  }
}

indexset compute_ancestry_completion(indexset const &iset,
                                     connect_1d const &hierarchy)
{
  int const num_dimensions = iset.num_dimensions();

  // store all missing ancestors here
  vector2d<int> missing_ancestors(num_dimensions, 0);

  // do just one pass, considering the indexes in the iset only
  // after this, missing_ancestors will hold those from iset
  // we need to recurs only on the missing_ancestors from now on

  #pragma omp parallel
  {
    std::array<int, max_num_dimensions> scratch;
    vector2d<int> local_missing(num_dimensions, 0);

    #pragma omp for
    for (int i = 0; i < iset.num_indexes(); i++)
    {
      // construct all parents, even considering the edges
      std::copy_n(iset[i], num_dimensions, scratch.begin());
      // check the parents in each direction
      for (int d = 0; d < num_dimensions; d++)
      {
        int const row = scratch[d];
        for (int j = hierarchy.row_begin(row); j < hierarchy.row_diag(row); j++)
        {
          scratch[d] = hierarchy[j];
          if (iset.missing(scratch.data()))
            local_missing.append(scratch.data(), 1);
        }
        scratch[d] = row;
      }
    }

    #pragma omp critical
    {
      missing_ancestors.append(local_missing[0], local_missing.num_strips());
    }
  }

  bool ancestry_complete = missing_ancestors.empty();

  indexset pad_indexes = make_index_set(missing_ancestors);

  // the assumption here it that the padded set will be smaller
  // then the iset, so we do one loop over the large set and then we work
  // only with the smaller pad_indexes
  while (not ancestry_complete)
  {
    // all new found indexes are already in pad_indexes
    // missing_ancestors holds the ones from this iteration only
    missing_ancestors.clear();

    #pragma omp parallel
    {
      std::array<int, max_num_dimensions> scratch;
      vector2d<int> local_missing(num_dimensions, 0);

      #pragma omp for
      for (int i = 0; i < pad_indexes.num_indexes(); i++)
      {
        // construct all parents, even considering the edges
        std::copy_n(pad_indexes[i], num_dimensions, scratch.begin());
        // check the parents in each direction
        for (int d = 0; d < num_dimensions; d++)
        {
          int const row = scratch[d];
          for (int j = hierarchy.row_begin(row); j < hierarchy.row_diag(row); j++)
          {
            scratch[d] = hierarchy[j];
            if (pad_indexes.missing(scratch.data()))
              local_missing.append(scratch.data(), 1);
          }
          scratch[d] = row;
        }
      }

      #pragma omp critical
      {
        missing_ancestors.append(local_missing[0], local_missing.num_strips());
      }
    }

    // check if every ancestor is already in either iset or pad_indexes
    ancestry_complete = missing_ancestors.empty();

    if (not ancestry_complete)
    {
      // add the new indexes into the pad_indexes (could be improved)
      missing_ancestors.append(pad_indexes[0], pad_indexes.num_indexes());
      pad_indexes = make_index_set(missing_ancestors);
    }
  }

  return pad_indexes;
}

sparse_grid::sparse_grid(prog_opts const &options)
  : mgroup(options.mgrid_group.value_or(-1))
{
  expect(not options.start_levels.empty());
  expect(mgroup < static_cast<int>(options.start_levels.size()));

  grid_type gtype = options.grid.value_or(grid_type::sparse); // defaults to sparse
  std::vector<int> const &levels = options.start_levels;

  std::fill(level_.begin(), level_.end(), 0);
  std::fill(max_index_.begin(), max_index_.end(), 0);

  indexset iset = [&]() -> indexset {
    switch (gtype)
    {
      case grid_type::dense:
        return make_level_set<grid_type::dense>(levels);
      case grid_type::sparse:
        return make_level_set<grid_type::sparse>(levels);
      default: // grid_type::mixed
        return make_level_set<grid_type::mixed>(levels);
    };
  }();

  int const numd = iset.num_dimensions();

  if (options.max_levels.empty()) { // testing or not using adaptivity
    for (int d : iindexof(numd)) {
      level_[d]     = levels[d];
      max_index_[d] = (levels[d] == 0) ? 1 : fm::ipow2(levels[d]);
    }
  } else {
    for (int d : iindexof(numd)) {
      level_[d]     = levels[d];
      max_index_[d] = (options.max_levels[d] == 0) ? 1 : fm::ipow2(options.max_levels[d]);
    }
  }

  int64_t const num_iset = iset.num_indexes();
  int64_t num_indexes    = 0;
  for (int64_t i = 0; i < num_iset; i++)
  {
    int const *p = iset[i];
    int64_t n = 1;
    for (int d = 0; d < numd; d++)
      n *= (p[d] < 2) ? 1 : fm::ipow2(p[d] - 1);
    num_indexes += n;
  }

  std::vector<int> idx_raw(num_indexes * numd);
  span2d<int> idx(numd, num_indexes, idx_raw.data());
  int64_t ii = 0;
  for (int64_t i = 0; i < num_iset; i++)
  {
    std::array<int, max_num_dimensions> offsets;
    int const *p = iset[i];
    for (int d = 0; d < numd; d++)
      offsets[d] = (p[d] < 2) ? 1 : fm::ipow2(p[d] - 1);

    std::array<int, max_num_dimensions> vec;
    std::fill(vec.begin(), vec.end(), 0);

    bool is_in = true;
    int c = 0;
    while (is_in or c > 0)
    {
      if (is_in)
      {
        int *v = idx[ii++];
        for (int d = 0; d < numd; d++)
          v[d] = (p[d] == 0) ? 0 : (offsets[d] + vec[d]);
        c = numd - 1;
        vec[c]++;
      }
      else
      {
        std::fill(vec.begin() + c, vec.begin() + numd, 0);
        vec[--c]++;
      }

      is_in = (vec[c] < offsets[c]);
    }
  }

  iset_  = make_index_set(idx);
  dsort_ = dimension_sort(iset_);
}

template<grid_type gtype>
indexset sparse_grid::make_level_set(std::vector<int> const &levels)
{
  int numd = static_cast<int>(levels.size());

  if constexpr (gtype == grid_type::dense)
  {
    std::vector<int> idx = asgard::generate_lower_index_set(
      numd, [&](std::array<int, max_num_dimensions> const &index)
        -> bool {
          for (int d = 0; d < numd; d++)
            if (index[d] > levels[d])
              return false;
          return true;
        });
    return indexset(numd, std::move(idx));
  }
  else if constexpr (gtype == grid_type::sparse)
  {
    int64_t m = 1;
    for (auto const &l : levels)
      m *= (l == 0) ? 1 : l;
    std::array<int, max_num_dimensions> lidx;
    for (int d : iindexof(numd))
      lidx[d] = (levels[d] == 0) ? (m + 1) : (m / levels[d]);
    std::vector<int> idx = asgard::generate_lower_index_set(
      numd, [&](std::array<int, max_num_dimensions> const &index)
        -> bool {
          int l = 0;
          for (int d = 0; d < numd; d++)
            l += lidx[d] * index[d];
          return (l <= m);
        });
    return indexset(numd, std::move(idx));
  }
  else // if constexpr (gtype == grid_type::mixed)
  {
    int64_t m = 1;
    for (auto const &l : levels)
      m *= l;
    std::array<int, max_num_dimensions> lidx;
    for (int i = 0; i < numd; i++)
      lidx[i] = m / levels[i];
    std::vector<int> idx = asgard::generate_lower_index_set(
      numd, [&](std::array<int, max_num_dimensions> const &index)
        -> bool {
          int l1 = 0, l2 = 0;
          for (int d = 0; d < mgroup; d++)
            l1 += lidx[d] * index[d];
          for (int d = mgroup; d < numd; d++)
            l2 += lidx[d] * index[d];
          return (std::max(l1, l2) <= m);
        });
    return indexset(numd, std::move(idx));
  }
}

template<typename P>
void sparse_grid::refine(P atol, P rtol, int block_size, connect_1d const &hierarchy,
                         strategy mode, std::vector<P> const &state)
{
  tools::time_event refining("grid refining");
  int const num_dims = iset_.num_dimensions();

  int64_t const num = iset_.num_indexes();
  std::vector<P> weights(num);

  P wsum = 0.0;

  // compute the L^2 weight of each multi-index
  #pragma omp parallel
  {
    P lsum = 0;

    #pragma omp for
    for (int64_t i = 0; i < num; i++)
    {
      P w{0};
      for (int j : iindexof(block_size)) {
        P s = state[i * block_size + j];
        w += s * s;
      }
      weights[i] = std::sqrt(w);

      lsum += weights[i];
    }

    #pragma omp atomic
    wsum += lsum;
  }

  P const tol = rtol * std::sqrt(wsum) + atol;

  // decide which index to keep and which to clear
  std::vector<istatus> stat(num, istatus::keep);
#pragma omp parallel for
  for (int64_t i = 0; i < num; i++)
  {
    std::array<int, max_num_dimensions> idx;
    std::copy_n(iset_[i], num_dims, idx.data());

    if (weights[i] >= tol and mode != strategy::coarsen) {
      // large weight, must refine but only if kids are missing
      for (int d : iindexof(num_dims)) {
        idx[d] *= 2;
        if (iset_.missing(idx))
          stat[i] = istatus::refine;

        idx[d] += 1;
        // dont' search for the second kid if the first is missing
        if (stat[i] != istatus::refine and iset_.missing(idx))
          stat[i] = istatus::refine;

        idx[d] = iset_[i][d];
      }
    } else {
      // maybe remove, but only if the parents are small
      if (mode != strategy::refine) { // if we are allowed to remove nodes
        bool keep = false;
        for (int d : iindexof(num_dims)) {
          if (idx[d] == 0)
            continue;

          idx[d] /= 2;
          if (weights[ iset_.find(idx.data()) ] >= tol)
            keep = true;

          idx[d] = iset_[i][d];
        }
        if (not keep)
          stat[i] = istatus::clear;
      }
    }
  }

  // never remove index 0, must have at least one cell in the grid
  if (stat.front() == istatus::clear)
    stat.front() = istatus::keep;

  // count an upper bound for the new nodes
  int const num_family = 1 + 2 * num_dims; // self + kids
  int64_t reserve = 0;
  for (int64_t i = 0; i < num; i++)
  {
    switch (stat[i]) {
      case istatus::keep:
        reserve += 1;
        break;
      case istatus::refine:
        {
          bool valid_kid = false;
          for (int d : iindexof(num_dims)) {
            int const kid = 2 * iset_[i][d];
            if (kid < max_index_[d]) { // enforce the max-level
              valid_kid = true;
              break; // stop the loop over num_dims
            }
          }
          if (valid_kid)
            reserve += num_family;
        }
        break;
      default:
        break;
    }
  }

  // assign new memory for the kept + refined nodes
  std::vector<int> update;
  update.reserve(num_dims * reserve);
  for (int64_t i = 0; i < num; i++)
  {
    std::array<int, max_num_dimensions> idx;

    switch (stat[i]) {
      case istatus::keep:
        update.insert(update.end(), iset_[i], iset_[i] + num_dims);
        break;
      case istatus::refine:
        {
          update.insert(update.end(), iset_[i], iset_[i] + num_dims);
          std::copy_n(iset_[i], num_dims, idx.data());
          for (int d : iindexof(num_dims)) {
            idx[d] *= 2;
            if (idx[d] >= max_index_[d]) { // enforce the max-level
              idx[d] = iset_[i][d];
              continue;
            }
            update.insert(update.end(), idx.data(), idx.data() + num_dims);
            idx[d] += 1;
            update.insert(update.end(), idx.data(), idx.data() + num_dims);
            idx[d] = iset_[i][d];
          }
        }
        break;
      default: // remove the point, nothing to do
        break;
    }
  }

  indexset inew = make_index_set(span2d<int>(num_dims, update));

  inew += compute_ancestry_completion(inew, hierarchy);

  // indexset hcheck = compute_ancestry_completion(inew, hierarchy);
  // std::cout << "  --     new nodes: " << inew.num_indexes() << "\n";
  // std::cout << "  -- missing nodes: " << hcheck.num_indexes() << " (should be zero)\n";

  // check if the new grid is different
  bool change = false;
  if (inew.num_indexes() != iset_.num_indexes()) {
    change = true;
  } else {
    for (int64_t i = 0; i < num; i++) {
      for (int d : iindexof(num_dims)) {
        if (inew[i][d] != iset_[i][d]) {
          change = true;
          break;
        }
      }
      if (change)
        break;
    }
  }

  if (not change) // done, nothing to do here
    return;

  // find the map from the old indexes to the new ones
  int64_t const num_new = inew.num_indexes();
  map_.resize(inew.num_indexes());
#pragma omp parallel for
  for (int64_t i = 0; i < num_new; i++) {
    map_[i] = iset_.find(inew[i]);
  }

  std::fill_n(level_.begin(), num_dims, 0);

  #pragma omp parallel
  {
    std::array<int, max_num_dimensions> mylvl;
    std::fill_n(mylvl.begin(), num_dims, 0);

    #pragma omp for
    for (int64_t i = 0; i < num_new; i++) {
      for (int d = 0; d < num_dims; d++) {
        int const l = (inew[i][d] == 0) ? 0 : (1 + fm::intlog2(inew[i][d]));
        mylvl[d] = std::max(mylvl[d], l);
      }
    }

    #pragma omp critical
    {
      for (int d = 0; d < num_dims; d++)
        level_[d] = std::max(level_[d], mylvl[d]);
    }
  }

  iset_  = std::move(inew);
  dsort_ = dimension_sort(iset_);

  generation_ += 1; // grid changed
}

template<typename P>
void sparse_grid::remap(int block_size, std::vector<P> &state) const
{
  int64_t const num = iset_.num_indexes();

  std::vector<P> snew(num * block_size);

  span2d<P> old_state(block_size, state);
  span2d<P> new_state(block_size, snew);

#pragma omp parallel for
  for (int64_t i = 0; i < num; i++) {
    if (map_[i] > -1)
      std::copy_n(old_state[map_[i]], block_size, new_state[i]);
    else
      std::fill_n(new_state[i], block_size, P{0});
  }

  state = std::move(snew);
}

void sparse_grid::print_stats(std::ostream &os) const {
  os << "sparse grid:\n";
  os << "      levels  ";
  for (int d : iindexof(num_dims()))
    os << std::setw(4) << level_[d];
  os << "\n  max levels  ";
  for (int d : iindexof(num_dims()))
    os << std::setw(4) << ((max_index_[d] == 0) ? 0 : fm::intlog2(max_index_[d]));
  os << "\n  num indexes   " << tools::split_style(iset_.num_indexes()) << '\n';
}

#ifdef ASGARD_USE_MPI
void sparse_grid::mpi_sync(resource_set const &rcs, int last_gen) {
  mpimeta.resize(2 * max_num_dimensions + 2);
  // sync meta-data
  if (rcs.is_leader()) {
    auto im = mpimeta.begin();
    im = std::copy_n(level_.begin(), max_num_dimensions, im);
    im = std::copy_n(max_index_.begin(), max_num_dimensions, im);
    *im++ = generation_;
    *im++ = static_cast<int>(iset_.num_indexes_); // TODO: figure out the narrowing
    rcs.bcast(mpimeta);
  } else {
    rcs.bcast(mpimeta);
    std::copy_n(mpimeta.begin(), max_num_dimensions, level_.begin());
    std::copy_n(mpimeta.begin() + max_num_dimensions,
                max_num_dimensions, max_index_.begin());
  }
  // stage 2, send/recv indexes
  if (rcs.is_leader()) {
    if (generation_ != last_gen)
      rcs.bcast(iset_.indexes_);
  }
  else if (last_gen < 0 or generation_ != mpimeta[2 * max_num_dimensions])
  {
    generation_        = mpimeta[2 * max_num_dimensions];
    iset_.num_indexes_ = mpimeta[2 * max_num_dimensions + 1];

    iset_.indexes_.resize(iset_.num_indexes_ * iset_.num_dimensions_);
    rcs.bcast(iset_.indexes_);

    dsort_ = dimension_sort(iset_);
  }
}
#endif

#ifdef ASGARD_USE_GPU
void sparse_grid::gpu_load() {
  int const num_gpus = compute->num_gpus();
  static std::vector<int> sorted, vec_levels;

  for (int dim : iindexof(iset_.num_dimensions())) {

    sorted.resize(dsort_.vec_end(dim, dsort_.num_vecs(dim) - 1));

    for (int j = 0; j < static_cast<int>(sorted.size()); j++)
      sorted[j] = dsorted(dim, j);

    vec_levels.resize(dsort_.num_vecs(dim));
    for (int j = 0; j < dsort_.num_vecs(dim); j++) {
      // compute the level for the largest index, should be the last index in the vector group
      int const idx = dsorted(dim, dsort_.vec_end(dim, j) - 1);
      vec_levels[j] = (idx == 0) ? 0 : fm::intlog2(idx) + 1;
    }

    #pragma omp parallel for schedule(static, 1)
    for (int g = 0; g < num_gpus; g++) {
      compute->set_device(gpu::device{g});
      gpu_grid_[g].num_vecs[dim] = dsort_.num_vecs(dim);

      gpu_grid_[g].sorted[dim] = sorted;
      gpu_grid_[g].pntr[dim]   = dsort_.pntr_[dim];
      gpu_grid_[g].order[dim]  = dsort_.iorder_[dim];

      gpu_grid_[g].vec_levels[dim] = vec_levels;
    }
  }
}
#endif

template indexset sparse_grid::make_level_set<grid_type::dense>(std::vector<int> const &);
template indexset sparse_grid::make_level_set<grid_type::sparse>(std::vector<int> const &);
template indexset sparse_grid::make_level_set<grid_type::mixed>(std::vector<int> const &);

template void sparse_grid::refine<double>(double,  double,int, connect_1d const &,
                                          strategy, std::vector<double> const &);
template void sparse_grid::refine<float>(float, float, int, connect_1d const &,
                                         strategy, std::vector<float> const &);
template void sparse_grid::remap<double>(int, std::vector<double> &) const;
template void sparse_grid::remap<float>(int, std::vector<float> &) const;

} // namespace asgard
