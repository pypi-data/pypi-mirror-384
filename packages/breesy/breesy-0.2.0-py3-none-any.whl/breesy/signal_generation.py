import numpy as np
import pandas as pd
from scipy import signal

from .constants import CLASSIC_BANDWIDTHS
from .errors import protect_from_lib_error, BreesyError
from .type_hints import enforce_type_hints


@enforce_type_hints
def generate_sine_wave(frequency: float,
                       amplitude: float,
                       duration: float,
                       sample_rate: int | float,
                       phase: float | int = 0.0) -> np.ndarray:
    """Generate a sine wave at the specified frequency.

    :param frequency: Frequency of the sine wave in Hz
    :param amplitude: Amplitude of the sine wave
    :param duration: Duration of the signal in seconds
    :param sample_rate: Sampling rate in Hz
    :param phase: Phase offset in radians (default: 0)

    :return: 1D numpy array containing the sine wave
    """

    if frequency >= sample_rate / 2:
        raise BreesyError(
            f"Frequency {frequency} Hz exceeds Nyquist frequency ({sample_rate / 2} Hz)",
            f"Choose a frequency below {sample_rate / 2} Hz or increase the sample rate"
        )

    # Generate time vector
    t = np.arange(0, duration, 1 / sample_rate)

    return amplitude * np.sin(2 * np.pi * frequency * t + phase)


@enforce_type_hints
@protect_from_lib_error("numpy")
def generate_white_noise(n_samples: int, random_state: int = 42) -> np.ndarray:
    """Generate Gaussian white noise.

    :param n_samples: Number of samples to generate
    :param random_state: Random seed for reproducibility
    :return: 1D numpy array of white noise
    """
    if n_samples <= 0:
        raise BreesyError(
            f"Number of samples must be positive, got {n_samples}",
            "Use a positive integer for n_samples"
        )

    rng = np.random.default_rng(random_state)
    return rng.normal(0, 1, n_samples)


@enforce_type_hints
@protect_from_lib_error("numpy")
def generate_pink_noise(n_samples: int, random_state: int = 42) -> np.ndarray:
    """Generate pink (1/f) noise.

    :param n_samples: Number of samples to generate
    :param random_state: Random seed for reproducibility

    :return: 1D numpy array of pink noise
    """
    if n_samples <= 0:
        raise BreesyError(
            f"Number of samples must be positive, got {n_samples}",
            "Use a positive integer for n_samples"
        )

    white = generate_white_noise(n_samples, random_state)

    f = np.fft.fftfreq(n_samples)
    f[0] = np.inf  # Avoid division by zero
    f = np.abs(f)

    pink = np.real(np.fft.ifft(np.fft.fft(white) / np.sqrt(f)))
    return pink / np.std(pink)


@enforce_type_hints
@protect_from_lib_error("scipy")
def generate_band_activity(n_samples: int, sample_rate: int | float, fmin: float, fmax: float,
                           random_state: int = 42) -> np.ndarray:
    """Generate band-limited noise in a specific frequency range.

    :param n_samples: Number of samples to generate
    :param sample_rate: Sampling frequency in Hz
    :param fmin: Lower frequency bound in Hz
    :param fmax: Upper frequency bound in Hz
    :param random_state: Random seed for reproducibility

    :return: 1D numpy array of band-limited noise
    """
    if fmax >= sample_rate / 2:
        raise BreesyError(
            f"Maximum frequency {fmax} Hz exceeds Nyquist frequency ({sample_rate / 2} Hz)",
            f"Choose a maximum frequency below {sample_rate / 2} Hz or increase the sampling frequency"
        )

    if fmin >= fmax:
        raise BreesyError(
            f"Minimum frequency {fmin} Hz is greater than maximum frequency {fmax} Hz",
            "Ensure fmin is less than fmax"
        )

    nyq = sample_rate / 2
    b, a = signal.butter(4, [fmin / nyq, fmax / nyq], btype='bp')

    white = generate_white_noise(n_samples, random_state)
    filtered = signal.filtfilt(b, a, white)

    return filtered / np.std(filtered)


@enforce_type_hints
@protect_from_lib_error("numpy")
def generate_background_activity(sample_rate: int | float, n_samples: int, channel_names: list[str],
                                 random_state: int = 42) -> np.ndarray:
    """Generate realistic background EEG activity for multiple channels.

    :param sample_rate: Sampling frequency in Hz
    :param n_samples: Number of samples to generate
    :param channel_names: List of channel names
    :param random_state: Random seed for reproducibility

    :return: 2D numpy array of shape (n_channels, n_samples)
    """
    if not channel_names:
        raise BreesyError(
            "Channel names list is empty",
            "Provide a list of channel names, e.g. ['Fz', 'C3', 'Cz', 'C4', 'Pz']"
        )

    n_channels = len(channel_names)
    background = np.zeros((n_channels, n_samples))

    # Generate pink noise base
    for ch in range(n_channels):
        background[ch] = generate_pink_noise(n_samples, random_state=random_state + ch * 2)

    # Add frequency band components
    for i, (band, (fmin, fmax)) in enumerate(CLASSIC_BANDWIDTHS.items()):
        band_signal = generate_band_activity(
            n_samples=n_samples, sample_rate=sample_rate,
            fmin=fmin, fmax=fmax, random_state=random_state + 1 + i)

        for ch in range(n_channels):
            # Adjust weights based on channel location
            # TODO: do we need P0 and FC below?
            if band == 'alpha' and any(x in channel_names[ch] for x in ['O', 'PO']):
                weight = 1.5  # Stronger alpha in posterior channels
            elif band == 'beta' and any(x in channel_names[ch] for x in ['C', 'FC']):
                weight = 1.5  # Stronger beta in central channels
            else:
                weight = 1.0

            background[ch] += weight * band_signal

    return background


@enforce_type_hints
def generate_mu_effect(sample_rate: int | float, n_samples: int, channel_names: list[str],
                       side: str, strength: float, mu_freq: int = 10) -> np.ndarray:
    """Generate mu rhythm modulation effect.

    :param sample_rate: Sampling frequency in Hz
    :param n_samples: Number of samples to generate
    :param channel_names: List of channel names
    :param side: Which side to generate effect for ('left' or 'right')
    :param strength: Strength of the effect (multiplicative factor)
    :param mu_freq: Frequency of mu rhythm in Hz

    :return: 2D numpy array of shape (n_channels, n_samples)
    """
    if side not in ['left', 'right']:
        raise BreesyError(
            f"Invalid side parameter value: {side}",
            "Use either 'left' or 'right' for the side parameter"
        )

    n_channels = len(channel_names)
    effect = np.zeros((n_channels, n_samples))

    duration = n_samples / sample_rate
    t = np.arange(n_samples) / sample_rate

    # Generate Gaussian-modulated mu rhythm
    mu_amp = np.exp(-((t - duration / 2) ** 2) / (duration / 4) ** 2)
    mu_rhythm = mu_amp * np.sin(2 * np.pi * mu_freq * t)

    # Apply to appropriate channels
    for ch in range(n_channels):
        if (side == 'left' and 'C4' in channel_names[ch]) or \
                (side == 'right' and 'C3' in channel_names[ch]):
            effect[ch] = strength * mu_rhythm
        else:
            effect[ch] = mu_rhythm

    return effect


@enforce_type_hints
def generate_cognitive_load_effect(condition: str, sample_rate: int | float, n_samples: int,
                                   channel_names: list[str], random_state: int = 42) -> np.ndarray:
    """Generate cognitive load-specific EEG modulation.
    Different conditions show distinct patterns in theta and gamma bands.

    :param condition: Task difficulty level ('rest', 'easy', 'medium', or 'hard')
    :param sample_rate: Sampling frequency in Hz
    :param n_samples: Number of samples to generate
    :param channel_names: List of channel names
    :param random_state: Random seed for reproducibility

    :return: 2D numpy array of shape (n_channels, n_samples)
    """
    valid_conditions = ['rest', 'easy', 'medium', 'hard']
    if condition not in valid_conditions:
        raise BreesyError(
            f"Invalid condition: {condition}",
            f"Use one of: {', '.join(valid_conditions)}"
        )

    if not channel_names:
        raise BreesyError(
            "Channel names list is empty",
            "Provide a list of channel names, e.g. ['Fz', 'FC1', 'FC2', 'Cz']"
        )

    n_channels = len(channel_names)
    effect = np.zeros((n_channels, n_samples))

    weights = {
        'theta': {'rest': 1.0, 'easy': 1.2, 'medium': 1.5, 'hard': 2.0},
        'gamma': {'rest': 0.8, 'easy': 1.0, 'medium': 1.3, 'hard': 1.6}
    }

    # Generate theta activity (4-8 Hz)
    theta = generate_band_activity(
        n_samples=n_samples, sample_rate=sample_rate,
        fmin=CLASSIC_BANDWIDTHS['theta'][0],
        fmax=CLASSIC_BANDWIDTHS['theta'][1],
        random_state=random_state
    )

    # Generate gamma activity (30-45 Hz)
    gamma = generate_band_activity(
        n_samples=n_samples, sample_rate=sample_rate,
        fmin=CLASSIC_BANDWIDTHS['gamma'][0],
        fmax=CLASSIC_BANDWIDTHS['gamma'][1],
        random_state=random_state + 1
    )

    for ch in range(n_channels):
        # Theta modulation in frontal midline
        if any(name in channel_names[ch] for name in ['Fz', 'FC1', 'FC2', 'Cz']):
            effect[ch] += weights['theta'][condition] * theta

        # Gamma modulation in frontal and parietal regions
        if any(name in channel_names[ch] for name in ['F', 'P']):
            effect[ch] += weights['gamma'][condition] * gamma

    return effect


@enforce_type_hints
def generate_working_memory_effect(condition: str, sample_rate: int | float, n_samples: int,
                                   channel_names: list[str], random_state: int = 42) -> np.ndarray:
    """Generate working memory-related activity.
    Alpha power decreases with cognitive load in posterior regions.

    :param condition: Task difficulty level ('rest', 'easy', 'medium', or 'hard')
    :param sample_rate: Sampling frequency in Hz
    :param n_samples: Number of samples to generate
    :param channel_names: List of channel names
    :param random_state: Random seed for reproducibility

    :return: 2D numpy array of shape (n_channels, n_samples)
    """
    valid_conditions = ['rest', 'easy', 'medium', 'hard']
    if condition not in valid_conditions:
        raise BreesyError(
            f"Invalid condition: {condition}",
            f"Use one of: {', '.join(valid_conditions)}"
        )

    if not channel_names:
        raise BreesyError(
            "Channel names list is empty",
            "Provide a list of channel names, e.g. ['P3', 'Pz', 'P4', 'O1', 'Oz', 'O2']"
        )

    n_channels = len(channel_names)
    effect = np.zeros((n_channels, n_samples))

    # Alpha suppression increases with cognitive load
    alpha_weights = {
        'rest': 1.0,
        'easy': 0.8,
        'medium': 0.6,
        'hard': 0.4
    }

    alpha = generate_band_activity(
        n_samples=n_samples, sample_rate=sample_rate,
        fmin=CLASSIC_BANDWIDTHS['alpha'][0],
        fmax=CLASSIC_BANDWIDTHS['alpha'][1],
        random_state=random_state
    )

    for ch in range(n_channels):
        if any(name in channel_names[ch] for name in ['P', 'PO', 'O']):
            effect[ch] += alpha_weights[condition] * alpha

    return effect


# TODO: #16 review this
@enforce_type_hints
def generate_spindle(
        sample_rate: int | float,
        n_samples: int,
        frequency: float | int = 13.0,
        strength: float | int = 1.0,
        random_state: int = 42
) -> np.ndarray:
    """Generate a sleep spindle waveform.

    .. note::
        Sleep spindles are bursts of oscillatory neural activity in the sigma band
        (typically 12-14 Hz) that occur during N2 sleep. They typically last 0.5-2 seconds
        and have a characteristic waxing-waning amplitude envelope.

    :param sample_rate: Sampling rate in Hz
    :param n_samples: Number of samples to generate
    :param frequency: Center frequency of the spindle in Hz (default: 13 Hz)
    :param strength: Scaling factor for spindle amplitude (default: 1.0)
    :param random_state: Random seed for reproducibility

    :return: 1D numpy array containing the spindle waveform
    """
    if frequency >= sample_rate / 2:
        raise BreesyError(
            f"Frequency {frequency} Hz exceeds Nyquist frequency ({sample_rate / 2} Hz)",
            f"Choose a frequency below {sample_rate / 2} Hz or increase the sample rate"
        )

    rng = np.random.default_rng(random_state)

    # Generate time vector
    t = np.arange(n_samples) / sample_rate
    duration = n_samples / sample_rate

    # Create amplitude envelope (Gaussian window)
    envelope = np.exp(-((t - duration / 2) ** 2) / ((duration / 6) ** 2))

    # Generate carrier signal with slight frequency modulation
    freq_mod = 0.5 * np.sin(2 * np.pi * 0.5 * t)  # 0.5 Hz frequency modulation
    phase = 2 * np.pi * frequency * t + freq_mod
    carrier = np.sin(phase)

    # Add small random phase jitter
    phase_jitter = rng.normal(0, 0.1, n_samples)
    carrier += 0.1 * np.sin(phase + phase_jitter)

    # Combine envelope and carrier
    spindle = strength * envelope * carrier

    # Normalize
    spindle = spindle / np.max(np.abs(spindle))

    return spindle


@enforce_type_hints
def concatenate_eeg_trials(trials: np.ndarray, sample_rate: int | float, channel_names: list[str],
                           trial_info: list[dict], iti_range: tuple[float, float],
                           random_state: int = 42) -> tuple[np.ndarray, pd.DataFrame]:
    """Combine individual EEG trials into a continuous signal with proper inter-trial intervals.

    :param trials: EEG trials array of shape (n_trials, n_channels, n_samples_per_trial)
    :param sample_rate: Sampling frequency in Hz
    :param channel_names: List of channel names
    :param trial_info: List of dictionaries containing trial metadata
    :param iti_range: Tuple of (min_iti, max_iti) in seconds
    :param random_state: Random seed for reproducibility

    :return: Tuple containing continuous_eeg and events_df
    """
    if not channel_names:
        raise BreesyError(
            "Channel names list is empty",
            "Provide a list of channel names matching the number of channels in trials"
        )

    if len(trials.shape) != 3:
        raise BreesyError(
            f"Invalid trials array shape: {trials.shape}",
            "Trials array should have shape (n_trials, n_channels, n_samples_per_trial); e.g., (100, 16, 512)"
        )

    n_trials, n_channels, n_samples_per_trial = trials.shape

    if n_channels != len(channel_names):
        raise BreesyError(
            f"Number of channels in trials ({n_channels}) doesn't match length of channel_names ({len(channel_names)})",
            "Ensure the number of channels matches the length of channel names list"
        )

    if len(trial_info) != n_trials:
        raise BreesyError(
            f"Number of trials ({n_trials}) doesn't match length of trial_info ({len(trial_info)})",
            "Ensure trial_info list has same length as number of trials"
        )

    if iti_range[0] > iti_range[1]:
        raise BreesyError(
            f"Invalid ITI range: ({iti_range[0]}, {iti_range[1]})",
            "Minimum ITI should be less than maximum ITI"
        )

    rng = np.random.default_rng(random_state)
    iti_durations = rng.uniform(iti_range[0], iti_range[1], n_trials)
    iti_samples = (iti_durations * sample_rate).astype(int)
    total_samples = n_samples_per_trial * n_trials + np.sum(iti_samples)
    continuous_eeg = np.zeros((n_channels, total_samples))

    events = []
    current_sample = 0

    for i in range(n_trials):
        # Add trial
        trial_start = current_sample
        trial_end = trial_start + n_samples_per_trial
        continuous_eeg[:, trial_start:trial_end] = trials[i]

        # Record event information
        event_info = trial_info[i].copy()
        event_info.update({
            'onset_sample': trial_start,
            'offset_sample': trial_end,
            'onset_time': trial_start / sample_rate,
            'offset_time': trial_end / sample_rate,
            'duration': n_samples_per_trial / sample_rate,
            'iti_duration': iti_durations[i] if i < n_trials - 1 else 0
        })
        events.append(event_info)

        # Add ITI if not last trial
        if i < n_trials - 1:
            iti_start = trial_end
            iti_end = iti_start + iti_samples[i]

            # Generate background activity for ITI
            iti_background = generate_background_activity(
                sample_rate=sample_rate,
                n_samples=iti_samples[i],
                channel_names=channel_names,
                random_state=random_state + i
            )

            continuous_eeg[:, iti_start:iti_end] = iti_background
            current_sample = iti_end

    return continuous_eeg, pd.DataFrame(events)


if __name__ == "__main__":
    # Basic test parameters
    duration = 1.0
    sample_rate = 250
    n_samples = int(duration * sample_rate)
    ch_names = ['Fz', 'FC1', 'FC2', 'Cz', 'P3', 'Pz', 'P4', 'O1', 'O2']

    # Test sine wave
    sine = generate_sine_wave(10., 1.0, duration, sample_rate)
    print(f"Sine wave: {len(sine)} samples")

    # Test cognitive load effect
    cognitive = generate_cognitive_load_effect('medium', sample_rate, n_samples, ch_names)
    print(f"Cognitive load effect shape: {cognitive.shape}")

    # Test working memory effect
    memory = generate_working_memory_effect('hard', sample_rate, n_samples, ch_names)
    print(f"Working memory effect shape: {memory.shape}")

    # Test trial concatenation
    n_trials = 3
    trials = np.random.randn(n_trials, len(ch_names), n_samples)  # Random trials
    trial_info = [{'condition': 'test'} for _ in range(n_trials)]
    continuous, events = concatenate_eeg_trials(trials, sample_rate, ch_names, trial_info, (0.5, 1.0))
    print(f"Continuous EEG shape: {continuous.shape}")
    print(f"Number of events: {len(events)}")
