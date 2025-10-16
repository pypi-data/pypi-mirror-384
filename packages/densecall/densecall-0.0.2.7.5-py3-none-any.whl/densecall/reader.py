"""
modified based on Bonito Read Utils
"""

from glob import iglob
from collections import OrderedDict
from importlib import import_module
import os, sys
import torch
import numpy as np


__formats__ = ["fast5", "pod5"]

# Normalisation parameters for kit 14 DNA
# Different parameters can be specified in the 'normalisation' section
# of a bonito config file
__default_norm_params__ = {'quantile_a' : 0.2,
                           'quantile_b' : 0.9,
                           'shift_multiplier' : 0.51,
                           'scale_multiplier' : 0.53}

class Reader:

    def __init__(self, directory, recursive=False):
        self.fmt = None
        if os.path.isfile(directory):  # 判断是否为文件
            # 从文件路径中提取扩展名
            file_ext = os.path.splitext(directory)[1].lstrip('.')
            if file_ext in __formats__:
                self.fmt = file_ext
            else:
                raise FileNotFoundError(f"Unsupported file format: {file_ext}")
        else:  # 处理文件夹情况
            for fmt in __formats__:
                pattern = f"**/*.{fmt}" if recursive else f"*.{fmt}"
                match = next(iglob(directory + "/" + pattern, recursive=True), None)
                if match is not None:
                    self.fmt = fmt
                    break
            else:
                raise FileNotFoundError()

        _reader = import_module(f"densecall.{self.fmt}")
        self._get_reads = getattr(_reader, "get_reads")
        self._get_read_groups = getattr(_reader, "get_read_groups")

    def get_reads(self, *args, **kwargs):
        return self._get_reads(*args, **kwargs)

    def get_read_groups(self, *args, **kwargs):
        return self._get_read_groups(*args, **kwargs)


class Read:

    def __init__(self, read, filename, meta=False):
        ...

    def __repr__(self):
        return "Read('%s')" % self.read_id

    def readgroup(self, model):
        self._groupdict = OrderedDict([
            ('ID', f"{self.run_id}_{model}"),
            ('PL', f"ONT"),
            ('DT', f"{self.exp_start_time}"),
            ('PU', f"{self.flow_cell_id}"),
            ('PM', f"{self.device_id}"),
            ('LB', f"{self.sample_id}"),
            ('SM', f"{self.sample_id}"),
            ('DS', f"%s" % ' '.join([
                f"run_id={self.run_id}",
                f"basecall_model={model}",
            ]))
        ])
        return '\t'.join(["@RG", *[f"{k}:{v}" for k, v in self._groupdict.items()]])

    def tagdata(self):
        return [
            f"mx:i:{self.mux}",
            f"ch:i:{self.channel}",
            f"st:Z:{self.start_time}",
            f"du:f:{self.duration}",
            f"rn:i:{self.read_number}",
            f"f5:Z:{self.filename}",
            f"sm:f:{self.shift}",
            f"sd:f:{self.scale}",
            f"sv:Z:quantile",
        ]


class ReadChunk:

    def __init__(self, read, chunk, i, n):
        self.read_id = "%s:%i:%i" % (read.read_id, i, n)
        self.run_id = read.run_id
        self.filename = read.filename
        self.mux = read.mux
        self.channel = read.channel
        self.start = read.start
        self.duration = read.duration
        self.template_start = self.start
        self.template_duration = self.duration
        self.signal = chunk
        self.num_samples = read.num_samples
        self.trimmed_samples = read.trimmed_samples

    def __repr__(self):
        return "ReadChunk('%s')" % self.read_id


def read_chunks(read, chunksize=4000, overlap=400):
    """
    Split a Read in fixed sized ReadChunks
    """
    if len(read.signal) < chunksize:
        return
    # import sys
    # print(chunksize, file=sys.stderr)
    _, offset = divmod(len(read.signal) - chunksize, chunksize - overlap)
    signal = torch.from_numpy(read.signal[offset:])
    blocks = signal.unfold(0, chunksize, chunksize - overlap)

    for i, block in enumerate(blocks):
        yield ReadChunk(read, block.numpy(), i+1, blocks.shape[0])


def trim(signal, window_size=40, threshold=2.4, min_trim=10, min_elements=3, max_samples=8000, max_trim=0.3):

    seen_peak = False
    num_windows = min(max_samples, len(signal)) // window_size

    for pos in range(num_windows):
        start = pos * window_size + min_trim
        end = start + window_size
        window = signal[start:end]
        if len(window[window > threshold]) > min_elements or seen_peak:
            seen_peak = True
            if window[-1] > threshold:
                continue
            if end >= min(max_samples, len(signal)) or end / len(signal) > max_trim:
                return min_trim
            return end

    return min_trim


def trim2(signal, threshold=2.4, window_size=100):
    """
    Trims the beginning of a signal.
    First, it finds an initial "active" window where all points are above the threshold.
    Then, it continues to find subsequent "active" windows where more than half the points
    are above the threshold.
    Returns the end of the last identified "active" window.
    """
    signal_len = len(signal)
    
    # 1. First, find an initial "active" window (all points > threshold)
    initial_active_start = -1 # Marker for the start of the first active window
    
    for start in range(0, signal_len - window_size + 1, window_size):
        current_window = signal[start : start + window_size]
        if np.all(current_window > threshold):
            initial_active_start = start
            break # Found the first active window, stop searching for it
    
    if initial_active_start == -1:
        # print("Debug: No initial active window found. Returning 0.") # Optional debug
        return 0

    # 2. Once an initial active window is found, proceed with the previous logic
    # starting from the end of this initial active window.
    last_valid_end = initial_active_start + window_size # Start tracking from here
    
    # Continue iterating from where the first active window ended
    for start in range(last_valid_end, signal_len, window_size):
        end = start + window_size
        if end > signal_len:
            # If the last window is partial, we stop checking.
            break 
            
        current_window = signal[start:end]
        
        # Count points in the window greater than the threshold
        points_above_threshold = np.sum(current_window > threshold) # Using np.sum for boolean array
        
        # Check if points above threshold exceed half the window size
        if points_above_threshold > (window_size / 2):
            last_valid_end = end # This window is "active", store its end
        else:
            break
            
    return last_valid_end


def normalisation(sig, scaling_strategy=None, norm_params=None):
    """
    Calculate signal shift and scale factors for normalisation or standardisation.
    If no information is provided in the config, quantile scaling is default.
    """
    
    return med_mad(sig)

    if scaling_strategy and scaling_strategy.get("strategy") == "pa":
        #sys.stderr.write("Using picoampere scaling\n")
        if norm_params.get("standardise") == 1:
            shift = norm_params.get('mean')
            scale = norm_params.get('stdev')
        elif norm_params.get("standardise") == 0:
            shift = 0.0
            scale = 1.0
        else:
            raise ValueError("Picoampere scaling requested, but standardisation flag not provided")

    elif scaling_strategy and scaling_strategy.get("strategy") == "mad":
            shift, scale = med_mad(sig)
            
    elif scaling_strategy is None or scaling_strategy.get("strategy") == "quantile":
        if norm_params is None:
            norm_params = __default_norm_params__

        qa, qb = np.quantile(sig, [norm_params['quantile_a'], norm_params['quantile_b']])
        shift = max(10, norm_params['shift_multiplier'] * (qa + qb))
        scale = max(1.0, norm_params['scale_multiplier'] * (qb - qa))
        
    
    else:
        raise ValueError(f"Scaling strategy {scaling_strategy.get('strategy')} not supported; choose quantile or pa.")
    return shift, scale


def med_mad(x, factor=1.4826):
    med = np.median(x)
    mad = np.median(np.absolute(x - med)) * factor
    return med, mad