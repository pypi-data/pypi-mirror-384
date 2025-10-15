import sys

from ctypes import c_char_p, c_int, c_int64, c_double, c_float, c_void_p, POINTER, CDLL, create_string_buffer, RTLD_GLOBAL
import numpy as np

import h5py # required for now, maybe add lighter module later

_matplotlib_found_ = True
try:
    import matplotlib.pyplot as asgplot
except:
    _matplotlib_found_ = False

from asgard_config import __version__, __author__, __pyasgard_libasgard_path__, __enable_double__

libasgard = CDLL(__pyasgard_libasgard_path__, mode = RTLD_GLOBAL)

libasgard.asgard_make_dreconstruct_solution.restype = c_void_p
libasgard.asgard_make_freconstruct_solution.restype = c_void_p

libasgard.asgard_make_dreconstruct_solution.argtypes = [c_int, c_int64, POINTER(c_int), c_int, POINTER(c_double)]
libasgard.asgard_make_freconstruct_solution.argtypes = [c_int, c_int64, POINTER(c_int), c_int, POINTER(c_float)]

libasgard.asgard_pydelete_reconstruct_solution.argtypes = [c_void_p, ]

libasgard.asgard_print_version_help.argtypes = []

libasgard.asgard_reconstruct_solution_setbounds.argtypes = [c_void_p, POINTER(c_double), POINTER(c_double)]
libasgard.asgard_reconstruct_solution.argtypes = [c_void_p, POINTER(c_double), c_int, POINTER(c_double)]
libasgard.asgard_reconstruct_cell_centers.argtypes = [c_void_p, POINTER(c_double)]

step_method_map = ("Steady state solver",
                   "Forward-Euler 1-step (explicit)",  "Runge-Kutta 2-step (explicit)",
                   "Runge-Kutta 3-step (explicit)",    "Runge-Kutta 4-step (explicit)",
                   "Backward-Euler 1-step (implicit)", "Crank-Nicolson 1-step (implicit)",
                   "Implicit-Explicit 1-step (imex)",  "Implicit-Explicit 2-step (imex)")

class pde_snapshot:
    '''
    Reads an ASGarD HDF5 file with wavelet information and reconstrcts data
    for plotting.

    Example:
      import asgard
      import matplotlib.pyplot as plt

      snapshot = asgard.pde_snapshot("asgard_wavelet_10.h5")
      z, x, y = snapshot.plot_data2d([[-1.0, 1.0], [-2.0, 2.0]], nump = 100)
      plt.imshow(h, cmap='jet', extent=[-1.0, 1.0, -2.0, 2.0])
    '''
    def __del__(self):
        if self.recsol != None:
            libasgard.asgard_pydelete_reconstruct_solution(self.recsol)

    def __init__(self, filename, verbose = False):
        self.verbose = verbose
        if filename == "::aux-filed":
            self.recsol = None
            return

        if self.verbose:
            print(' -- reading from: %s' % filename)

        with h5py.File(filename, "r") as fdata:
            # keep this for reference of the keys that we may need
            self.params = {} # extra parameters

            self.title    = fdata['title'][()].decode("utf-8")
            self.subtitle = fdata['subtitle'][()].decode("utf-8")

            self.degree = fdata['degree'][()]
            self.state  = fdata['state'][()]

            self.timer_report = fdata['timer_report'][()].decode("utf-8")

            assert 'num_dims' in fdata, f"'{filename}' doesn't appear to be a valid asgard file"

            self.default_view = fdata['default_plotter_view'][()].decode("utf-8")

            # problem dimensions
            self.num_dimensions = fdata['num_dims'][()]

            self.num_position = fdata['num_pos'][()]
            self.num_velocity = fdata['num_vel'][()]

            drange = fdata['domain_range'][()] # domain ranges

            self.dimension_names = [None for i in range(self.num_dimensions)]
            self.dimension_min = np.zeros((self.num_dimensions,))
            self.dimension_max = np.zeros((self.num_dimensions,))
            for i in range(self.num_dimensions):
                self.dimension_names[i] = fdata['dim{0}_name'.format(i)][()].decode("utf-8")
                self.dimension_min[i] = drange[2 * i]
                self.dimension_max[i] = drange[2 * i + 1]

            # grid data and adaptive parameters
            self.cells = fdata['grid_indexes'][()]

            self.num_cells = fdata['grid_num_indexes'][()]
            assert self.num_cells == int(len(self.cells) / self.num_dimensions), "file corruption detected: wront number of cells"

            val = fdata['grid_adapt_threshold'][()]
            if val > -1:
                self.params['grid_adapt_threshold'] = val
            val = fdata['grid_adapt_relative'][()]
            if val > -1:
                self.params['grid_adapt_relative'] = val

            # numeric time-data
            self.time  = fdata['dtime_time'][()]
            self.params['dtime_smethod'] = fdata['dtime_smethod'][()]
            self.params['dtime_dt'] = fdata['dtime_dt'][()]
            self.params['dtime_stop'] = fdata['dtime_stop'][()]
            self.params['dtime_step'] = fdata['dtime_step'][()]
            self.params['dtime_remaining'] = fdata['dtime_remaining'][()]

            # aux fields
            num_aux = fdata['num_aux_fields'][()]
            self.aux_fields = [None for i in range(num_aux)]
            for i in range(num_aux):
                self.aux_fields[i] = {
                    'name' : fdata[f"aux_field_{i}_name"][()].decode("utf-8"),
                    'data' : fdata[f"aux_field_{i}_data"][()],
                    'grid' : fdata[f"aux_field_{i}_grid"][()]
                    }

        # for plotting purposes, say aways from the domain edges
        # rounding error at the edge may skew the plots
        self.eps = 1.E-6 * np.min(self.dimension_max - self.dimension_min)

        if self.verbose:
            if self.state.dtype == np.float64:
                print('using double precision data (double) - 64-bit')
            else:
                print('using single precision data (float) - 32-bit')
            print('dimensions:  {0}'.format(self.num_dimensions))

            print('domain ranges')
            for i in range(self.num_dimensions):
                print('  {0}:  {1: <16f}  {2: <16f}'
                        .format(i, self.dimension_min[i], self.dimension_max[i]))

            print('number of sparse grid cells: %d' % self.num_cells)

        self.recsol = None
        if self.state.dtype == np.float64:
            self.double_precision = True
            self.recsol = libasgard.asgard_make_dreconstruct_solution(
                self.num_dimensions, self.num_cells, np.ctypeslib.as_ctypes(self.cells.reshape(-1,)),
                self.degree, np.ctypeslib.as_ctypes(self.state.reshape(-1,)))
        else:
            self.double_precision = False
            self.recsol = libasgard.asgard_make_freconstruct_solution(
                self.num_dimensions, self.num_cells, np.ctypeslib.as_ctypes(self.cells.reshape(-1,)),
                self.degree, np.ctypeslib.as_ctypes(self.state.reshape(-1,)))

        libasgard.asgard_reconstruct_solution_setbounds(self.recsol,
                                                        np.ctypeslib.as_ctypes(self.dimension_min.reshape(-1,)),
                                                        np.ctypeslib.as_ctypes(self.dimension_max.reshape(-1,)))

    def get_aux_field(self, auxid):
        '''
        If the snapshot data in the HDF5 file contains auxiliary fields,
        this method can create a new snapshot object this time holding
        the field as the state.
        auxid is the auxiliary field id, it can be either a string, which will
              be matched to the id name used in the C++ code,
              or the auxid can be a number indicating the index (0-base)
              that is the index according to the order in which the field was loaded
        '''
        assert isinstance(auxid, int) or isinstance(auxid, string), "auxid must be in int or a string"
        if isinstance(auxid, int):
            assert 0 <= auxid and auxid < len(self.aux_fields), f"the auxid {auxid} must point to a valid entry in the list with size {len(self.aux_fields)}"

            idnum = auxid
        else: # must be a string due to the assertion on top
            idnum = -1
            for i in range(len(self.aux_fields)):
                if self.aux_fields[i].name == auxid:
                    idnum = i
                    break
            assert idnum != -1, f"the auxid '{auxid}' is not in the list of aux-fields"

        aux = pde_snapshot("::aux-filed", self.verbose)

        aux.title    = self.aux_fields[idnum]['name']
        aux.subtitle = "aux-field"
        aux.degree   = self.degree
        aux.state    = self.aux_fields[idnum]['data']
        aux.cells    = self.aux_fields[idnum]['grid']

        aux.default_view = self.default_view

        aux.num_dimensions = self.num_dimensions
        aux.num_position   = self.num_position
        aux.num_velocity   = self.num_velocity
        aux.num_cells      = int(aux.cells.shape[0] / aux.num_dimensions)

        aux.time  = self.time
        aux.time  = self.time

        aux.dimension_names = self.dimension_names
        aux.dimension_min   = self.dimension_min
        aux.dimension_max   = self.dimension_max

        aux.aux_fields = []

        aux.eps = self.eps

        if self.state.dtype == np.float64:
            aux.double_precision = True

            aux.recsol = libasgard.asgard_make_dreconstruct_solution(
                self.num_dimensions, aux.num_cells, np.ctypeslib.as_ctypes(aux.cells.reshape(-1,)),
                self.degree, np.ctypeslib.as_ctypes(aux.state.reshape(-1,)))

        else:
            aux.double_precision = False

            aux.recsol = libasgard.asgard_make_freconstruct_solution_v2(
                self.num_dimensions, aux.num_cells, np.ctypeslib.as_ctypes(aux.cells.reshape(-1,)),
                self.degree, np.ctypeslib.as_ctypes(aux.state.reshape(-1,)))

        libasgard.asgard_reconstruct_solution_setbounds(aux.recsol,
                                                        np.ctypeslib.as_ctypes(self.dimension_min.reshape(-1,)),
                                                        np.ctypeslib.as_ctypes(self.dimension_max.reshape(-1,)))

        return aux

    def plot_data1d(self, dims, num_points = 32):
        '''
        Generates two 1d arrays (vals, x), so that vals is the values
        of the computed solution at the corresponding points in x.
        The array x is constructed from numpy linspace().
        The min/max values of x are provided in the dims list.
        The dims list also holds nominal values for the fixed dimensions.
        '''
        assert len(dims) == self.num_dimensions, "the length of dims (%d) must match num_dimensions (%d)" % (len(dims), self.num_dimensions)

        irange = -1
        minmax = None
        for i in range(self.num_dimensions):
            if isinstance(dims[i], (list, tuple)):
                assert len(dims[i]) == 2 or len(dims[i]) == 0, "elements of dims must be scalars or tuples/lists of len 2 or 0"
                assert irange == -1, "there should be only one dimension with a range in dims"
                irange = i
                if len(dims[i]) == 2:
                    assert self.dimension_min[i] <= dims[i][0] and dims[i][0] <= self.dimension_max[i], "range min for dimension %d is out of bounds" %i
                    assert self.dimension_min[i] <= dims[i][1] and dims[i][1] <= self.dimension_max[i], "range max for dimension %d is out of bounds" %i
                    minmax = (dims[i][0], dims[i][1])
                else:
                    minmax = (self.dimension_min[i], self.dimension_max[i])
            else:
                assert self.dimension_min[i] <= dims[i] and dims[i] <= self.dimension_max[i], "nominal value for dimension %d is out of bounds" %i

        assert irange > -1, "there should be one dimension with a range in dims"

        x = np.linspace(minmax[0] + self.eps, minmax[1] - self.eps, num_points)

        pnts = np.zeros((x.size, self.num_dimensions))
        for i in range(self.num_dimensions):
            if i == irange:
                pnts[:, i] = x
            else:
                pnts[:, i] = dims[i] * np.ones(x.shape)

        return self.evaluate(pnts).reshape(x.shape), x

    def plot_data2d(self, dims, num_points = 32):
        '''
        Generates three 2d arrays (vals, x1, x2), so that vals is the values
        of the computed solution at the corresponding points in x1 and x2.
        The x1/2 arrays are constructed from numpy linspace() and meshgrid().
        The min/max values of x1/2 are provided in the dims list.
        The dims list also holds nominal values for the fixed dimensions.

        Example2:
        plot_data2d((0.5, (0.0, 1.0), (0.5, 1.0)))
          - plots for 3d problem over points (0.5, x_1, x_2)
            where x_1 in (0.0, 1.0) and x_2 in (0.5, 1.0)

        plot_data2d(((0.0, 1.0), 0.3, 0.4, (0.1, 0.3)))
          - plots for 4d problem over points (x_1, 0.3, 0.4, x_2)
            where x_1 in (0.0, 1.0) and x_2 in (0.1, 0.3)

        The min/max ranges can be subset of the corresponding domain min/max
        but should not exit the domain as the solution will not be valid.

        num_points is the number of points to take in each direction,
          keep the number even to avoid putting points right at the discontinuities
          in-between the basis functions
        '''
        assert len(dims) == self.num_dimensions, "the length of dims must match num_dimensions"
        assert num_points % 2 == 0, "num_points must be an even number"

        irange = []
        for i in range(self.num_dimensions):
            if isinstance(dims[i], (list, tuple)):
                assert len(dims[i]) == 2 or len(dims[i]) == 0, "elements of dims must be scalars or tuples/lists of len 0/2"
                irange.append(i)
            else:
                assert self.dimension_min[i] <= dims[i] and dims[i] <= self.dimension_max[i], "nominal value for dimension %d is out of bounds" %i

        assert len(irange) == 2, "there should be only 2 ranges with min/max in dims"

        mins = []
        maxs = []
        for i in irange:
            if len(dims[i]) == 2:
                for v in dims[i]:
                    assert self.dimension_min[i] <= v and v <= self.dimension_max[i], "range for dimension %d is out of bounds" %i
                mins.append(dims[i][0])
                maxs.append(dims[i][1])
            else:
                mins.append(self.dimension_min[i])
                maxs.append(self.dimension_max[i])

        x = np.linspace(mins[0] + self.eps, maxs[0] - self.eps, num_points)
        y = np.linspace(mins[1] + self.eps, maxs[1] - self.eps, num_points)

        XX, YY = np.meshgrid(x, y)

        pgrid = np.zeros((XX.size, self.num_dimensions))
        pgrid[:, irange[0]] = XX.reshape((-1,))
        pgrid[:, irange[1]] = YY.reshape((-1,))

        for i in range(self.num_dimensions):
            if not isinstance(dims[i], (list, tuple)):
                pgrid[:, i] = dims[i]

        return self.evaluate(pgrid).reshape(XX.shape), XX, YY

    def evaluate(self, points):
        '''
        points must be a 2d numpy array with shape (num_x, num_dimensions)
        where the num_x is the number of points for the evaluate command

        each row must describe a point inside the domain, but no checking will
        be performed

        returns a vector with the size num_x holding the corresponding values
        of the field
        '''
        assert len(points.shape) == 2, 'points must be a 2d numpy array with num-columns equal to self.num_dimensions'
        assert points.shape[1] == self.num_dimensions, 'points.shape[1] (%d) must be equal to self.num_dimensions (%d)' % (points.shape[1], self.num_dimensions)

        presult = np.empty((points.shape[0], ), np.float64)
        libasgard.asgard_reconstruct_solution(self.recsol,
                                              np.ctypeslib.as_ctypes(points.reshape(-1,)),
                                              points.shape[0],
                                              np.ctypeslib.as_ctypes(presult.reshape(-1,)))
        return presult

    def cell_centers(self):
        '''
        returns the geometric centers of the sparse grid cells

        do not attempt to plot at these points as they are set right on the
        the discontinuities of the basis functions and the evaluate()
        algorithm may be unstable due to rounding error
        '''
        presult = np.empty((self.num_cells, self.num_dimensions), np.float64)

        libasgard.asgard_reconstruct_cell_centers(self.recsol,
                                                  np.ctypeslib.as_ctypes(presult.reshape(-1,)))

        return presult

    def __str__(self):
        s = "title: %s\n" % self.title
        if self.subtitle != "":
            s += "        %s\n" % self.subtitle
        if self.num_position == 0 and self.num_velocity == 0:
            s += "  num-dimensions: %d\n" % self.num_dimensions
        else: # have position/velocity dimensions
            s += f"  num-dimensions: {self.num_dimensions}  ({self.num_position}x{self.num_velocity}v)\n"
        s += "  degree:         %d\n" % self.degree
        s += "  num-indexes:    %d\n" % self.num_cells
        s += "  state size:     %d\n" % self.state.size
        s += "  time:           %f\n" % self.time
        return s

    def long_str(self):
        s = str(self) + '\n'
        if 'grid_adapt_threshold' not in self.params and 'grid_adapt_relative' not in self.params:
            s += '  non-adaptive grid\n'
        else:
            if 'grid_adapt_relative' in self.params:
                s += f"  relative adaptive tolerance: {self.params['grid_adapt_relative']:1.10e}\n"
            if 'grid_adapt_threshold' in self.params:
                s += f"  absolute adaptive tolerance: {self.params['grid_adapt_threshold']:1.10e}\n"

        s += '\ntime stepping:'
        s += "\n  method          " + step_method_map[ self.params['dtime_smethod'] ]
        s += "\n  time (t)        %f" % self.time
        s += "\n  stop-time (T)   %f" % self.params['dtime_stop']
        s += "\n  num-steps       %d" % self.params['dtime_step']
        s += "\n  remaining steps %d" % self.params['dtime_remaining']
        s += f"\n  time-step (dt)  {self.params['dtime_dt']:1.10e}\n"

        return '\n' + s


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-v", "-version", "--version"):
        libasgard.asgard_print_version_help()
    elif sys.argv[1] in ("-h", "-help", "--help"):
        print("")
        print("python -m asgard plt.data")
        print("   makes a quick 1D or 2D plot of output contained in out.data")
        print("")
        print("python -m asgard -g plt.data")
        print("   makes a quick 1D or 2D plot of the grid contained in out.data")
        print("")
        print("python -m asgard -s plt.data")
        print("   shows summary of the snapshot contained in the out.data")
        print("")
        print("python -m asgard plt.data <-view string/-fig filename/-grid>")
        print("   same as the first example but also adds more options,")
        print("   set the view plane, save the figure to a file, add the grid entries")
        print("")
        print("options:")
        print(" -h, -help, --help           : shows this help text")
        print(" -v, -version, --version     : shows the library version info")
        print(" -s, -stat, -stats, -summary : shows the summary of a snapshot")
        print(" -ss, -vv                    : super-summary or very-verbose info")
        print(" -g, -grid                   : plot the grid")
        print(" -view                       : adjust the view plane")
        print("")
        print("no file and no option provided, shows the version of the")
        print("")
    elif sys.argv[1] in ("-s", "-stat", "-stats", "-summary"):
        if len(sys.argv) < 3:
            print("stats summary option requires a filename")
        else:
            shot = pde_snapshot(sys.argv[2])
            print("\n", shot, shot.timer_report)
    elif sys.argv[1] in ("-ss", "-vv"):
        if len(sys.argv) < 3:
            print("-ss/-vv summary option requires a filename")
        else:
            shot = pde_snapshot(sys.argv[2])
            print("\n", shot.long_str(), shot.timer_report)
    elif not _matplotlib_found_:
        print("could not 'import matplotlib'")
        print("can only print stats-summary, use")
        print("  python3 -m asgard -s %s" % sys.argv[2])
        libasgard.asgard_print_version_help()
    elif sys.argv[1] in ("-grid", "-g"):
        if len(sys.argv) < 3:
            print("-grid option requires a filename")
        else:
            shot = pde_snapshot(sys.argv[2])
            print("\n", shot)

            asgplot.title(shot.title, fontsize = 'large')

            cells = shot.cell_centers()
            if shot.num_dimensions == 1:
                asgplot.plot(cells[:,0], np.zeros(cells[:,0].shape), 'ro')
            else:
                asgplot.scatter(cells[:,0], cells[:,1], 5 * np.ones(cells[:,0].shape), color='red')

        if len(sys.argv) > 3:
            asgplot.savefig(sys.argv[3])
        else:
            asgplot.show()

    else:
        shot = pde_snapshot(sys.argv[1])
        print("\n", shot)

        # we are plotting, consider extra options
        plotview = None
        savefig  = None
        auxfield = None
        addgrid  = False
        if len(sys.argv) > 2:
            i = 2
            n = len(sys.argv)
            while i < n:
                if sys.argv[i] == "-view":
                    plotview = sys.argv[i + 1] if i + 1 < n else None
                    i += 2
                elif sys.argv[i] == "-fig":
                    savefig = sys.argv[i + 1] if i + 1 < n else None
                    i += 2
                elif sys.argv[i] == "-aux":
                    auxfield = sys.argv[i + 1] if i + 1 < n else None
                    i += 2
                    assert auxfield is not None, "-aux requires an filed number"
                    auxfield = int(auxfield)
                elif sys.argv[i] == "-grid":
                    addgrid = True
                    i += 1
                else:
                    savefig = sys.argv[i]
                    i += 1

        if auxfield is not None:
            shot = shot.get_aux_field(auxfield)

        asgplot.title(shot.title, fontsize = 'large')

        if shot.num_dimensions == 1:
            z, x = shot.plot_data1d(((),), num_points = 256)
            asgplot.plot(x, z)
            asgplot.xlabel(shot.dimension_names[0], fontsize = 'large')

            if addgrid:
                cc = shot.cell_centers()
                ymin = np.min(z)
                asgplot.plot(cc, ymin * np.ones(cc.shape), 'om')

        else:
            if plotview is None and shot.default_view != "":
                plotview = shot.default_view

            dims = [0, 1]

            if plotview is None:
                plist = [(), ()]
                for i in range(2, shot.num_dimensions):
                    plist.append(0.5 * (shot.dimension_max[i] + shot.dimension_min[i]) + shot.eps)
            else:
                ss = plotview.split(':')
                plist = []
                dims = []
                for i in range(len(ss)):
                    s = ss[i]
                    if '*' in s:
                        plist.append(())
                        dims.append(i)
                    else:
                        plist.append(float(s))

            z, x, y = shot.plot_data2d(plist, num_points = 256)

            xmin = shot.dimension_min[dims[0]]
            ymin = shot.dimension_min[dims[1]]
            xmax = shot.dimension_max[dims[0]]
            ymax = shot.dimension_max[dims[1]]

            #p = asgplot.pcolor(x, y, z, cmap='jet')
            p = asgplot.imshow(np.flipud(z), cmap='jet', extent=[xmin, xmax, ymin, ymax])

            asgplot.colorbar(p, orientation='vertical')

            asgplot.gca().set_anchor('C')

            if addgrid:
                cc = shot.cell_centers()
                asgplot.scatter(cc[:,0], cc[:,1], 5 * np.ones(cc[:,0].shape), color='purple')

            asgplot.xlabel(shot.dimension_names[dims[0]], fontsize='large')
            asgplot.ylabel(shot.dimension_names[dims[1]], fontsize='large')

        if savefig is not None and savefig != "":
            asgplot.savefig(savefig)
        else:
            asgplot.show()
