import numpy as np
from scipy.signal import butter, sosfilt, resample as sp_resample
from scipy.fft import rfft, rfftfreq
from numba import njit, prange

# Signal processing functions

def bandpass_filter(dt, rec, lowcut=0.1, highcut=25.0, order=4):
    """
    Apply a band-pass Butterworth filter to remove low-frequency drift.
    """
    nyquist = 0.5 / dt  # Nyquist frequency
    low = lowcut / nyquist
    highcut = min(highcut, nyquist * 0.99)
    high = highcut / nyquist
    sos = butter(order, [low, high], btype='band', output='sos')
    n = len(rec)
    next_pow2 = int(2 ** np.ceil(np.log2(2 * n)))
    pad_width = next_pow2 - n
    signal_padded = np.pad(rec, (pad_width // 2, pad_width - pad_width // 2), mode='constant')
    filtered_rec = sosfilt(sos, signal_padded)
    filtered_rec = filtered_rec[pad_width // 2: -(pad_width - pad_width // 2)]
    return filtered_rec

def baseline_correction(rec, degree=1):
    " Baseline correction using polynomial fit "
    n = len(rec)
    x = np.arange(n)
    baseline_coefficients = np.polyfit(x, rec, degree)
    baseline = np.polyval(baseline_coefficients, x)
    corrected_signal = rec - baseline
    return corrected_signal

def moving_average(rec, window_size=9):
    """
    Perform a moving average smoothing on the input records.
    """
    if window_size % 2 == 0:
        raise ValueError("Window size should be odd.")
    window = np.ones(window_size) / window_size
    if rec.ndim == 1:
        smoothed_rec = np.convolve(rec, window, mode='same')
    elif rec.ndim == 2:
        smoothed_rec = np.apply_along_axis(lambda x: np.convolve(x, window, mode='same'), axis=1, arr=rec)
    else:
        raise ValueError("Input must be a 1D or 2D array.")
    return smoothed_rec

def resample(dt, dt_new, rec):
    """
    resample a time series from an original time step dt to a new one dt_new.
    """
    npts = len(rec)
    duration = (npts - 1) * dt
    npts_new = int(np.floor(duration / dt_new)) + 1
    ac_new = sp_resample(rec, npts_new)
    return npts_new, dt_new, ac_new

# Properties of the signal

def get_mzc(rec):
    """
    The mean cumulative number of zero up and down crossings
    """
    cross_mask = rec[..., :-1] * rec[..., 1:] < 0
    cross_vec = np.empty_like(rec)
    cross_vec[..., :-1] = cross_mask * 0.5
    cross_vec[..., -1] = cross_vec[..., -2]
    return np.cumsum(cross_vec, axis=-1)

def get_pmnm(rec):
    """
    The mean cumulative number of positive-minima and negative-maxima
    """
    pmnm_mask =((rec[..., :-2] < rec[..., 1:-1]) & (rec[..., 1:-1] > rec[..., 2:]) & (rec[..., 1:-1] < 0) |
               (rec[..., :-2] > rec[..., 1:-1]) & (rec[..., 1:-1] < rec[..., 2:]) & (rec[..., 1:-1] > 0))
    pmnm_vec = np.empty_like(rec)
    pmnm_vec[..., 1:-1] = pmnm_mask * 0.5
    pmnm_vec[..., 0] = pmnm_vec[..., 1]
    pmnm_vec[..., -1] = pmnm_vec[..., -2]
    return np.cumsum(pmnm_vec, axis=-1)

def get_mle(rec):
    """
    The mean cumulative number of local extrema (peaks and valleys)
    """
    mle_mask = ((rec[..., :-2] < rec[..., 1:-1]) & (rec[..., 1:-1] > rec[..., 2:]) |
                (rec[..., :-2] > rec[..., 1:-1]) & (rec[..., 1:-1] < rec[..., 2:]))
    mle_vec = np.empty_like(rec)
    mle_vec[..., 1:-1] = mle_mask * 0.5
    mle_vec[..., 0] = mle_vec[..., 1]
    mle_vec[..., -1] = mle_vec[..., -2]
    return np.cumsum(mle_vec, axis=-1)

@njit('float64[:, :, :, :](float64, float64[:, :], float64[:], float64, float64)', fastmath=True, parallel=True, cache=True)
def run_sdof_linear(dt, rec, period, zeta, mass):
    """
    linear analysis of a SDOF model using newmark method
    It parallelizes the computation across different SDOF periods

    Effective force for ground motion excitation
        Use: p = -m * rec

    The total acceleration are computed as ac_tot = ac + rec
    disp, vel, ac are relative to the ground

    Parameters
    ----------
    dt : float
        time step.
    rec
        input ground motions 2d-array.
    period : np.array
        period array.
    zeta : float, optional
        damping ration of SDOF. The default is 0.05.
    mass : float, optional
        mass of SDOF. The default is 1.0.

    sdf_responses : 4d-array (response_type, n_rec, npts, n_period)
        response_type corresponds to disp, vel, ac, ac_tot
    """
    n_rec = rec.shape[0]
    npts = rec.shape[1]
    n_sdf = len(period)
    
    out_responses = np.empty((4, n_rec, npts, n_sdf))
    p = -mass * rec

    wn = 2 * np.pi / period
    k = mass * wn**2
    c = 2 * mass * wn * zeta

    # Newmark-beta coefficients
    gamma = 0.5
    beta_vals = np.full(n_sdf, 1.0 / 6.0) # Linear acceleration
    beta_vals[dt / period > 0.551] = 0.25 # Constant average acceleration

    for j in prange(n_sdf):
        # Extract scalar values for the current system for faster access
        k_j, c_j, beta_j = k[j], c[j], beta_vals[j]

        # Pre-calculate Newmark coefficients for the current system
        a1 = mass / (beta_j * dt**2) + c_j * gamma / (beta_j * dt)
        a2 = mass / (beta_j * dt) + c_j * (gamma / beta_j - 1)
        a3 = mass * (1 / (2 * beta_j) - 1) + c_j * dt * (gamma / (2 * beta_j) - 1)
        k_hat = k_j + a1

        # Get views into the output array for cleaner indexing
        disp = out_responses[0, :, :, j]
        vel = out_responses[1, :, :, j]
        acc = out_responses[2, :, :, j]
        acc_tot = out_responses[3, :, :, j]

        # Initial acceleration (disp and vel are already 0)
        acc[:, 0] = (p[:, 0] - c_j * vel[:, 0] - k_j * disp[:, 0]) / mass
        acc_tot[:, 0] = acc[:, 0] + rec[:, 0]

        # Inner loop: Time-stepping for a single SDOF system
        for i in range(npts - 1):
            dp = p[:, i + 1] + a1 * disp[:, i] + a2 * vel[:, i] + a3 * acc[:, i]
            disp[:, i + 1] = dp / k_hat
            vel[:, i + 1] = ((gamma / (beta_j * dt)) * (disp[:, i + 1] - disp[:, i]) +
                             (1 - gamma / beta_j) * vel[:, i] +
                             dt * acc[:, i] * (1 - gamma / (2 * beta_j)))
            acc[:, i + 1] = ((disp[:, i + 1] - disp[:, i]) / (beta_j * dt**2) -
                             vel[:, i] / (beta_j * dt) -
                             acc[:, i] * (1 / (2 * beta_j) - 1))
            acc_tot[:, i + 1] = acc[:, i + 1] + rec[:, i + 1]
    return out_responses    

def get_spectra(dt: float, rec: np.ndarray, period: np.ndarray, zeta: float = 0.05, chunk_size: int = 10):
    """
    Calculates displacement, velocity, and total acceleration response spectra (SD, SV, SA)
    """
    n_rec, npts = rec.shape
    n_period = len(period)

    sd = np.empty((n_rec, n_period))
    sv = np.empty((n_rec, n_period))
    sa = np.empty((n_rec, n_period))

    for start in range(0, n_rec, chunk_size):
        end = min(start + chunk_size, n_rec)
        rec_chunk = rec[start:end]
        sdf_responses_chunk = run_sdof_linear(dt, rec_chunk, period, zeta, 1.0)

        np.abs(sdf_responses_chunk, out=sdf_responses_chunk)
        np.max(sdf_responses_chunk[0], axis=1, out=sd[start:end])
        np.max(sdf_responses_chunk[1], axis=1, out=sv[start:end])
        np.max(sdf_responses_chunk[3], axis=1, out=sa[start:end])

    return sd, sv, sa

def slice_energy(ce: np.ndarray, target_range: tuple[float, float] = (0.001, 0.999)):
    " A slicer of the input motion using a target cumulative energy range (as a fraction of total energy) "
    total_energy = ce[-1]
    start_idx = np.searchsorted(ce, target_range[0] * total_energy)
    end_idx = np.searchsorted(ce, target_range[1] * total_energy)
    return slice(start_idx, end_idx + 1)

def slice_amplitude(rec: np.ndarray, threshold: float):
    " A slicer of the input motion using an amplitude threshold. "
    indices = np.nonzero(np.abs(rec) > threshold)[0]
    if len(indices) == 0:
        raise ValueError("No values exceed the threshold. Consider using a lower threshold value.")
    return slice(indices[0], indices[-1] + 1)

def slice_freq(freq: np.ndarray, target_range: tuple[float, float] = (0.1, 25.0)):
    " A slicer of the frequencies using a frequency range in Hz"
    start_idx = np.searchsorted(freq, target_range[0] * 2 * np.pi)
    end_idx = np.searchsorted(freq, target_range[1] * 2 * np.pi)
    return slice(start_idx, end_idx + 1)

def get_ce(dt: float, rec: np.ndarray):
    """
    Compute the cumulative energy
    """
    return np.cumsum(rec ** 2, axis=-1) * dt

def get_integral(dt: float, rec: np.ndarray):
    """
    Compute the velocity of an acceleration input
    """
    return np.cumsum(rec, axis=-1) * dt

def get_integral_detrend(dt: float, rec: np.ndarray):
    """
    Compute the integral with linear detrending
    """
    uvec = get_integral(dt, rec)
    return uvec - np.linspace(0.0, uvec[-1], len(uvec))

def get_peak_param(rec: np.ndarray):
    " Peak ground motion parameter"
    return np.max(np.abs(rec), axis=-1)

def get_cav(dt: float, rec: np.ndarray):
    " Cumulative absolute velocity"
    return np.sum(np.abs(rec), axis=-1) * dt

def get_fas(npts, rec):
    " Fourier amplitude spectrum "
    return np.abs(rfft(rec)) / np.sqrt(npts / 2)

def get_freq(npts, dt):
    " Angular frequency upto Nyq "
    return rfftfreq(npts, dt) * 2 * np.pi

def get_time(npts, dt):
    " time array "
    return np.linspace(0, (npts - 1) * dt, npts)

def get_magnitude(rec1, rec2):
    " magnitude of a vector that is indepednent of coordinate system"
    return np.sqrt(np.abs(rec1) ** 2 + np.abs(rec2) ** 2)

def get_angle(rec1, rec2):
    " angle of a vector that is depednent on coordinate system"
    return np.unwrap(np.arctan2(rec2, rec1))

def get_turning_rate(dt, rec1, rec2):
    " turning rate or angular velocity of a vector that is indepednent of coordinate system"
    anlges = get_angle(rec1, rec2)
    if len(anlges.shape) == 1:
        return np.diff(anlges, prepend=anlges[0]) / dt
    else:
        return np.diff(anlges, prepend=anlges[..., 0][:, None]) / dt

def rotate_records(rec1, rec2, angle):
    " rotated components in the new coordinate system"
    xr = rec1 * np.cos(angle) - rec2 * np.sin(angle)
    yr = rec1 * np.sin(angle) + rec2 * np.cos(angle)
    return xr, yr

def get_correlation(rec1, rec2):
    " correlation between two signals"
    return np.sum(rec1 * rec2) / np.sqrt(np.sum(rec1 ** 2) * np.sum(rec2 ** 2))