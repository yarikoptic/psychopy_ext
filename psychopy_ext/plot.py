#!/usr/bin/env python

# Part of the psychopy_ext library
# Copyright 2010-2013 Jonas Kubilius
# The program is distributed under the terms of the GNU General Public License,
# either version 3 of the License, or (at your option) any later version.

"""
A wrapper of matplotlib for producing pretty plots by default. As `pandas`
evolves, some of these improvements will hopefully be merged into it.

Usage:
    import plot
    plt = plot.Plot(nrows_ncols=(1,2))
    plt.plot(data)  # plots data on the first subplot
    plt.plot(data2)  # plots data on the second subplot
    plt.show()

"""

import sys

import numpy as np
import scipy.stats
import pandas

import matplotlib.pyplot as plt
import matplotlib as mpl
from mpl_toolkits.axes_grid1 import ImageGrid
from matplotlib.patches import Rectangle


# parameters for pretty plots in the ggplot style
# from https://gist.github.com/huyng/816622
# inspiration from mpltools
# will soon be removed as pandas has this implemented in the dev versions
s = {'axes.facecolor': '#eeeeee',
     'axes.edgecolor': '#bcbcbc',
     'axes.linewidth': 1,
     'axes.grid': True,
     'axes.titlesize': 'x-large',
     'axes.labelsize': 'large',  # 'x-large'
     'axes.labelcolor': '#555555',
     'axes.axisbelow': True,
     'axes.color_cycle': ['#348ABD', # blue
                          '#7A68A6', # purple
                          '#A60628', # red
                          '#467821', # green
                          '#CF4457', # pink
                          '#188487', # turquoise
                          '#E24A33'], # orange

     'figure.facecolor': '0.85',
     'figure.edgecolor': '0.5',
     'figure.subplot.hspace': .5,

     'font.family': 'monospace',
     'font.size': 10,

     'xtick.color': '#555555',
     'xtick.direction': 'in',
     'xtick.major.pad': 6,
     'xtick.major.size': 0,
     'xtick.minor.pad': 6,
     'xtick.minor.size': 0,

     'ytick.color': '#555555',
     'ytick.direction': 'in',
     'ytick.major.pad': 6,
     'ytick.major.size': 0,
     'ytick.minor.pad': 6,
     'ytick.minor.size': 0,

     'legend.fancybox': True,

     'lines.antialiased': True,
     'lines.linewidth': 1.0,

     'patch.linewidth'        : .5,     # edge width in points
     'patch.facecolor'        : '#348ABD', # blue
     'patch.edgecolor'        : '#eeeeee',
     'patch.antialiased'      : True,    # render patches in antialised (no jaggies)

     }
plt.rcParams.update(s)


class Plot(object):

    def __init__(self, kind='', figsize=None, nrows=1, ncols=1, rect=111,
                 cbar_mode='single', squeeze=False, **kwargs):
        self._create_subplots(kind=kind, figsize=figsize, nrows=nrows,
            ncols=ncols, **kwargs)

    def _create_subplots(self, kind='', figsize=None, nrows=1, ncols=1, rect=111,
        cbar_mode='single', squeeze=False, **kwargs):
        """
        :Kwargs:
            - kind (str, default: '')
                The kind of plot. For plotting matrices or images
                (`matplotlib.pyplot.imshow`), choose `matrix`, otherwise leave
                blank.
            - figsize (tuple, defaut: None)
                Size of the figure.
            - nrows_ncols (tuple, default: (1, 1))
                Shape of subplot arrangement.
            - **kwargs
                A dictionary of keyword arguments that `matplotlib.ImageGrid`
                or `matplotlib.pyplot.suplots` accept. Differences:
                    - `rect` (`matplotlib.ImageGrid`) is a keyword argument here
                    - `cbar_mode = 'single'`
                    - `squeeze = False`
        :Returns:
            `matplotlib.pyplot.figure` and a grid of axes.
        """

        if 'nrows_ncols' not in kwargs:
            nrows_ncols = (nrows, ncols)
        else:
            nrows_ncols = kwargs['nrows_ncols']
            del kwargs['nrows_ncols']
        try:
            num = self.fig.number
            self.fig.clf()
        except:
            num = None
        if kind == 'matrix':
            self.fig = self.figure(figsize=figsize, num=num)
            self.axes = ImageGrid(self.fig, rect,
                                  nrows_ncols=nrows_ncols,
                                  cbar_mode=cbar_mode,
                                  **kwargs
                                  )
        else:
            self.fig, self.axes = plt.subplots(
                nrows=nrows_ncols[0],
                ncols=nrows_ncols[1],
                figsize=figsize,
                squeeze=squeeze,
                num=num,
                **kwargs
                )
            self.axes = self.axes.ravel()  # turn axes into a list
        self.kind = kind
        self.subplotno = -1  # will get +1 after the plot command
        self.nrows_ncols = nrows_ncols
        return (self.fig, self.axes)

    def __getattr__(self, name):
        """Pass on a `matplotlib` function that we haven't modified
        """
        def method(*args, **kwargs):
            return getattr(plt, name)(*args, **kwargs)

        try:
            return method  # is it a function?
        except TypeError:  # so maybe it's just a self variable
            return getattr(self, name)

    def __getitem__(self, key):
        """Allow to get axes as Plot()[key]
        """
        if key > len(self.axes):
            raise IndexError
        if key < 0:
            key += len(self.axes)
        return self.axes[key]

    def get_ax(self, subplotno=None):
        """
        Returns the current or the requested axis from the current figure.

        :note: The :class:`Plot()` is indexable so you should access axes as
        `Plot()[key]` unless you want to pass a list like (row, col).

        :Kwargs:
            subplotno (int, default: None)
                Give subplot number explicitly if you want to get not the
                current axis

        :Returns:
            ax
        """
        if subplotno is None:
            no = self.subplotno
        else:
            no = subplotno

        if isinstance(no, int):
            ax = self.axes[no]
        else:
            if no[0] < 0: no += len(self.axes._nrows)
            if no[1] < 0: no += len(self.axes._ncols)

            if isinstance(self.axes, ImageGrid):  # axes are a list
                if self.axes._direction == 'row':
                    no = self.axes._ncols * no[0] + no[1]
                else:
                    no = self.axes._nrows * no[0] + no[1]
            else:  # axes are a grid
                no = self.axes._ncols * no[0] + no[1]
            ax = self.axes[no]

        return ax

    def next(self):
        """
        Returns the next axis.

        This is useful when a plotting function is not implemented by
        :mod:`plot` and you have to instead rely on matplotlib's plotting
        which does not advance axes automatically.
        """
        self.subplotno += 1
        return self.get_ax()

    def sample_paired(self, ncolors=2):
        """
        Returns colors for matplotlib.cm.Paired.
        """
        if ncolors <= 12:
            colors_full = [mpl.cm.Paired(i * 1. / 11) for i in range(1, 12, 2)]
            colors_pale = [mpl.cm.Paired(i * 1. / 11) for i in range(10, -1, -2)]
            colors = colors_full + colors_pale
            return colors[:ncolors]
        else:
            return [mpl.cm.Paired(c) for c in np.linspace(0,ncolors)]

    def get_colors(self, ncolors=2, cmap='Paired'):
        """
        Get a list of nice colors for plots.

        FIX: This function is happy to ignore the ugly settings you may have in
        your matplotlibrc settings.
        TODO: merge with mpltools.color

        :Kwargs:
            ncolors (int, default: 2)
                Number of colors required. Typically it should be the number of
                entries in the legend.
            cmap (str or matplotlib.cm, default: 'Paired')
                A colormap to sample from when ncolors > 12

        :Returns:
            a list of colors
        """
        colorc = plt.rcParams['axes.color_cycle']
        if ncolors < len(colorc):
            colors = colorc[:ncolors]
        elif ncolors <= 12:
            colors = self.sample_paired(ncolors=ncolors)
        else:
            thisCmap = mpl.cm.get_cmap(cmap)
            norm = mpl.colors.Normalize(0, 1)
            z = np.linspace(0, 1, ncolors + 2)
            z = z[1:-1]
            colors = thisCmap(norm(z))
        return colors

    def pivot_plot(self,df,rows=None,cols=None,values=None,yerr=None,
                   **kwargs):
        agg = self.aggregate(df, rows=rows, cols=cols,
                                 values=values, yerr=yerr)
        if yerr is None:
            no_yerr = True
        else:
            no_yerr = False
        return self._plot(agg, no_yerr=no_yerr,**kwargs)


    def _plot(self, agg, ax=None,
                   title='', kind='bar', xtickson=True, ytickson=True,
                   no_yerr=False, numb=False, autoscale=True, **kwargs):
        """DEPRECATED plotting function"""
        print "plot._plot() has been DEPRECATED; please don't use it anymore"
        self.plot(agg, ax=ax,
                   title=title, kind=kind, xtickson=xtickson, ytickson=ytickson,
                   no_yerr=no_yerr, numb=numb, autoscale=autoscale, **kwargs)

    def plot(self, agg, subplots=None, **kwargs):
        """
        The main plotting function.

        :Args:
            agg (`pandas.DataFrame` or similar)
                A structured input, preferably a `pandas.DataFrame`, but in
                principle accepts anything that can be converted into it.

        :Kwargs:
            - subplots (None, True, or False; default=None)
                Whether you want to split data into subplots or not. If True,
                the top level is treated as a subplot. If None, detects
                automatically based on `agg.columns.names` -- the first entry
                to start with `subplots.` will be used. This is the default
                output from `stats.aggregate` and is recommended.
            - **kwargs
                Keyword arguments for plotting

        :Returns:
            A list of axes of all plots.
        """
        agg = pandas.DataFrame(agg)
        axes = []
        try:
            s_idx = [s for s,n in enumerate(agg.columns.names) if n.startswith('subplots.')]
        except:
            s_idx = None
        if s_idx is not None:  # subplots implicit in agg
            if len(s_idx) != 0:
                sbp = agg.columns.levels[s_idx[0]]
            else:
                sbp = None
        elif subplots:  # get subplots from the top level column
            sbp = agg.columns.levels[0]
        else:
            sbp = None

        if sbp is None:
            axes = [self._plot_ax(agg, **kwargs)]
        else:
            # if haven't made any plots yet...
            if self.subplotno == -1:
                num_subplots = len(sbp)
                # ...can still adjust the number of subplots
                if num_subplots > len(self.axes):
                    self._create_subplots(ncols=num_subplots)

            for no, subname in enumerate(sbp):
                # all plots are the same, onle legend will suffice
                if subplots is None or subplots:
                    if no == 0:
                        legend = True
                    else:
                        legend = False
                else:  # plots vary; each should get a legend
                    legend = True
                ax = self._plot_ax(agg[subname], title=subname, legend=legend,
                                **kwargs)
                if 'title' in kwargs:
                    ax.set_title(kwargs['title'])
                else:
                    ax.set_title(subname)
                axes.append(ax)
        return axes

    def _plot_ax(self, agg, ax=None,
                   title='', kind='bar', legend=True,
                   xtickson=True, ytickson=True,
                   no_yerr=False, numb=False, autoscale=True, order=None,
                   **kwargs):
        if ax is None:
            self.subplotno += 1
            ax = self.get_ax()
        if isinstance(agg, pandas.DataFrame):
            mean, p_yerr = self.errorbars(agg)
        else:
            mean = agg
            p_yerr = np.zeros((len(agg), 1))

        if mean.index.nlevels == 1:  # oops, nothing to unstack
            mean = pandas.DataFrame(mean).T
            p_yerr = pandas.DataFrame(p_yerr).T
        else:
            # make columns which will turn into legend entries
            for name in agg.columns.names:
                if name.startswith('cols.'):
                    mean = mean.unstack(level=name)
                    p_yerr = p_yerr.unstack(level=name)

        if isinstance(agg, pandas.Series) and kind=='bean':
            kind = 'bar'
            print 'WARNING: Beanplot not available for a single measurement'

        if kind == 'bar':
            self.barplot(mean, yerr=p_yerr, ax=ax)
        elif kind == 'line':
            self.lineplot(mean, yerr=p_yerr, ax=ax)
        elif kind == 'bean':
            autoscale = False  # FIX: autoscaling is incorrect on beanplots
            #if len(mean.columns) <= 2:
            ax = self.beanplot(agg, ax=ax, order=order, **kwargs)#, pos=range(len(mean.index)))
            #else:
                #raise Exception('Beanplot is not available for more than two '
                                #'classes.')
        else:
            raise Exception('%s plot not recognized. Choose from '
                            '{bar, line, bean}.' %kind)

        # TODO: xticklabel rotation business is too messy
        if 'xticklabels' in kwargs:
            ax.set_xticklabels(kwargs['xticklabels'], rotation=0)
        if not xtickson:
            ax.set_xticklabels(['']*len(ax.get_xticklabels()))

        labels = ax.get_xticklabels()
        max_len = max([len(label.get_text()) for label in labels])
        for label in labels:
            if max_len > 20:
                label.set_rotation(90)
            else:
                label.set_rotation(0)
            #label.set_size('x-large')
        #ax.set_xticklabels(labels, rotation=0, size='x-large')

        if not ytickson:
            ax.set_yticklabels(['']*len(ax.get_yticklabels()))
        ax.set_xlabel('')

        # set y-axis limits
        if 'ylim' in kwargs:
            ax.set_ylim(kwargs['ylim'])
        elif autoscale:
            mean_array = np.asarray(mean)
            r = np.max(mean_array) - np.min(mean_array)
            ebars = np.where(np.isnan(p_yerr), r/3., p_yerr)
            if kind == 'bar':
                ymin = np.min(np.asarray(mean) - ebars)
                if ymin > 0:
                    ymin = 0
                else:
                    ymin = np.min(np.asarray(mean) - 3*ebars)
            else:
                ymin = np.min(np.asarray(mean) - 3*ebars)
            if kind == 'bar':
                ymax = np.max(np.asarray(mean) + ebars)
                if ymax < 0:
                    ymax = 0
                else:
                    ymax = np.max(np.asarray(mean) + 3*ebars)
            else:
                ymax = np.max(np.asarray(mean) + 3*ebars)
            ax.set_ylim([ymin, ymax])

        # set x and y labels
        if 'xlabel' in kwargs:
            ax.set_xlabel(kwargs['xlabel'])
        else:
            ax.set_xlabel(self._get_title(mean, 'rows'))
        if 'ylabel' in kwargs:
            ax.set_ylabel(kwargs['ylabel'])
        else:
            ax.set_ylabel(self._get_title(mean, 'cols'))

        # set x tick labels
        #FIX: data.index returns float even if it is int because dtype=object
        #if len(mean.index) == 1:  # no need to put a label for a single bar group
            #ax.set_xticklabels([''])
        #else:
        ax.set_xticklabels(mean.index.tolist())

        ax.set_title(title)
        self._draw_legend(ax, visible=legend, data=mean, **kwargs)
        if numb == True:
            self.add_inner_title(ax, title='%s' % self.subplotno, loc=2)

        return ax

    def _get_title(self, data, pref):
        if pref == 'cols':
            dnames = data.columns.names
        else:
            dnames = data.index.names
        title = [n.split('.',1)[1] for n in dnames if n.startswith(pref+'.')]

        title = ', '.join(title)
        return title

    def _draw_legend(self, ax, visible=True, data=None, **kwargs):
        l = ax.get_legend()  # get an existing legend
        if l is None:  # create a new legend
            l = ax.legend()
        l.legendPatch.set_alpha(0.5)
        l.set_title(self._get_title(data, 'cols'))

        if 'legend_visible' in kwargs:
            l.set_visible(kwargs['legend_visible'])
        elif visible is not None:
            l.set_visible(visible)
        else:  #decide automatically
            if len(l.texts) == 1:  # showing a single legend entry is useless
                l.set_visible(False)
            else:
                l.set_visible(True)

    def hide_plots(self, nums):
        """
        Hides an axis.

        :Args:
            nums (int, tuple or list of ints)
                Which axes to hide.
        """
        if isinstance(nums, int) or isinstance(nums, tuple):
            nums = [nums]
        for num in nums:
            ax = self.get_ax(num)
            ax.axis('off')

    def barplot(self, data, yerr=None, ax=None):
        """
        Plots a bar plot.

        :Args:
            data (`pandas.DataFrame` or any other array accepted by it)
                A data frame where rows go to the x-axis and columns go to the
                legend.

        """
        data = pandas.DataFrame(data)
        if yerr is None:
            yerr = np.empty(data.shape)
            yerr = yerr.reshape(data.shape)  # force this shape
            yerr = np.nan
        if ax is None:
            self.subplotno += 1
            ax = self.get_ax()

        colors = self.get_colors(len(data.columns))

        n = len(data.columns)
        idx = np.arange(len(data))
        width = .75 / n
        rects = []
        for i, (label, column) in enumerate(data.iteritems()):
            rect = ax.bar(idx+i*width+width/2, column, width, label=str(label),
                yerr=yerr[label].tolist(), color = colors[i], ecolor='black')
            # TODO: yerr indexing might need fixing
            rects.append(rect)
        ax.set_xticks(idx + width*n/2 + width/2)
        ax.legend(rects, data.columns.tolist())

        return ax

    def lineplot(self, data, yerr=None, ax=None):
        """
        Plots a bar plot.

        :Args:
            data (`pandas.DataFrame` or any other array accepted by it)
                A data frame where rows go to the x-axis and columns go to the
                legend.

        """
        data = pandas.DataFrame(data)
        if yerr is None:
            yerr = np.empty(data.shape)
            yerr = yerr.reshape(data.shape)  # force this shape
            yerr = np.nan
        if ax is None:
            self.subplotno += 1
            ax = self.get_ax()

        #colors = self.get_colors(len(data.columns))

        x = range(len(data))
        lines = []
        for i, (label, column) in enumerate(data.iteritems()):
            line = ax.plot(x, column, label=str(label))
            lines.append(line)
            ax.errorbar(x, column, yerr=yerr[label].tolist(), fmt=None,
                ecolor='black')
        #ticks = ax.get_xticks().astype(int)
        #if ticks[-1] >= len(data.index):
            #labels = data.index[ticks[:-1]]
        #else:
            #labels = data.index[ticks]
        #ax.set_xticklabels(labels)
        #ax.legend()
        #loc='center left', bbox_to_anchor=(1.3, 0.5)
        #loc='upper right', frameon=False
        return ax

    def scatter(self, x, y, ax=None, labels=None, title='', **kwargs):
        """
        Draws a scatter plot.

        This is very similar to `matplotlib.pyplot.scatter` but additionally
        accepts labels (for labeling points on the plot), plot title, and an
        axis where the plot should be drawn.

        :Args:
            - x (an iterable object)
                An x-coordinate of data
            - y (an iterable object)
                A y-coordinate of data

        :Kwargs:
            - ax (default: None)
                An axis to plot in.
            - labels (list of str, default: None)
                A list of labels for each plotted point
            - title (str, default: '')
                Plot title
            - ** kwargs
                Additional keyword arguments for `matplotlib.pyplot.scatter`

        :Return:
            Current axis for further manipulation.

        """
        if ax is None:
            self.subplotno += 1
            ax = self.get_ax()
        plt.rcParams['axes.color_cycle']
        ax.scatter(x, y, marker='o', color=self.get_colors()[0], **kwargs)
        if labels is not None:
            for c, (pointx, pointy) in enumerate(zip(x,y)):
                ax.text(pointx, pointy, labels[c])
        ax.set_title(title)
        return ax

    def matrix_plot(self, matrix, ax=None, title='', **kwargs):
        """
        Plots a matrix.

        .. warning:: Not tested yet

        :Args:
            matrix

        :Kwargs:
            - ax (default: None)
                An axis to plot on.
            - title (str, default: '')
                Plot title
            - **kwargs
                Keyword arguments to pass to `matplotlib.pyplot.imshow`

        """
        if ax is None:
            ax = plt.subplot(111)
        import matplotlib.colors
        norm = matplotlib.colors.normalize(vmax=1, vmin=0)
        mean, sem = self.errorbars(matrix)
        #matrix = pandas.pivot_table(mean.reset_index(), rows=)
        im = ax.imshow(mean, norm=norm, interpolation='none', **kwargs)
        # ax.set_title(title)

        ax.cax.colorbar(im)#, ax=ax, use_gridspec=True)
        # ax.cax.toggle_label(True)

        t = self.add_inner_title(ax, title, loc=2)
        t.patch.set_ec("none")
        t.patch.set_alpha(0.8)
        xnames = ['|'.join(map(str,label)) for label in matrix.minor_axis]
        ax.set_xticks(range(len(xnames)))
        ax.set_xticklabels(xnames)
        # rotate long labels
        if max([len(n) for n in xnames]) > 20:
            ax.axis['bottom'].major_ticklabels.set_rotation(90)
        ynames = ['|'.join(map(str,label)) for label in matrix.major_axis]
        ax.set_yticks(range(len(ynames)))
        ax.set_yticklabels(ynames)
        return ax

    def add_inner_title(self, ax, title, loc=2, size=None, **kwargs):
        from matplotlib.offsetbox import AnchoredText
        from matplotlib.patheffects import withStroke
        if size is None:
            size = dict(size=plt.rcParams['legend.fontsize'])
        at = AnchoredText(title, loc=loc, prop=size,
                          pad=0., borderpad=0.5,
                          frameon=False, **kwargs)
        ax.add_artist(at)
        at.txt._text.set_path_effects([withStroke(foreground="w", linewidth=3)])
        return at

    def errorbars(self, df, yerr_type='sem'):
        # Set up error bar information
        if yerr_type == 'sem':
            mean = df.mean()  # mean across items
            # std already has ddof=1
            sem = df.std() / np.sqrt(len(df))
            #yerr = np.array(sem)#.reshape(mean.shape)  # force this shape
        elif yerr_type == 'binomial':
            pass
            # alpha = .05
            # z = stats.norm.ppf(1-alpha/2.)
            # count = np.mean(persubj, axis=1, ddof=1)
            # p_yerr = z*np.sqrt(mean*(1-mean)/persubj.shape[1])

        return mean, sem

    def stats_test(self, agg, test='ttest'):
        d = agg.shape[0]

        if test == 'ttest':
            # 2-tail T-Test
            ttest = (np.zeros((agg.shape[1]*(agg.shape[1]-1)/2, agg.shape[2])),
                     np.zeros((agg.shape[1]*(agg.shape[1]-1)/2, agg.shape[2])))
            ii = 0
            for c1 in range(agg.shape[1]):
                for c2 in range(c1+1,agg.shape[1]):
                    thisTtest = stats.ttest_rel(agg[:,c1,:], agg[:,c2,:], axis = 0)
                    ttest[0][ii,:] = thisTtest[0]
                    ttest[1][ii,:] = thisTtest[1]
                    ii += 1
            ttestPrint(title = '**** 2-tail T-Test of related samples ****',
                values = ttest, plotOpt = plotOpt,
                type = 2)

        elif test == 'ttest_1samp':
            # One-sample t-test
            m = .5
            oneSample = stats.ttest_1samp(agg, m, axis = 0)
            ttestPrint(title = '**** One-sample t-test: difference from %.2f ****' %m,
                values = oneSample, plotOpt = plotOpt, type = 1)

        elif test == 'binomial':
            # Binomial test
            binom = np.apply_along_axis(stats.binom_test,0,agg)
            print binom
            return binom


    def ttestPrint(self, title = '****', values = None, xticklabels = None, legend = None, bon = None):

        d = 8
        # check if there are any negative t values (for formatting purposes)
        if np.any([np.any(val < 0) for val in values]): neg = True
        else: neg = False

        print '\n' + title
        for xi, xticklabel in enumerate(xticklabels):
            print xticklabel

            maxleg = max([len(leg) for leg in legend])
#            if type == 1: legendnames = ['%*s' %(maxleg,p) for p in plotOpt['subplot']['legend.names']]
#            elif type == 2:
            pairs = q.combinations(legend,2)
            legendnames = ['%*s' %(maxleg,p[0]) + ' vs ' + '%*s' %(maxleg,p[1]) for p in pairs]
            #print legendnames
            for yi, legendname in enumerate(legendnames):
                if values[0].ndim == 1:
                    t = values[0][xi]
                    p = values[1][xi]
                else:
                    t = values[0][yi,xi]
                    p = values[1][yi,xi]
                if p < .001/bon: star = '***'
                elif p < .01/bon: star = '**'
                elif p < .05/bon: star = '*'
                else: star = ''

                if neg and t > 0:
                    outputStr = '    %(s)s: t(%(d)d) =  %(t).3f, p = %(p).3f %(star)s'
                else:
                    outputStr = '    %(s)s: t(%(d)d) = %(t).3f, p = %(p).3f %(star)s'

                print outputStr \
                    %{'s': legendname, 'd':(d-1), 't': t,
                    'p': p, 'star': star}

    def mds(self, results, labels, fonts='freesansbold.ttf', title='',
        ax = None):
        """Plots Multidimensional scaling results"""
        if ax is None:
            try:
                row = self.subplotno / self.axes[0][0].numCols
                col = self.subplotno % self.axes[0][0].numCols
                ax = self.axes[row][col]
            except:
                ax = self.axes[self.subplotno]
        ax.set_title(title)
        # plot each point with a name
        dims = results.ndim
        try:
            if results.shape[1] == 1:
                dims = 1
        except:
            pass
        if dims == 1:
            df = pandas.DataFrame(results, index=labels, columns=['data'])
            df = df.sort(columns='data')
            self._plot(df)
        elif dims == 2:
            for c, coord in enumerate(results):
                ax.plot(coord[0], coord[1], 'o', color=mpl.cm.Paired(.5))
                ax.text(coord[0], coord[1], labels[c], fontproperties=fonts[c])
        else:
            print 'Cannot plot more than 2 dims'


    def _violinplot(self, data, pos, rlabels, ax=None, bp=False, cut=None, **kwargs):
        """
        Make a violin plot of each dataset in the `data` sequence.

        Based on `code by Teemu Ikonen
        <http://matplotlib.1069221.n5.nabble.com/Violin-and-bean-plots-tt27791.html>`_
        which was based on `code by Flavio Codeco Coelho
        <http://pyinsci.blogspot.com/2009/09/violin-plot-with-matplotlib.html>`)
        """
        def draw_density(p, low, high, k1, k2, ncols=2):
            m = low #lower bound of violin
            M = high #upper bound of violin
            x = np.linspace(m, M, 100) # support for violin
            v1 = k1.evaluate(x) # violin profile (density curve)
            v1 = w*v1/v1.max() # scaling the violin to the available space
            v2 = k2.evaluate(x) # violin profile (density curve)
            v2 = w*v2/v2.max() # scaling the violin to the available space

            if ncols == 2:
                ax.fill_betweenx(x, -v1 + p, p, facecolor='black', edgecolor='black')
                ax.fill_betweenx(x, p, p + v2, facecolor='grey', edgecolor='gray')
            else:
                ax.fill_betweenx(x, -v1 + p, p + v2, facecolor='black', edgecolor='black')


        if pos is None:
            pos = [0,1]
        dist = np.max(pos)-np.min(pos)
        w = min(0.15*max(dist,1.0),0.5) * .5

        #for major_xs in range(data.shape[1]):
        for num, rlabel in enumerate(rlabels):
            p = pos[num]
            d1 = data.ix[rlabel, 0]
            k1 = scipy.stats.gaussian_kde(d1) #calculates the kernel density
            if data.shape[1] == 1:
                d2 = d1
                k2 = k1
            else:
                d2 = data.ix[rlabel, 1]
                k2 = scipy.stats.gaussian_kde(d2) #calculates the kernel density
            cutoff = .001
            if cut is None:
                upper = max(d1.max(),d2.max())
                lower = min(d1.min(),d2.min())
                stepsize = (upper - lower) / 100
                area_low1 = 1  # max cdf value
                area_low2 = 1  # max cdf value
                low = min(d1.min(), d2.min())
                while area_low1 > cutoff or area_low2 > cutoff:
                    area_low1 = k1.integrate_box_1d(-np.inf, low)
                    area_low2 = k2.integrate_box_1d(-np.inf, low)
                    low -= stepsize
                    #print area_low, low, '.'
                area_high1 = 1  # max cdf value
                area_high2 = 1  # max cdf value
                high = max(d1.max(), d2.max())
                while area_high1 > cutoff or area_high2 > cutoff:
                    area_high1 = k1.integrate_box_1d(high, np.inf)
                    area_high2 = k2.integrate_box_1d(high, np.inf)
                    high += stepsize
            else:
                low, high = cut

            draw_density(p, low, high, k1, k2, ncols=data.shape[1])


        # a work-around for generating a legend for the PolyCollection
        # from http://matplotlib.org/users/legend_guide.html#using-proxy-artist
        left = Rectangle((0, 0), 1, 1, fc="black", ec='black')
        right = Rectangle((0, 0), 1, 1, fc="gray", ec='gray')

        ax.legend((left, right), data.columns.tolist())
        #import pdb; pdb.set_trace()
        #ax.set_xlim(pos[0]-3*w, pos[-1]+3*w)
        #if bp:
            #ax.boxplot(data,notch=1,positions=pos,vert=1)
        return ax


    def _stripchart(self, data, pos, rlabels, ax=None, mean=False, median=False,
        width=None, discrete=True, bins=30):
        """Plot samples given in `data` as horizontal lines.

        :Kwargs:
            mean: plot mean of each dataset as a thicker line if True
            median: plot median of each dataset as a dot if True.
            width: Horizontal width of a single dataset plot.
        """
        def draw_lines(d, maxcount, hist, bin_edges, sides=None):
            if discrete:
                bin_edges = bin_edges[:-1]  # upper edges not needed
                hw = hist * w / (2.*maxcount)
            else:
                bin_edges = d
                hw = w / 2.

            ax.hlines(bin_edges, sides[0]*hw + p, sides[1]*hw + p, color='white')
            if mean:  # draws a longer black line
                ax.hlines(np.mean(d), sides[0]*2*w + p, sides[1]*2*w + p,
                    lw=2, color='black')
            if median:  # puts a white dot
                ax.plot(p, np.median(d), 'o', color='white', markeredgewidth=0)

        #data, pos = self._beanlike_setup(data, ax)

        if width:
            w = width
        else:
            #if pos is None:
                #pos = [0,1]
            dist = np.max(pos)-np.min(pos)
            w = min(0.15*max(dist,1.0),0.5) * .5

        #colnames = [d for d in data.columns.names if d.startswith('cols.') ]
        #if len(colnames) == 0:  # nothing specified explicitly as a columns
            #try:
                #colnames = data.columns.levels[-1]
            #except:
                #colnames = data.columns

        #func1d = lambda x: np.histogram(x, bins=bins)
        # apply along cols
        hist, bin_edges = np.apply_along_axis(np.histogram, 0, data, bins)
        # it return arrays of object type, so we got to correct that
        hist = np.array(hist.tolist())
        bin_edges = np.array(bin_edges.tolist())
        maxcount = np.max(hist)

        for n, rlabel in enumerate(rlabels):
            p = pos[n]
            d = data.ix[:,rlabel]
            if len(d.columns) == 1:
                draw_lines(d.ix[:,0], maxcount, hist[0], bin_edges[0], sides=[-1,1])
            else:
                draw_lines(d.ix[:,0], maxcount, hist[0], bin_edges[0], sides=[-1,0])
                draw_lines(d.ix[:,1], maxcount, hist[1], bin_edges[1], sides=[ 0,1])

        ax.set_xlim(min(pos)-3*w, max(pos)+3*w)
        #ax.set_xticks([-1]+pos+[1])
        ax.set_xticks(pos)
        #import pdb; pdb.set_trace()
        #ax.set_xticklabels(['-1']+np.array(data.major_axis).tolist()+['1'])
        if len(rlabels) > 1:
            ax.set_xticklabels(rlabels)
        else:
            ax.set_xticklabels('')

        return ax


    def beanplot(self, data, ax=None, pos=None, mean=True, median=True, cut=None,
        order=None, discrete=True, **kwargs):
        """Make a bean plot of each dataset in the `data` sequence.

        Reference: http://www.jstatsoft.org/v28/c01/paper
        """

        data_tr, pos, rlabels = self._beanlike_setup(data, ax, order)

        dist = np.max(pos) - np.min(pos)
        w = min(0.15*max(dist,1.0),0.5) * .5
        ax = self._stripchart(data, pos, rlabels, ax=ax, mean=mean, median=median,
            width=0.8*w, discrete=discrete)
        ax = self._violinplot(data_tr, pos, rlabels, ax=ax, bp=False, cut=cut)

        return ax

    def _beanlike_setup(self, data, ax, order=None):
        data = pandas.DataFrame(data)  # Series will be forced into a DataFrame
        data = data.unstack([n for n in data.index.names if n.startswith('yerr.')])
        data = data.unstack([n for n in data.index.names if n.startswith('rows.')])
        rlabels = data.columns
        data = data.unstack([n for n in data.index.names if n.startswith('yerr.')])
        data = data.T  # now rows and values are in rows, cols in cols

        #if len(data.columns) > 2:
            #raise Exception('Beanplot cannot handle more than two categories')
        if len(data.index.levels[-1]) <= 1:
            raise Exception('Cannot make a beanplot for a single observation')

        ## put columns at the bottom so that it's easy to iterate in violinplot
        #order = {'rows': [], 'cols': []}
        #for i,n in enumerate(data.columns.names):
            #if n.startswith('cols.'):
                #order['cols'].append(i)
            #else:
                #order['rows'].append(i)
        #data = data.reorder_levels(order['rows'] + order['cols'], axis=1)

        if ax is None:
            ax = self.next()
        #if order is None:
        pos = range(len(rlabels))
        #else:
            #pos = np.lexsort((np.array(data.index).tolist(), order))

        return data, pos, rlabels


if __name__ == '__main__':
    n = 8
    nsampl = 10
    k = n * nsampl
    data = {
        'subplots': ['session1']*k*18 + ['session2']*k*18,
        'cond': [1]*k*9 + [2]*k*9 + [1]*k*9 + [2]*k*9,
        'name': (['one', 'one', 'one']*k + ['two', 'two', 'two']*k +
                ['three', 'three', 'three']*k) * 4,
        'levels': (['small']*k + ['medium']*k + ['large']*k)*12,
        'subjID': ['subj%d' % (i+1) for i in np.repeat(range(n),nsampl)] * 36,
        'RT': range(k)*36,
        'accuracy': np.random.randn(36*k)
        }
    df = pandas.DataFrame(data, columns = ['subplots','cond','name','levels','subjID','RT',
        'accuracy'])
    #df = df.reindex_axis(['subplots','cond','name','levels','subjID','RT',
        #'accuracy'], axis=1)
    agg = stats.aggregate(df, subplots='subplots', rows=['cond', 'name'],
        col='levels', yerr='subjID', values='RT')
    fig = Plot(ncols=2)
    fig.plot(agg, subplots=True, yerr=True)
    fig.show()
