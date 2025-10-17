import numpy as np
from .utils import compute_recipe_metrics, analyze_tie_tolerance_impact
from numba import njit, prange


@njit(parallel=True)
def numba_calculate_utility_gain(
    U_np, selected_wines_arr, top_k, weights_arr, num_recipes, num_wines, current_utility_per_recipe
):
    utility_gains = np.zeros(num_wines, dtype=np.float64)
    num_selected = len(selected_wines_arr)

    for j in prange(num_wines):
        is_selected = False
        for s_idx in range(num_selected):
            if selected_wines_arr[s_idx] == j:
                is_selected = True
                break
        if is_selected:
            utility_gains[j] = -np.inf
            continue

        total_gain = 0.0

        for i in range(num_recipes):
            wine_utility = U_np[i, j]
            if wine_utility <= 0.0:
                continue

            current_utilities_i = np.empty(num_selected, dtype=np.float64)
            valid_count = 0
            for s_idx in range(num_selected):
                u_s = U_np[i, selected_wines_arr[s_idx]]
                if u_s > 0:
                    current_utilities_i[valid_count] = u_s
                    valid_count += 1

            combined_utilities = np.empty(valid_count + 1, dtype=np.float64)
            combined_utilities[:valid_count] = current_utilities_i[:valid_count]
            combined_utilities[valid_count] = wine_utility
            combined_utilities = -np.sort(-combined_utilities)

            new_utility = 0.0
            num_to_sum = min(len(combined_utilities), top_k)
            for k in range(num_to_sum):
                new_utility += weights_arr[k] * combined_utilities[k]

            gain = new_utility - current_utility_per_recipe[i]
            total_gain += gain

        utility_gains[j] = total_gain

    return utility_gains


def greedy_select_topk_weighted(
    U,
    C,
    caps,
    W_E,
    max_card_size=999,
    verbose=False,
    top_k=3,
    weights=None,
    lambda_div=0.3,
    tie_tolerance=0.02,
    tie_method="adaptive",
):
    # Ensure U is NumPy
    U_np = np.array(U, dtype=np.float64)

    num_recipes, num_wines = U_np.shape
    num_constraints = C.shape[1]

    # Default weights: exponential decay
    if weights is None:
        weights = np.array([0.6**i for i in range(top_k)], dtype=np.float64)
        weights[0] = 1.0
    else:
        weights = np.array(weights, dtype=np.float64)

    current_counts = np.zeros(num_constraints, dtype=int)
    selected = []
    current_utility_per_recipe = np.zeros(num_recipes, dtype=np.float64)
    selected_per_group = {k: [] for k in range(num_constraints)}

    # Normalize wine embeddings for cosine similarity (NumPy)
    W_E_np = W_E / np.linalg.norm(W_E, axis=1, keepdims=True)

    while len(selected) < max_card_size and len(selected) < sum(caps):
        selected_arr = np.array(selected, dtype=np.int32)

        # --- Numba Optimized Utility Gain Calculation ---
        utility_gains = numba_calculate_utility_gain(
            U_np, selected_arr, top_k, weights, num_recipes, num_wines, current_utility_per_recipe
        )

        scores = np.full(num_wines, -np.inf)
        diversity_gains = np.zeros(num_wines)

        for j in range(num_wines):
            if j in selected:
                continue

            if np.any(current_counts + C[j] > caps):
                scores[j] = -np.inf
                continue

            groups_j = np.where(C[j] == 1)[0]
            if len(groups_j) == 0:
                scores[j] = -np.inf
                continue

            div_gain = 0.0
            for k in groups_j:
                selected_indices = selected_per_group[k]
                if len(selected_indices) == 0:
                    div_gain += 1.0
                else:
                    sims = np.dot(W_E_np[j : j + 1], W_E_np[selected_indices].T)
                    avg_sim = sims.mean()
                    div_gain += 1 - avg_sim
            div_gain /= len(groups_j)
            diversity_gains[j] = div_gain

        utility_max = utility_gains[np.isfinite(utility_gains)].max()
        diversity_max = diversity_gains.max()

        utility_norm = utility_gains / utility_max if utility_max > 0 else utility_gains
        diversity_norm = diversity_gains / diversity_max if diversity_max > 0 else diversity_gains

        scores = (1 - lambda_div) * utility_norm + lambda_div * diversity_norm

        best_score = np.nanmax(scores)

        if tie_method == "adaptive":
            threshold = best_score * (1 - tie_tolerance)
            best_candidates = np.where(scores >= threshold)[0]
        elif tie_method == "absolute":
            threshold = best_score - tie_tolerance
            best_candidates = np.where(scores >= threshold)[0]
        elif tie_method == "top_n":
            n = max(1, int(tie_tolerance))
            valid_indices = np.where(np.isfinite(scores) & (scores > 0))[0]
            if len(valid_indices) == 0:
                break
            temp_scores = scores[valid_indices]
            top_indices_local = np.argpartition(temp_scores, -n)[-n:]
            best_candidates = valid_indices[top_indices_local]
        else:
            raise ValueError(f"Unknown tie_method: {tie_method}")

        quality_threshold = best_score * 0.90
        best_candidates = best_candidates[scores[best_candidates] >= quality_threshold]

        if len(best_candidates) == 0:
            best_candidates = np.array([np.argmax(scores)])

        best_wine = np.random.choice(best_candidates)
        selected.append(best_wine)

        U_selected = U_np[:, selected]
        for i in range(num_recipes):
            utilities = U_selected[i, :]
            if len(utilities) > 0:
                if len(utilities) >= top_k:
                    top_indices = np.argpartition(utilities, -top_k)[-top_k:]
                    top_k_utils = utilities[top_indices]
                    top_k_utils.sort()
                    top_k_utils = top_k_utils[::-1]
                else:
                    top_k_utils = np.sort(utilities)[::-1]

                new_util_i = sum(weights[k] * top_k_utils[k] for k in range(len(top_k_utils)))
            else:
                new_util_i = 0.0
            current_utility_per_recipe[i] = new_util_i

        groups_best = np.where(C[best_wine] == 1)[0]
        for k in groups_best:
            selected_per_group[k].append(best_wine)
        current_counts += C[best_wine]

        if verbose:
            new_total_utility = np.sum(current_utility_per_recipe)
            tie_analysis = analyze_tie_tolerance_impact(scores, tie_tolerance, tie_method)
            print(
                f"Step {len(selected):2d} | Added wine {best_wine:3d} | "
                # f"Utility gain = {utility_gains[best_wine]:8.3f} | "
                # f"Diversity gain = {diversity_gains[best_wine]:8.3f} | "
                # f"Total utility = {new_total_utility:8.3f} | "
                f"Tie pool = {len(best_candidates)} wines | "
                f"Current counts = {current_counts} | "
                f"Picked {C[best_wine]}"
            )

    total_utility = np.sum(current_utility_per_recipe)
    metrics = compute_recipe_metrics(U, selected, top_k=top_k)

    return selected, total_utility, metrics
