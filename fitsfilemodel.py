import glob
from os import path, remove, rename
import copy
from collections import deque
import csv


class PairLabelModel:

    """Implements logic for when you want to label pairs of fitsfiles"""

    def __init__(self):
        self.working_dir = None
        self.pairs = None
        self.cur_dir = None
        self.label_file = None
        self.unlabeled_pairs = None
        self.cur_msg = None
        self.prev = None
        self.buffer = []

    def set_working_dir(self, working_dir):
        self.working_dir = working_dir
        self.pairs = self._get_pairs()
        self.cur_dir = path.split(working_dir)[1]
        self.label_file = path.join(working_dir, "{}_labels.csv".format(self.cur_dir))

        if not path.isfile(self.label_file):
            with open(self.label_file, 'wb') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["pair", "label"], delimiter=',')
                writer.writeheader()
                self.unlabeled_pairs = copy.copy(self.pairs)

        else:
            self.unlabeled_pairs = copy.copy(self.pairs)
            with open(self.label_file, 'rb') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=",")
                next(csvreader, None)
                for row in csvreader:
                    self.unlabeled_pairs.pop(row[0])

    def get_pairs(self):
        return self.pairs.items()

    def get_unlabeled_pairs(self):
        return self.unlabeled_pairs.items()

    def get_next_unlabeled(self):
        if len(self.unlabeled_pairs) == 0:  # Done with labeling
            return None,  None

        return self.unlabeled_pairs.items()[0]

    def _get_pairs(self):
        pattern = '_OFF.fits'
        files = glob.glob(path.join(self.working_dir, '*.fits'))
        bag = {}
        for file in files:
            on = file[:-9] + '.fits' if file.endswith(pattern) else file
            if on not in bag:
                bag[on] = on[:-5] + pattern
        return bag

    def write_row(self, fname, label):
        self.prev = fname
        self.unlabeled_pairs.pop(fname)
        with open(self.label_file, "a") as csvfile:
            w = csv.writer(csvfile, delimiter=",")
            w.writerow([fname, label])

    def write_buffer(self, fname, label):
        self.prev = fname
        self.unlabeled_pairs.pop(fname)
        self.buffer.append([fname, label])

    def write_buffer_to_csv(self):
        with open(self.label_file, "a") as csvfile:
            for row in self.buffer:
                w = csv.writer(csvfile, delimiter=",")
                w.writerow(row)


    def undo(self):
        if not self.prev:  # No previous
            return None, None

        # have to rewrite csv if undoing a label
        with open(self.label_file, 'rb') as inp, open('new.csv', 'wb') as out:
            writer = csv.writer(out)
            for row in csv.reader(inp):
                if row[0] != self.prev:
                    writer.writerow(row)
        remove(self.label_file)
        rename('new.csv', self.label_file)

        # Return previous fits file so can plot
        tmp = self.prev
        self.prev = None
        self.unlabeled_pairs[tmp] = tmp[:-5] + "_OFF.fits"
        return tmp, tmp[:-5] + "_OFF.fits"


class SingleLabelModel:

    def __init__(self):
        self.working_dir = None
        self.cur_dir = None
        self.files = None
        self.label_file = None
        self.unlabeled_files = None
        self.cur_msg = None
        self.prev = None
        self.buffer = []

    def set_working_dir(self, working_dir):
        self.working_dir = working_dir
        self.files = deque(glob.glob(path.join(self.working_dir, '*.fits')))
        self.cur_dir = path.split(working_dir)[1]
        self.label_file = path.join(working_dir, "{}_labels.csv".format(self.cur_dir))

        if not path.isfile(self.label_file):
            with open(self.label_file, 'wb') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["pair", "label"], delimiter=',')
                writer.writeheader()
                self.unlabeled_files = copy.copy(self.files)

        else:
            self.unlabeled_files = copy.copy(self.files)
            with open(self.label_file, 'rb') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=",")
                next(csvreader, None)
                for row in csvreader:
                    self.unlabeled_files.remove(row[0])

    def get_files(self):
        return self.files

    def get_unlabeled_files(self):
        return self.unlabeled_files

    def get_next_unlabeled(self):
        if len(self.unlabeled_files) == 0:  # Done with labeling
            return None

        return list(self.unlabeled_files)[0]

    def write_row(self, fname, label):
        self.prev = fname
        self.unlabeled_files.pop(fname)
        with open(self.label_file, "a") as csvfile:
            w = csv.writer(csvfile, delimiter=",")
            w.writerow([fname, label])

    def undo(self):
        if not self.prev:  # No previous
            return None

        # have to rewrite csv if undoing a label
        with open(self.label_file, 'rb') as inp, open('new.csv', 'wb') as out:
            writer = csv.writer(out)
            for row in csv.reader(inp):
                if row[0] != self.prev:
                    writer.writerow(row)
        remove(self.label_file)
        rename('new.csv', self.label_file)

        # Return previous fits file so can plot
        tmp = self.prev
        self.prev = None
        self.unlabeled_files.leftappend(tmp)
        return tmp
