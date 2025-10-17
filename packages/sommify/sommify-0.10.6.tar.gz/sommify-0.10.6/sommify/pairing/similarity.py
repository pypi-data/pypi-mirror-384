import numpy as np

def cosine_similarity_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between all rows of A and B."""
    A_norm = A / np.linalg.norm(A, axis=1, keepdims=True)
    B_norm = B / np.linalg.norm(B, axis=1, keepdims=True)
    return A_norm @ B_norm.T  # shape: [A.shape[0], B.shape[0]]


def bin_similarities(sim_matrix: np.ndarray, thresholds=None) -> np.ndarray:
    """
    Discretize cosine similarity scores into bins (0=bad, 1=ok, 2=good, 3=excellent).
    thresholds: list of 3 cutoffs between 0 and 1, e.g. [0.6, 0.75, 0.9]
    """
    if thresholds is None:
        thresholds = [0.6, 0.75, 0.9]
    bins = np.digitize(sim_matrix, thresholds).astype(np.int32)  # explicit signed integer
    return bins
