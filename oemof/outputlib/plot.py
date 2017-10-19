import logging
import pandas as pd
import matplotlib.pyplot as plt
from oemof.outputlib import views


class ViewPlot:
    r"""Creates plots based on the subset of a multi-indexed pandas dataframe
    of the :class:`ResultsDataFrame class
    <oemof.outputlib.to_pandas.ResultsDataFrame>`.

    Parameters
    ----------
    subset : pandas.DataFrame
        A subset of the results DataFrame.
    ax : matplotlib axis object
        Axis object of the last plot.

    Attributes
    ----------
    subset : pandas.DataFrame
        A subset of the results DataFrame.
    ax : matplotlib axis object
        Axis object of the last plot.
    """

    def __init__(self, results, node=None, **kwargs):
        self.results = results
        self.seq = pd.DataFrame()
        self.subset = pd.DataFrame()
        self.in_cols = None
        self.out_cols = None
        self.node = None
        self.ax = kwargs.get('ax')
        self.legend_kwargs = {}
        if node is not None:
            self.update_node(node)

    def update_node(self, node):
        self.seq = views.node(self.results, node)['sequences']
        self.in_cols = [
            c for c in self.seq.columns if (len(c[0]) > 1 and c[0][1] == node)]
        self.out_cols = [
            c for c in self.seq.columns if (len(c[0]) > 1 and c[0][0] == node)]
        self.node = node
        self.subset = self.seq
        self.legend_kwargs.pop('labels', None)
        self.legend_kwargs.pop('handles', None)

    def rearrange_subset(self, order, df=None):
        r"""
        Change the order of the subset DataFrame

        Parameters
        ----------
        df : pd.DataFrame
            Table to rearrange.
        order : list
            New order of columns

        Returns
        -------
        self
        """
        if df is None:
            df = self.subset
            use_subset = True
        else:
            use_subset = False
        cols = list(df.columns.values)
        neworder = [x for x in list(order) if x in set(cols)]
        missing = [x for x in list(cols) if x not in set(order)]
        if len(missing) > 0:
            logging.warning(
                "Columns that are not part of the order list are removed: " +
                str(missing))
        if use_subset:
            self.subset = df[neworder]
        return df[neworder]

    def color_from_dict(self, colordict, df=None):
        r""" Method to convert a dictionary containing the components and its
        colors to a color list that can be directly used with the color
        parameter of the pandas plotting method.

        Parameters
        ----------
        colordict : dictionary
            A dictionary that has all possible components as keys and its
            colors as items.
        df : pd.DataFrame
            Table to fetch colors for..

        Returns
        -------
        list
            Containing the colors of all components of the subset attribute
        """
        if df is None:
            df = self.subset
        tmplist = list(
            map(colordict.get, list(df.columns)))
        tmplist = ['#ff00f0' if v is None else v for v in tmplist]
        if len(tmplist) == 1:
            colorlist = tmplist[0]
        else:
            colorlist = tmplist

        return colorlist

    def set_datetime_ticks(self, tick_distance=None, number_autoticks=3,
                           date_format='%d-%m-%Y %H:%M'):
        r""" Set configurable ticks for the time axis. One can choose the
        number of ticks or the distance between ticks and the format.

        Parameters
        ----------
        tick_distance : real
            The distance between to ticks in hours. If not set autoticks are
            set (see number_autoticks).
        number_autoticks : int (default: 3)
            The number of ticks on the time axis, independent of the time
            range. The higher the number of ticks is, the shorter should be the
            date_format string.
        date_format : string (default: '%d-%m-%Y %H:%M')
            The string to define the format of the date and time. See
            https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior
            for more information.
        """
        dates = self.subset.index

        xticks = [int(x) for x in self.ax.get_xticks()]

        if tick_distance is None:
            tick_distance = int(len(dates) / number_autoticks) - 1

        self.ax.set_xticks(range(xticks[0], xticks[-1], tick_distance),
                           minor=False)
        self.ax.set_xticklabels(
            [item.strftime(date_format)
             for item in dates.tolist()[0::tick_distance]],
            rotation=0, minor=False)

    def clear_legend_labels(self):
        if 'handles' not in self.legend_kwargs:
            self.legend_kwargs['handles'] = (
                self.ax.get_legend_handles_labels()[0])
        if 'labels' not in self.legend_kwargs:
            self.legend_kwargs['labels'] = (
                self.ax.get_legend_handles_labels()[1])

        new_labels = []
        for label in self.legend_kwargs['labels']:
            label = label.replace('(', '')
            label = label.replace('), flow)', '')
            label = label.replace(self.node, '')
            label = label.replace(',', '')
            label = label.replace(' ', '')
            new_labels.append(label)
            self.legend_kwargs['labels'] = new_labels
        self.ax.legend(**self.legend_kwargs)

    def outside_legend(self, reverse=False, plotshare=0.9, **kwargs):
        r""" Move the legend outside the plot. Bases on the ideas of Joe
        Kington. See
        http://stackoverflow.com/questions/4700614/how-to-put-the-legend-out-of-the-plot
        for more information.

        Parameters
        ----------
        reverse : boolean (default: False)
            Print out the legend in reverse order. This is interesting for
            stack-plots to have the legend in the same order as the stacks.
        plotshare : real (default: 0.9)
            Share of the plot area to create space for the legend (0 to 1).

        Other Parameters
        ----------------
        loc : string (default: 'center left')
            Location of the plot.
        bbox_to_anchor : tuple (default: (1, 0.5))
            Set the anchor for the legend.
        ncol : integer (default: 1)
            Number of columns of the legend.
        handles : list of handles
            A list of handels if they are already modified by another function
            or method. Normally these handles will be automatically taken from
            the artist object.
        lables : list of labels
            A list of labels if they are already modified by another function
            or method. Normally these handles will be automatically taken from
            the artist object.
        Note
        ----
        All keyword arguments (kwargs) will be directly passed to the
        matplotlib legend class. See
        http://matplotlib.org/api/legend_api.html#matplotlib.legend.Legend
        for more parameters.
        """
        self.legend_kwargs.update(kwargs)
        self.legend_kwargs.setdefault('loc', 'center left')
        self.legend_kwargs.setdefault('bbox_to_anchor', (1, 0.5))
        self.legend_kwargs.setdefault('ncol', 1)
        if 'handles' not in self.legend_kwargs:
            self.legend_kwargs['handles'] = (
                self.ax.get_legend_handles_labels()[0])
        if 'labels' not in self.legend_kwargs:
            self.legend_kwargs['labels'] = (
                self.ax.get_legend_handles_labels()[1])

        if reverse:
            self.legend_kwargs['handles'].reverse()
            self.legend_kwargs['labels'].reverse()

        box = self.ax.get_position()
        self.ax.set_position([box.x0, box.y0, box.width * plotshare,
                              box.height])

        self.ax.legend(**self.legend_kwargs)

    def slice_results(self, date_from=None, date_to=None):
        if date_from is None:
            date_from = self.seq.index[0]
        if date_to is None:
            date_to = self.seq.index[-1]

        self.subset = self.seq.loc[date_from:date_to]

    def plot(self, node=None, original_xticks=True, **kwargs):
        r""" Passing the subset attribute to the pandas plotting method. All
        parameters will be directly passed to pandas.DataFrame.plot(). See
        http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.plot.html
        for more information.

        Returns
        -------
        self
        """
        if node is not None:
            self.update_node(node)
        if original_xticks:
            self.ax = self.subset.plot(**kwargs)
        else:
            self.ax = self.subset.reset_index(drop=True).plot(**kwargs)
        self.legend_kwargs['handles'] = self.ax.get_legend_handles_labels()[0]
        self.legend_kwargs['labels'] = self.ax.get_legend_handles_labels()[1]
        return self

    def io_plot(self, node=None, cdict=None, line_kwa=None, bar_kwa=None,
                area_kwa=None, inorder=None, outorder=None, smooth=False,
                ax=None):
        r""" Plotting a combined bar and line plot to see the fitting of in-
        and out-coming flows of a bus balance.

        Parameters
        ----------
        cdict : dictionary
            A dictionary that has all possible components as keys and its
            colors as items.
        node : str
            Label of the component you want to plot.
        line_kwa : dictionary
            Keyword arguments to be passed to the pandas line plot.
        bar_kwa : dictionary
            Keyword arguments to be passed to the pandas bar plot.
        inorder : list
            Order of columns to plot the line plot
        outorder : list
            Order of columns to plot the bar plot

        Note
        ----
        Further keyword arguments will be passed to the
        :class:`slice_unstacked method <DataFramePlot.slice_unstacked>`.

        Returns
        -------
        handles, labels
            Manipulated labels to correct the unusual construction of the
            stack line plot. You can use them for further manipulations.
        """
        if node is not None:
            self.update_node(node)

        if ax is not None:
            self.ax = ax

        if bar_kwa is None:
            bar_kwa = {}
        if line_kwa is None:
            line_kwa = {}
        if area_kwa is None:
            area_kwa = {}

        if self.ax is None:
            fig = plt.figure()
            self.ax = fig.add_subplot(1, 1, 1)

        local_subset = self.subset.reset_index(drop=True)

        # Create a bar plot for all input flows
        seq_in = local_subset[self.in_cols]

        if inorder is not None:
            seq_in = self.rearrange_subset(inorder, seq_in)

        if cdict is not None:
            colors = self.color_from_dict(cdict, seq_in)
        else:
            colors = None

        if smooth:
            seq_in.plot(kind='area', linewidth=0, stacked=True,
                        ax=self.ax, color=colors, **area_kwa)
        else:
            seq_in.plot(kind='bar', linewidth=0, stacked=True, width=1,
                        ax=self.ax, color=colors, **bar_kwa)

        # Create a line plot for all output flows
        seq_out = local_subset[self.out_cols]

        if outorder is not None:
            seq_out = self.rearrange_subset(outorder, seq_out)
        # The following changes are made to have the bottom line on top layer
        # of all lines. Normally the bottom line is the first line that is
        # plotted and will be on the lowest layer. This is difficult to read.
        new_df = pd.DataFrame(index=seq_out.index)
        n = 0
        tmp = 0
        for col in seq_out.columns:
            if n < 1:
                new_df[col] = seq_out[col]
            else:
                new_df[col] = seq_out[col] + tmp
            tmp = new_df[col]
            n += 1
        if outorder is None:
            new_df.sort_index(axis=1, ascending=False, inplace=True)
        else:
            lineorder = list(outorder)
            lineorder.reverse()
            new_df = new_df[lineorder]

        if cdict is not None:
            colorlist = self.color_from_dict(cdict, seq_out)
        else:
            colorlist = None

        if isinstance(colorlist, list):
            colorlist.reverse()

        separator = len(new_df.columns)

        if smooth:
            new_df.plot(kind='line', ax=self.ax, color=colorlist, **line_kwa)
        else:
            new_df.plot(kind='line', ax=self.ax, color=colorlist,
                        drawstyle='steps-mid', **line_kwa)

        # Adapt the legend to the new order
        handles, labels = self.ax.get_legend_handles_labels()
        tmp_lab = [x for x in reversed(labels[0:separator])]
        tmp_hand = [x for x in reversed(handles[0:separator])]
        handles = tmp_hand + handles[separator:]
        labels = tmp_lab + labels[separator:]
        labels.reverse()
        handles.reverse()

        self.ax.legend(handles, labels)
        self.legend_kwargs['handles'] = handles
        self.legend_kwargs['labels'] = labels
