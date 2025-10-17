import numpy as np

def print_utilities_matrix(utilities_matrix, max_recipes_display=20):
    """
    Pretty print the utilities matrix showing top-K utilities per recipe.

    Parameters
    ----------
    utilities_matrix : np.ndarray
        Matrix of shape [num_recipes x top_k] with utilities
    max_recipes_display : int
        Maximum number of recipes to display (to avoid overwhelming output)
    """
    num_recipes, top_k = utilities_matrix.shape

    # Header
    header = "Recipe | " + " | ".join([f"Rank {i+1}" for i in range(top_k)])
    print("\n" + "=" * len(header))
    print("Top-K Utilities per Recipe")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    # Determine which recipes to show
    if num_recipes <= max_recipes_display:
        recipes_to_show = range(num_recipes)
    else:
        # Show first half and last half
        half = max_recipes_display // 2
        recipes_to_show = list(range(half)) + ["..."] + list(range(num_recipes - half, num_recipes))

    # Print rows
    for idx in recipes_to_show:
        if idx == "...":
            print("  ...  | " + " | ".join(["  ...  "] * top_k))
        else:
            row_str = f"{idx:6d} | "
            row_str += " | ".join([f"{utilities_matrix[idx, k]:7.3f}" for k in range(top_k)])
            print(row_str)

    print("=" * len(header))

    # Summary statistics
    print(f"\nSummary Statistics:")
    print(f"  Total recipes: {num_recipes}")
    for k in range(top_k):
        col = utilities_matrix[:, k]
        print(f"  Rank {k+1}: mean={col.mean():.3f}, std={col.std():.3f}, " f"min={col.min():.3f}, max={col.max():.3f}")
    print()


def analyze_tie_tolerance_impact(scores, tie_tolerance, tie_method="adaptive"):
    """
    Analyze the quality impact of different tie tolerance settings.

    Parameters
    ----------
    scores : np.ndarray
        Score array for all candidates
    tie_tolerance : float
        Tolerance parameter
    tie_method : str
        Method for determining ties

    Returns
    -------
    dict with analysis metrics
    """
    valid_scores = scores[np.isfinite(scores) & (scores > 0)]
    if len(valid_scores) == 0:
        return {"num_candidates": 0, "quality_loss": 0.0}

    best_score = valid_scores.max()

    if tie_method == "adaptive":
        threshold = best_score * (1 - tie_tolerance)
        candidates = valid_scores[valid_scores >= threshold]
    elif tie_method == "absolute":
        threshold = best_score - tie_tolerance
        candidates = valid_scores[valid_scores >= threshold]
    elif tie_method == "top_n":
        n = max(1, int(tie_tolerance))
        n = min(n, len(valid_scores))
        candidates = np.sort(valid_scores)[-n:]
    else:
        candidates = np.array([best_score])

    worst_in_pool = candidates.min()
    quality_loss = (best_score - worst_in_pool) / best_score if best_score > 0 else 0.0

    return {
        "num_candidates": len(candidates),
        "best_score": best_score,
        "worst_in_pool": worst_in_pool,
        "quality_loss_pct": quality_loss * 100,
        "avg_score": candidates.mean(),
        "score_std": candidates.std(),
    }


def compute_recipe_metrics(U, selected_wines, top_k=3):
    """
    Compute recipe-centric utility metrics for a wine selection.

    Parameters
    ----------
    U : np.ndarray
        Utility matrix [num_recipes x num_wines] - binned cosine similarities (0-n)
    selected_wines : list of int
        Indices of selected wines
    top_k : int
        Number of top wines to consider per recipe (default 3)

    Returns
    -------
    dict with keys:
        - 'coverage': int, number of top-K slots filled with highest bin (max utility)
        - 'coverage_rate': float, coverage / (num_recipes * top_k)
        - 'max_possible_coverage': int, num_recipes * top_k
        - 'avg_max_utility': float, average of best utility per recipe
        - 'avg_top_k_utility': float, average of top-k utilities per recipe
        - 'recipe_top_wines': list of lists, top-k wines per recipe with utilities
        - 'global_top_wines': list of tuples, top-k wines overall (recipe_id, wine_id, utility)
    """
    # Convert to numpy if needed
    U_np = U.astype(float)

    num_recipes, _ = U_np.shape

    # Determine the highest utility bin (max value in U)
    max_bin = U_np.max()

    # Filter utility matrix to only selected wines
    U_selected = U_np[:, selected_wines]  # [num_recipes x num_selected]

    # Average max utility
    max_utilities_per_recipe = U_selected.max(axis=1)
    avg_max_utility = max_utilities_per_recipe.mean()

    # Top-K utilities per recipe and coverage calculation
    recipe_top_wines = []
    top_k_utilities = []
    coverage = 0  # Count of top-K slots with max_bin utility

    for recipe_idx in range(num_recipes):
        utilities = U_selected[recipe_idx]

        # Get top-k indices and values
        if len(utilities) >= top_k:
            top_indices = np.argpartition(utilities, -top_k)[-top_k:]
            top_indices = top_indices[np.argsort(utilities[top_indices])[::-1]]
        else:
            top_indices = np.argsort(utilities)[::-1]

        # Store wine IDs and utilities
        top_wines_info = [(selected_wines[idx], utilities[idx]) for idx in top_indices]
        recipe_top_wines.append(top_wines_info)

        # Calculate average of top-k
        top_k_utils = [u for _, u in top_wines_info]
        top_k_utilities.append(np.mean(top_k_utils))

        # Count how many of the top-K are in the highest bin
        coverage += sum(1 for u in top_k_utils if u == max_bin)

    max_possible_coverage = num_recipes * top_k
    coverage_rate = coverage / max_possible_coverage if max_possible_coverage > 0 else 0.0
    avg_top_k_utility = np.mean(top_k_utilities)

    # Global top wines (ignoring constraints, using full U matrix)
    global_top_wines = []
    for recipe_idx in range(num_recipes):
        for wine_idx in selected_wines:
            utility = U_np[recipe_idx, wine_idx]
            if utility > 0:
                global_top_wines.append((recipe_idx, wine_idx, utility))

    # Sort and get top-k globally
    global_top_wines.sort(key=lambda x: x[2], reverse=True)
    global_top_wines = global_top_wines[:top_k]

    # Create utilities matrix [num_recipes x top_k]
    utilities_matrix = np.zeros((num_recipes, top_k))
    for recipe_idx, top_wines in enumerate(recipe_top_wines):
        for k_idx, (_, utility) in enumerate(top_wines):
            if k_idx < top_k:
                utilities_matrix[recipe_idx, k_idx] = utility

    return {
        "coverage": coverage,
        "coverage_rate": coverage_rate,
        "max_possible_coverage": max_possible_coverage,
        "highest_bin": max_bin,
        "avg_max_utility": avg_max_utility,
        "avg_top_k_utility": avg_top_k_utility,
        "recipe_top_wines": recipe_top_wines,
        "global_top_wines": global_top_wines,
        "max_utilities_per_recipe": max_utilities_per_recipe,
        "top_k_utilities_per_recipe": top_k_utilities,
        "utilities_matrix": utilities_matrix,  # [num_recipes x top_k]
    }

