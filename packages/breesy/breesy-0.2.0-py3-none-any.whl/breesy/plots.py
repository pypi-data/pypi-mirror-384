import matplotlib.pyplot as plt

from .filtering import select_bandwidth
import numpy as np

from .recording import Recording, select_channels, cut_by_sample_range
from .errors import BreesyError
from . import constants
from .processing import get_frequency_spectrum, get_ica_components
from .type_hints import enforce_type_hints
from .breesy_scipy import _si_get_rbf_interpolator

LENGTH_PLOT_PARAMS = """
:param start: Start time in seconds for the plot
:param duration: Duration in seconds to plot; use -1 to use the whole recording
"""

MONTAGE_PLOT_PARAMS = """
:param head_radius: Relative radius of the head outline
:param head_color: Fill color for the head outline
:param edge_color: Color for head outline
:param fontsize: Font size for electrode labels
"""

MONTAGE_ELECTRODE_COLORS_PARAMS = """
:param electrode_color: Color to fill electrodes
:param electrode_highlight_color: Color to fill highlighted electrodes
"""

COLOR_CYCLE_PARAMS = """
:param cmap: Name of a Matplotlib colormap to use (see https://matplotlib.org/stable/users/explain/colors/colormaps.html for more information)
:param cmap_size: Number of colors to use from the colormap (useful for continuous colormaps)
"""

HEATMAP_PARAMS = """
:param cmap: Name of a Matplotlib colormap to use (see https://matplotlib.org/stable/users/explain/colors/colormaps.html for more information); recommended to use a diverging colormap
:param vmin: Minimum value for color scaling
:param vmax: Maximum value for color scaling
"""

COMMON_PLOT_PARAMS = """
:param savepath: Path to file if you want to save the plot (not saved by default)
:param save_format: Format for saving the plot into a file (default is PDF which is lossless hense publication-ready)
:param figsize: Size of the figure in inches as a tuple: (width, height); each plot has its own recommended figsize used by default
"""

TOPOGRAPHY_PARAMS = """
:param grid_resolution: Resolution of interpolation grid
:param contour_levels: Number of contour levels for visualization
:param contour_alpha: Alpha of the contour lines; set to 0 to remove countours
:param contour_color: Color of contour lines
:param contour_width: Width of contour lines
:param show_electrodes: Whether to show electrode positions
:param electrode_color: Color for electrode markers
:param electrode_size: Size of electrode markers
:param label_electrodes: Whether to label electrodes with channel names
"""

# -------- signal plots


@enforce_type_hints
def plot_recording(recording: Recording,                   
                   start: float | int = 0.0, duration: float | int | None = 60.0,
                   savepath: str | None = None, save_format: str = "pdf",
                   figsize: tuple[int | float, int | float] = None,
                   padding: float | int = 1.0,
                   cmap: str = 'Dark2', cmap_size: int = 8) -> None:
    f"""Plot EEG signals with channels spread vertically.

    :param recording: Input recording
    {LENGTH_PLOT_PARAMS}
    {COMMON_PLOT_PARAMS}
    :param padding: Vertical spacing multiplier between channels, can be increased if signals overlap too much, or decreased if signals are not detailed enough
    {COLOR_CYCLE_PARAMS}
    """

    # TODO: add event visualization

    if figsize is None:
        figsize = (12, recording.number_of_channels/2 * padding)
    fig, ax = plt.subplots(figsize=figsize)

    if duration > recording.duration:
        duration = recording.duration

    _plot_signal(ax=ax, data=recording.data, sample_rate=recording.sample_rate, channel_names=recording.channel_names, 
                 start=start, duration=duration, padding=padding, cmap=cmap, cmap_size=cmap_size)
    _finalize_plot(savepath=savepath, save_format=save_format)


@enforce_type_hints
def plot_recording_channels(recording: Recording,
                            channel_names: list[str],
                            start: float | int = 0.0, duration: float | int = 60.0,
                            savepath: str | None = None, save_format: str = "pdf",
                            figsize: tuple[int | float, int | float] = None,
                            padding: float | int = 1.0,
                            cmap: str = 'Dark2', cmap_size: int = 8) -> None:
    f"""Plot EEG signals for selected channels only.

    :param recording: Input recording
    :param channel_names: List of channel names to include in the plot
    {LENGTH_PLOT_PARAMS}
    {COMMON_PLOT_PARAMS}
    :param padding: Vertical spacing multiplier between channels, can be increased if signals overlap too much, or decreased if signals are not detailed enough
    {COLOR_CYCLE_PARAMS}
    """

    if figsize is None:
        figsize = (12, recording.number_of_channels/2 * padding)
    fig, ax = plt.subplots(figsize=figsize)

    subrecording = select_channels(recording, channel_names)

    _plot_signal(ax=ax, data=subrecording.data, sample_rate=subrecording.sample_rate, channel_names=subrecording.channel_names, 
                 start=start, duration=duration, padding=padding, cmap=cmap, cmap_size=cmap_size)
    _finalize_plot(savepath=savepath, save_format=save_format)


@enforce_type_hints
def plot_decomposed_signal(recording: Recording,
                           bandwidths: dict[str, tuple[float, float]] | None = None,
                           start: float | int = 0, duration: float | int = 3.0,                           
                           savepath: str | None = None, save_format: str = "pdf",
                           figsize: tuple[int | float, int | float] = None,
                           cmap: str = 'Dark2', cmap_size: int = 8) -> None:
    f"""Plot recording signal decomposed into frequency bands.

    :param recording: Input recording
    :param bandwidths: Dictionary of band names and frequency ranges (will use classical bandwidths by default, such as alpha, beta etc.)
    {LENGTH_PLOT_PARAMS}
    {COMMON_PLOT_PARAMS}
    {COLOR_CYCLE_PARAMS}
    """

    if bandwidths is None:
        bandwidths = constants.CLASSIC_BANDWIDTHS   

    start_sample, n_samples, time = _get_timepoints(recording.data, sample_rate=recording.sample_rate, start=start, duration=duration)

    if figsize is None:
        figsize = (12, 2 * len(bandwidths))

    fig, axes = plt.subplots(nrows=len(bandwidths), ncols=1, figsize=figsize, sharex=True, sharey=True)
    
    for (name, (low, high)), ax in zip(bandwidths.items(), axes):
        color_cycle = _get_color_cycle(cmap=cmap, cmap_size=cmap_size)
        filtered = select_bandwidth(recording, low, high)
        for i in range(len(recording.channel_names)):
            ax.plot(time, filtered.data[i, start_sample:n_samples+start_sample], lw=1, alpha=0.8, color=next(color_cycle))
        ax.set_title(f'{name} ({low}-{high} Hz)')
        ax.set_xlim(start, duration+start)
        ax.grid(True)

    plt.xlabel('Time (s)')
    _finalize_plot(savepath=savepath, save_format=save_format)


# -------- frequency plots


@enforce_type_hints
def plot_mean_frequency_spectrum(recording: Recording,
                                 start: float | int = 0, duration: float | int = -1,
                                 savepath: str | None = None, save_format: str = "pdf",
                                 figsize: tuple[int | float, int | float] = None,
                                 color: str = '#aa0000') -> None:
    f"""Plot mean frequency spectrum calculated from all channels. Method used: periodogram.

    :param recording: Input EEG recording
    {LENGTH_PLOT_PARAMS}
    {COMMON_PLOT_PARAMS}
    :param color: Color for the spectrum line
    """

    if figsize is None:
        figsize = (12, 4)
    fig, ax = plt.subplots(figsize=figsize)
    ax.grid(True)
    plt.box(False)

    if (start != 0) or (duration != -1):
        start_sample, n_samples, _ = _get_timepoints(data=recording.data, sample_rate=recording.sample_rate, 
                                                        start=start, duration=duration)
        subrecording = cut_by_sample_range(recording, start_sample, start_sample+n_samples)
    else:
        subrecording = recording

    f, periodograms = get_frequency_spectrum(recording)
    mean_periodogram = periodograms.mean(axis=0)
    geom_mean = np.exp(np.mean(np.log(mean_periodogram)))

    ax.semilogy(f, mean_periodogram, lw=1, color=color)
    ax.set_title(f'Mean periodogram of {len(subrecording.channel_names)} EEG channels')
    ax.set_ylim(geom_mean**2 / mean_periodogram.max(), mean_periodogram.max())
    ax.set_xlim(0, subrecording.sample_rate / 2)
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Power')
    _finalize_plot(savepath=savepath, save_format=save_format)


@enforce_type_hints
def plot_frequency_spectrum(recording: Recording,
                            start: float | int = 0, duration: float | int = -1,
                            savepath: str | None = None, save_format: str = "pdf",
                            figsize: tuple[int | float, int | float] = None,
                            cmap: str = 'Dark2', cmap_size: int = 8) -> None:
    f"""Plot frequency spectrum for all channels in one plot. Method used: periodogram.

    :param recording: Input EEG recording
    {LENGTH_PLOT_PARAMS}
    {COMMON_PLOT_PARAMS}
    {COLOR_CYCLE_PARAMS}
    """

    if figsize is None:
        figsize = (12, 4)
    fig, ax = plt.subplots(figsize=figsize)
    ax.grid(True)
    plt.box(False)

    if (start != 0) or (duration != -1):
        start_sample, n_samples, _ = _get_timepoints(data=recording.data, sample_rate=recording.sample_rate, 
                                                        start=start, duration=duration)
        subrecording = cut_by_sample_range(recording, start_sample, start_sample+n_samples)
    else:
        subrecording = recording

    f, periodograms = get_frequency_spectrum(subrecording)
    geom_mean = np.mean(np.exp(np.mean(np.log(periodograms), axis=1)))

    nch = len(subrecording.channel_names)
    color_cycle = _get_color_cycle(cmap=cmap, cmap_size=cmap_size)
    for i in range(nch):
        ax.semilogy(f, periodograms[i], lw=1, color=next(color_cycle), alpha=max(0.2, min(2/nch, 0.9)))
    ax.set_title(f'Periodogram ({nch} EEG channels)')
    ax.set_xlim(0, subrecording.sample_rate / 2)
    ax.set_ylim(geom_mean**2 / periodograms.max(), periodograms.max())
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Power')
    _finalize_plot(savepath=savepath, save_format=save_format)


# ---- montage plots


@enforce_type_hints
def plot_recording_electrodes(recording: Recording,                              
                              savepath: str | None = None, save_format: str = "pdf",
                              figsize: tuple[int | float, int | float] = None,
                              hide_unused: bool = True, to_highlight: list[str] | None = None,
                              head_radius: int | float = 1.0,
                              head_color: str = constants.COLOR_HEAD_FILL,
                              edge_color: str = constants.COLOR_HEAD_EDGE,
                              fontsize: str | int | float = 10,
                              electrode_color: str = constants.COLOR_ELECTRODE,
                              electrode_highlight_color: str = constants.COLOR_HIGHLIGHT_ELECTRODE) -> None:
    f"""Plot electrode montage showing electrode positions for the recording channels.

    :param recording: Input EEG recording
    {COMMON_PLOT_PARAMS}
    :param hide_unused: Whether to hide electrodes not present in the recording
    :param to_highlight: Which electrodes to highlight with different color (none will be highlighted by default)
    {MONTAGE_PLOT_PARAMS}
    {MONTAGE_ELECTRODE_COLORS_PARAMS}
    """

    montage_name = _detect_montage_type(recording.channel_names)
    locations = _get_locations_for_montage(montage_name)

    if figsize is None:
        figsize = (8, 8)
    fig, ax = plt.subplots(figsize=figsize)

    electrode_names = list(locations.keys())
    electrode_colors = _get_electrode_colors(used_names=recording.channel_names, 
                                             to_show=recording.channel_names if hide_unused else electrode_names, 
                                             to_highlight=to_highlight or [],
                                             head_color=head_color, electrode_color=electrode_color, electrode_highlight_color=electrode_highlight_color)
    _plot_electrode_montage(
        ax=ax,
        locations=locations, electrode_colors=electrode_colors,
        head_radius=head_radius, head_color=head_color, edge_color=edge_color, fontsize=fontsize
    )
    _finalize_plot(savepath=savepath, save_format=save_format)


@enforce_type_hints
def plot_default_montage(montage: str = "10-10",
                         savepath: str | None = None, save_format: str = "pdf",
                         figsize: tuple[int | float, int | float] = None,
                         to_highlight: list[str] | None = None,
                         head_radius: int | float = 1.0,
                         head_color: str = constants.COLOR_HEAD_FILL,
                         edge_color: str = constants.COLOR_HEAD_EDGE,
                         fontsize: str | int | float = 10,
                         electrode_color: str = "#ffffff",
                         electrode_highlight_color: str = constants.COLOR_HIGHLIGHT_ELECTRODE) -> None:
    f"""Plot a standard EEG electrode montage.

    :param montage: EEG montage system (currently supporting "10-10" and "10-20")
    {COMMON_PLOT_PARAMS}
    :param to_highlight: Which electrodes to highlight with different color (none will be highlighted by default)
    {MONTAGE_PLOT_PARAMS}
    {MONTAGE_ELECTRODE_COLORS_PARAMS}
    """

    locations = _get_locations_for_montage(montage)
    electrode_names = list(locations.keys())
    electrode_colors = _get_electrode_colors(used_names=electrode_names, 
                                             to_show=electrode_names, 
                                             to_highlight=to_highlight or [],
                                             head_color=head_color, electrode_color=electrode_color, electrode_highlight_color=electrode_highlight_color)

    if figsize is None:
        figsize = (8, 8)
    fig, ax = plt.subplots(figsize=figsize)

    _plot_electrode_montage(
        ax=ax,
        locations=locations, electrode_colors=electrode_colors,
        head_radius=head_radius, head_color=head_color, edge_color=edge_color, fontsize=fontsize
    )
    _finalize_plot(savepath=savepath, save_format=save_format)


@enforce_type_hints
def plot_electrode_values(recording: Recording,
                          start: float | int, duration: float | int = 1.0,
                          savepath: str | None = None, save_format: str = "pdf",
                          figsize: tuple[int | float, int | float] = None,
                          head_radius: int | float = 1.0,
                          head_color: str = constants.COLOR_HEAD_FILL,
                          edge_color: str = constants.COLOR_HEAD_EDGE,
                          fontsize: str | int | float = 10,
                          cmap: str = 'coolwarm', vmin: float | None = None, vmax: float | None = None) -> None:
    f"""Plot electrodes colored by mean signal values of a certain recording moment.

    :param recording: Input EEG recording
    {LENGTH_PLOT_PARAMS}
    {COMMON_PLOT_PARAMS}
    {MONTAGE_PLOT_PARAMS}    
    {HEATMAP_PARAMS}
    """

    montage_name = _detect_montage_type(recording.channel_names)
    locations = _get_locations_for_montage(montage_name)

    if figsize is None:
        figsize = (8, 8)
    fig, ax = plt.subplots(figsize=figsize)

    start_sample, n_samples, _ = _get_timepoints(data=recording.data, sample_rate=recording.sample_rate, start=start, duration=duration)
    subrecording = cut_by_sample_range(recording, start_sample, start_sample+n_samples)

    values = {}
    for i, name in enumerate(subrecording.channel_names):
        mean_value = subrecording.data[i].mean()
        values[name] = mean_value

    electrode_colors = _values_to_colors(values=values, cmap=cmap, vmin=vmin, vmax=vmax)

    _plot_electrode_montage(
        ax=ax,
        locations=locations, electrode_colors=electrode_colors,
        head_radius=head_radius, head_color=head_color, edge_color=edge_color, fontsize=fontsize
    )
    _finalize_plot(savepath=savepath, save_format=save_format)


# -------- topography map plots


@enforce_type_hints
def plot_mean_topography(recording: Recording,
                         start: float | int, duration: float | int = 1.0,
                         savepath: str | None = None, save_format: str = "pdf",
                         figsize: tuple[int | float, int | float] = None,
                         head_radius: int | float = 1.0,
                         head_color: str = constants.COLOR_HEAD_FILL,
                         edge_color: str = constants.COLOR_HEAD_EDGE,
                         fontsize: str | int | float = 10,
                         grid_resolution: int = constants.TOPOGRAPHY_GRID_RESOLUTION, 
                         contour_levels: int = constants.TOPOGRAPHY_CONTOUR_LEVELS,
                         contour_alpha: float | int = constants.TOPOGRAPHY_CONTOUR_ALPHA,
                         contour_color: str = constants.TOPOGRAPHY_CONTOUR_COLOR,
                         contour_width: int | float = constants.TOPOGRAPHY_CONTOUR_WIDTH,
                         show_electrodes: bool = True,
                         electrode_color: str = constants.TOPOGRAPHY_ELECTRODE_COLOR, 
                         electrode_size: int | float = constants.TOPOGRAPHY_ELECTRODE_SIZE,
                         label_electrodes: bool = False,
                         cmap: str = 'RdBu_r', vmin: float | None = None, vmax: float | None = None) -> None:
    f"""Plot a mean topographic map of a certain recording moment.

    :param recording: Input EEG recording
    {LENGTH_PLOT_PARAMS}
    {COMMON_PLOT_PARAMS}
    {MONTAGE_PLOT_PARAMS}
    {TOPOGRAPHY_PARAMS}
    {HEATMAP_PARAMS}
    """

    # TODO: use vmin and vmax

    montage_name = _detect_montage_type(recording.channel_names)
    locations = _get_locations_for_montage(montage_name, recording.channel_names)

    if figsize is None:
        figsize = (8, 8)
    fig, ax = plt.subplots(figsize=figsize)

    start_sample, n_samples, _ = _get_timepoints(data=recording.data, sample_rate=recording.sample_rate, start=start, duration=duration)
    subrecording = cut_by_sample_range(recording, start_sample, start_sample+n_samples)

    values = {}
    for i, name in enumerate(subrecording.channel_names):
        mean_value = subrecording.data[i].mean()
        values[name] = mean_value   

    _plot_eeg_topography(ax=ax,
                         locations=locations, values=values,
                         grid_resolution=grid_resolution, cmap=cmap,
                         contour_levels=contour_levels, contour_alpha=contour_alpha,
                         contour_color=contour_color, contour_width=contour_width,
                         show_electrodes=show_electrodes, electrode_color=electrode_color,
                         electrode_size=electrode_size, label_electrodes=label_electrodes, fontsize=fontsize,
                         head_radius=head_radius, head_color=head_color, edge_color=edge_color)
    _finalize_plot(savepath=savepath, save_format=save_format)


@enforce_type_hints
def plot_frequency_topography(recording: Recording, frequency: int,
                              start: float | int = 0, duration: float | int = -1,
                              savepath: str | None = None, save_format: str = "pdf",
                              figsize: tuple[int | float, int | float] = None,
                              head_radius: int | float = 1.0,
                              head_color: str = constants.COLOR_HEAD_FILL,
                              edge_color: str = constants.COLOR_HEAD_EDGE,
                              fontsize: str | int | float = 10,
                              grid_resolution: int = constants.TOPOGRAPHY_GRID_RESOLUTION, 
                              contour_levels: int = constants.TOPOGRAPHY_CONTOUR_LEVELS,
                              contour_alpha: float | int = constants.TOPOGRAPHY_CONTOUR_ALPHA,
                              contour_color: str = constants.TOPOGRAPHY_CONTOUR_COLOR,
                              contour_width: int | float = constants.TOPOGRAPHY_CONTOUR_WIDTH,
                              show_electrodes: bool = True,
                              electrode_color: str = constants.TOPOGRAPHY_ELECTRODE_COLOR, 
                              electrode_size: int | float = constants.TOPOGRAPHY_ELECTRODE_SIZE,
                              label_electrodes: bool = False,
                              cmap: str = 'RdBu_r', vmin: float | None = None, vmax: float | None = None) -> None:
    """Plot a single-frequency power topographic map of a certain recording moment.

    :param recording: Input EEG recording
    :param frequency: Target frequency (in Hz)
    {LENGTH_PLOT_PARAMS}
    {COMMON_PLOT_PARAMS}
    {MONTAGE_PLOT_PARAMS}
    {TOPOGRAPHY_PARAMS}
    {HEATMAP_PARAMS}
    """

    # TODO: use vmin and vmax

    montage_name = _detect_montage_type(recording.channel_names)
    locations = _get_locations_for_montage(montage_name, recording.channel_names)

    if figsize is None:
        figsize = (8, 8)
    fig, ax = plt.subplots(figsize=figsize)

    if (start != 0) or (duration != -1):
        start_sample, n_samples, _ = _get_timepoints(data=recording.data, sample_rate=recording.sample_rate, 
                                                        start=start, duration=duration)
        subrecording = cut_by_sample_range(recording, start_sample, start_sample+n_samples)
    else:
        subrecording = recording

    f, periodograms = get_frequency_spectrum(subrecording)
    freq_i = np.searchsorted(f, frequency)
    values = {ch:v for ch, v in zip(recording.channel_names, periodograms[:, freq_i])}

    _plot_eeg_topography(ax=ax,
                         locations=locations, values=values,
                         grid_resolution=grid_resolution, cmap=cmap,
                         contour_levels=contour_levels, contour_alpha=contour_alpha,
                         contour_color=contour_color, contour_width=contour_width,
                         show_electrodes=show_electrodes, electrode_color=electrode_color,
                         electrode_size=electrode_size, label_electrodes=label_electrodes, fontsize=fontsize,
                         head_radius=head_radius, head_color=head_color, edge_color=edge_color)
    _finalize_plot(savepath=savepath, save_format=save_format)


# -------- ICA


def plot_ica_components(recording: Recording, n_components: int, duration: int = 10,
                        normal_range: float | int = 5.0, random_state: int = 42) -> None:
    """Plot Independent Component Analysis (ICA) components from EEG data.

    :param recording: Input EEG recording
    :param n_components: Number of ICA components to compute and display
    :param duration: Duration of signal segments to show around min/max values (in seconds)
    :param normal_range: Y-axis range for reference lines
    :param random_state: Random seed for reproducible ICA decomposition
    """

    components = get_ica_components(recording=recording, n_components=n_components, random_state=random_state)
    time = np.arange(0, recording.number_of_samples) / recording.sample_rate

    min_signal = np.abs(components).argmin(axis=1)
    max_signal = np.abs(components).argmax(axis=1)
    halflen = int(duration // 2 * recording.sample_rate) 

    fig, ax = plt.subplots(n_components, 2, figsize=(14, n_components*1))
    for i in range(n_components):
        _plot_ica_component_segment(
            ax=ax[i, 0],
            time=time, component=components[i],
            sample=min_signal[i], halflen=halflen, normal_range=normal_range)
        _plot_ica_component_segment(
            ax=ax[i, 1],
            time=time, component=components[i],
            sample=max_signal[i], halflen=halflen, normal_range=normal_range)
        ax[i, 0].set_ylabel(f'IC {i}')        

    plt.suptitle('ICA sources')
    ax[0, 0].set_title("Around min source value")
    ax[0, 1].set_title("Around max source value")
        
    plt.tight_layout()
    plt.show()


def _plot_ica_component_segment(ax, time: np.ndarray, component: np.ndarray,
                                sample: int, halflen: int, normal_range: float) -> None:
    help_line_kwargs = {'alpha': 0.6, 'lw': 1, 'ls': '--', 'c': '#ff8800'}
    center_line_kwargs = {'alpha': 0.6, 'lw': 1, 'ls': '--', 'c': '#888888'}
    start, end = max(0, sample - halflen), min(sample + halflen, component.shape[-1])
    ax.plot(time[start:end], component[start:end], lw=1)
    ax.axhline(-normal_range, **help_line_kwargs)
    ax.axhline(normal_range, **help_line_kwargs)
    ax.axhline(0, **center_line_kwargs)
    ax.axvline(0, **help_line_kwargs)
    ax.axvline(time[-1], **help_line_kwargs)
    ax.set_xlim(time[start], time[end])
    ax.set_ylim(component[start:end].min(), component[start:end].max())


# -------- internal functions


def _plot_signal(ax: plt.Axes,
                 data: np.ndarray,
                 sample_rate: int | float, channel_names: list[str],
                 start: float | int, duration: float | int,
                 padding: float | int, cmap: str, cmap_size: int,
                 center_data: bool = True) -> None:
    
    n_channels = len(channel_names)
    start_sample, n_samples, time = _get_timepoints(data=data, sample_rate=sample_rate, start=start, duration=duration)

    visible_data = data[:, start_sample:n_samples+start_sample]
    offset = max([visible_data[i].std()*2 for i in range(n_channels)]) * padding

    color_cycle = _get_color_cycle(cmap=cmap, cmap_size=cmap_size)
    plt.box(False)

    yticks_positions = []
    for i in range(n_channels):
        to_plot = visible_data[i]
        if center_data:
            to_plot = to_plot - to_plot.mean() + i * offset
        ax.plot(time, to_plot, lw=1, alpha=0.8, color=next(color_cycle))
        yticks_positions.append(to_plot[0])

    ax.set_yticks(yticks_positions, channel_names)
    ax.set_ylabel('Channel name')
    ax.set_xlabel('Time (s)')
    ax.set_xlim(start, start+duration)
    ax.grid(True)


def _plot_electrode_montage(ax: plt.Axes,
                            locations: dict[str, tuple[float, float]], electrode_colors: dict[str, str],
                            head_radius: float | int, head_color: str, edge_color: str,
                            fontsize: str | int | float) -> None:
    
    not_in_locations = set(electrode_colors.keys()) - set(locations.keys())
    if not_in_locations:
        print(f'Unrecognized channel names: {", ".join(list(not_in_locations))}. Cannot obtain locations for these channels, so will ignore them.')

    _draw_head(ax=ax, head_radius=head_radius, head_color=head_color, edge_color=edge_color)

    for name, location in locations.items():
        if name in electrode_colors:
            _draw_electrode(ax=ax, name=name, location=location, head_radius=head_radius, color=electrode_colors[name], edge_color=edge_color, fontsize=fontsize)

    ax.set_xlim((-head_radius * 1.25, head_radius * 1.25))
    ax.set_ylim((-head_radius * 1.25, head_radius * 1.25))
    ax.set_aspect('equal')
    ax.set_axis_off()


def _draw_head(ax: plt.Axes, head_radius: float, head_color: str, edge_color: str) -> None:
    import matplotlib.patches as patches

    ear_left = patches.Ellipse(
        xy=(-head_radius, 0),
        width=head_radius / 6,
        height=head_radius / 3,
        fill=True,
        facecolor=head_color,
        edgecolor=edge_color,
        lw=2
    )
    ear_right = patches.Ellipse(
        xy=(head_radius, 0),
        width=head_radius / 6,
        height=head_radius / 3,
        fill=True,
        facecolor=head_color,
        edgecolor=edge_color,
        lw=2
    )
    nose = patches.FancyArrow(
        x=0,
        y=head_radius * 0.95,
        dx=0,
        dy=head_radius / 5,
        fill=True,
        facecolor=head_color,
        edgecolor=edge_color,
        head_width=head_radius / 3,
        head_length=head_radius / 5,
        length_includes_head=True,
        lw=2
    )
    head_circle = patches.Circle(
        xy=(0, 0),
        radius=head_radius,
        facecolor=head_color,
        edgecolor=edge_color,
        fill=True,
        lw=2
    )
    inner_circle = patches.Circle(
        xy=(0, 0),
        radius=head_radius * 0.8,
        color=edge_color,
        fill=False,
        ls='--',
        lw=1
    )

    ax.add_patch(ear_left)
    ax.add_patch(ear_right)
    ax.add_patch(nose)
    ax.add_patch(head_circle)
    ax.add_patch(inner_circle)
    ax.plot([-head_radius, head_radius], [0, 0], ls='--', lw=1, color=edge_color)
    ax.plot([0, 0], [-head_radius, head_radius], ls='--', lw=1, color=edge_color)


def _draw_electrode(ax: plt.Axes, name: str, location: tuple[float, float],
                    head_radius: float, color: str, edge_color: str, fontsize: str) -> None:
    import matplotlib.patches as patches

    electrode_circle = patches.Circle(
        xy=location,
        radius=head_radius / 14,
        facecolor=color,
        edgecolor=edge_color,
        fill=True,
        zorder=2
    )
    ax.add_patch(electrode_circle)

    ax.text(
        x=location[0],
        y=location[1],
        s=name,
        color=edge_color,
        va='center',
        ha='center',
        fontsize=fontsize,
        zorder=2
    )


def _interpolated_head_grid(coords_arr: np.ndarray, values_arr: np.ndarray, 
                            head_radius: float, grid_resolution: int):
    grid_extent = head_radius * 1.1  # Slightly larger than head
    xi = np.linspace(-grid_extent, grid_extent, grid_resolution)
    yi = np.linspace(-grid_extent, grid_extent, grid_resolution)
    xi_grid, yi_grid = np.meshgrid(xi, yi)
    
    rbf = _si_get_rbf_interpolator(coords_arr, values_arr)
    grid_points = np.column_stack([xi_grid.ravel(), yi_grid.ravel()])
    interpolated_values = rbf(grid_points).reshape(xi_grid.shape)

    distance_from_center = np.sqrt(xi_grid**2 + yi_grid**2)
    circular_mask = distance_from_center <= head_radius
    masked_values = np.where(circular_mask, interpolated_values, np.nan)

    return xi_grid, yi_grid, masked_values


def _plot_eeg_topography(ax: plt.Axes,
                         locations: dict[str, tuple[float, float]], values: dict[str, float],
                         grid_resolution: int, cmap: str,
                         contour_levels: int, contour_alpha: float | int, contour_color: str, contour_width: int | float,
                         show_electrodes: bool, electrode_color: str,  electrode_size: float | int, label_electrodes: bool,
                         fontsize: int | float, head_radius: float | int, head_color: str, edge_color: str) -> None:
    import matplotlib.patches as patches

    _draw_head(ax=ax, head_radius=head_radius, head_color=head_color, edge_color=edge_color)

    ch_names = list(locations.keys())
    coords_arr = np.array([locations[ch] for ch in ch_names])
    values_arr = np.array([values[ch] for ch in ch_names])
    xi_grid, yi_grid, interpolated = _interpolated_head_grid(
        coords_arr=coords_arr, values_arr=values_arr, 
        head_radius=head_radius, grid_resolution=grid_resolution
    )
    contour_fill = ax.contourf(xi_grid, yi_grid, interpolated, 
                               levels=contour_levels, cmap=cmap, 
                               extend='both')
    ax.contour(xi_grid, yi_grid, interpolated, 
               levels=contour_levels, colors=contour_color, 
               alpha=contour_alpha, linewidths=contour_width)

    if show_electrodes:
        ax.scatter(coords_arr[:, 0], coords_arr[:, 1], c=electrode_color, s=electrode_size, zorder=5)
        if label_electrodes:
            for name in ch_names:
                ax.annotate(name, locations[name], fontsize=fontsize)

    head_circle = patches.Circle(xy=(0, 0), radius=head_radius, color=edge_color, fill=False, lw=2)
    ax.add_patch(head_circle)

    ax.set_xlim((-head_radius * 1.25, head_radius * 1.25))
    ax.set_ylim((-head_radius * 1.25, head_radius * 1.25))
    ax.set_aspect('equal')
    ax.set_axis_off()

    cbar = plt.colorbar(contour_fill, ax=ax, shrink=0.8, aspect=20)
    cbar.set_label('Amplitude', rotation=270, labelpad=15)


def _finalize_plot(savepath: str | None, save_format: str) -> None:
    plt.tight_layout()
    if savepath:
        plt.savefig(savepath, format=save_format)
    plt.show()


# ---- helping functions


def _get_timepoints(data: np.ndarray, sample_rate: int | float, start: int | float, duration: int | float) -> tuple[int, int, np.ndarray]:
    start_sample = int(start * sample_rate)
    if duration == -1:
        duration = data.number_of_samples - start_sample
    n_samples = int(duration * sample_rate)
    time = np.arange(n_samples) / sample_rate + start
    return start_sample, n_samples, time


def _get_color_cycle(cmap: str = 'Dark2', cmap_size: int = 8):
    from matplotlib import colormaps
    from itertools import cycle
    return cycle(colormaps[cmap](np.linspace(0, 1, cmap_size)))


def _get_electrode_colors(used_names: list[str], to_show: list[str], to_highlight: list[str],
                          head_color: str, electrode_color: str, electrode_highlight_color: str) -> dict[str, str]:
    colors = {}
    for name in to_show:
        if name in to_highlight:
            color = electrode_highlight_color
        elif name not in used_names:
            color = head_color
        else:
            color = electrode_color
        colors[name] = color
    return colors


def _values_to_colors(values: dict[str, float], cmap: str, vmin: float, vmax: float) -> dict:
    import matplotlib.colors as colors
    from matplotlib import colormaps
    vmin = vmin or min(values.values())
    vmax = vmax or min(values.values())
    norm = colors.Normalize(vmin=vmin, vmax=vmax)
    colormap = colormaps.get_cmap(cmap)
    color_dict = {name: colormap(norm(values[name])) for name in values}
    return color_dict


def _get_locations_for_montage(montage_name: str = "10-10", channel_names: list[str] | None = None) -> dict[str, tuple[float, float]]:
    if montage_name in ['10-20', '10_20', '1020']:
        locations = constants.EEG_MONTAGES['10-20']
    elif montage_name in ['10-10', '10_10', '1010']:
        locations = constants.EEG_MONTAGES['10-10']
    else:
        raise BreesyError(f'Unknown montage type: {montage_name}. Use either 10-10 (default) or 10-20.')
    if channel_names is not None:
        locations = {ch: coords for ch, coords in locations.items() if ch in channel_names}
        if len(locations) < len(channel_names):
            unknown_channels = [ch for ch in channel_names if ch not in locations.keys()]
            raise BreesyError(f'Found unknown channel(s) not defined for the {montage_name} montage: {", ".join(unknown_channels)}')
    return locations


def _detect_montage_type(ch_names: list[str]) -> str:
    if any([ch.lower() in [x.lower() for x in constants.EEG_MONTAGES['10-10'].keys()] for ch in ch_names]):
        print("Using 10-10 montage...")
        return "10-10"
    else:
        print("Using 10-20 montage...")
        return "10-20"
