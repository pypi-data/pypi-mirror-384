#include "asgard_wavelet_basis.hpp"

namespace asgard::basis
{
// generate_multi_wavelets routine creates wavelet basis (phi_co)
// then uses these to generate the two-scale coefficients which can be
// used (outside of this routine) to construct the forward multi-wavelet
// transform
std::array<std::vector<double>, 4> generate_multi_wavelets(int const degree)
{
  expect(degree >= 0);

  int const pdof = degree + 1;

  // These are the function outputs
  // g0,g1,h0, and h1 are two-scale coefficients
  // The returned phi_co is the wavelet basis
  // scalet_coefficients are the scaling function basis
  //   -- the scalet coefficients form the legendre basis
  //      from a monomial basis

  // hard-cording degree 0, 1, 2 (mostly for less rounding)
  if (degree <= 2)
  {
    constexpr double s2 = 1.41421356237309505;

    switch (degree)
    {
    case 0: {
      double const is2 = 1 / s2;
      std::vector<double> h0 = {is2,};
      std::vector<double> h1 = {is2,};
      std::vector<double> g0 = {-is2,};
      std::vector<double> g1 = {is2,};
      return {h0, h1, g0, g1};
    }
    case 1: {
      double const is2  = 1 / s2;
      double const is22 = 1 / (2 * s2);
      double const is6  = std::sqrt(6.0) / 4;
      std::vector<double> h0 = {is2, -is6, 0, is22};
      std::vector<double> h1 = {is2,  is6, 0, is22};
      std::vector<double> g0 = {0,  is22, -is2, is6};
      std::vector<double> g1 = {0, -is22,  is2, is6};
      return {h0, h1, g0, g1};
    }
    case 2: {
      double const is2  = 1 / s2;
      double const is22 = 1 / (2 * s2);
      double const is24 = 1 / (4 * s2);
      double const is6  = std::sqrt(6.0) / 4;
      double const is30 = 15 / (4.0 * std::sqrt(30.0));
      std::vector<double> h0 = {is2, -is6, 0, 0, is22, -is30, 0, 0, is24};
      std::vector<double> h1 = {is2,  is6, 0, 0, is22,  is30, 0, 0, is24};
      std::vector<double> g0 = {0, 0, -is22, 0,  is24, -is6, -is2, is30, 0};
      std::vector<double> g1 = {0, 0,  is22, 0, -is24, -is6,  is2, is30, 0};
      return {h0, h1, g0, g1};
    }
    default:
      break;
    };
  }

  std::vector<double> g0(pdof * pdof);
  std::vector<double> g1(pdof * pdof);
  std::vector<double> h0(pdof * pdof);
  std::vector<double> h1(pdof * pdof);

  basis::canonical_integrator quad(degree);

  // those are the transposes compared to the matrices used in the rest of the code
  auto leg = basis::legendre_poly<double>(degree);
  auto wav = basis::wavelet_poly(leg, quad);

  double constexpr  s2 = 1.41421356237309505;
  double constexpr is2 = 1.0 / s2;

  // Calculate Two-Scale Coefficients

  // Sums to directly generate H0, H1, G0, G1
  //  H0 and H1 are the "coarsening coefficients"
  //  These describe how two adjacent locations of a higher (finer resolution)
  //  level sum to give a lower (more coarse resolution) level coefficients
  //  G0 and G1 are the "refining or detail coefficients"
  //  These describe how lower level (more coarse resolution)
  //  is split into two higher (finer resolution) level coefficients
  //  H0 is the inner product of the scaling functions of two successive
  //   levels - thus the difference in roots
  // elem_1 is the scalet functions on (-1,0)
  // elem_2 is the scalet function of a lower level and therefore spans (-1,1)
  //  H1 is also the inner product of the scaling functions of two successive
  //   levels - thus the difference in roots
  // elem_3 is the scalet functions on (0,1)
  //  G0 is the inner product of the wavelet functions of one level
  //   with the scalet functions of a lower level
  //   - thus the difference in roots
  // elem_4 is the wavelet functions on (-1,0)
  //  G1 is also the inner product of the wavelet functions of one level
  //   with the scalet functions of a lower level
  // elem_5 is the scalet functions on (0,1)

  // if you have a function represented on a finer grid (say 2 n cells) with
  // a set of legendre coefficients per cell
  // representing the function using the n cell wavelets means multiplying by
  // the adjacent cells by G0 and G1 and adding them together
  // the remainder is formed by multiplying by H0 an H1 and adding it up
  // no we have the wavelets at level n and the corresponding remainder going up
  // on level 0, there will be just a remainders

  auto leg2 = basis::legendre_poly<double, basis::integ_range::right>(degree);
  double s = 1.0;

  for (int row = 0; row < pdof; ++row)
  {
    for (int col = 0; col < row; ++col)
    {
      double const it = quad.integrate_right(leg2[col], leg[row]);

      h1[row + col * pdof] = it;
      h0[row + col * pdof] = ((row - col) % 2 == 0) ? it : -it;
    }

    h0[row + row * pdof] = is2 / s;
    h1[row + row * pdof] = h0[row + row * pdof];

    s *= 2;
  }

  for (int row = 0; row < pdof; ++row)
  {
    for (int col = degree - row; col < pdof; ++col)
    {
      double const it = is2 * quad.integrate_right(leg2[col], wav[row] + pdof);

      g1[row + col * pdof] = it;
      g0[row + col * pdof] = ((col - row + degree) % 2 == 0) ? -it : it;
    }
  }

  double constexpr tol = 1.e-12;

  auto const normalize = [&](std::vector<double> &mat) -> void {
    for (auto &m : mat)
      if (std::abs(m) < tol)
        m = 0;
  };
  normalize(h0);
  normalize(h1);
  normalize(g0);
  normalize(g1);

  return {h0, h1, g0, g1};
}

} // namespace asgard::basis
