import torch
from sommify.pairing import (
    cosine_similarity_matrix,
    bin_similarities,
    greedy_select_topk_weighted,
)

recipes = torch.randn(10, 256) # 10 recipes with 256-dim embeddings
wines = torch.randn(400, 256) # 400 wines with 256-dim embeddings

sim = cosine_similarity_matrix(recipes, wines) # shape [10, 400]
binned = bin_similarities(
    sim,
    thresholds=[0.6, 0.75, 0.9]
) # shape [10, 400], values binned to {0,1,2,3}

U = binned.float()  # use discrete pairing scores
C = torch.ones(400, 3)  # a num_wines x num_groups binary matrix, where C[j,k]=1 if wine j belongs to group k (or meets constraint k)
caps = [
    10, # max 10 wines from group 0
    10, # max 10 wines from group 1
    10, # max 10 wines from group 2
]


selected, total_max, total_weighted = greedy_select_topk_weighted(
    U, 
    C, 
    caps, 
    W_E=wines, 
    verbose=True, 
    lambda_div=0.3,
    top_k=3,
)


print("\n✅ Selected wines:", selected) # indices of selected wines