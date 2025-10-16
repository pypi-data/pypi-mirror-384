"""
modified based on Bonito fast5
"""

import sys
from glob import glob
from pathlib import Path
from itertools import chain
from functools import partial
from multiprocessing import Pool
from datetime import timedelta, timezone
from numba import jit, njit
import os
import numpy as np
import densecall.reader
from tqdm import tqdm
from dateutil import parser
from ont_fast5_api.fast5_interface import get_fast5_file


class Read(densecall.reader.Read):

    def __init__(self, read, filename, meta=False, do_trim=True, scaling_strategy=None, norm_params=None):

        self.meta = meta
        self.read_id = read.read_id
        self.filename = filename.name
        self.run_id = read.get_run_id()
        if type(self.run_id) in (bytes, np.bytes_):
            self.run_id = self.run_id.decode('ascii')

        tracking_id = read.handle[read.global_key + 'tracking_id'].attrs

        try:
            self.sample_id = tracking_id['sample_id']
        except KeyError:
            self.sample_id = 'unset'
        if type(self.sample_id) in (bytes, np.bytes_):
            self.sample_id = self.sample_id.decode()

        self.exp_start_time = tracking_id['exp_start_time']
        if type(self.exp_start_time) in (bytes, np.bytes_):
            self.exp_start_time = self.exp_start_time.decode('ascii')
        self.exp_start_time = self.exp_start_time.replace('Z', '')

        self.flow_cell_id = tracking_id['flow_cell_id']
        if type(self.flow_cell_id) in (bytes, np.bytes_):
            self.flow_cell_id = self.flow_cell_id.decode('ascii')

        self.device_id = tracking_id['device_id']
        if type(self.device_id) in (bytes, np.bytes_):
            self.device_id = self.device_id.decode('ascii')

        if self.meta:
            return

        read_attrs = read.handle[read.raw_dataset_group_name].attrs
        channel_info = read.handle[read.global_key + 'channel_id'].attrs

        self.offset = int(channel_info['offset'])
        self.sample_rate = channel_info['sampling_rate']
        self.scaling = channel_info['range'] / channel_info['digitisation']

        self.mux = read_attrs['start_mux']
        self.read_number = read_attrs['read_number']
        self.channel = channel_info['channel_number']
        if type(self.channel) in (bytes, np.bytes_):
            self.channel = self.channel.decode()

        self.start = read_attrs['start_time'] / self.sample_rate
        self.duration = read_attrs['duration'] / self.sample_rate

        exp_start_dt = parser.parse('2024-01-01' )
        start_time = exp_start_dt + timedelta(seconds=self.start)
        self.start_time = start_time.astimezone(timezone.utc).isoformat(timespec="milliseconds")

        raw = read.handle[read.raw_dataset_name][:]
        self.scaled = np.array(self.scaling * (raw + self.offset), dtype=np.float32)
        #adaptor_start, adaptor_end, _, polya_end = find_segments(self.scaled)
        self.num_samples = len(self.scaled)
        self.shift, self.scale = densecall.reader.normalisation(self.scaled, scaling_strategy, norm_params)
        
        self.trimmed_samples = densecall.reader.trim(self.scaled, threshold=self.scale * 2.4 + self.shift) if do_trim else 0
        self.template_start = self.start + (self.trimmed_samples / self.sample_rate)
        self.template_duration = self.duration - (self.trimmed_samples / self.sample_rate)
        self.signal = (self.scaled[self.trimmed_samples:] - self.shift) / self.scale
        #print(self.read_id, self.shift, self.scale, self.signal[:1000])
        #print(len(self.signal), len(self.scaled))
        #self.signal = np.clip(self.signal, -5, 5)
        #self.signal = self.signal[adaptor_start:adaptor_end] if adaptor_start != -1 else self.signal



def med_mad(x, factor=1.4826):
    med = np.median(x)
    mad = np.median(np.absolute(x - med)) * factor
    return med, mad


@njit
def find_segment(signal, min_length, max_value):
    start = -1
    s = 0

    for inx in range(len(signal)):
        i = signal[inx]
        if i < max_value:
            if start == -1:
                start = inx
            s += 1
        else:
            if s > min_length:
                return (start, inx)
            s = 0
            start = -1

    if s > min_length:
        return (start, len(signal))

    return (-1, 0)

@njit
def find_segments(signal, t1=2000, t2=100, t3=100):
    start, end = find_segment(signal, t1, t2)

    if start != -1:
        start2, end2 = find_segment(signal[end:], t3, t2)
        if start2 != -1:
            start2 += end
            end2 += end
        else:
            start2, end2 = 0, 0
    else:
        start2, end2 = 0, 0

    return start, end, start2, end2

def get_meta_data(filename, read_ids=None, skip=False):
    """
    Get the meta data from the fast5 file for a given `filename`.
    """
    meta_reads = []
    try:
        with get_fast5_file(filename, 'r') as f5_fh:
            try:
                all_read_ids = f5_fh.get_read_ids()
            except RuntimeError as e:
                sys.stderr.write(f"> warning: f{filename} - {e}\n")
                return meta_reads
            for read_id in all_read_ids:
                if read_ids is None or (read_id in read_ids) ^ skip:
                    meta_reads.append(
                        Read(f5_fh.get_read(read_id), filename, meta=True)
                    )
            return meta_reads
    except Exception as e:
        sys.stderr.write(f"> warning: f{filename} - {e}\n")
        return meta_reads

def get_read_groups(directory, model, read_ids=None, skip=False, n_proc=1, recursive=False, cancel=None):
    """
    Get all the read meta data for a given `directory`.
    """
    groups = set()
    num_reads = 0
    pattern = "**/*.fast5" if recursive else "*.fast5"
    fast5s = [Path(x) for x in glob(directory + "/" + pattern, recursive=True)]
    get_filtered_meta_data = partial(get_meta_data, read_ids=read_ids, skip=skip)

    with Pool(n_proc) as pool:
        for reads in tqdm(
                pool.imap(get_filtered_meta_data, fast5s), total=len(fast5s), leave=False,
                desc="> preprocessing reads", unit=" fast5s", ascii=True, ncols=100
        ):
            groups.update({read.readgroup(model) for read in reads})
            num_reads += len(reads)
        return groups, num_reads


def get_read_ids(filename, read_ids=None, skip=False):
    """
    Get all the read_ids from the file `filename`.
    """
    with get_fast5_file(filename, 'r') as f5_fh:
        try:
            ids = [(filename, rid) for rid in f5_fh.get_read_ids()]
        except RuntimeError as e:
            sys.stderr.write(f"> warning: f{filename} - {e}\n")
            return []
        if read_ids is None:
            return ids
        return [rid for rid in ids if (rid[1] in read_ids) ^ skip]


def get_raw_data_for_read(info, do_trim=True, scaling_strategy=None, norm_params=None):
    """
    Get the raw signal from the fast5 file for a given filename, read_id pair
    """
    filename, read_id = info
    with get_fast5_file(filename, 'r') as f5_fh:
        return Read(f5_fh.get_read(read_id), filename, do_trim=do_trim, scaling_strategy=scaling_strategy, norm_params=norm_params)


def get_raw_data(filename, read_ids=None, skip=False):
    """
    Get the raw signal and read id from the fast5 files
    """
    with get_fast5_file(filename, 'r') as f5_fh:
        for read_id in f5_fh.get_read_ids():
            if read_ids is None or (read_id in read_ids) ^ skip:
                yield Read(f5_fh.get_read(read_id), filename)


def get_reads(directory, read_ids=None, skip=False, n_proc=1, recursive=False, cancel=None, do_trim=True, scaling_strategy=None, norm_params=None):
    """
    Get all reads in a given `directory`.
    """
    # 判断 directory 是文件还是文件夹
    if os.path.isfile(directory):
        reads = [Path(directory)]
    else:
        pattern = "**/*.fast5" if recursive else "*.fast5"
        reads = [Path(x) for x in glob(directory + "/" + pattern, recursive=True)]

    get_filtered_reads = partial(get_read_ids, read_ids=read_ids, skip=skip)
    get_raw_data = partial(get_raw_data_for_read, do_trim=do_trim, scaling_strategy=scaling_strategy, norm_params=norm_params)

    # 打乱文件顺序
    poem = np.arange(len(reads))
    np.random.seed(1)
    np.random.shuffle(poem)
    reads = [reads[i] for i in poem]

    with Pool(n_proc) as pool:
        for job in chain(pool.imap(get_filtered_reads, reads)):
            for read in pool.imap(get_raw_data, job):
                yield read
                if cancel is not None and cancel.is_set():
                    return
