#pragma once
#include "asgard_tools.hpp"

/*!
 * \file asgard_program_options.hpp
 * \brief Defines common enums and the options manager class prog_opts
 * \author The ASGarD Team
 * \ingroup asgard_common_options
 */

namespace asgard
{
/*!
 * \defgroup asgard_common_options ASGarD Common Options
 *
 * Common options shared by most or even all PDEs and discretization methods.
 * The tools provided here allow for reading the options from either the
 * command line or an input file and also specify PDE specific options.
 */

// forward declaration that can befriend relevant classes
template<typename P>
class h5manager;

/*!
 * \ingroup asgard_common_options
 * \brief Allows reducing the amount of cout-noise
 *
 * The high noise is usually desired for large simulations as the cout stream
 * will become a log for the various aspects of the problem.
 * This is very useful for debugging, catching early problems and keeping
 * an eye on a long simulation.
 *
 * However, high noise is bad for testing and potentially some large
 * applications, e.g., high verbosity may drown important messages from other
 * sub-systems.
 */
enum class verbosity_level
{
  //! do not generate cout output, except on errors and important warnings
  quiet,
  //! provides a few details but not too many
  low,
  //! provide a detailed log of the various aspects of the simulation
  high
};

/*!
 * \ingroup asgard_common_options
 * \brief the available solvers for implicit time stepping
 */
enum class solver_method
{
  //! direct solve using LAPACK, slow but stable
  direct,
  //! popular iterative solver, can be sensitive to the tolerance and restart frequency
  gmres,
  //! alternative to gmres, cheaper when taking many steps between restarts
  bicgstab
};

/*!
 * \ingroup asgard_common_options
 * \brief the available preconditioners for the solvers
 */
enum class precon_method
{
  //! probably not a good idea for an iterative solve
  none = 0,
  //! diagonal Jacobi preconditioner
  jacobi,
  //! using alternating direction pseudoinverse (experimental)
  adi
};

#ifndef __ASGARD_DOXYGEN_SKIP
/*!
 * \internal
 * \ingroup asgard_common_options
 * \brief Used for some methods, increment or replace the data in the call
 *
 * Allows to switch between incrementing the existing data or replacing it
 * right out.
 *
 * \endinternal
 */
enum class data_mode
{
  //! repalce/overwrite the current data
  replace,
  //! scale and overwrite, e.g., y = alpha * x
  scal_rep,
  //! increment the current data, e.g., y += x
  increment,
  //! scale and increment data, e.g., y += alpha * x
  scal_inc,
  //! multiply, e.g., y *= x
  multiply
};
#endif

/*!
 * \ingroup asgard_common_options
 * \brief Type of discretization grid
 */
enum class grid_type
{
  //! Standard spars grid
  sparse,
  //! Dense grid
  dense,
  //! Dense tensor of two sparse grids
  mixed
};

/*!
 * \ingroup asgard_common_options
 * types of time advance methods, declared here to be used in the program options
 */
enum class time_method
{
  //! steady state solution, not a time-stepping method
  steady = 0,
  //! forward euler method
  forward_euler,
  //! Runge Kutta 2-stage method, 3d order accuracy
  rk2,
  //! Runge Kutta 3-stage method, 4th order accuracy
  rk3,
  //! Runge Kutta 4-stage method, 4th order accuracy
  rk4,
  //! Implicit Backward-Euler, first order
  back_euler,
  //! Implicit Crank-Nicolson, second order
  cn,
  //! Implicit-explicit, first order
  imex1,
  //! Implicit-explicit, second order
  imex2,
};
/*!
 * \ingroup asgard_common_options
 * returns true if the given time_method is explicit
 */
bool is_explicit(time_method method);
/*!
 * \ingroup asgard_common_options
 * returns true if the given time_method is implicit
 */
bool is_implicit(time_method method);
/*!
 * \ingroup asgard_common_options
 * returns true if the given time_method is mixed implicit-explicit
 */
bool is_imex(time_method method);

/*!
 * \internal
 * \brief Internal use and testing
 *
 * Allows constructing prog_opts directly from a vector of string_view.
 * Works around the ambiguity in the constructor between using a filename
 * and a list of views.
 *
 * This takes non-owning reference to a vector of string_view objects,
 * useful for testing and making intermediate calls, but do not use for long term
 * storage, due to broken references during relocation.s
 * \endinternal
 */
struct vecstrview
{
  //! create a non-owning wrapper around string views
  explicit vecstrview(std::vector<std::string_view> const &s) : s_(s) {}
  //! returns the indexes, simplier
  operator std::vector<std::string_view> const &() const { return s_; }
  //! keep a reference to the list of views
  std::vector<std::string_view> const &s_;
};

/*!
 * \internal
 * \brief Internal use only
 *
 * Takes ownership of a vector of strings and creates an associated vector
 * of string_view that can be used until this object is destroyed.
 *
 * Used in conjuction with split_argv to hold the temporary result.
 * \endinternal
 */
struct split_views
{
  //! the ownership of a set of vectors
  split_views(std::vector<std::string> &&own)
      : own_(std::move(own)), strview(views_)
  {
    views_.reserve(own_.size() + 1);
    views_.push_back("test");
    for (auto &s : own_)
      views_.emplace_back(s);
  }
  //! pass the string_view vector to a method
  operator std::vector<std::string_view> const &()
  {
    return views_;
  }
  //! pass the vecstrview vector to a method
  operator vecstrview const &()
  {
    return strview;
  }
  //! the now owned vector of strings
  std::vector<std::string> own_;
  //! the corresponding vector of views
  std::vector<std::string_view> views_;
  //! wrapper around the views
  vecstrview strview;
};

/*!
 * \ingroup asgard_common_options
 * \brief Reads options from the command line and input files
 *
 * Processes all the options listed with
 * \code
 *   ./asgard --help
 * \endcode
 *
 * The file and command line capabilities are provided for
 * convenience and are entirely optional.
 * The asgsrd::prog_opts objects can be default-constructed as empty,
 * i.e., no options provided, then each of the values can be set manually
 * before passing into other ASGarD objects.
 * In most cases, if an option is not set, a default values will be used
 * based on the hardcoded PDE specification.
 *
 * Reading from the command line example:
 * \code
 *   int main(int argc, char **argv) {
 *
 *     asgard::prog_opts options(argc, argv);
 *
 *     // add defaults
 *     options.default_start_levels = {4, };
 *
 *     asgard::PDE<P> pde(options, domain);
 *
 * \endcode
 * This will process the inputs from argv and will also include any inputs
 * from a file. If an option is present multiple times, the last option
 * will take precedence, this options hard-coded in the file can be adjusted
 * from the command line, but only if they appear after the -if option.
 *
 * List of the standard ASGarD options can be seen with:
 * \code
 *   ./asgard --help # from the command line
 *   or
 *   asgard::prog_opts::print_help(); // from C++
 * \endcode
 *
 * If the input file options (-infile or -if) is encountered when processing
 * the command line argv, then the corresponding file will be processed as well.
 * The common options provided in the file (e.g., time-stepping method or
 * starting levels) will override any command line options before the -infile/if
 * option and will be overridden by any following command line options.
 *
 * The input file format consists of simple pairs of keys-values separated by colon ":"
 * Keys that match command line input options will be used as if provided by
 * the command line, other values can be specified in the file and retrieved
 * in the C++ code, e.g.,
 * \code
 *  # ASGarD standard options
 *  -tile         : read from test file
 *  -start_levels : 4 5
 *  -max_levels   : 7 8
 *
 *  # user specific options
 *  my keyname 1  : 1.E-4
 *  my keyname 2  : 5
 *  my keyname 3  : enable
 *  my keyname 4  : my favorite pde
 * \endcode
 * The three keys can be retrieved as double, int and bool respectively, or they can
 * all be read as strings.
 *
 * Reading extra options, e.g., if using the file above
 * \code
 *   // bar.value() will be set to 1.E-4
 *   std::optional<double> bar = options.file_value<double>("my keyname 1");
 *
 *   // foo.value() will be set to 5
 *   std::optional<int> foo = options.file_value<int>("my keyname 2");
 *
 *   // extra_name will be set to "my favorite pde"
 *   std::optional<std::string> extra_name = options.file_value<std::string>("my keyname 4");
 *
 *   // key3 will be empty, the keyname is missing/misspelled (missing "my")
 *   std::optional<bool> key3 = options.file_value<bool>("keyname 3");
 * \endcode
 * Supported types are bool, int, float, double, and std::string.
 * A good practice is to provide meaningful names for the keys, e.g.,
 * "temperature" or "Young's modulus".
 *
 * Reading from a hard-coded filename reduces flexibility but can improve
 * reproducibility:
 * \code
 *   prog_opts options("intput_filename.txt")
 * \endcode
 *
 * Notes about the API:
 * - If the keyword is missing or it is missing a value, the optional will be empty.
 * - The file_value() method may throw conversion error, e.g., trying to read
 *   an int from a sting describing a double.
 * - Boolean values interpreted as true are "true", "on", "enable", "1", "yes"
 * - Boolean values interpreted as false are "false", "off", "disable", "0", "no"
 * - Other boolean values are not accepted, will return empty optional.
 * - ASGarD will not automatically interpret or access or use any of the extra
 *   options provided in the file or the command line, those are a responsibility
 *   of the user code.
 */
struct prog_opts
{
  //! if provided, the title helps organize projects with multiple files
  std::string title;
  //! if provided, the subtitile is an addition to the main title
  std::string subtitle;

  //! read from -start_levels
  std::vector<int> start_levels;
  //! read from -max_levels
  std::vector<int> max_levels;

  //! sparse, dense or mixed grid
  std::optional<grid_type> grid;
  //! if using mixed group, the size of the first mixed group
  std::optional<int> mgrid_group;
  //! degree of the polynomial basis
  std::optional<int> degree;

  //! provides the absolute tolerance threshold for adaptivity
  std::optional<double> adapt_threshold;
  //! provides the relative tolerance threshold for adaptivity
  std::optional<double> adapt_ralative;

  //! time stepping method, explicit, implicit or imex
  std::optional<time_method> step_method;
  //! final time for the integration
  std::optional<double> stop_time;
  //! fixed time step, if missing the default cfl condition will be used
  std::optional<double> dt;
  //! number of fixed time steps to take
  std::optional<int> num_time_steps;

  //! solver for implicit or imex methods: direct, gmres, bicgstab
  std::optional<solver_method> solver;
  //! preconditioner, used for iterative solvers
  std::optional<precon_method> precon;
  //! tolerance for the iterative solvers (gmres, bicgstab)
  std::optional<double> isolver_tolerance;
  //! max number of iterations (inner iterations for gmres)
  std::optional<int> isolver_iterations;
  //! max number of output gmres iterations
  std::optional<int> isolver_inner_iterations;

  //! restart the simulation from a file
  std::string restart_file;
  //! filename for the last time step
  std::filesystem::path outfile;

  //! indicates if the --help option was selected
  bool show_help = false;
  //! indicates if the --version option was selected
  bool show_version = false;
  //! indicates if the exact solution should be ignored or the error computed and shown every time-step
  bool ignore_exact = false;

  //! print list of ASGarD specific options
  static void print_help(std::ostream &os = std::cout);
  //! print version and build (cmake) options
  static void print_version_help(std::ostream &os = std::cout);
  //! print the current set of options
  void print_options(std::ostream &os = std::cout) const;

  //! argv input values unrecognized by ASGarD
  std::vector<std::string> externals;

  //! converts the start_levels to a human readable string
  std::string start_levels_str() const { return vect_to_str(start_levels); }
  //! converts the max_levels to a human readable string
  std::string max_levels_str() const { return vect_to_str(max_levels); }

  //! create empty options, allows to manually fill the options later
  prog_opts() = default;

  //! process the command line arguments
  prog_opts(int const argc, char const *const *argv);

  //! process from a file
  explicit prog_opts(std::filesystem::path const &filename)
      : infile(filename)
  {
    process_file("<executable>");
  }

  //! for testing purposes, can read from manually specified argc/argv
  explicit prog_opts(vecstrview const &argv)
  {
    process_inputs(argv, handle_mode::from_cli);
  }

  //! read an extra option from a file
  template<typename out_type>
  std::optional<out_type> file_value(std::string_view const &s) const
  {
    return get_val<out_type>(filedata, s);
  }
  //! read an extra option from the cli extras
  template<typename out_type>
  std::optional<out_type> extra_cli_value(std::string_view const &s) const
  {
    return get_val<out_type>(externals, s);
  }
  //! read an extra option from the cli extras
  template<typename out_type>
  std::optional<out_type> extra_cli_value_group(std::vector<std::string> const &group) const
  {
    std::optional<out_type> result;
    for (auto const &g : group) {
      if (not result)
        result = get_val<out_type>(externals, g);
      if (not result)
        result = get_val<out_type>(filedata, g);
    }
    return result;
  }
  //! check if an extra option was present in the cli
  bool has_cli_entry(std::string_view const &s) const
  {
    return std::any_of(externals.begin(), externals.end(),
                       [&](std::string const &v)-> bool { return (v == s); });
  }
  //! check if an extra option was present in the cli or set to true in a file
  bool has_entry(std::string_view const &s) const
  {
    if (has_cli_entry(s)) // if present in the cli
      return true;
    // not in the cli, check the file
    return file_value<bool>(s).value_or(false);
  }

  /*!
   * \brief returns a list of cli options that are neither ASGarD standard nor in the provded lists
   *
   * Since custom files can include problem specific command line options,
   * it is important to allow custom options, while also provide a way to catch
   * misspelled or erroneous entries.
   * This method will return a vector of command line entries that
   * are not standard ASGarD options and not included in either of the two
   * user-provided lists.
   *
   * \param singles are valid custom options that appear by themselves, i.e.,
   *                do not require a second value entry
   * \param with_value are valid custom options that should be followed by a value,
   *                   this, both entries are considered "known"
   *
   * \returns a list of command-line entries that are neither ASGarD nor known custom
   *          options
   *
   * See \ref asgard_examples_continuity_md
   */
  std::vector<std::string> get_unknown(std::vector<std::string> const &singles,
                                       std::vector<std::string> const &with_value) const
  {
    std::vector<std::string> result;
    auto ie = externals.begin();
    while (ie < externals.end())
    {
      if (std::any_of(singles.begin(), singles.end(),
                      [&](std::string const &s)-> bool { return (s == *ie); }))
      {
        ++ie;
      } else if (std::any_of(with_value.begin(), with_value.end(),
                             [&](std::string const &s)-> bool { return (s == *ie); }))
      {
        std::advance(ie, 2); // the second entry is the value
      }
      else
      {
        // unknown entry
        result.push_back(*ie++);
      }
    }
    return result;
  }
  //! throws if unknown command line arguments are encountered, see get_unknown()
  void throw_if_argv_not_in(std::vector<std::string> const &singles,
                            std::vector<std::string> const &with_value) const {
    std::vector<std::string> unknown = get_unknown(singles, with_value);
    if (not unknown.empty()) {
      std::string ucli = "unknown command line argument(s) encountered\n";
      for (auto const &u : unknown)
        ucli += u + '\n';

      throw std::runtime_error(ucli);
    }
  }
  //! throws if any invalid (unknown by ASGarD) command line arguments are present
  void throw_if_invalid() const {
    throw_if_argv_not_in({}, {});
  }

  //! sets the title, if the user did not provide a custom title
  void set_default_title(std::string_view const &dtitle) {
    if (title.empty())
      title = dtitle;
  }

  //! reads and returns a file_value, skips the optional but throws if the value is missing
  template<typename out_type>
  out_type file_required(std::string_view const &s) const
  {
    std::optional<out_type> x = file_value<out_type>(s);
    if (infile.empty())
      throw std::runtime_error(std::string("missing an input file with required entry '")
                               + std::string(s) + std::string("'"));
    if (not x)
      throw std::runtime_error(std::string("file '") + std::string(infile)
                               + std::string("' is missing required entry '")
                               + std::string(s) + std::string("'"));
    return x.value();
  }

  //! throw an exception if the user attempts to select a non-imex stepping method
  void throw_if_not_imex_stepper() const {
    // if either default or specific step_method has been set, check if it is imex
    // if not set or not imex, then throw
    if ((step_method or default_step_method) and
         is_imex(step_method.value_or(default_step_method.value())))
        return;

    throw std::runtime_error("invalid time-stepping method, only imex methods are allowed");
  }

  //! sets the step-method but issues a warning if a method is already provided
  void force_step_method(time_method method)
  {
    if (step_method)
      std::cerr << "warning: overriding the user-requested -step-method" << std::endl;
    step_method = method;
  }
  //! sets the step-method but issues a warning if a method is already provided
  void force_solver(solver_method method)
  {
    if (solver)
      std::cerr << "warning: overriding the user-requested -solver" << std::endl;
    solver = method;
  }
  //! used in palce of start_levels, if start_levels is not provided
  std::vector<int> default_start_levels;
  //! used in palce of degree, if degree is not provided
  std::optional<int> default_degree;
  //! used in place of dt, if dt is not set
  std::optional<double> default_dt;
  //! used in place of stop time, if stop time is not provided
  std::optional<double> default_stop_time;
  //! used in place of the step method, if step method is provided
  std::optional<time_method> default_step_method;
  //! used in place of the solver type, if solver type is not provided
  std::optional<solver_method> default_solver;
  //! used in place of the preconditioner type, if preconditioner is not specified
  std::optional<precon_method> default_precon;
  //! used in place of the tolerance, if tolerance is not specified
  std::optional<double> default_isolver_tolerance;
  //! max number of iterations (inner iterations for gmres)
  std::optional<int> default_isolver_iterations;
  //! max number of outer gmres iterations
  std::optional<int> default_isolver_inner_iterations;

  //! returns the first available from stop-time, default-stop-time or -1
  double get_stop_time() const { return stop_time.value_or(default_stop_time.value_or(-1)); }
  //! returns the first available from dt, default-dt or -1
  double get_dt() const { return dt.value_or(dt.value_or(-1)); }
  //! returns the max-level based on the current set of options
  int max_level() const {
    int ml = 0;
    if (start_levels.empty() and not default_start_levels.empty())
      ml = *std::max_element(default_start_levels.begin(),default_start_levels.end());
    if (not start_levels.empty())
      ml = std::max(ml, *std::max_element(start_levels.begin(),start_levels.end()));
    if (not max_levels.empty())
      ml = std::max(ml, *std::max_element(max_levels.begin(),max_levels.end()));
    return ml;
  }

  //! returns true if the options indicate a restart file
  bool restarting() const { return not restart_file.empty(); }

  //! sets default view for the plotter
  std::string default_plotter_view;
  //! allows overriding the verbosity level
  std::optional<verbosity_level> verbosity;

  #ifdef ASGARD_USE_MPI
  //! MPI communicator to be used, it defaults to MPI_COMM_WORLD
  MPI_Comm mpicomm = MPI_COMM_WORLD;
  //! returns true if this rank is rank 0 on the current mpicomm
  bool is_mpi_rank_zero() const { return (mpi::comm_rank(mpicomm) == 0); }
  #else
  bool constexpr is_mpi_rank_zero() const { return true; } // always "zero rank"
  #endif

  //! (internal use) if we encounter a "no-adapt" option, must skip adaptivity during restart
  bool set_no_adapt = false;

  //! provides a long string for the given time-stepping method
  static std::string get_name(time_method);

  //! testing/development purposes, not needed in production, interpolation points in (-1, 1), must be degree + 1
  std::vector<double> interp_points;
  //! testing/development purposes, not needed in production, order on the higher level, see the comment in asgard_interp.cpp
  std::vector<int> interp_horder;

private:
  //! mapping from cli options to variables and actions
  enum class optentry
  {
    show_help,
    version_help,
    input_file,
    ignore_exact,
    title,
    subtitle,
    grid_mode,
    step_method,
    adapt_threshold,
    adapt_relative,
    no_adapt,
    start_levels,
    max_levels,
    degree,
    num_time_steps,
    output_file,
    stop_time,
    dt,
    solver,
    precond,
    isol_tolerance,
    isol_iterations,
    isol_inner_iterations,
    restart_file,
    view,
    set_verbosity
  };
  //! indicate how the reading is done
  enum class handle_mode
  {
    from_file, // reading from file
    from_cli   // reading from cli
  };

  //! input filename
  std::filesystem::path infile;

  //! file inputs, ordered as pairs by line
  std::vector<std::string> filedata;
  //! process input file, exec_name is the name of the executable
  void process_file(std::string_view const &exec_name);

  //! not in the constructor so it can be reused when reading from file
  void process_inputs(std::vector<std::string_view> const &argv, handle_mode mode);

  //! converts a string of ints into a vector of ints, limited to max_num_dimensions
  static std::vector<int> parse_ints(std::string const &number_string)
  {
    std::stringstream number_stream(number_string);
    std::vector<int> result;
    result.reserve(max_num_dimensions);
    while (!number_stream.eof())
    {
      std::string word;
      number_stream >> word;
      int temp_int = -1;

      // remove any leading or trailing '"'
      size_t pos = word.find_first_of('\"');
      if (pos != std::string::npos)
        word.erase(word.begin() + pos);

      if (std::stringstream(word) >> temp_int)
      {
        if (result.size() == max_num_dimensions)
        { // too many ints, return invalid result
          result.clear();
          return result;
        }
        else
          result.push_back(temp_int);
      }
    }

    return result;
  }
  /*!
   * \brief Find the value (with specified type) for the given parameter "s"
   *
   * \tparam out_type is the type of the value, supported types are int, bool, float/double, and string
   *
   * \param strs list of strings representing parameters, may come from a file or a testing string
   * \param s is the string representing the parameter, e.g., '-dims'
   *
   * \returns empty optional if the parameter is missing or (if found) the value
   *
   * \throws runtime error is there is a problem with the conversion
   */
  template<typename out_type>
  std::optional<out_type> get_val(std::vector<std::string> const &strs,
                                  std::string_view const &s) const
  {
    static_assert(std::is_same_v<out_type, int> or std::is_same_v<out_type, bool>
                  or std::is_same_v<out_type, float> or std::is_same_v<out_type, double>
                  or std::is_same_v<out_type, std::string>,
                  "prog_opts can only process: int, float, double, bool or string");
    for (size_t i = 0; i < strs.size(); i++)
    {
      if (strs[i] == s)
      {
        try {
          if (i + 1 == strs.size())
            return {};
          const std::string &val = strs[i + 1];
          if constexpr (std::is_same_v<out_type, std::string>)
            return val;
          else if constexpr (std::is_same_v<out_type, int>)
            return std::stoi(val);
          else if constexpr (std::is_same_v<out_type, double>)
            return std::stod(val);
          else if constexpr (std::is_same_v<out_type, float>)
            return std::stof(val);
          else if constexpr (std::is_same_v<out_type, bool>)
          {
            if (val == "on" or val == "yes" or val == "enable" or val == "true"
                or val == "1")
              return true;
            else if (val == "off" or val == "no" or val == "disable"
                    or val == "false" or val == "0")
              return false;
            else
              throw std::invalid_argument("bad value for bool");
          }
        } catch (std::invalid_argument &) {
          std::string msg = std::string("invalid value for '") + std::string(s)
              + "', cannot convert '" + strs[i + 1] + "' to '";
          if constexpr (std::is_same_v<out_type, std::string>)
            msg += "string'";
          else if constexpr (std::is_same_v<out_type, int>)
            msg += "int'";
          else if constexpr (std::is_same_v<out_type, double>)
            msg += "double'";
          else if constexpr (std::is_same_v<out_type, float>)
            msg += "float'";
          else if constexpr (std::is_same_v<out_type, bool>)
            msg += "bool'";

          throw std::runtime_error(msg);
        } catch (std::out_of_range &) {
          std::string msg = std::string("invalid value for '") + std::string(s)
              + "', out-of-range error in conversion of '" + strs[i + 1] + "' to '";
          if constexpr (std::is_same_v<out_type, std::string>)
            msg += "string'";
          else if constexpr (std::is_same_v<out_type, int>)
            msg += "int'";
          else if constexpr (std::is_same_v<out_type, double>)
            msg += "double'";
          else if constexpr (std::is_same_v<out_type, float>)
            msg += "float'";
          else if constexpr (std::is_same_v<out_type, bool>)
            msg += "bool'";

          throw std::runtime_error(msg);
        }
      }
    }
    return {};
  }

  //! converts vector of ints into a string
  static std::string vect_to_str(std::vector<int> const &ints)
  {
    std::string s = "";
    for (auto i : ints)
      s += ((i < 10) ? "  " : " ") + std::to_string(i);
    return s;
  }
};

#ifndef __ASGARD_DOXYGEN_SKIP
/*!
 * \internal
 * \brief (testing) splits a single string into multiple strings by spaces
 *
 * The method is intended for testing where it is much easier to write
 * a single string, e.g., "-p continuity_1 -d 3 -l 4" as opposed to multiple
 * lines setting pde_choice, degree and start_levels.
 *
 * However, the parsing of the string has little to no robustness,
 * especially when it comes to passing in lists.
 *
 * The use of this method in production is strongly discouraged.
 * \endinternal
 */
split_views split_argv(std::string_view const &opts);

/*!
 * \internal
 * \brief Makes a prog_opts object from a single sting, see split_argv
 *
 * \endinternal
 */
inline prog_opts make_opts(std::string const &cli)
{
  return prog_opts(split_argv(cli));
}
#endif

//! overload for writing options to a stream
inline std::ostream &operator<<(std::ostream &os, prog_opts const &options)
{
  options.print_options(os);
  return os;
}

} // namespace asgard
