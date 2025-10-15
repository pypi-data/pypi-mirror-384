import warnings
from PySide6.QtCore import Signal, QObject
from h5py import File
from HDF5DataModel.Model.subclasses import Dataset


class H5DataModel(QObject):
    modelUpdated = Signal()

    def __init__(self, file_path=None):
        super().__init__()
        self.file_path = file_path
        self.fid = None
        self.datasets = {}

    def add_dataset(self, name):
        self.datasets[name] = Dataset(name)
        return self.datasets[name]

    def to_hdf5_file(self):
        if self.fid is None:
            self.to_new_hdf5_file()
        else:
            self.to_existing_hdf5_file()
        self.modelUpdated.emit()

    def to_new_hdf5_file(self):
        with File(self.file_path, 'w') as f:
            for name, dataset in self.datasets.items():
                dataset.to_hdf5_file(f)
        self.get_fid()

    def to_existing_hdf5_file(self):
        for ds_name in list(self.fid.keys()):
            if ds_name not in self.datasets:
                del self.fid[ds_name]
        for name, dataset in self.datasets.items():
            dataset.to_existing_hdf5_file(self.fid)

    def get_datasets(self):
        self.get_fid()
        for key in self.fid.keys():
            if self.fid[key].attrs['version'][:-4] == 'HDF5DataModel':
                dataset = Dataset()
                dataset.from_h5(self.fid, key)
                self.datasets[key] = dataset
            else:
                warnings.warn('version not recognized')

    def get_fid(self):
        if self.fid is None:
            self.fid = File(self.file_path, 'r+')

    def close_fid(self):
        if self.fid is not None:
            try:
                self.fid.close()
            except Exception:
                pass
            self.fid = None

    def __del__(self):
        self.close_fid()


if __name__ == '__main__':
    h5 = H5DataModel(r'C:\Users\devie\Documents\Programmes\HDF5DataModel\test.h5')
    h5.get_datasets()
