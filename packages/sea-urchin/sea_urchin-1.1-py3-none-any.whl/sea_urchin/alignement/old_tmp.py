#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 13 18:39:03 2024

@author: roncofaber
"""

# perform a chain alignment of a list of structures by creating a random
# linkage (biased according to their RMSD) and trying to minimize the total
# distances
def optimal_alignment(structures, nmax, alignment):

    # update alignment parameters from default dict
    alipar = copy.deepcopy(default_parameters["alignment"])
    alipar.update(alignment)

    # check alignment type
    # check_alignment_type(alipar["type"])

    # calculate distance matrix
    dist_mat = met.get_all_distances_matrix(structures, alipar)

    old_dist = np.inf
    for ii in range(nmax):

        to_move = np.random.randint(0, len(structures))

        new_structures, new_dist = align_representatives(
            structures, dist_mat, alipar, to_move=to_move, hard_link=not ii)


        if new_dist < old_dist:# or random.uniform(0, 1) < np.exp(-(new_dist-old_dist)/0.001):

            structures = new_structures
            old_dist   = new_dist
            print(UP, end=CLEAR)
            print("{:4}|{:3}: ".format(ii, to_move) + Fore.GREEN +
                  "{:5.6f}".format(new_dist) + Style.RESET_ALL, end="\r")
            print("")

        else:
            print(UP, end=CLEAR)
            print("{:4}|{:3}: ".format(ii, to_move) + Fore.RED +
                  "{:5.6f}".format(new_dist) + Style.RESET_ALL, end="\r")

    return new_structures

# align all structures to mean structure, update mean structure and redo
# everything until the mean structure converges
def align_to_mean_structure(structures, alignment, start_structure=None,
                            nmax=30, conv=1e-5):

    # update alignment parameters from default dict
    alipar = copy.deepcopy(default_parameters["alignment"])
    alipar.update(alignment)

    # check alignment type
    # check_alignment_type(alipar["type"])

    # start from mean structure
    if start_structure is None:
        mean_structure = structures[0].copy()
        mean_structure.set_positions(np.mean([cc.get_positions() for cc in structures], axis=0))
    else:
        mean_structure = start_structure.copy()

    # change conv according to atom types
    conv = conv*np.sum(met.get_distances([structures[0]]))

    mean_structures = [mean_structure]
    new_structures = [clu.copy() for clu in structures]

    for ii in range(nmax):

        new_structures, __ = align_clusters_to_references_parallel(
            new_structures, [mean_structure], alipar)

        new_mean_structure = structures[0].copy()

        new_mean_structure.set_positions(
            np.mean([cc.get_positions() for cc in new_structures], axis=0))

        rmsd = met.rmsd_calculator(mean_structure, new_mean_structure)

        mean_structure = new_mean_structure.copy()
        mean_structures.append(mean_structure)

        if  rmsd < conv:

            print(UP, end=CLEAR)
            print("{:4}| ".format(ii) + Fore.GREEN +
                  "{:5.6e}".format(rmsd) + Style.RESET_ALL, end="\r")
            print("")

            break

        print(UP, end=CLEAR)
        print("{:4}| ".format(ii) + Fore.RED +
              "{:5.6e}".format(rmsd) + Style.RESET_ALL, end="\r")

    return new_structures, mean_structures


def align_representatives(representatives, dist_mat0, alipar,
                          to_move=0, hard_link=False):

    # define common variables
    permute = alipar["permute"]
    invert  = alipar["inversion"]

    # generate permutations
    permlist = per.get_permutation_list(representatives[0], permute)

    new_representatives = [rep.copy() for rep in representatives]
    nrep = len(representatives)

    linkage, __ = aux.make_linkage(dist_mat0, to_move=to_move, hard_link=hard_link)

    new_dist = 0
    for link in linkage:

        to_move_idx = link[1]
        target_idx  = link[0]

        if alipar["type"] == "fastoverlap":

            scale  = alipar["fo_scale"]  # Set this to be ~ half interatomic separation
            maxl   = alipar["fo_maxl"]   # Max degree of spherical harmonic

            fastdist = ari.run_fastoverlap(
                new_representatives[target_idx],
                new_representatives[to_move_idx], scale, maxl, invert, permlist)

        elif alipar["type"] == "bnb":

            niter    = alipar["bnb_niter"]

            fastdist = ari.run_bnb(new_representatives[target_idx],
             new_representatives[to_move_idx], permlist, invert, niter)

        elif alipar["type"] == "molalign":

            tolerance    = alipar["ma_tol"]
            biasing      = alipar["ma_biasing"]
            iteration    = alipar["ma_iteration"]
            massweighted = alipar["ma_massweigh"]
            bonding      = alipar["ma_bonding"]

            fastdist = ari.run_molalign(new_representatives[target_idx],
             new_representatives[to_move_idx], biasing, iteration,
             massweighted, bonding, tolerance)

        else:
            raise RuntimeError("{} is not a properly implemented\
                               implemented method".format(alipar["type"]))

        new_representatives[to_move_idx].set_positions(fastdist[2])
        new_dist += met.rmsd_calculator(new_representatives[to_move],
                                        new_representatives[target_idx])
    # calculate new distances #TODO: can be improved?
    # new_dist_mat = met.get_simple_distance_matrix(new_representatives, parallel=True)
    # new_dist = np.linalg.norm(np.triu(new_dist_mat, k=1))/((nrep*(nrep - 1))/2)

    return new_representatives, new_dist/len(new_representatives)


#Obtain distance matrix for a list of same-composition clusters using fastoverlap
def compute_distance_distance_matrix(clusters, alignment):

    # update alignment parameters from default dict
    alipar = copy.deepcopy(default_parameters["alignment"])
    alipar.update(alignment)

    # check alignment type
    # check_alignment_type(alipar["type"])

    # initialize distance matrix and other variables
    distances = np.zeros([len(clusters), len(clusters)])
    permute   = alipar["permute"]
    invert    = alipar["inversion"]

    # generate permutations
    permlist = per.get_permutation_list(clusters[0], permute)

    # get indices for computing distances
    indices = np.triu_indices_from(distances, k=1)

    # calculate numbers of cores
    num_cores = aux.optimal_n_jobs(len(indices[0]), full=True)

    if alipar["type"] == "fastoverlap":

        scale  = alipar["fo_scale"]  # Set this to be ~ half interatomic separation
        maxl   = alipar["fo_maxl"]   # Max degree of spherical harmonic

        with Parallel(n_jobs=num_cores, backend="loky") as PAR:
            dist, __, __, __, __, __ = zip(*PAR(delayed(ari.run_fastoverlap)(
                clusters[i0], clusters[i1], scale, maxl, invert, permlist)
                for i0, i1 in zip(*indices)))

    elif alipar["type"] == "bnb":

        niter    = alipar["bnb_niter"]

        with Parallel(n_jobs=num_cores, backend="loky", batch_size=1) as PAR:
            dist, __, __, __ = zip(*PAR(delayed(ari.run_bnb)
                                    (clusters[i0], clusters[i1], permlist,
                                     invert, niter) for i0, i1 in zip(*indices)))

    elif alipar["type"] == "molalign":

        tolerance    = alipar["ma_tol"]
        biasing      = alipar["ma_biasing"]
        iteration    = alipar["ma_iteration"]
        massweighted = alipar["ma_massweigh"]
        bonding      = alipar["ma_bonding"]

        with Parallel(n_jobs=num_cores, backend="loky") as PAR:
            dist, __, __ = zip(*PAR(delayed(ari.run_molalign)
                                  (clusters[i0], clusters[i1], biasing,
                                   iteration, massweighted, bonding, tolerance)
                                  for i0, i1 in zip(*indices)))

    else:
        raise RuntimeError("{} is not a properly implemented\
                           implemented method".format(alignment))

    # rearrange computed distances into a matrix
    distances[indices] = dist
    distances += distances.T

    return distances

def align_cluster(reference, cluster, alignment):

    alipar = copy.deepcopy(default_parameters["alignment"])
    alipar.update(alignment)

    permute   = alipar["permute"]
    invert    = alipar["inversion"]
    permlist  = per.get_permutation_list(cluster, permute)
    scale     = alipar["fo_scale"]  # Set this to be ~ half interatomic separation
    maxl      = alipar["fo_maxl"]   # Max degree of spherical harmonic

    fastdist = ari.run_fastoverlap(reference, cluster, scale, maxl, invert, permlist)

    new_cluster = cluster.copy()
    new_cluster.set_positions(fastdist[2])

    return new_cluster


def align_labeled_clusters(references, clusters, labels, alignment):

    # update alignment parameters from default dict
    alipar = copy.deepcopy(default_parameters["alignment"])
    alipar.update(alignment)

    # select number of cores
    num_cores = aux.optimal_n_jobs(len(clusters), full=True)

    # define common variables
    permute = alipar["permute"]
    invert  = alipar["inversion"]

    # generate permutation
    permlist = per.get_permutation_list(clusters[0], permute)

    # check_alignment_type(alipar["type"])
    if alipar["type"] == "fastoverlap":

        scale  = alipar["fo_scale"]  # Set this to be ~ half interatomic separation
        maxl   = alipar["fo_maxl"]   # Max degree of spherical harmonic

        with Parallel(n_jobs=num_cores, backend="loky") as PAR:
            fastdists = PAR(delayed(ari.run_fastoverlap)
                                    (references[labels[cc]], cluster, scale,
                                     maxl, invert, permlist)
                                    for cc, cluster in enumerate(clusters))

    elif alipar["type"] == "bnb":

        niter    = alipar["bnb_niter"]

        with Parallel(n_jobs=num_cores, backend="loky", batch_size=1) as PAR:
            fastdists = PAR(delayed(ari.run_bnb)
                                    (references[labels[cc]], cluster, permlist,
                                     invert, niter)
                                    for cc, cluster in enumerate(clusters))

    elif alipar["type"] == "molalign":

        tolerance    = alipar["ma_tol"]
        biasing      = alipar["ma_biasing"]
        iteration    = alipar["ma_iteration"]
        massweighted = alipar["ma_massweigh"]
        bonding      = alipar["ma_bonding"]

        with Parallel(n_jobs=num_cores, backend="loky") as PAR:
            fastdists = PAR(delayed(ari.run_molalign)
                             (references[labels[cc]], cluster, biasing,
                              iteration, massweighted, bonding, tolerance)
                             for cc, cluster in enumerate(clusters))

    else:
        raise RuntimeError("{} is not a properly\
                           implemented method".format(alignment))


    # improve alignment and select clusters
    with Parallel(n_jobs=num_cores, backend="loky") as PAR:
        aligned_clusters = PAR(delayed(set_new_pos)
                                (clusters[cc], fastdists[cc][2])
                                for cc, idx in enumerate(labels))

    return aligned_clusters

def align_clusters_to_references_parallel(clusters, references, alignment):

    # update alignment parameters from default dict
    alipar = copy.deepcopy(default_parameters["alignment"])
    alipar.update(alignment)

    # generate data to be iterated
    data = itertools.product(clusters, references)

    # select number of cores
    num_cores = aux.optimal_n_jobs(len(clusters)*len(references), full=True)

    permute = alipar["permute"]
    invert  = alipar["inversion"]

    # generate permutation list
    permlist = per.get_permutation_list(clusters[0], permute)
    
    # initialize variable
    rot = None
    
    # choose alignment routine
    # check_alignment_type(alipar["type"])
    if alipar["type"] == "fastoverlap":

        scale  = alipar["fo_scale"]  # Set this to be ~ half interatomic separation
        maxl   = alipar["fo_maxl"]   # Max degree of spherical harmonic

        with Parallel(n_jobs=num_cores, backend="loky") as PAR:
            dist, __, npos, rot, P, inv = zip(*PAR(delayed(ari.run_fastoverlap)
                                    (reference, cluster, scale, maxl,
                                     invert, permlist)
                                    for cluster, reference in data))

    elif alipar["type"] == "bnb":

        niter    = alipar["bnb_niter"]

        with Parallel(n_jobs=num_cores, backend="loky", batch_size=1) as PAR:
            dist, __, npos, __ = zip(*PAR(delayed(ari.run_bnb)
                                    (reference, cluster, permlist, invert, niter)
                                    for cluster, reference in data))

    elif alipar["type"] == "molalign":

        tolerance    = alipar["ma_tol"]
        biasing      = alipar["ma_biasing"]
        iteration    = alipar["ma_iteration"]
        massweighted = alipar["ma_massweigh"]
        bonding      = alipar["ma_bonding"]

        with Parallel(n_jobs=num_cores, backend="loky") as PAR:
            dist, __, npos = zip(*PAR(delayed(ari.run_molalign)
                                  (reference, cluster, biasing, iteration,
                                   massweighted, bonding, tolerance)
                                  for cluster, reference in data))

    else:
        raise RuntimeError("{} is not a properly implemented\
                           implemented method".format(alignment))

    # reshape clusters
    distances = np.reshape(dist, (len(clusters), len(references)))
    positions = np.reshape(npos, (len(clusters), len(references), -1, 3))

    # get indexes of best alignment
    indexes = np.argmin(distances, axis=1)

    # improve alignment and select clusters
    with Parallel(n_jobs=num_cores, backend="loky") as PAR:

        aligned_clusters = PAR(delayed(set_new_pos)
                                (clusters[cc], positions[cc][idx])
                                for cc, idx in enumerate(indexes))

    if not min_distances:
        distances = met.get_simple_distances(references, aligned_clusters)
        
    if return_rot:
        
        if rot is None:
            return aligned_clusters, distances, None
        
        rot = np.reshape(rot, (len(clusters), len(references), 3, 3))
        
        rotations = []
        
        for cc, idx in enumerate(indexes):
            rotations.append(rot[cc][idx])
            
        return aligned_clusters, distances, rotations
    
    return aligned_clusters, distances