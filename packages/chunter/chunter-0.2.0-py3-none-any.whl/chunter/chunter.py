import random
import warnings

import anndata
import matplotlib.cm as colormaps
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import ringity as rng
import scanpy as sc
import scipy.sparse as sp
import scipy.stats as ss
import seaborn as sns
from ripser import ripser
from scipy.sparse.linalg import eigsh
from scipy.spatial import distance
from scipy.spatial.distance import cdist
from sklearn.neighbors import KernelDensity, NearestNeighbors
from tqdm import tqdm


def weighted_circular_coordinate(
    data,
    distance_matrix=False,
    ripser_result=False,
    prime=3,
    cocycle_n=None,
    eps=None,
    weight_ft: callable = None,
    return_aux=False,
):
    """
    Compute weighted circular coordinates from data using persistent cohomology.
    (Modified version from Paik et al. 2023)
    """
    if not ripser_result:
        ripser_result = ripser(data, distance_matrix=distance_matrix, coeff=prime, do_cocycles=True)
    else:
        ripser_result = data

    dist_mat = ripser_result["dperm2all"]
    n_vert = len(dist_mat)

    argsort_eps = np.argsort(np.diff(ripser_result["dgms"][1], 1)[:, 0])[::-1]
    if cocycle_n is None:
        cocycle_n = argsort_eps[0]
    else:
        cocycle_n = argsort_eps[cocycle_n]

    if eps is None:
        birth, death = ripser_result["dgms"][1][cocycle_n]
        eps = (birth + death) / 2

    # Delta
    edges = np.asarray((dist_mat <= eps).nonzero()).T
    n_edges = len(edges)
    I = np.c_[np.arange(n_edges), np.arange(n_edges)]
    I = I.flatten()
    J = edges.flatten()
    V = np.c_[-1 * np.ones(n_edges), np.ones(n_edges)]
    V = V.flatten()
    delta = sp.coo_matrix((V, (I, J)), shape=(n_edges, n_vert))

    # Cocycle
    cocycle = ripser_result["cocycles"][1][cocycle_n]
    val = cocycle[:, 2]
    val[val > (prime - 1) / 2] -= prime
    Y = sp.coo_matrix((val, (cocycle[:, 0], cocycle[:, 1])), shape=(n_vert, n_vert))
    Y = Y - Y.T
    cocycle = np.asarray(Y[edges[:, 0], edges[:, 1]])[0]

    # Minimize
    if weight_ft is None:
        mini = sp.linalg.lsqr(delta, cocycle)[0]
    else:
        new_delta, new_cocycle = weight_ft(delta, cocycle, dist_mat, edges)
        mini = sp.linalg.lsqr(new_delta, new_cocycle)[0]

    if return_aux:
        return new_delta, mini, new_cocycle, edges
    else:
        return np.mod(mini, 1.0)


def weight_ft_0(k, t=None, alpha=0.2):
    def _weight_ft(delta, cocycle, dist_mat, edges):
        nonlocal t
        if t is None:
            tmp = dist_mat[edges[:, 0], edges[:, 1]]
            t = alpha * np.mean(tmp[tmp != 0])
            print(t)
        G = np.exp(-(dist_mat**2) / (4 * t))
        G = G / ((4 * np.pi * t) ** (k / 2))
        P = np.mean(G, axis=0)
        P_inv = np.diag(1 / P)
        W = G @ P_inv
        D = np.sum(W, axis=1)
        L_w = P_inv @ (np.diag(D * P) - G) @ P_inv
        metric_weight = -L_w[edges[:, 0], edges[:, 1]]
        metric_weight = np.maximum(metric_weight, 0)  # for safety
        sqrt_weight = np.sqrt(metric_weight)

        new_delta = delta.multiply(sqrt_weight[:, None])
        new_cocycle = sqrt_weight * cocycle

        return new_delta, new_cocycle

    return _weight_ft


def phase_rotate(adata, theta):
    assert -1 <= theta <= 1, "Theta must be between -1 and 1"

    exp = np.exp(2 * np.pi * 1j * theta)  # exp(2*pi*i*theta)

    adata.var["gene_phase"] = (adata.var["gene_phase"] + 2 * np.pi * theta) % (2 * np.pi)

    # rotate the lead-lag eigenvector
    adata.varm["leadlag_pcs"][:, 0] = exp * adata.varm["leadlag_pcs"][:, 0]

    return adata


def reparametrize(adata, theta, plot=False):
    adata.obs["coords"] = (adata.obs["coords"] + theta) % 1

    if "gene_phase" in adata.var:
        # make sure theta between 0 and 1
        assert -1 <= theta <= 1, "Theta must be between -1 and 1"

        # exp(2*pi*i*theta)
        exp = np.exp(2 * np.pi * 1j * theta)

        adata.var["gene_phase"] = (adata.var["gene_phase"] + 2 * np.pi * theta) % (2 * np.pi)

        # rotate the lead-lag eigenvector
        adata.varm["leadlag_pcs"][:, 0] = exp * adata.varm["leadlag_pcs"][:, 0]

        if plot:
            phase_plot(adata, topk=10)
            plot_2d(adata, c="coords", mode="ll")

        return adata


def align(adata):
    # Compute target values
    target = np.cos(adata.obs["coords"] * 2 * np.pi).values

    # Get top genes and subset the data
    genes = get_top_genes(adata, k=20)
    subset = adata[:, genes]
    X = subset.X

    # If X is a sparse matrix, convert it to a dense array
    if hasattr(X, "toarray"):
        X = X.toarray()

    # Ensure X is at least 2D (if it's a scalar or 1D, reshape it)
    X = np.atleast_2d(X)

    # Normalize the columns of X using keepdims so the result is broadcastable
    norms = np.linalg.norm(X, axis=0, keepdims=True)
    # Avoid division by zero by setting zero norms to 1
    norms[norms == 0] = 1
    X = X / norms

    # Normalize the target vector
    target_norm = np.linalg.norm(target)
    if target_norm == 0:
        target_norm = 1
    target = target / target_norm

    # Calculate correlations between each gene (column) and target
    scores = X.T @ target

    # Find the gene with the highest correlation
    argmax = np.argmax(scores)
    starting_gene = subset.var_names[argmax]
    print("Estimated starting gene:", starting_gene)

    # Get phase correction from the gene's data
    phase_correction = subset.var["gene_phase"][starting_gene]
    print("Phase correction:", phase_correction, "rad")

    # Apply phase rotation
    phase_rotate(adata, -phase_correction / (2 * np.pi))

    return adata


def extend_coordinates(adata_main, adata_sub, key="coords", comp=0, sigma=0.2):
    """
    Extend a circle-valued function defined on a subset of cells (contained in a smaller AnnData object)
    to all cells in a main AnnData object using a heat kernel affinity computed on a lead-lag projection.

    In adata_sub, the function values are stored in adata_sub.obs[key] (assumed to be in [0,1)),
    and are scaled by 2π to convert them into radians. These values are then mapped onto adata_main
    by matching cell names. The lead-lag projection is stored in adata_main.varm['leadlag_pcs'], and
    its real and imaginary parts for component `comp` are used to create a 2D embedding.

    A Gaussian kernel (heat kernel) is computed on the 2D coordinates to determine an affinity between
    cells. For each cell in adata_main, a weighted circular mean (using the unit circle representation)
    of the known function values is computed and then normalized back to the [0, 1) range.

    Parameters:
    -----------
    adata_main : AnnData
        The main AnnData object for which you want to extend the function.
    adata_sub : AnnData
        The smaller AnnData object that contains the function values in adata_sub.obs[key].
    key : str, default 'coords'
        The key in adata_sub.obs that stores the function values (assumed to be in [0,1)).
    comp : int, default 0
        The index of the lead-lag eigenvector to use. The eigenvectors are stored as pairs:
        column 2*comp is the real part and column 2*comp+1 is the imaginary part.
    sigma : float, default 0.2
        The bandwidth parameter for the Gaussian kernel.

    Returns:
    --------
    adata_main : AnnData
        A copy of the main AnnData object with the extended function added to adata_main.obs["f_extended"].
    """
    # Create a copy of the main AnnData object
    adata_main = adata_main.copy()

    # Compute sub_coords from the subset adata: scale the 'key' values by 2π to convert [0,1) to radians.
    sub_coords = adata_sub.obs[key] * (2 * np.pi)
    # Convert the series to a dictionary (keys are cell names in adata_sub.obs_names)
    sub_coords_dict = sub_coords.to_dict()

    # For each cell in adata_main, assign the corresponding value if present, otherwise NaN.
    coords = [sub_coords_dict.get(cell, np.nan) for cell in adata_main.obs_names]
    adata_main.obs["f"] = coords  # these are the function values in radians (if defined)

    # Retrieve the lead-lag principal components from adata_main.varm.
    eigvecs = adata_main.varm["leadlag_pcs"]
    # For the chosen component, take the real and imaginary parts.
    re = eigvecs[:, 2 * comp].real
    im = eigvecs[:, 2 * comp].imag

    # Project the main data (adata_main.X) onto these components.
    proj_re = adata_main.X @ re
    proj_im = adata_main.X @ im
    # Store the 2D projection (lead-lag embedding) in adata_main.obsm.
    adata_main.obsm["X_LL"] = np.vstack((proj_re, proj_im)).T

    # Identify cells with defined function values.
    mask = ~adata_main.obs["f"].isna()
    f_known = adata_main.obs["f"].values[mask]  # angles in radians

    # Get the 2D embedding for all cells and for cells with known function values.
    X_all = adata_main.obsm["X_LL"]
    X_known = X_all[mask]

    # Compute pairwise squared Euclidean distances from every cell to each known cell.
    D2 = np.sum((X_all[:, np.newaxis, :] - X_known[np.newaxis, :, :]) ** 2, axis=2)

    # Compute the Gaussian (heat) kernel weights.
    weights = np.exp(-D2 / (2 * sigma**2))  # shape: (n_cells, n_known)

    # For circle-valued data, convert the known angles to complex numbers on the unit circle.
    weighted_complex = np.sum(weights * np.exp(1j * f_known), axis=1) / np.sum(weights, axis=1)
    f_extended = np.angle(weighted_complex)  # get the weighted circular mean (in radians)

    # Normalize the angles to the interval [0, 1)
    f_extended = (f_extended % (2 * np.pi)) / (2 * np.pi)

    # Store the extended function in the main AnnData object's .obs.
    adata_main.obs["coords"] = f_extended

    print("Extended function computed for all cells.")
    return adata_main


# Example usage:
# adata_ext = extend_circle_function_from_subadata(lum_full_andro, andro, key='coords', comp=0, sigma=0.2)


def filter_cells_by_density(adata, n_pcs=3, bandwidth=0.5, lower_percentile=10, upper_percentile=90):
    """
    Filters cells in an AnnData object based on the density of their PCA coordinates.

    Parameters:
    -----------
    adata : AnnData
        The annotated data matrix.
    n_pcs : int, optional (default: 3)
        Number of principal components to consider for density estimation.
    bandwidth : float, optional (default: 0.5)
        Bandwidth parameter for the Gaussian kernel in KDE.
    lower_percentile : float, optional (default: 10)
        Lower percentile threshold to filter out cells with the lowest density.
    upper_percentile : float, optional (default: 90)
        Upper percentile threshold to filter out cells with the highest density.

    Returns:
    --------
    AnnData
        Filtered AnnData object containing only cells within the specified density range.
    """
    # Check if PCA has been computed; if not, compute it
    if "X_pca" not in adata.obsm:
        sc.tl.pca(adata)

    # Extract the first `n_pcs` PCA coordinates
    X = adata.obsm["X_pca"][:, :n_pcs]

    # Fit a Kernel Density Estimator using a Gaussian kernel
    kde = KernelDensity(kernel="gaussian", bandwidth=bandwidth)
    kde.fit(X)

    # Evaluate the density at each data point
    log_density = kde.score_samples(X)
    density = np.exp(log_density)

    # Add density values to the AnnData object
    adata.obs["density"] = density

    # Determine the density thresholds
    lower_threshold = np.percentile(density, lower_percentile)
    upper_threshold = np.percentile(density, upper_percentile)

    # Create a boolean mask for cells with density within the specified range
    keep_idx = (density > lower_threshold) & (density < upper_threshold)

    # Filter the AnnData object to retain only cells within the specified density range
    adata_filtered = adata[keep_idx].copy()

    return adata_filtered


# a function for recentering around a harmonic
def harmonic_recenter(data, delta, mini, cocycle, edges, return_center=False):
    # calculate the barycenter of each edge
    barycenters = (data[edges[:, 0]] + data[edges[:, 1]]) / 2

    # calculate the harmonic
    harmonic = delta @ mini - cocycle

    # take the absolute value of the harmonic
    harmonic = np.abs(harmonic)

    # divide the harmonic by its norm
    harmonic = harmonic / np.sum(harmonic)

    # calculate the harmonic center
    harmonic_center = harmonic.T @ barycenters

    # subtract the harmonic center from the data
    data = data - harmonic_center

    if return_center:
        return data, harmonic_center

    else:
        return data


## effective resistence


def compute_knn_adjacency(X, num_neighbors=10):
    """
    Compute a binary symmetric k-nearest neighbor (kNN) adjacency matrix from a point cloud.

    Two points i and j are connected (i.e. A[i, j] = 1) if either j is among the
    num_neighbors nearest neighbors of i or vice versa.

    Parameters:
        X (ndarray or sparse matrix): An n x d array where each row is a point in d-dimensional space.
        num_neighbors (int): Number of nearest neighbors to include for each point.

    Returns:
        A (ndarray): An n x n binary adjacency matrix.
    """
    # Convert X to dense if it is sparse.
    if sp.issparse(X):
        X = X.toarray()

    n = X.shape[0]
    dists = cdist(X, X)  # Compute full pairwise Euclidean distances.
    A = np.zeros((n, n), dtype=int)

    # For each node, select the num_neighbors nearest neighbors (excluding itself).
    for i in range(n):
        neighbors = np.argsort(dists[i])[1 : num_neighbors + 1]
        A[i, neighbors] = 1

    # Make the graph symmetric (if either i or j is a neighbor, connect i and j).
    A = np.maximum(A, A.T)
    return A


def compute_effective_resistance_embedding(X, num_neighbors=10, k=10):
    """
    Compute the effective resistance embedding from a point cloud using a binary symmetric kNN graph.

    This function:
      1. Constructs the binary symmetric kNN adjacency matrix.
      2. Computes its degree vector and forms the symmetrically normalized Laplacian.
      3. Computes the first k+1 smallest eigenpairs (discarding the trivial eigenpair).
      4. Constructs the embedding using the scaling factors (scale = (1 - mu) / sqrt(mu)) and
         normalizing by 1/sqrt(degree).

    Parameters:
        X (ndarray or sparse matrix): An n x d point cloud.
        num_neighbors (int): Number of nearest neighbors for the kNN graph.
        k (int): Number of nontrivial eigen-components (embedding dimensions) to retain.

    Returns:
        e_eff (ndarray): An n x k effective resistance embedding. The squared Euclidean distances
                         between rows correspond to the effective resistance between points.
    """
    # Build the binary symmetric kNN adjacency matrix.
    A_dense = compute_knn_adjacency(X, num_neighbors)
    n = A_dense.shape[0]

    # Convert the dense adjacency matrix to a sparse matrix.
    A_sparse = sp.csr_matrix(A_dense)

    # Compute the degree vector: d_i = sum_j A[i,j]
    d = np.array(A_sparse.sum(axis=1)).ravel()
    d_inv_sqrt = 1.0 / np.sqrt(d)

    # Create the diagonal matrix D^(-1/2)
    D_inv_sqrt = sp.diags(d_inv_sqrt)

    # Compute the symmetrically normalized adjacency matrix: A_sym = D^(-1/2) * A * D^(-1/2)
    A_sym_sparse = D_inv_sqrt @ A_sparse @ D_inv_sqrt

    # Compute the normalized Laplacian: L_sym = I - A_sym
    L_sym_sparse = sp.identity(n) - A_sym_sparse

    # Compute the first k+1 smallest eigenpairs (k+1 because the smallest eigenpair is trivial)
    eigenvals, eigenvecs = eigsh(L_sym_sparse, k=k + 1, which="SM")

    # Sort eigenpairs in ascending order.
    idx = eigenvals.argsort()
    eigenvals = eigenvals[idx]
    eigenvecs = eigenvecs[:, idx]

    # Discard the trivial eigenpair (first eigenpair with eigenvalue close to 0).
    mu_nontriv = eigenvals[1 : k + 1]
    U_nontriv = eigenvecs[:, 1 : k + 1]

    # Compute scaling factors: scale = (1 - mu) / sqrt(mu)
    scale = (1 - mu_nontriv) / np.sqrt(mu_nontriv)

    # Construct the effective resistance embedding:
    # For each node i, its embedding is
    #   e_eff[i] = (1/sqrt(d_i)) * [scale[0]*U_nontriv[i, 0], …, scale[k-1]*U_nontriv[i, k-1]]
    e_eff = d_inv_sqrt[:, None] * (U_nontriv * scale[None, :])
    return e_eff


def effective_resistence(adata, num_neighbors=10, k=10):
    """
    Computes the effective resistance embedding from adata.X using the binary symmetric kNN graph,
    and appends it to the AnnData object as adata.obsm['X_ef'].

    Parameters:
        adata (anndata.AnnData): An AnnData object (e.g., from scRNA-seq experiments).
        num_neighbors (int): Number of nearest neighbors to use for constructing the kNN graph.
        k (int): Number of nontrivial eigen-components (embedding dimensions) to retain.

    Returns:
        None: The function modifies the AnnData object in-place.
    """
    # Compute the effective resistance embedding using adata.X as the point cloud.
    embedding = compute_effective_resistance_embedding(adata.X, num_neighbors, k)
    # Store the embedding in adata.obsm under the key 'X_ef'
    adata.obsm["X_ef"] = embedding


### --- AnnData Object Compatibility Functions --- ###


def circular(adata, comp=[0, 1], alpha=0.2, recenter=False, mode="pca"):
    if mode == "pca":
        data = adata.obsm["X_pca"][:, comp]
    elif mode == "ef":  # effective resistance
        data = adata.obsm["X_ef"][:, comp]
    else:
        raise ValueError("mode must be either 'pca' or 'ef'")

    # generate the weighted circular coordinates
    delta, mini, cocycle, edges = weighted_circular_coordinate(
        data, weight_ft=weight_ft_0(k=data.shape[1], alpha=alpha), return_aux=True
    )  # weighted circular coordinates

    # put the above into a dict
    circular = {"delta": delta, "mini": mini, "cocycle": cocycle, "edges": edges, "harm": delta @ (mini) - cocycle}

    adata.uns["circular"] = circular

    adata.uns["circular"]["delta"]

    # add circular coordinates to adata_cc_genes
    adata.obs["coords"] = mini % 1

    # add log counts to adata
    adata.obs["log_counts"] = np.log(adata.X.sum(axis=1) + 1)

    if recenter:
        # recenter circular coordinates around lowest expression cell
        low = adata.obs["log_counts"].idxmin()
        low_coord = adata[low,].obs["coords"]
        adata.obs["coords"] = (adata.obs["coords"] - low_coord.iloc[0]) % 1

    return adata


def h_recenter(adata):
    delta = adata.uns["circular"]["delta"]
    mini = adata.uns["circular"]["mini"]
    cocycle = adata.uns["circular"]["cocycle"]
    edges = adata.uns["circular"]["edges"]

    adata.layers["h_recenter"] = harmonic_recenter(adata.X, delta, mini, cocycle, edges)

    return adata


def leadlag_matrix(X, edges, harm):
    # get the P and Q matrices, start and end points of the edges
    P = X[edges[:, 0], :]
    Q = X[edges[:, 1], :]

    # stack the P and Q matrices
    PQ = np.stack([P, Q])

    # permute dimensions of PQ
    PQ = np.transpose(PQ, (1, 2, 0))

    # calculate det of PQ[:,[i,j],:] FOR ALL i<j without using for loop
    ll = np.zeros((X.shape[1], X.shape[1]))
    for i in tqdm(range(X.shape[1])):
        for j in range(i + 1, X.shape[1]):
            ll[i, j] = 0.5 * np.linalg.det(PQ[:, [i, j], :]).T @ harm
            ll[j, i] = -ll[i, j]

    return ll


def leadlag(adata, alignment=True):
    # Recentering the Data
    print("Harmonic Recentering")
    adata = h_recenter(adata)

    X = adata.layers["h_recenter"]
    edges = adata.uns["circular"]["edges"]
    harm = adata.uns["circular"]["harm"]

    print("Calculating Leadlag Matrix")
    adata.uns["leadlag"] = leadlag_matrix(X, edges, harm)

    print("Calculating Spectral Information")
    # compute the eigenvalues and eigenvectors of the integrals
    eigvals, eigvecs = np.linalg.eig(adata.uns["leadlag"])
    adata.varm["leadlag_pcs"] = eigvecs
    adata.uns["leadlag_eigvals"] = eigvals
    adata.var["gene_phase"] = np.angle(eigvecs[:, 0]) % (2 * np.pi)
    adata.var["gene_amp"] = np.abs(eigvecs[:, 0])

    if alignment:
        print("Aligning Data")
        # align the data to the first gene
        adata = align(adata)

    return adata


def reverse(adata):
    adata.uns["circular"]["harm"] = -adata.uns["circular"]["harm"]
    adata.obs["coords"] = -adata.obs["coords"] % 1

    if "gene_phase" in adata.var:
        phases = np.exp(1j * adata.var["gene_phase"])
        phases = np.conjugate(phases)
        adata.var["gene_phase"] = np.angle(phases) % (2 * np.pi)
        adata.varm["leadlag_pcs"] = adata.varm["leadlag_pcs"].conj()

        phase_plot(adata, topk=10)
        plot_2d(adata, c="coords", mode="ll")

    return adata


# takes an adata object and returns the top k genes by gene_amp sorted by gene_phase
def get_top_genes(adata, k=10):
    gene_amps = adata.var["gene_amp"]

    # find top 10 genes by gene_amp
    top_genes = gene_amps.sort_values(ascending=False).index[:k]

    top_genes = list(top_genes)

    gene_phases = adata.var["gene_phase"] % (2 * np.pi)

    # sort top_genes by their phase
    top_genes = sorted(top_genes, key=lambda x: gene_phases[x])

    return top_genes


# fit a lead-lag plane to new data
def fit_leadlag_plane(
    adata_sub: anndata.AnnData, adata_full: anndata.AnnData, vertical_layer: str = None, leadlag_layer: str = None
) -> anndata.AnnData:
    """
    Fits a simple linear model (with real and imaginary parts) to each gene in `adata_full`
    using the first lead-lag principal component from `adata_sub`.

    Args:
        adata_sub: An AnnData subset that already contains the first lead-lag PC in .varm['leadlag_pcs'].
        adata_full: The full AnnData object to be modeled and expanded.
        vertical_layer: (Optional) Name of the layer in `adata_full` to fit. If None, uses `adata_full.X`.
        leadlag_layer: (Optional) Name of the layer in `adata_full` from which the lead-lag PC projection is computed.
                       If None, uses `adata_full.X`.

    Returns:
        A copy of `adata_full` (`expansion`) with various regression metrics and fits saved to .var.
        Also updates .varm['leadlag_pcs'] with the normalized real + imaginary coefficients.
    """

    # Select the data for projection onto the lead-lag PC
    if leadlag_layer is not None:
        X_data = adata_full[:, adata_sub.var_names].layers[leadlag_layer]
    else:
        X_data = adata_full[:, adata_sub.var_names].X

    # Retrieve the first leadlag PC from adata_sub and normalize it
    pcs = adata_sub.varm["leadlag_pcs"][:, 0]
    pcs = pcs / np.linalg.norm(pcs)

    # Project full data onto the first leadlag PC
    proj = np.dot(X_data, pcs)
    real = np.real(proj)
    imag = np.imag(proj)

    # Make a copy of the full adata for storing results
    expansion = adata_full.copy()

    # Select the target data (the values to be fitted)
    if vertical_layer is not None:
        targets = expansion.layers[vertical_layer]
    else:
        targets = expansion.X

    # Step 1: Create design matrix (1, real, imag)
    X = np.column_stack((np.ones_like(real), real, imag))  # shape: (n_cells, 3)

    # Step 2: Compute the Moore-Penrose pseudoinverse of X
    X_pinv = np.linalg.pinv(X)  # shape: (3, n_cells)

    # Step 3: Estimate coefficients for all target variables at once
    # Resulting shape: (3, n_genes)
    coefficients = X_pinv @ targets

    # Step 4: Compute predictions
    # Shape: (n_cells, n_genes)
    predictions = X @ coefficients

    # Step 5: Compute residuals
    residuals = targets - predictions

    # Step 6: Compute sum of squared residuals (losses) for each gene
    losses = np.sum(residuals**2, axis=0)

    # Step 7: Compute total variance for each target gene
    target_means = np.mean(targets, axis=0)
    total_variance = np.sum((targets - target_means) ** 2, axis=0)

    # Step 8: Compute R^2 for each target
    r_squared = 1 - (losses / total_variance)

    # Step 9: Record R^2 and other fits in the AnnData object
    expansion.var["r_squared"] = r_squared
    expansion.var["r"] = np.sqrt(r_squared)

    expansion.var["real_fit"] = coefficients[1]
    expansion.var["imag_fit"] = coefficients[2]
    expansion.var["const_fit"] = coefficients[0]
    expansion.var["radius_fit"] = coefficients[1] ** 2 + coefficients[2] ** 2
    expansion.var["complex_fit"] = coefficients[1] + 1j * coefficients[2]
    expansion.var["loss"] = losses

    # Compute amplitude and phase of each gene
    expansion.var["gene_amp"] = np.sqrt(expansion.var["real_fit"] ** 2 + expansion.var["imag_fit"] ** 2)
    expansion.var["gene_phase"] = np.arctan2(expansion.var["imag_fit"], expansion.var["real_fit"])
    expansion.var["gene_phase"] = expansion.var["gene_phase"] % (2 * np.pi)

    # Normalize the real and imaginary coefficient vectors
    # (Note: This normalizes across genes, so ensure it matches your intention.)
    coefficients[1] = coefficients[1] / np.linalg.norm(coefficients[1])
    coefficients[2] = coefficients[2] / np.linalg.norm(coefficients[2])

    # Store normalized lead-lag PC in varm
    # Here we combine real+imag parts into one complex vector, and expand dims to (n_genes, 1)
    expansion.varm["leadlag_pcs"] = coefficients[1] + 1j * coefficients[2]
    expansion.varm["leadlag_pcs"] = np.expand_dims(expansion.varm["leadlag_pcs"], axis=1)

    # Optional check of shape
    _ = expansion.varm["leadlag_pcs"].shape  # just for confirmation/debugging

    return expansion


##### ADATA PLOTTING FUNCTIONS #####


def phase_plot(adata, genes=None, scale=1, topk=10, color=None, size=None):
    if genes is not None:
        subset = adata.copy()[:, genes]
    else:
        subset = adata.copy()

    # sort subset by gene_amp
    subset = subset[:, subset.var["gene_amp"].sort_values(ascending=False).index]

    phases = subset.var["gene_phase"]
    amps = subset.var["gene_amp"] / (1.5 * subset.var["gene_amp"].max())

    exp = np.exp(1j * phases) * amps

    labels = subset.var_names

    # plot some labelled level sets of the function x^2 + y^2
    x = np.linspace(-1, 1, 100)
    y = np.linspace(-1, 1, 100)
    X, Y = np.meshgrid(x, y)
    Z = X**2 + Y**2

    # plot the level sets with a low opacity and a labelling
    plt.contour(X, Y, Z, levels=np.linspace(0, 1, 10) ** 2, alpha=0.2, colors="black")

    # do the

    # make the plot square
    plt.gca().set_aspect("equal", adjustable="box")

    # make lines radiating from the origin with a label of their angle
    for i in range(0, 360, 30):
        plt.plot([0, np.cos(i * np.pi / 180)], [0, np.sin(i * np.pi / 180)], "k", alpha=0.2)
        plt.text(1.15 * np.cos(i * np.pi / 180), 1.05 * np.sin(i * np.pi / 180), str(i) + str("°"))

    # plot a black boundary around the circle
    plt.plot(np.cos(np.linspace(0, 2 * np.pi, 100)), np.sin(np.linspace(0, 2 * np.pi, 100)), "k")

    if color is not None:
        # check the type of elements in subset.var[color]
        if isinstance(subset.var[color][0], str):
            print("O")
            for t in subset.var[color].unique():
                # find indices of genes in group t
                indices = subset.var[subset.var[color] == t].index

                plt.scatter(
                    exp[indices].values.real,
                    exp[indices].values.imag,
                    s=amps[indices] * 200,
                    edgecolors="black",
                    alpha=1,
                    label=t,
                )
        else:
            plt.scatter(
                exp.values.real, exp.values.imag, s=amps * 200, c=subset.var[color], edgecolors="black", alpha=1
            )

    else:
        # plot the entries of eigenvector 0 on the complex plane with size the modulus of the entry
        plt.scatter(
            exp.values.real,
            exp.values.imag,
            s=amps * 200,
            c=np.angle(exp.values) % (2 * np.pi),
            cmap="hsv",
            vmin=0,
            vmax=2 * np.pi,
            edgecolors="black",
            alpha=1,
        )

    # label the points with the index
    for i in range(min(len(exp), topk)):
        # position of the point
        v = [exp.values.real[i], exp.values.imag[i]]

        v = v / np.linalg.norm(v)

        # add a random scaling factor to the vector
        v = v * (1 + np.random.rand() * 0.5)

        # scale the vector by 0.7
        v = v * 0.6

        # plot the text, colored by the angle of eigvecs[i,0] and with the label labels[i], at position v
        plt.text(v[0], v[1], labels[i], fontsize=10)

        # draw a line from the point to the text
        plt.plot([exp.values.real[i], v[0]], [exp.values.imag[i], v[1]], alpha=0.3, color="black")

    # remove the axes
    plt.axis("off")

    # make the plot bigger
    plt.gcf().set_size_inches(scale * 10, scale * 10)

    plt.legend(loc="upper right")

    if color is not None:
        if not isinstance(subset.var[color][0], str):
            plt.colorbar(label=color)

    plt.show()


def plot_heatmap(
    adata: anndata.AnnData,
    coords_key: str = "coords",
    phase_key: str = "gene_phase",
    layer: str = None,
    cmap: str = "viridis",
    figsize: tuple = (10, 6),
    show_gene_labels: bool = True,
    rotate_xticks: int = 90,
    title: str = "Heatmap sorted by circular coord (rows) and gene_phase (columns)",
):
    """
    Plot a heatmap of cells × genes in `adata`, with rows (cells) sorted by
    a circular coordinate (e.g., 'coords') and columns (genes) sorted by a phase variable
    (e.g., 'gene_phase').

    Args:
        adata: The AnnData object containing at least:
            - .obs[coords_key]: A numeric or circular coordinate for each cell
            - .var[phase_key]: A numeric or circular phase for each gene
        coords_key: The key in adata.obs used to sort cells (defaults to 'coords').
        phase_key: The key in adata.var used to sort genes (defaults to 'gene_phase').
        layer: If specified, use adata.layers[layer] for the expression matrix;
               otherwise use adata.X.
        cmap: Colormap string passed to seaborn.heatmap (e.g., 'viridis', 'magma', etc.).
        figsize: Size of the figure (width, height) in inches.
        show_gene_labels: Whether to show gene names on the x-axis.
        rotate_xticks: Degrees to rotate the x-axis tick labels (e.g., 0, 45, 90).
        title: Title for the heatmap.
    """

    # 1. Determine sorted order of cells by 'coords_key'
    cell_order = np.argsort(adata.obs[coords_key])

    # 2. Determine sorted order of genes by 'phase_key'
    gene_order = np.argsort(adata.var[phase_key])

    # 3. Subset and reorder the data matrix
    #    If 'layer' is provided, use that, otherwise use adata.X
    if layer is not None:
        data_matrix = adata.layers[layer]
    else:
        data_matrix = adata.X

    # Slice rows and columns in sorted order
    data_matrix = data_matrix[cell_order, :][:, gene_order]

    # Convert to dense if it's sparse (caution with large data)
    if sp.issparse(data_matrix):
        data_matrix = data_matrix.toarray()

    # 4. Extract the gene names in the new sorted order
    genes_sorted = adata.var_names[gene_order] if show_gene_labels else False

    # 5. Plot the heatmap
    plt.figure(figsize=figsize)
    sns.heatmap(
        data_matrix,
        cmap=cmap,
        xticklabels=genes_sorted,  # gene names as column labels (or False if not shown)
        yticklabels=False,  # often too many cells to label; set to False or subset
    )

    if rotate_xticks != 0 and show_gene_labels:
        plt.xticks(rotation=rotate_xticks)

    plt.title(title)
    plt.xlabel(f"Genes (sorted by {phase_key})")
    plt.ylabel(f"Cells (sorted by {coords_key})")
    plt.tight_layout()
    plt.show()


def leadlag_plot(adata, genes=None, k=10):
    if genes is None:
        genes = get_top_genes(adata, k=k)
    total_indices = [adata.var_names.get_loc(gene) for gene in genes]
    l = adata.uns["leadlag"]
    l = l[total_indices]
    l = l[:, total_indices]
    plt.figure(figsize=(10, 10))
    plt.imshow(l, cmap="bwr", aspect="auto", interpolation="nearest")
    plt.colorbar()
    plt.xticks(ticks=np.arange(0, len(total_indices)), labels=genes, rotation=90)
    plt.yticks(ticks=np.arange(0, len(total_indices)), labels=genes)


def elbow_plot(adata):
    # assert that the leadlag_eigvals are in adata.uns
    assert "leadlag_eigvals" in adata.uns, "leadlag_eigvals not in adata.uns. please run chnt.leadlag"

    eigvals = adata.uns["leadlag_eigvals"]

    plt.plot(np.abs(eigvals[::2]), "o")
    plt.xticks(np.arange(len(eigvals) / 2))
    plt.title("Modulus of Complex Eigenvalues")
    plt.show()


# turn the above into a function plot_top_genes which takes in adata, k and returns the above plot
def plot_top_genes(adata, k=10):
    top_genes = get_top_genes(adata, k=k)

    gene_phases = adata[:, top_genes].var["gene_phase"]

    genes = top_genes

    # set up 4 subplots stack ontop of each other
    fig, axs = plt.subplots(len(top_genes), 1, figsize=(10, len(genes) * 2))

    hsv_colors = colormaps.get_cmap("hsv")

    # plot gene expression
    for i, gene in enumerate(genes):
        gene_exp = adata[:, genes[i]].X
        # map gene_phase to a hsv color
        color = hsv_colors(gene_phases[gene] / (2 * np.pi))

        axs[i].scatter(adata.obs["coords"], gene_exp, label=genes[i], color=color)
        axs[i].set_ylabel("Gene Expression")
        axs[i].legend()

        # color by phase of gene

        if i == len(genes) - 1:
            axs[i].set_xlabel("Circular Coordinate")

    # add a colorbar to the figure
    fig.colorbar(plt.cm.ScalarMappable(cmap="hsv"), ax=axs, orientation="vertical", label="Gene Phase", shrink=0.5)

    # make the width of the colorbar small
    plt.show()


def pc_column_plot(adata, ax, c, comp=[0, 1]):
    # add c to title
    ax.set_title(c)

    if c in adata.obs.columns:
        # check if the column is categorical
        if adata.obs[c].dtype == "category":
            for iden in adata.obs[c].unique():
                sub_adata = adata[adata.obs[c] == iden]
                ax.scatter(sub_adata.obsm["X_pca"][:, comp[0]], sub_adata.obsm["X_pca"][:, comp[1]], label=iden)

            # Shrink current axis by 20%
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

            # Put a legend to the right of the current axis
            ax.legend(loc="upper left", bbox_to_anchor=(1, 1))

            ax.set_title(c)

        elif c == "coords":
            ax.scatter(
                adata.obsm["X_pca"][:, comp[0]], adata.obsm["X_pca"][:, comp[1]], c=list(adata.obs[c]), cmap="hsv"
            )

            # add a colorbar to the figure
            cbar = plt.colorbar(ax.collections[0], ax=ax)
            cbar.set_label(c)

        else:
            ax.scatter(adata.obsm["X_pca"][:, comp[0]], adata.obsm["X_pca"][:, comp[1]], c=list(adata.obs[c]))

            # add a colorbar to the figure
            cbar = plt.colorbar(ax.collections[0], ax=ax)
            cbar.set_label(c)

    elif c in adata.var_names:
        ax.scatter(adata.obsm["X_pca"][:, comp[0]], adata.obsm["X_pca"][:, comp[1]], c=list(adata[:, c].X))
        cbar = plt.colorbar(ax.collections[0], ax=ax)
        cbar.set_label(c)

    ax.set_title(c)

    # axis labels
    ax.set_xlabel(f"PC {comp[0]}")
    ax.set_ylabel(f"PC {comp[1]}")


# rewrite the pc_column_plot to plot on the LL pcs
def ll_column_plot(adata, ax, c, comp=0):
    # add c to title
    ax.set_title(c)

    eigvecs = adata.varm["leadlag_pcs"]

    # take the real and complex part of the first eigenvector
    re = eigvecs[:, 2 * comp].real
    im = eigvecs[:, 2 * comp].imag

    # project the data onto the real and imaginary parts of the first eigenvector
    proj_re = adata.X @ re
    proj_im = adata.X @ im

    if c in adata.obs.columns:
        # check if the column is categorical
        if adata.obs[c].dtype == "category":
            for iden in adata.obs[c].unique():
                sub_adata = adata[adata.obs[c] == iden]
                # project the data onto the real and imaginary parts of the first eigenvector
                proj_re_iden = sub_adata.X @ re
                proj_im_iden = sub_adata.X @ im
                ax.scatter(proj_re_iden, proj_im_iden, label=iden)

            ax.legend()
            # put legend in top right

            # Shrink current axis by 20%
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

            # Put a legend to the right of the current axis
            ax.legend(loc="upper left", bbox_to_anchor=(1, 1))

            ax.set_title(c)
            # add a colorbar

        elif "coords" in c:
            ax.scatter(proj_re, proj_im, c=list(adata.obs[c]), cmap="hsv")

            # add a colorbar to the figure
            cbar = plt.colorbar(ax.collections[0], ax=ax)
            cbar.set_label(c)
            ax.set_xlabel("LL PCA Real")
            ax.set_ylabel("LL PCA Imaginary")
            ax.set_title(c)

        else:
            ax.scatter(proj_re, proj_im, c=list(adata.obs[c]))

            # add a colorbar to the figure
            cbar = plt.colorbar(ax.collections[0], ax=ax)
            cbar.set_label(c)
            ax.set_xlabel("LL PCA Real")
            ax.set_ylabel("LL PCA Imaginary")
            ax.set_title(c)

    # c is a gene
    elif c in adata.var_names:
        ax.scatter(proj_re, proj_im, c=list(adata[:, c].X), cmap="viridis")
        ax.set_xlabel("LL PCA Real")
        ax.set_ylabel("LL PCA Imaginary")
        ax.set_title(c)
        cbar = plt.colorbar(ax.collections[0], ax=ax)
        cbar.set_label(c)


def plot_2d(adata, c, mode="ll", comp=None, scale=1):
    # if c is not a list make it a list
    if not isinstance(c, list):
        c = [c]

    # if mode is ll make sure that leadlag_pcs is in adata.varm
    if mode == "ll":
        if "leadlag_pcs" not in adata.varm.keys():
            raise ValueError("leadlag_pcs not in adata.varm, please run chnt.leadlag()")

    # if mode is pca make sure that X_pca is in adata.obsm
    if mode == "pca":
        if "X_pca" not in adata.obsm.keys():
            raise ValueError("PCA not computed")

    # intialize the figure with len(c) subplots, and a size which is a function of len(c)
    _, ax = plt.subplots(1, len(c), figsize=(scale * 8 * (len(c)), scale * 6))

    a = len(c)

    for i, c in enumerate(c):
        if mode == "ll":
            if comp is None:
                comp = 0

            if a == 1:
                ll_column_plot(adata, ax, c, comp)
            elif a > 1:
                ll_column_plot(adata, ax[i], c, comp)
        elif mode == "pca":
            if comp is None:
                comp = [0, 1]

            if a == 1:
                pc_column_plot(adata, ax, c, comp)
            elif a > 1:
                pc_column_plot(adata, ax[i], c, comp)

    plt.show()


def scatter3D(adata, color=None, comp=[0, 1, 2], title=False, color_continuous_scale="Viridis", mode="pca"):
    # check length of combo is 3
    if len(comp) != 3:
        raise ValueError("combo must be a list of length 3")

    # check pca is computed
    if mode == "pca":
        if "X_pca" not in adata.obsm.keys():
            raise ValueError("PCA not computed")
        data = adata.obsm["X_pca"][:, comp]
    elif mode == "ef":
        if "X_ef" not in adata.obsm.keys():
            raise ValueError("Effective Resistance not computed")
        data = adata.obsm["X_ef"][:, comp]
    else:
        raise ValueError("mode must be either 'pca' or 'ef'")

    # check color is in adata.obs
    if color is not None:
        if color not in adata.var_names:
            if color not in adata.obs.columns:
                raise ValueError(
                    "color not in adata.obs or adata.var_names, please select one of the following: "
                    + str(adata.obs.columns)
                )

    # make a dataframe of the data and phases
    dummy_df = pd.DataFrame(data)

    # exact the color and save to df
    if color is not None:
        if color in adata.obs.columns:
            dummy_df["color"] = list(adata.obs[color])
        elif color in adata.var_names:
            dummy_df["color"] = list(adata[:, color].X[:, 0])

    # make a 3d scatter plot of the data using plotly express

    if color is not None:
        fig = px.scatter_3d(dummy_df, x=0, y=1, z=2, color="color", color_continuous_scale=color_continuous_scale)
    else:
        fig = px.scatter_3d(dummy_df, x=0, y=1, z=2)

    # make plotly figure square
    fig.update_layout(scene_aspectmode="cube")

    # add a legend to the figure specifying which color corresponds to which phase
    fig.update_layout(legend=dict(title=color, yanchor="top", y=0.99, xanchor="left", x=0.01))
    fig.update_layout(showlegend=True)

    # make the points in the legend larger
    fig.update_layout(legend=dict(itemsizing="constant"))

    # make the markers in the smaller, and give them a thin black  outline
    fig.update_traces(marker=dict(size=4, line=dict(width=1, color="DarkSlateGrey")))

    # set the title centering it at the top of the plot
    if title:
        fig.update_layout(
            title=dict(text=title, xref="paper", x=0.5, yref="paper", y=1.0, font=dict(size=24, color="#7f7f7f"))
        )

    # make figure height larger
    fig.update_layout(height=800)

    # make figure width smaller
    fig.update_layout(width=1000)

    fig.show()


### --- PERSISTENCE DIAGRAM STATISTICS --- ###


def l_transform(pdgm):
    pratios = [elem[1] / elem[0] for elem in pdgm]
    loglog_ratio = np.log(np.log(pratios))
    corr_factor = np.euler_gamma + np.mean(loglog_ratio)
    l_value = loglog_ratio - corr_factor
    return l_value


def pdgm_to_pBS(pdgm):
    """
    Calculate the KS test p-value of the L-transformed persistence diagram against the L-Gumbel distribution.
    """
    pval = ss.ks_1samp(l_transform(pdgm), ss.gumbel_l().cdf).pvalue
    return pval


def pdgm_to_pNorm(pdgm):
    """
    Calculate the KS test p-value of the persistence diagram against the Normal distribution.
    """
    pratios = [elem[1] / elem[0] for elem in pdgm]
    mu = np.mean(pratios)
    sd = np.std(pratios)
    pval = ss.ks_1samp(pratios, ss.norm(loc=mu, scale=sd).cdf).pvalue
    return pval


# rewrite the code in the box above as a function with input adata and combos
def PCA_persistence_info(adata, pca_combos, mode="pca"):
    """
    A function to calculate the persistence diagram and assosicated statistics
    for each combo in combos and store them in a list
    ----------

    Parameters:
        adata (anndata.AnnData): an AnnData object
        pca_combos (list): a list of lists of integers, each list of integers is a combination of PCs

    Returns:
        df (pandas.DataFrame): a pandas dataframe with the following columns:
            combo (list): a list of integers, each integer is a PCA index
            min_adj_pvals (float): the minimum adjusted p-value for the persistence diagram
            minpvals (float): the minimum p-value for the persistence diagram
            ksLGumbel (float): the Kolmogorov-Smirnov statistic for the persistence diagram
                               under the L-transformed LGumbel distribution
            ksNormal (float): the Kolmogorov-Smirnov statistic for the persistence diagram
                              under the L-transformed Normal distribution
            adj_pvals (list): a list of adjusted p-values for each point in the persistence diagram
            pvals (list): a list of p-values for each point in the persistence diagram
            pdgm (list): a list of lists, each list is a point in the persistence diagram
    """

    pds = []
    for combo in pca_combos:
        if mode == "pca":
            pds.append(ripser(adata.obsm["X_pca"][:, combo])["dgms"][1])
        elif mode == "ef":
            pds.append(ripser(adata.obsm["X_ef"][:, combo])["dgms"][1])

    pds_L = []
    ksLGumbel = []
    ksNormal = []

    for p in pds:
        pds_L.append(l_transform(p))
        ksLGumbel.append(pdgm_to_pBS(p))
        ksNormal.append(pdgm_to_pNorm(p))

    pvals = []
    minpvals = []
    adj_pvals = []
    min_adj_pvals = []

    for L in pds_L:
        pvals.append(np.exp(-np.exp(L)))
        minpvals.append(np.exp(-np.exp(np.min(L))))
        adj_pvals.append(np.exp(-np.exp(L)) * len(L))
        min_adj_pvals.append(np.min(np.exp(-np.exp((L))) * len(L)))

    df = pd.DataFrame(
        {
            "combo": pca_combos,
            "min_adj_pvals": min_adj_pvals,
            "minpvals": minpvals,
            "ksLGumbel": ksLGumbel,
            "ksNormal": ksNormal,
            "adj_pvals": adj_pvals,
            "pvals": pvals,
            "pdgm": pds,
        }
    )

    df = df.sort_values(by=["min_adj_pvals"])
    return df


# turn the above 3 cells into a single function with inputs adata, gs_collection, random state
# and outputs the df
def circ_enrich(
    adata,
    gs_collection,
    comp=[0, 1, 2],
    k=None,
    exponent=2,
    min_genes=None,
    bandwidth=None,
    lower_percentile=None,
    upper_percentile=None,
    mode="pca",
    n_neighbors=5,
):
    if k is not None:
        comp = list(range(k))
    else:
        k = max(comp) + 1

    pdgm_ls = []
    pbar = tqdm(gs_collection.items(), total=len(gs_collection))

    if min_genes is None:
        min_genes = k + 1

    for gs_name, gs in pbar:
        sub_gs_genes = adata.var_names.intersection(gs)
        sub_adata = adata[:, sub_gs_genes].copy()

        if sub_adata.n_vars < min_genes:
            continue

        if mode == "pca":
            sc.tl.pca(sub_adata, n_comps=k)

            if bandwidth is not None:
                sub_adata = filter_cells_by_density(
                    sub_adata,
                    n_pcs=k,
                    bandwidth=bandwidth,
                    lower_percentile=lower_percentile,
                    upper_percentile=upper_percentile,
                )

            diameter = max(distance.pdist(sub_adata.obsm["X_pca"]))
        elif mode == "ef":
            effective_resistence(sub_adata, num_neighbors=n_neighbors, k=k)
            diameter = max(distance.pdist(sub_adata.obsm["X_ef"]))
        else:
            raise ValueError()

        pdgm_pca = PCA_persistence_info(sub_adata, [comp], mode=mode)
        pdgm_pca["diameter"] = diameter
        pdgm_pca.index = [gs_name]
        pdgm_ls.append(pdgm_pca)

    if len(pdgm_ls) == 0:
        raise ValueError()

    df = pd.concat(pdgm_ls)

    data_dict = {}
    for gs_name, row in df.iterrows():
        pdgm = rng.PDiagram(row.pdgm, diameter=row.diameter, dim=1)
        data_dict[gs_name] = [
            rng.ring_score_from_pdiagram(pdgm, score_type="length", exponent=exponent),
            rng.ring_score_from_pdiagram(pdgm, score_type="diameter", exponent=exponent),
            rng.ring_score_from_pdiagram(pdgm, score_type="ratio", exponent=exponent),
            rng.ringscore.statistics.min_pvalue_from_pdiagram(pdgm),
            rng.ringscore.statistics.min_pvalue_from_pdiagram(
                pdgm,
                remove_top_n=0,
            ),
        ]

    col_names = [
        "score_length",
        "score_diameter",
        "score_ratio",
        "min_pvalue",
        "min_pvalue_no_top",
    ]

    ring_score_df = pd.DataFrame(data_dict, index=col_names).T

    df = df.merge(ring_score_df, left_index=True, right_index=True)

    return df


def filter_cells_by_density_iterative(
    adata,
    n_iter=3,
    n_pcs=3,
    bandwidth=0.5,
    lower_percentile=10,
    upper_percentile=90,
    n_neighbors=30,
    recompute_pca=False,
):
    """
    Iteratively filters cells in an AnnData object based on the density of their PCA coordinates,
    using a nearest-neighbor approximation for efficiency.

    Parameters:
    -----------
    adata : AnnData
        The annotated data matrix.
    n_iter : int, optional (default: 3)
        Number of iterations to perform density-based filtering.
    n_pcs : int, optional (default: 3)
        Number of principal components to consider for density estimation.
    bandwidth : float, optional (default: 0.5)
        Bandwidth parameter for the Gaussian kernel used in density estimation.
    lower_percentile : float, optional (default: 10)
        Lower percentile threshold to filter out cells with the lowest density.
    upper_percentile : float, optional (default: 90)
        Upper percentile threshold to filter out cells with the highest density.
    n_neighbors : int, optional (default: 30)
        Number of nearest neighbors to use for density estimation.
    recompute_pca : bool, optional (default: False)
        Whether to recompute PCA on the filtered data at each iteration.

    Returns:
    --------
    AnnData
        Filtered AnnData object containing only cells within the specified density range
        after the iterative filtering process.
    """

    # Compute PCA if not already done
    if "X_pca" not in adata.obsm:
        sc.tl.pca(adata)

    # Extract the first `n_pcs` PCA coordinates
    X = adata.obsm["X_pca"][:, :n_pcs]

    for i in range(n_iter):
        # Build the nearest neighbor model and query the n_neighbors for each cell
        nbrs = NearestNeighbors(n_neighbors=n_neighbors, algorithm="auto").fit(X)
        distances, _ = nbrs.kneighbors(X)

        # Compute density using only the nearest neighbors.
        # Here, each cell's density is the sum of Gaussian weights of its distances.
        # The Gaussian kernel used is: exp(-0.5 * (distance / bandwidth)**2)
        density = np.sum(np.exp(-0.5 * (distances / bandwidth) ** 2), axis=1)

        # Store density for this iteration in the AnnData object
        adata.obs[f"density_iter_{i + 1}"] = density

        # Determine density thresholds based on the desired percentiles
        lower_threshold = np.percentile(density, lower_percentile)
        upper_threshold = np.percentile(density, upper_percentile)

        # Create a mask for cells whose density falls within the specified range
        keep_idx = (density > lower_threshold) & (density < upper_threshold)
        adata = adata[keep_idx].copy()
        print(f"Iteration {i + 1}: {adata.n_obs} cells remain.")

        # Update the PCA coordinates for the next iteration:
        if recompute_pca:
            sc.tl.pca(adata, n_comps=n_pcs)
            X = adata.obsm["X_pca"][:, :n_pcs]
        else:
            # If not recomputing PCA, filter the existing PCA coordinate matrix
            X = X[keep_idx]

    return adata


def circ_enrich_ef(adata, gs_collection, comp=[0, 1, 2], k=None, exponent=2, min_genes=None, n_neighbors=5):
    warnings.warn(
        'circ_enrich_ef is deprecated. Use `circ_enrich` with `mode="ef"` instead.',
        DeprecationWarning,
        stacklevel=2,
    )
    return circ_enrich(
        adata=adata,
        gs_collection=gs_collection,
        comp=comp,
        k=k,
        exponent=exponent,
        min_genes=min_genes,
        mode="ef",
        n_neighbors=n_neighbors,
    )


def circ_enrich_density(
    adata,
    gs_collection,
    comp=[0, 1, 2],
    k=None,
    exponent=2,
    bandwidth=0.3,
    lower_percentile=5,
    upper_percentile=100,
    min_genes=None,
):
    warnings.warn(
        "circ_enrich_density is deprecated. Use `circ_enrich` instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return circ_enrich(
        adata=adata,
        gs_collection=gs_collection,
        comp=comp,
        k=k,
        exponent=exponent,
        min_genes=min_genes,
        bandwidth=bandwidth,
        lower_percentile=lower_percentile,
        upper_percentile=upper_percentile,
    )


def ring_score(adata, score_type="ratio", exponent=2, comp=np.arange(5), recompute=False):
    if "pdgm" not in adata.uns.keys() or recompute:
        adata.uns["pdgm"] = rng.pdiagram(adata.obsm["X_pca"][:, comp])

    return rng.ring_score_from_pdiagram(adata.uns["pdgm"], score_type=score_type, exponent=exponent)


def calculate_pvalue_from_empirical_scores(test_score, empirical_scores):
    ecdf = ss.ecdf(empirical_scores)
    return ecdf.sf.evaluate(test_score)


def calculate_pvalue_from_empirical_scores2(test_score, empirical_scores):
    from statsmodels.distributions.empirical_distribution import ECDF

    ecdf = ECDF(empirical_scores)
    return 1 - ecdf(test_score)


def permutation_pvalue(
    adata,
    gs,
    n_ensemble=2**7,
    score_type="diameter",
    n_comps=3,
    bandwidth=0.3,
    lower_percentile=5,
    upper_percentile=100,
):
    sub_gs_genes = adata.var_names.intersection(gs)
    sub_adata = adata[:, sub_gs_genes].copy()

    sc.tl.pca(sub_adata, n_comps=n_comps)

    sub_adata = filter_cells_by_density(
        sub_adata,
        n_pcs=n_comps,
        bandwidth=bandwidth,
        lower_percentile=lower_percentile,
        upper_percentile=upper_percentile,
    )

    test_pdgm = rng.pdiagram_from_point_cloud(sub_adata.obsm["X_pca"])
    test_score = rng.ring_score_from_pdiagram(test_pdgm, score_type=score_type)

    empirical_scores = []

    pbar = tqdm(range(n_ensemble), total=n_ensemble)
    for _ in pbar:
        n_genes = len(sub_gs_genes)

        random_gs_genes = random.sample(list(adata.var_names), n_genes)
        sub_adata = adata[:, random_gs_genes].copy()

        sc.tl.pca(sub_adata, n_comps=3)
        diameter = max(distance.pdist(sub_adata.obsm["X_pca"]))
        pdgm_pca = PCA_persistence_info(sub_adata, [[0, 1, 2]])
        pdgm = rng.PDiagram(pdgm_pca.pdgm[0], diameter=diameter, dim=1)
        score = rng.ring_score_from_pdiagram(pdgm, score_type="diameter")
        empirical_scores.append(score)

    pvalue = calculate_pvalue_from_empirical_scores2(test_score, empirical_scores)

    _, ax = plt.subplots()

    ax.hist(empirical_scores, bins=20, alpha=0.5, label="empirical")
    ax.axvline(test_score, color="r", label="test")

    # label axes
    ax.set_xlabel("Ring score")
    ax.set_ylabel("Frequency")

    return pvalue, empirical_scores, test_score


def plot_diagram(adata, comp=[0, 1, 2]):
    # check PCA computed
    if "X_pca" not in adata.obsm:
        sc.tl.pca(adata, n_comps=5)

    ripser_result = ripser(
        adata.obsm["X_pca"][:, comp],
        coeff=3,
        do_cocycles=True,
        maxdim=1,
    )
    # Get 1-persistence diagram
    pdgm = ripser_result["dgms"][1]

    # identify the index of the longest interval
    idx = np.argmax(pdgm[:, 1] - pdgm[:, 0])
    max_birth, max_death = pdgm[idx]

    _, ax = plt.subplots()
    rng.PDiagram(pdgm).plot(ax=ax)
    ax.scatter(max_birth, max_death, 75, "k", "x")
    ax.set_title(f"Max 1D birth = {max_birth:.2f}, death = {max_death:.2f}")
