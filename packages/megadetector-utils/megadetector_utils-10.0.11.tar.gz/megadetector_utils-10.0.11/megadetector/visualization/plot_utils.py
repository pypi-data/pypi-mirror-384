"""

plot_utils.py

Utility functions for plotting, particularly for plotting confusion matrices
and precision-recall curves.

"""

#%% Imports

import numpy as np

# This also imports mpl.{cm, axes, colors}
import matplotlib.figure


#%% Plotting functions

def plot_confusion_matrix(matrix,
                          classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=matplotlib.cm.Blues,
                          vmax=None,
                          use_colorbar=True,
                          y_label=True,
                          fmt= '{:.0f}',
                          fig=None):
    """
    Plots a confusion matrix.

    Args:
        matrix (np.ndarray): shape [num_classes, num_classes], confusion matrix
            where rows are ground-truth classes and columns are predicted classes
        classes (list of str): class names for each row/column
        normalize (bool, optional): whether to perform row-wise normalization;
            by default, assumes values in the confusion matrix are percentages
        title (str, optional): figure title
        cmap (matplotlib.colors.colormap, optional): colormap for cell backgrounds
        vmax (float, optional): value corresponding to the largest value of the colormap;
            if None, the maximum value in [matrix] will be used
        use_colorbar (bool, optional): whether to show colorbar
        y_label (bool, optional): whether to show class names on the y axis
        fmt (str, optional): format string for rendering numeric values
        fig (Figure, optional): existing figure to which we should render, otherwise
            creates a new figure

    Returns:
        matplotlib.figure.Figure: the figure we rendered to or created
    """

    num_classes = matrix.shape[0]
    assert matrix.shape[1] == num_classes
    assert len(classes) == num_classes

    normalized_matrix = matrix.astype(np.float64) / (
        matrix.sum(axis=1, keepdims=True) + 1e-7)
    if normalize:
        matrix = normalized_matrix

    fig_h = 3 + 0.3 * num_classes
    fig_w = fig_h
    if use_colorbar:
        fig_w += 0.5

    if fig is None:
        fig = matplotlib.figure.Figure(figsize=(fig_w, fig_h), tight_layout=True)
    ax = fig.subplots(1, 1)
    im = ax.imshow(normalized_matrix, interpolation='nearest', cmap=cmap, vmax=vmax)
    ax.set_title(title)

    if use_colorbar:
        cbar = fig.colorbar(im, fraction=0.046, pad=0.04,
                            ticks=[0.0, 0.25, 0.5, 0.75, 1.0])
        cbar.set_ticklabels(['0%', '25%', '50%', '75%', '100%'])

    tick_marks = np.arange(num_classes)
    ax.set_xticks(tick_marks)
    ax.set_yticks(tick_marks)
    ax.set_xticklabels(classes, rotation=90)
    ax.set_xlabel('Predicted class')

    if y_label:
        ax.set_yticklabels(classes)
        ax.set_ylabel('Ground-truth class')

    for i, j in np.ndindex(matrix.shape):
        v = matrix[i, j]
        ax.text(j, i, fmt.format(v),
                horizontalalignment='center',
                verticalalignment='center',
                color='white' if normalized_matrix[i, j] > 0.5 else 'black')

    return fig

# ...def plot_confusion_matrix(...)


def plot_precision_recall_curve(precisions,
                                recalls,
                                title='Precision/recall curve',
                                xlim=(0.0,1.05),
                                ylim=(0.0,1.05)):
    """
    Plots a precision/recall curve given lists of (ordered) precision
    and recall values.

    Args:
        precisions (list of float): precision for corresponding recall values,
            should have same length as [recalls].
        recalls (list of float): recall for corresponding precision values,
            should have same length as [precisions].
        title (str, optional): plot title
        xlim (tuple, optional): x-axis limits as a length-2 tuple
        ylim (tuple, optional): y-axis limits as a length-2 tuple

    Returns:
        matplotlib.figure.Figure: the (new) figure
    """

    assert len(precisions) == len(recalls)

    fig = matplotlib.figure.Figure(tight_layout=True)
    ax = fig.subplots(1, 1)
    ax.step(recalls, precisions, color='b', alpha=0.2, where='post')
    ax.fill_between(recalls, precisions, alpha=0.2, color='b', step='post')

    ax.set_xlabel('Recall')
    ax.set_ylabel('Precision')
    ax.set_title(title)
    ax.set_xlim(xlim[0],xlim[1])
    ax.set_ylim(ylim[0],ylim[1])

    return fig

# ...def plot_precision_recall_curve(...)


def plot_stacked_bar_chart(data,
                           series_labels=None,
                           col_labels=None,
                           x_label=None,
                           y_label=None,
                           log_scale=False):
    """
    Plot a stacked bar chart, for plotting e.g. species distribution across locations.

    Reference: https://stackoverflow.com/q/44309507

    Args:
        data (np.ndarray or list of list): data to plot; rows (series) are species, columns
            are locations
        series_labels (list of str, optional): series labels, typically species names
        col_labels (list of str, optional): column labels, typically location names
        x_label (str, optional): x-axis label
        y_label (str, optional): y-axis label
        log_scale (bool, optional): whether to plot the y axis in log-scale

    Returns:
        matplotlib.figure.Figure: the (new) figure
    """

    data = np.asarray(data)
    num_series, num_columns = data.shape
    ind = np.arange(num_columns)

    fig = matplotlib.figure.Figure(tight_layout=True)
    ax = fig.subplots(1, 1)
    colors = matplotlib.cm.rainbow(np.linspace(0, 1, num_series))

    # stacked bar charts are made with each segment starting from a y position
    cumulative_size = np.zeros(num_columns)
    for i_row, row_data in enumerate(data):
        if series_labels is None:
            label = 'series_{}'.format(str(i_row).zfill(2))
        else:
            label = series_labels[i_row]
        ax.bar(ind, row_data, bottom=cumulative_size, label=label,
               color=colors[i_row])
        cumulative_size += row_data

    if (col_labels is not None) and (len(col_labels) < 25):
        ax.set_xticks(ind)
        ax.set_xticklabels(col_labels, rotation=90)
    elif (col_labels is not None):
        ax.set_xticks(list(range(0, len(col_labels), 20)))
        ax.set_xticklabels(col_labels[::20], rotation=90)

    if x_label is not None:
        ax.set_xlabel(x_label)
    if y_label is not None:
        ax.set_ylabel(y_label)
    if log_scale:
        ax.set_yscale('log')

    # To fit the legend in, shrink current axis by 20%
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

    # Put a legend to the right of the current axis
    ax.legend(loc='center left', bbox_to_anchor=(0.99, 0.5), frameon=False)

    return fig

# ...def plot_stacked_bar_chart(...)


def calibration_ece(true_scores, pred_scores, num_bins):
    r"""
    Expected calibration error (ECE) as defined in equation (3) of
    Guo et al. "On Calibration of Modern Neural Networks." (2017).

    Implementation modified from sklearn.calibration.calibration_curve()
    in order to implement ECE calculation. See:

    https://github.com/scikit-learn/scikit-learn/issues/18268

    Args:
        true_scores (list of int): true values, length N, binary-valued (0 = neg, 1 = pos)
        pred_scores (list of float): predicted confidence values, length N, pred_scores[i] is the
            predicted confidence that example i is positive
        num_bins (int): number of bins to use (`M` in eq. (3) of Guo 2017)

    Returns:
        tuple: a length-three tuple containing:
            - accs: np.ndarray, shape [M], type float64, accuracy in each bin,
              M <= num_bins because bins with no samples are not returned
            - confs: np.ndarray, shape [M], type float64, mean model confidence in
              each bin
            - ece: float, expected calibration error
    """

    assert len(true_scores) == len(pred_scores)

    bins = np.linspace(0., 1. + 1e-8, num=num_bins + 1)
    binids = np.digitize(pred_scores, bins) - 1

    bin_sums = np.bincount(binids, weights=pred_scores, minlength=len(bins))
    bin_true = np.bincount(binids, weights=true_scores, minlength=len(bins))
    bin_total = np.bincount(binids, minlength=len(bins))

    nonzero = bin_total != 0
    accs = bin_true[nonzero] / bin_total[nonzero]
    confs = bin_sums[nonzero] / bin_total[nonzero]

    weights = bin_total[nonzero] / len(true_scores)
    ece = np.abs(accs - confs) @ weights
    return accs, confs, ece

# ...def calibration_ece(...)


def plot_calibration_curve(true_scores,
                           pred_scores,
                           num_bins,
                           name='calibration',
                           plot_perf=True,
                           plot_hist=True,
                           ax=None,
                           **fig_kwargs):
    """
    Plots a calibration curve.

    Args:
        true_scores (list of int): true values, length N, binary-valued (0 = neg, 1 = pos)
        pred_scores (list of float): predicted confidence values, length N, pred_scores[i] is the
            predicted confidence that example i is positive
        num_bins (int): number of bins to use (`M` in eq. (3) of Guo 2017)
        name (str, optional): label in legend for the calibration curve
        plot_perf (bool, optional): whether to plot y=x line indicating perfect calibration
        plot_hist (bool, optional): whether to plot histogram of counts
        ax (Axes, optional): if given then no legend is drawn, and fig_kwargs are ignored
        fig_kwargs (dict): only used if [ax] is None

    Returns:
        matplotlib.figure.Figure: the (new) figure
    """

    accs, confs, ece = calibration_ece(true_scores, pred_scores, num_bins)

    created_fig = False
    if ax is None:
        created_fig = True
        fig = matplotlib.figure.Figure(**fig_kwargs)
        ax = fig.subplots(1, 1)
    ax.plot(confs, accs, 's-', label=name)  # 's-': squares on line
    ax.set(xlabel='Model confidence', ylabel='Actual accuracy',
           title=f'Calibration plot (ECE: {ece:.02g})')
    ax.set(xlim=[-0.05, 1.05], ylim=[-0.05, 1.05])
    if plot_perf:
        ax.plot([0, 1], [0, 1], color='black', label='perfect calibration')
    ax.grid(True)

    if plot_hist:
        ax1 = ax.twinx()
        bins = np.linspace(0., 1. + 1e-8, num=num_bins + 1)
        counts = ax1.hist(pred_scores, alpha=0.5, label='histogram of examples',
                          bins=bins, color='tab:red')[0]
        max_count = np.max(counts)
        ax1.set_ylim([-0.05 * max_count, 1.05 * max_count])
        ax1.set_ylabel('Count')

    if created_fig:
        fig.legend(loc='upper left', bbox_to_anchor=(0.15, 0.85))

    return ax.figure

# ...def plot_calibration_curve(...)
