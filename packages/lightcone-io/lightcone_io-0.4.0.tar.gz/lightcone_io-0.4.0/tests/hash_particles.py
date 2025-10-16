#!/bin/env python

import hashlib
import h5py
import numpy as np
import glob
import sys

reported=False

from mpi4py import MPI
comm_rank = MPI.COMM_WORLD.Get_rank()

def read_particle_file(fname, ptype):
    """
    Generator which returns particle data in chunks
    in the form of a numpy record array.
    """
    block_size = 10000000

    f = h5py.File(fname, "r")
    group  = f[ptype]

    # Reordering a dataset with the scale-offset filter changes the values,
    # so exclude these
    #names = []
    #excluded = []
    #for name in f[ptype]:
    #    if hasattr(f[ptype][name], "dtype"):
    #        if f[ptype][name].scaleoffset is None:
    #            names.append(name)
    #        else:
    #            excluded.append(name)

    # Use all datasets
    names = []
    excluded = []
    for name in f[ptype]:
      if hasattr(f[ptype][name], "dtype"):
          names.append(name)

    global reported
    if not(reported) and comm_rank==1:
        print("Datasets used : ", names)
        print("Datasets excluded : ", excluded)
    reported = False

    dtypes = [group[name].dtype for name in names]
    shapes = [group[name].shape[1:] for name in names]
    dtype = [(name, dtype, shape) for (name, dtype, shape) in zip(names, dtypes, shapes)]

    ntot = group[names[0]].shape[0]
    i1 = 0
    while True:
        i2 = i1 + block_size
        if i2 > ntot:
            i2 = ntot
        nread = i2 - i1
        if nread > 0:
            data = np.ndarray(nread, dtype=dtype)
            for name in names:
                data[name] = group[name][i1:i2,...]
            yield data
            i1 = i2
        else:
            break

    f.close()


def hash_particle_file(fname, ptype):
    """
    Hash each particle in the file and bitwise xor the
    hashes together. This results in a hash which is
    not dependent of the ordering of the particles.
    """
    
    from mpi4py import MPI
    comm_rank = MPI.COMM_WORLD.Get_rank()
    print("Rank %d hashing file: %s" % (comm_rank, fname))

    # Set initial hash to zero (xor with zero is just assignment)
    hash_xor = bytearray(hashlib.sha256().digest_size)

    # Loop over particles in the file
    file_data = read_particle_file(fname, ptype)
    for chunk in file_data:
        for particle in chunk:

            # Hash this particle
            part_hash = bytearray(hashlib.sha256(particle).digest())

            # xor this particle's hash with current hash
            hash_xor = np.bitwise_xor(hash_xor, part_hash)

    return hash_xor


if __name__ == "__main__":

    from mpi4py import MPI
    from mpi4py.futures import MPICommExecutor
    
    comm = MPI.COMM_WORLD
    comm_rank = comm.Get_rank()
    comm_size = comm.Get_size()

    # Get command line args
    args = {}
    if comm_rank == 0:
        args["basedir"]  = sys.argv[1]
        args["basename"] = sys.argv[2]
        args["ptype"]    = sys.argv[3]
    args = comm.bcast(args)

    # Make the full list of files to hash
    if comm_rank == 0:
        index_filename = "%s/%s_index.hdf5" % (args["basedir"], args["basename"])
        with h5py.File(index_filename, "r") as infile:
            nr_mpi_ranks = int(infile["Lightcone"].attrs["nr_mpi_ranks"])
            final_particle_file_on_rank = infile["Lightcone"].attrs["final_particle_file_on_rank"]
        filenames = []
        for rank_nr in range(nr_mpi_ranks):
            for file_nr in range(final_particle_file_on_rank[rank_nr]+1):
                filename = "%s/%s_particles/%s_%04d.%d.hdf5" % (args["basedir"],
                                                                args["basename"],
                                                                args["basename"],
                                                                file_nr, rank_nr,)
                filenames.append(filename)
    else:
        filenames = None
    filenames = comm.bcast(filenames)

    with MPICommExecutor(MPI.COMM_WORLD, root=0) as executor:
        if executor is not None:

            # Hash the files
            hashes = executor.map(hash_particle_file, filenames, (args["ptype"],)*len(filenames))

            # Combine hashes from files
            hash_xor = bytearray(hashlib.sha256().digest_size)
            for file_hash in hashes:
                hash_xor = np.bitwise_xor(hash_xor, file_hash)

            print("Hash: ", hash_xor.tobytes().hex())
