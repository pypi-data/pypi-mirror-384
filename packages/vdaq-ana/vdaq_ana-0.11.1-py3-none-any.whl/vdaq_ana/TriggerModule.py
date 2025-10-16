#!/usr/bin/env python3
"""AliVATA module data class."""
from collections import namedtuple

class TriggerModule:
    """TriggerModule data."""
    def __init__(self, modid, data_file):
        """Initialize.

        Args:
            modid: the module ID
            data_file: the hdf5 data file object.

        """
        path = "/modules/%s/data/vdaq_trigger" % modid
        self.data = data_file[path]
        path = "/modules/%s/data/time" % modid
        self.time = data_file[path]

        self.id = int(modid)

        names = ['mod_id', 'evt_time']
        names.extend([x.strip() for x in self.data.dtype.names])
        print(names)
        self.type = namedtuple("TriggerModuleData", names)


    @staticmethod
    def is_valid_module(modid, data_file):
        """Checks that the module is one of ours."""
        path = "/modules/%s/data/vdaq_trigger" % modid
        if path in data_file:
            return True
        else:
            return False

    def __iter__(self):
        """REturn the iterator."""
        return VDaqTrgModuleIterator(self)


def __dummy_cond__(*args):
    return True

class VDaqTrgModuleIterator:
    """The data iterator."""
    def __init__(self, module, start=0, stop=0xffffffffffffffff, condition=__dummy_cond__):
        """Initialization.

        args:
            module: the TriggerModule object
            condition: a boolean function that receives the module data.
                       Iteration will stop when the function returns False

        """
        self.M = module
        self.condition = condition
        self.start = start
        self.stop = stop
        self.nevts = self.M.data.shape[0]

        self.chunk_size = 20*self.M.data.chunks[0]
        self.first_chunk = -1
        self.last_chunk = -1
        self.current_chunk = -1
        self.end_of_chunk = -1

        self.indx = 0
        self.TS = None
        self.DS = None
        self.first_in_chunck = 0

        self.init_iter()

    def init_iter(self):
        """Initialize the iterator."""
        if self.indx > 0:
            return

        if self.start < 0:
            self.start = 0

        if  self.stop > self.nevts:
            self.stop = self.nevts

        self.first_chunk = int(self.start/self.chunk_size)
        self.last_chunk = int(self.stop/self.chunk_size) + 1
        self.current_chunk = self.first_chunk
        self.end_of_chunk = (self.current_chunk + 1) * self.chunk_size
        if self.end_of_chunk > self.stop:
            self.end_of_chunk = self.stop

        # offs is the beginning of the chuck
        self.first_in_chunck = int(self.current_chunk*self.chunk_size)
        self.indx = self.start

        print("Iter initialized. indx {} start {} stop {}".format(self.indx, self.start, self.stop))

    def __iter__(self):
        """Return iterator."""
        self.init_iter()
        return self

    def __next__(self):
        """Iterator next function."""
        if self.indx >= self.stop:
            print("End of iter")
            raise StopIteration

        else:
            while True:
                # index within chunck
                ii = self.indx - self.first_in_chunck

                if self.TS is None or ii % self.chunk_size == 0:
                    self.first_in_chunck = self.indx
                    if self.TS is not None:
                        self.current_chunk += 1
                        self.end_of_chunk = (self.current_chunk + 1) * self.chunk_size
                        if self.end_of_chunk > self.stop:
                            self.end_of_chunk = self.stop

                    self.TS = self.M.time[self.first_in_chunck:self.end_of_chunk]
                    self.DS = self.M.data[self.first_in_chunck:self.end_of_chunk]
                    ii = 0

                try:
                    values = [self.M.id, self.TS[ii]]
                    values.extend(self.DS[ii])
                    obj = self.M.type._make(values)

                except IndexError as exc:
                    raise StopIteration from exc

                self.indx += 1
                if self.indx >= self.stop:
                    raise StopIteration

                if self.condition(obj):
                    return obj