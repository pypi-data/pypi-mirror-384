import collections, copy
import numpy as np
from HDF5DataModel.Model.attrsclasses import DatasetAttrs, AcquisitionAtrrs, AcqSigAttrs, GenSigAttrs, AcqTraceAttrs
from datetime import datetime
from pyseg2.rawseg2 import write_raw_seg2, read_raw_seg2


class Dataset:
    def __init__(self, name='default', parent: "H5DataModel"=None):
        self.name = name
        self.attrs = DatasetAttrs()
        self.acquisitions = collections.OrderedDict()
        self.parent = parent  # the parent H5DataModel of this dataset

    def add_acquisition(self, name):
        self.acquisitions[name] = Acquisition()
        return self.acquisitions[name]

    def to_hdf5_file(self, h5file):
        """Save the experiment to a HDF5 file"""
        # Si le groupe existe déjà, on le récupère, sinon on le crée
        dataset_group = h5file.create_group(self.name)
        dataset_group.attrs.update(self.attrs.__dict__)
        for acq_name, acquisition in self.acquisitions.items():
            acquisition_group = dataset_group.create_group(acq_name)
            acquisition_group.attrs.update(acquisition.attrs.__dict__)
            for sig_name, acq_sig in acquisition.acq_sigs.items():
                acq_sig_group = acquisition_group.create_group(sig_name)
                acq_sig_group.attrs.update(acq_sig.attrs.__dict__)
                for trace_name in acq_sig.traces:
                    trace = acq_sig.traces[trace_name]
                    trace_group = acq_sig_group.create_group(trace_name)
                    trace_group.attrs.update(trace.attrs.__dict__)
                    trace_group.create_dataset('signal', data=trace.data)
            for gen_name, gen_sig in acquisition.gen_sigs.items():
                gen_sig_group = acquisition_group.create_group(gen_name)
                gen_sig_group.attrs.update(gen_sig.attrs.__dict__)
                if gen_sig.signal is not None:
                    gen_sig_group.create_dataset('signal', data=gen_sig.signal)

    def to_existing_hdf5_file(self, h5file):
        """Save the experiment to a HDF5 file"""
        if self.name in h5file:
            dataset_group = h5file[self.name]
        else:
            dataset_group = h5file.create_group(self.name)
        dataset_group.attrs.update(self.attrs.__dict__)

        # Suppression des acquisitions absentes
        for acq_name in list(dataset_group.keys()):
            if acq_name not in self.acquisitions:
                del dataset_group[acq_name]

        for acq_name, acquisition in self.acquisitions.items():
            if acq_name in dataset_group:
                acquisition_group = dataset_group[acq_name]
            else:
                acquisition_group = dataset_group.create_group(acq_name)
            acquisition_group.attrs.update(acquisition.attrs.__dict__)

            acq_sig_names = set(acquisition.acq_sigs.keys())
            gen_sig_names = set(acquisition.gen_sigs.keys())
            for sig_name in list(acquisition_group.keys()):
                if sig_name not in acq_sig_names and sig_name not in gen_sig_names:
                    del acquisition_group[sig_name]

            # AcqSigs
            for sig_name, acq_sig in acquisition.acq_sigs.items():
                if sig_name in acquisition_group:
                    acq_sig_group = acquisition_group[sig_name]
                else:
                    acq_sig_group = acquisition_group.create_group(sig_name)
                acq_sig_group.attrs.update(acq_sig.attrs.__dict__)
                for trace_name in acq_sig.traces:
                    trace = acq_sig.traces[trace_name]
                    if trace_name in acq_sig_group:
                        trace_group = acq_sig_group[trace_name]
                    else:
                        trace_group = acq_sig_group.create_group(trace_name)
                    trace_group.attrs.update(trace.attrs.__dict__)
                    # N'écrase le dataset que si trace._data est en mémoire
                    if trace._data is not None:
                        if 'signal' in trace_group:
                            del trace_group['signal']
                        trace_group.create_dataset('signal', data=trace._data)

            # GenSigs
            for gen_name, gen_sig in acquisition.gen_sigs.items():
                if gen_name in acquisition_group:
                    gen_sig_group = acquisition_group[gen_name]
                else:
                    gen_sig_group = acquisition_group.create_group(gen_name)
                gen_sig_group.attrs.update(gen_sig.attrs.__dict__)
                if gen_sig.signal is not None:
                    if 'signal' in gen_sig_group:
                        del gen_sig_group['signal']
                    gen_sig_group.create_dataset('signal', data=gen_sig.signal)

    def from_h5(self, h5file, experiment_name):
        """Load the experiment from a HDF5 file"""
        self.name = experiment_name
        dataset_group = h5file[experiment_name]
        self.attrs = DatasetAttrs()
        self.attrs.set_attrs_from_dict(dict(dataset_group.attrs))
        for acq_name in dataset_group:
            acquisition_group = dataset_group[acq_name]
            self.add_acquisition(acq_name)
            self.acquisitions[acq_name].attrs = AcquisitionAtrrs()
            self.acquisitions[acq_name].attrs.set_attrs_from_dict(dict(acquisition_group.attrs))
            for sig_name in acquisition_group:
                if acquisition_group[sig_name].attrs['type'] == 'Acquisition attributes':
                    self.acquisitions[acq_name].add_acq_sig(sig_name)
                    acq_sig_group = acquisition_group[sig_name]
                    # trace_order = acq_sig_group.attrs.pop('trace_order', list(acq_sig_group.keys()))
                    trace_names = list(acq_sig_group.keys())
                    trace_names_sorted = sorted(trace_names, key=lambda name: acq_sig_group[name].attrs.get('index', 0))
                    self.acquisitions[acq_name].acq_sigs[sig_name].attrs = AcqSigAttrs()
                    self.acquisitions[acq_name].acq_sigs[sig_name].attrs.set_attrs_from_dict(dict(acq_sig_group.attrs))
                    for trace_name in trace_names_sorted:
                        trace_group = acq_sig_group[trace_name]
                        self.acquisitions[acq_name].acq_sigs[sig_name].add_trace(trace_name)
                        self.acquisitions[acq_name].acq_sigs[sig_name].traces[trace_name].attrs = AcqTraceAttrs()
                        self.acquisitions[acq_name].acq_sigs[sig_name].traces[trace_name].attrs.set_attrs_from_dict(dict(trace_group.attrs))
                        self.acquisitions[acq_name].acq_sigs[sig_name].traces[trace_name]._h5signal = trace_group['signal']
                        self.acquisitions[acq_name].acq_sigs[sig_name].traces[trace_name]._data = None
                elif acquisition_group[sig_name].attrs['type'] == 'Generation attributes':
                    self.acquisitions[acq_name].add_gen_sig(sig_name)
                    gen_sig_group = acquisition_group[sig_name]
                    self.acquisitions[acq_name].gen_sigs[sig_name].attrs = GenSigAttrs()
                    self.acquisitions[acq_name].gen_sigs[sig_name].attrs.set_attrs_from_dict(dict(gen_sig_group.attrs))
                    self.acquisitions[acq_name].gen_sigs[sig_name].signal = np.array(gen_sig_group['signal'])


class Acquisition:
    """An acquisition is a set of one generation signal and multiple acquisition signals with the sample and config"""
    def __init__(self, parent: "Dataset"=None):
        self.attrs = AcquisitionAtrrs()
        self.acq_sigs = collections.OrderedDict()
        self.gen_sigs = collections.OrderedDict()
        self.parent = parent  # the Parent Acquisition of self

    def add_acq_sig(self, name):
        self.acq_sigs[name] = AcqSig()
        return self.acq_sigs[name]

    def add_gen_sig(self, name):
        self.gen_sigs[name] = GenSig()
        return self.gen_sigs[name]

    def from_seg2(self, filepath: str):
        """
        Read a SEG2 file and return an AcqSig object containing the data and metadata.
        The function uses the pyseg2 library to read the SEG2 file and extracts relevant
        metadata to populate the attributes of the AcqSig and its traces.

        Parameters:
        filepath (str): Path to the SEG2 file.

        Returns:
        AcqSig: An AcqSig object containing the traces and their metadata.
        """
        fileheader, trace_header_and_data = read_raw_seg2(filepath, evaluate_types=True)
        sig = AcqSig()
        sig.attrs.set_attrs_from_dict(fileheader)

        # Sécurisation de l'accès aux attributs
        acq_date = getattr(sig.attrs, 'ACQUISITION_DATE', None)
        acq_time = getattr(sig.attrs, 'ACQUISITION_TIME', None)
        if acq_date is not None and acq_time is not None:
            date_str = acq_date + acq_time
            try:
                dati = datetime.strptime(date_str, '%d/%m/%Y%H:%M:%S')
            except ValueError:
                dati = datetime.strptime(date_str, '%d/%m/%y%H:%M:%S')
            sig.attrs.start_time = dati.timestamp()
            if hasattr(sig.attrs, 'ACQUISITION_DATE'):
                delattr(sig.attrs, 'ACQUISITION_DATE')
            if hasattr(sig.attrs, 'ACQUISITION_TIME'):
                delattr(sig.attrs, 'ACQUISITION_TIME')
        sig.attrs.traces_number = len(trace_header_and_data)

        for trace_index, (trace_header, trace_data) in enumerate(trace_header_and_data):
            trace = sig.add_trace(name=f"trace{trace_index}")
            trace.data = trace_data.astype('float32')
            trace.attrs.set_attrs_from_dict(trace_header)
            trace.attrs.start_time = getattr(sig.attrs, 'start_time', None)
            trace.attrs.index = trace_index
            trace.attrs.channel = getattr(trace.attrs, 'CHANNEL_NUMBER', None)
            if hasattr(trace.attrs, 'CHANNEL_NUMBER'):
                delattr(trace.attrs, 'CHANNEL_NUMBER')
            trace.attrs.sampling_freq = 1 / float(getattr(trace.attrs, 'SAMPLE_INTERVAL', 1.0))
            if hasattr(trace.attrs, 'SAMPLE_INTERVAL'):
                delattr(trace.attrs, 'SAMPLE_INTERVAL')
            trace.attrs.pretrig_duration = float(getattr(trace.attrs, 'DELAY', 0.0))
            if hasattr(trace.attrs, 'DELAY'):
                delattr(trace.attrs, 'DELAY')
            position = [float(x) for x in getattr(trace.attrs, 'RECEIVER_LOCATION', '0 0 0').split()]
            trace.attrs.position_x = position[0]
            trace.attrs.position_y = position[1] if len(position) > 1 else 0.0
            trace.attrs.position_z = position[2] if len(position) > 2 else 0.0
            if hasattr(trace.attrs, 'RECEIVER_LOCATION'):
                delattr(trace.attrs, 'RECEIVER_LOCATION')
        self.acq_sigs['AcqSig1'] = sig
        self.attrs.start_time = getattr(sig.attrs, 'start_time', None)


class AcqSig:
    def __init__(self, parent: "Acquisition"=None):
        self.attrs = AcqSigAttrs()
        self.traces = collections.OrderedDict()
        self.parent = parent

    def add_trace(self, name):
        self.traces[name] = AcqTrace()
        return self.traces[name]

    def to_seg2(self, filename: str, allow_overwrite: bool=False, include_type_names: bool=False):
        self.attrs.ACQUISITION_DATE = datetime.fromtimestamp(self.attrs.start_time).strftime('%d/%m/%Y')
        self.attrs.ACQUISITION_TIME = datetime.fromtimestamp(self.attrs.start_time).strftime('%H:%M:%S')

        trace_header_and_data = []
        for trace in self.traces.values():
            trace: AcqTrace

            meta_dict = copy.deepcopy(trace.attrs.__dict__)
            meta_dict['SAMPLE_INTERVAL'] = 1. / trace.attrs.sampling_freq
            meta_dict['DELAY'] = trace.attrs.pretrig_duration
            meta_dict['CHANNEL_NUMBER'] = trace.attrs.channel
            meta_dict['RECEIVER_LOCATION'] = f"{trace.attrs.position_x} {trace.attrs.position_y} {trace.attrs.position_z}"

            trace_header_and_data.append((meta_dict, trace.data))

        write_raw_seg2(
            filename=filename,
            file_header=self.attrs.__dict__,
            trace_header_and_data=trace_header_and_data,
            allow_overwrite=allow_overwrite,
            include_type_names=include_type_names,
            )


class GenSig:
    def __init__(self, parent: "Acquisition"=None):
        self.attrs = GenSigAttrs()
        self.signal = np.zeros(1)
        self.parent = parent  # the parent Acquisition of self


class AcqTrace:
    def __init__(self, parent: "AcqSig"=None):
        self._data = None
        self._h5signal = None  # référence au dataset HDF5
        self.attrs = AcqTraceAttrs()
        self.parent = parent

    @property
    def data(self):
        if self._data is not None:
            return self._data
        elif self._h5signal is not None:
            # Chargement à la demande
            self._data = np.array(self._h5signal)
            return self._data
        else:
            return None

    @data.setter
    def data(self, value):
        self._data = value
        self._h5signal = None
