"""
Recipe feature extraction module for neural networks.

This module provides functions to convert recipe data into feature vectors
suitable for neural network models by combining binary ingredient vectors
with text embeddings from sentence transformers.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set, Union
import warnings
import yaml
from functools import lru_cache
import re
import json
import os
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import torch
from sentence_transformers import SentenceTransformer

# Set environment variable to avoid tokenizer parallelism warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from ..recipes import Recipe


# Check if torch is available for CUDA detection and tensor conversion
def is_torch_available():
    """Check if PyTorch is available."""
    try:
        import torch

        return True
    except ImportError:
        return False


# Global torch availability flag
TORCH_AVAILABLE = is_torch_available()


# Check if torch is available for CUDA detection
def is_cuda_available():
    """Check if PyTorch with CUDA is available."""
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False


def to_tensor(array):
    """Convert numpy array to torch tensor if torch is available."""
    if TORCH_AVAILABLE:
        try:
            import torch

            return torch.tensor(array)
        except Exception as e:
            warnings.warn(
                f"Error converting to torch tensor: {str(e)}. Returning numpy array."
            )
    return array


# Load utensils and cooking techniques data
def load_json_data(file_name):
    file_path = os.path.join(os.path.dirname(__file__), "config", file_name)
    with open(file_path, "r") as f:
        return json.load(f)


def load_yaml_config(file_name="recipe_config.yaml"):
    """Load YAML configuration file."""
    file_path = os.path.join(os.path.dirname(__file__), "config", file_name)
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


# Load config files
recipe_config = load_yaml_config()
utensils_data = load_json_data("cooking_utensils.json")
cooking_techniques_data = load_json_data("cooking_techniques.json")

# Extract data structures
utensils = utensils_data["items"]
cooking_techniques = {
    technique["name"].lower(): technique["pattern"]
    for technique in cooking_techniques_data["techniques"]
}

# Pre-compile regex patterns for performance
compiled_utensil_patterns = []
for utensil in utensils:
    pattern = utensil["pattern"]
    category = utensil["category"].lower().replace(" ", "_")
    name = utensil["name"].lower().replace(" ", "_").replace("'", "")
    compiled_pattern = re.compile(rf"(?i)\b(?:{pattern})\b")
    compiled_utensil_patterns.append((compiled_pattern, f"ut_{category}_{name}"))

compiled_technique_patterns = []
for name, pattern in cooking_techniques.items():
    compiled_pattern = re.compile(rf"(?i)\b(?:{pattern})\b")
    compiled_technique_patterns.append((compiled_pattern, f"tech_{name.lower()}"))


def extract_cooking_utensils(text, debug=False):
    """Extract cooking utensils from text using pre-compiled patterns."""
    found = []
    for pattern, feature_name in compiled_utensil_patterns:
        if pattern.search(text):
            found.append(feature_name)
    return found


def extract_cooking_techniques(text, debug=False):
    """Extract cooking techniques from text using pre-compiled patterns."""
    found = []
    for pattern, feature_name in compiled_technique_patterns:
        if pattern.search(text):
            found.append(feature_name)
    return found


def is_text_embedding_available():
    """Check if sentence-transformers is available without importing it."""
    try:
        import importlib.util

        return importlib.util.find_spec("sentence_transformers") is not None
    except ImportError:
        return False


def format_recipe(title, ingredients=None, instructions=None):
    """
    Format a recipe with clear section delineations for embedding.
    Skips sections that are not provided (None or empty).

    Parameters:
    -----------
    title : str
        The title of the recipe
    ingredients : list, optional
        List of ingredient strings (e.g. ["1 tbsp paprika", "2 cups flour"])
    instructions : list, optional
        List of instruction steps

    Returns:
    --------
    str
        Formatted recipe text ready for embedding
    """
    # Start with the title
    formatted_recipe = f"Title: {title}"

    # Add ingredients section if provided
    if ingredients and len(ingredients) > 0:
        ingredients_text = "\n".join([f"- {ingredient}" for ingredient in ingredients])
        formatted_recipe += f"\n\nIngredients:\n{ingredients_text}"

    # Add instructions section if provided
    if instructions and len(instructions) > 0:
        instructions_text = "\n".join(
            [f"{i+1}. {step}" for i, step in enumerate(instructions)]
        )
        formatted_recipe += f"\n\nInstructions:\n{instructions_text}"

    return formatted_recipe


def batch_format_recipes(recipes_data, debug=False):
    """
    Format multiple recipes in batch for efficient processing.

    Parameters:
    -----------
    recipes_data : list of dicts
        Each dict should contain at least a 'title' key and optionally
        'ingredients' and 'instructions' keys.
    debug : bool, default=False
        Whether to print debug timing information

    Returns:
    --------
    list of str
        List of formatted recipe texts ready for embedding
    """
    formatted_recipes = []

    for recipe in recipes_data:
        # Get ingredients from either 'ingredients' or 'phrases' key
        ingredients = recipe.get("ingredients", recipe.get("phrases", []))

        formatted_recipes.append(
            format_recipe(
                recipe.get("title", ""), ingredients, recipe.get("instructions", [])
            )
        )

    return formatted_recipes


def validate_recipe_keys(recipe: Dict) -> Tuple[bool, Optional[str]]:
    """
    Validate that a recipe dictionary has the required keys.

    Parameters:
    -----------
    recipe : Dict
        Recipe dictionary to validate

    Returns:
    --------
    Tuple[bool, Optional[str]]
        (is_valid, error_message)
    """
    # Check for title
    if "title" not in recipe:
        return False, "Recipe is missing required 'title' key"

    # Check for ingredients (either as 'ingredients' or 'phrases')
    has_ingredients = "ingredients" in recipe
    has_phrases = "phrases" in recipe

    if not (has_ingredients or has_phrases):
        return (
            False,
            "Recipe is missing both 'ingredients' and 'phrases' keys, one is required",
        )

    # Check for instructions
    if "instructions" not in recipe:
        return False, "Recipe is missing required 'instructions' key"

    return True, None


@lru_cache(maxsize=8)  # Cache common feature_versions
def get_whitelist_lookup(
    feature_version: str,
) -> Tuple[Dict[str, bool], Dict[str, bool]]:
    """
    Get efficient lookup dictionaries for whitelists. Using dictionaries
    preserves order while providing O(1) lookup time.

    Parameters:
    -----------
    feature_version : str
        Version of feature configuration to use

    Returns:
    --------
    Tuple[Dict[str, bool], Dict[str, bool]]
        (utensil_whitelist_lookup, technique_whitelist_lookup)
    """
    if feature_version not in recipe_config:
        raise ValueError(
            f"Feature version '{feature_version}' not found in recipe config"
        )

    config = recipe_config[feature_version]

    # Create lookup dictionaries that maintain order
    utensil_whitelist = config.get("utensil_whitelist", [])
    technique_whitelist = config.get("technique_whitelist", [])

    utensil_lookup = {utensil: True for utensil in utensil_whitelist}
    technique_lookup = {technique: True for technique in technique_whitelist}

    return utensil_lookup, technique_lookup


def extract_features_from_recipe(
    recipe: Dict, feature_version: str = "v1", debug: bool = False
) -> Dict[str, List[str]]:
    """
    Extract features from a recipe based on config version.

    Parameters:
    -----------
    recipe : Dict
        Recipe dictionary with keys: "title", "instructions", and "ingredients"/"phrases"
    feature_version : str
        Version of feature configuration to use from recipe_config
    debug : bool, default=False
        Whether to print debug timing information

    Returns:
    --------
    Dict[str, List[str]]
        Dictionary with 'utensils' and 'techniques' lists of features
    """
    # Get lookup tables for whitelists (cached for performance)
    utensil_lookup, technique_lookup = get_whitelist_lookup(feature_version)

    # Extract text for feature extraction
    title = recipe.get("title", "")
    instructions = recipe.get("instructions", [])

    # Use sets for faster intersection
    utensils_found = set()
    techniques_found = set()

    # Extract from title
    utensils_found.update(extract_cooking_utensils(title, debug))
    techniques_found.update(extract_cooking_techniques(title, debug))

    # Combine all instructions into a single string for faster processing
    # (most regex engines are optimized for longer texts)
    if instructions:
        combined_instructions = " ".join(instructions)
        utensils_found.update(extract_cooking_utensils(combined_instructions, debug))
        techniques_found.update(
            extract_cooking_techniques(combined_instructions, debug)
        )

    # Filter by whitelist if configured using dict lookup (O(1) operation)
    if utensil_lookup:
        utensils_found = {u for u in utensils_found if u in utensil_lookup}

    if technique_lookup:
        techniques_found = {t for t in techniques_found if t in technique_lookup}

    return {"utensils": list(utensils_found), "techniques": list(techniques_found)}


def _extract_features_worker(recipe_batch, feature_version, debug=False):
    """Worker function for parallel feature extraction."""
    results = []
    for recipe in recipe_batch:
        results.append(extract_features_from_recipe(recipe, feature_version, debug))
    return results


def extract_features_from_recipes_batch(
    recipes: List[Dict],
    feature_version: str = "v1",
    n_jobs: Optional[int] = None,
    debug: bool = False,
) -> List[Dict[str, List[str]]]:
    """
    Extract features from multiple recipes in parallel for better performance.

    Parameters:
    -----------
    recipes : List[Dict]
        List of recipe dictionaries
    feature_version : str
        Version of feature configuration to use
    n_jobs : int, optional
        Number of parallel jobs. If None, uses CPU count.
    debug : bool, default=False
        Whether to print debug timing information

    Returns:
    --------
    List[Dict[str, List[str]]]
        List of dictionaries with 'utensils' and 'techniques' lists of features
    """
    if not recipes:
        return []

    # For small batches, don't use parallelism
    if len(recipes) < 100:
        return [
            extract_features_from_recipe(r, feature_version, debug) for r in recipes
        ]

    # Determine number of workers
    if n_jobs is None:
        n_jobs = max(1, multiprocessing.cpu_count() - 1)

    n_jobs = min(n_jobs, len(recipes))

    if debug:
        print(f"PERF: Using {n_jobs} parallel workers for feature extraction")

    # Split recipes into batches
    batch_size = max(1, len(recipes) // n_jobs)
    batches = [recipes[i : i + batch_size] for i in range(0, len(recipes), batch_size)]

    # Process batches in parallel
    results = []
    with ProcessPoolExecutor(max_workers=n_jobs) as executor:
        futures = [
            executor.submit(_extract_features_worker, batch, feature_version, debug)
            for batch in batches
        ]

        # Collect results as they complete
        for i, future in enumerate(futures):
            results.extend(future.result())

    return results


def create_recipe_feature_vector(
    recipe: Dict,
    feature_version: str = "v1",
    use_text_embedding: bool = True,
    use_cuda: bool = False,
    debug: bool = False,
    sentence_transformer: Optional[SentenceTransformer] = None
) -> np.ndarray | torch.Tensor:
    """
    Create a feature vector from a recipe dictionary combining utensils, techniques,
    binary ingredient vectors, and optionally text embeddings.

    Parameters:
    -----------
    recipe : Dict
        The recipe dictionary with keys: "title", "instructions", and "ingredients"/"phrases"
    feature_version : str
        Version of feature configuration to use from recipe_config
    use_text_embedding : bool, default=True
        Whether to include text embeddings in the feature vector
    use_cuda : bool, default=None
        Whether to use CUDA for the model. If None, automatically uses CUDA if available.
    debug : bool, default=False
        Whether to print debug timing information

    Returns:
    --------
    torch.Tensor or np.ndarray
        The combined feature vector for the recipe in order:
        [utensil_cols, technique_cols, ingredient_cols, text_emb_cols]
        Returns torch.Tensor if PyTorch is available, otherwise np.ndarray

    Raises:
    ------
    ValueError
        If the recipe doesn't have the required keys or feature_version is invalid
    """
    # Validate recipe keys
    is_valid, error_msg = validate_recipe_keys(recipe)
    if not is_valid:
        raise ValueError(error_msg)

    # Get configuration for this feature version
    if feature_version not in recipe_config:
        raise ValueError(
            f"Feature version '{feature_version}' not found in recipe config"
        )

    config = recipe_config[feature_version]

    # Extract features from recipe
    features = extract_features_from_recipe(recipe, feature_version, debug)

    # Extract binary vectors for utensils and techniques
    utensil_whitelist = config.get("utensil_whitelist", [])
    technique_whitelist = config.get("technique_whitelist", [])

    # Create binary vectors for utensils and techniques
    utensil_vector = np.zeros(len(utensil_whitelist), dtype=np.float32)
    for i, utensil in enumerate(utensil_whitelist):
        if utensil in features["utensils"]:
            utensil_vector[i] = 1.0

    technique_vector = np.zeros(len(technique_whitelist), dtype=np.float32)
    for i, technique in enumerate(technique_whitelist):
        if technique in features["techniques"]:
            technique_vector[i] = 1.0

    # Get ingredient binary vector from Recipe class
    # Choose 'ingredients' key if available, otherwise use 'phrases'
    ingredients = recipe.get("ingredients", recipe.get("phrases", []))
    binary_vector = Recipe(phrases=ingredients).vector

    # Combine vectors in the specified order
    feature_vector = np.concatenate([utensil_vector, technique_vector, binary_vector])

    # Add text embedding if requested and available
    if use_text_embedding:
        if not is_text_embedding_available():
            warnings.warn(
                "Text embedding requested but sentence-transformers not installed. "
                'Install with: pip install "sommify[text_embeddings]". '
                "Returning only binary feature vector."
            )
        else:
            try:
                # Determine device to use
                if use_cuda is None:
                    use_cuda = is_cuda_available()

                device = "cuda" if use_cuda else "cpu"

                # Get model name from config or use default
                model_name = config.get(
                    "embedding_model", "sentence-transformers/all-MiniLM-L6-v2"
                )

                # Create text representation
                recipe_text = format_recipe(
                    title=recipe.get("title", ""),
                    ingredients=ingredients,
                    instructions=recipe.get("instructions", []),
                )

                # Load model and create embedding
                if sentence_transformer is not None:
                    model = sentence_transformer
                else:
                    model = SentenceTransformer(model_name, device=device)
                    
                text_embedding = model.encode(recipe_text)

                # Combine with existing features
                feature_vector = np.concatenate([feature_vector, text_embedding])
            except Exception as e:
                warnings.warn(
                    f"Error creating text embedding: {str(e)}. Returning only binary feature vector."
                )

    # Convert to torch tensor if available
    return to_tensor(feature_vector)


def create_recipe_feature_vector_batch(
    recipes: List[Dict],
    feature_version: str = "v1",
    use_text_embedding: bool = True,
    use_cuda: bool = False,
    batch_size: int = 32,
    n_jobs: Optional[int] = None,
    debug: bool = False,
    sentence_transformer: Optional[SentenceTransformer] = None,
) -> np.ndarray | torch.Tensor:
    """
    Create feature vectors for multiple recipes efficiently in a batch.

    Parameters:
    -----------
    recipes : List[Dict]
        List of recipe dictionaries to convert to feature vectors
    feature_version : str
        Version of feature configuration to use from recipe_config
    use_text_embedding : bool, default=True
        Whether to include text embeddings in the feature vectors
    use_cuda : bool, default=None
        Whether to use CUDA for the model. If None, automatically uses CUDA if available.
    batch_size : int, default=32
        Batch size for text embedding generation
    n_jobs : int, optional
        Number of parallel jobs for feature extraction. If None, uses CPU count - 1.
    debug : bool, default=False
        Whether to print debug information

    Returns:
    --------
    torch.Tensor or np.ndarray
        Array of feature vectors for the recipes
        Returns torch.Tensor if PyTorch is available, otherwise np.ndarray

    Raises:
    ------
    ValueError
        If any recipe doesn't have the required keys or feature_version is invalid
    """
    if not recipes:
        # Return empty tensor/array of appropriate type
        if TORCH_AVAILABLE:
            import torch

            return torch.empty((0, 0), dtype=torch.float32)
        return np.array([])

    # Get configuration for this feature version
    if feature_version not in recipe_config:
        raise ValueError(
            f"Feature version '{feature_version}' not found in recipe config"
        )

    config = recipe_config[feature_version]

    # Validate all recipes first
    for i, recipe in enumerate(recipes):
        is_valid, error_msg = validate_recipe_keys(recipe)
        if not is_valid:
            raise ValueError(f"Recipe at index {i}: {error_msg}")

    # Extract all features in a batch using parallelism
    all_features = extract_features_from_recipes_batch(
        recipes, feature_version, n_jobs, debug
    )

    # Get whitelist configurations
    utensil_whitelist = config.get("utensil_whitelist", [])
    technique_whitelist = config.get("technique_whitelist", [])

    # Create binary vectors for all recipes (preallocate for efficiency)
    utensil_vectors = np.zeros((len(recipes), len(utensil_whitelist)), dtype=np.float32)
    technique_vectors = np.zeros(
        (len(recipes), len(technique_whitelist)), dtype=np.float32
    )

    # Fill vectors efficiently
    for i, features in enumerate(all_features):
        # Utensil vectors
        for j, utensil in enumerate(utensil_whitelist):
            if utensil in features["utensils"]:
                utensil_vectors[i, j] = 1.0

        # Technique vectors
        for j, technique in enumerate(technique_whitelist):
            if technique in features["techniques"]:
                technique_vectors[i, j] = 1.0

    # Create binary ingredient vectors for all recipes
    binary_vectors = []
    for recipe in recipes:
        # Choose 'ingredients' key if available, otherwise use 'phrases'
        ingredients = recipe.get("ingredients", recipe.get("phrases", []))
        binary_vectors.append(Recipe(phrases=ingredients).vector)

    binary_vectors = np.stack(binary_vectors)

    # Combine vectors in the specified order
    feature_vectors = np.concatenate(
        [utensil_vectors, technique_vectors, binary_vectors], axis=1
    )

    # Return early if no text embeddings requested
    if not use_text_embedding:
        return to_tensor(feature_vectors)

    # Check if text embeddings are available
    if not is_text_embedding_available():
        warnings.warn(
            "Text embedding requested but sentence-transformers not installed. "
            'Install with: pip install "sommify[text_embeddings]". '
            "Returning only binary feature vectors."
        )
        return to_tensor(feature_vectors)

    try:
        # Determine device to use
        if use_cuda is None:
            use_cuda = is_cuda_available()

        device = "cuda" if use_cuda else "cpu"

        if debug and use_cuda:
            print(f"Using CUDA for sentence transformer model")

        # Get model name from config or use default
        model_name = config.get(
            "embedding_model", "sentence-transformers/all-MiniLM-L6-v2"
        )

        # Format all recipes as text for batch processing
        formatted_recipes = []
        for recipe in recipes:
            # Choose 'ingredients' key if available, otherwise use 'phrases'
            ingredients = recipe.get("ingredients", recipe.get("phrases", []))
            formatted_recipes.append(
                format_recipe(
                    title=recipe.get("title", ""),
                    ingredients=ingredients,
                    instructions=recipe.get("instructions", []),
                )
            )

        # Load model once with specified device
        if sentence_transformer is not None:
            model = sentence_transformer
        else:
            model = SentenceTransformer(model_name, device=device)

        # Generate embeddings in batches
        show_progress = len(recipes) > 100
        text_embeddings = model.encode(
            formatted_recipes,
            batch_size=batch_size,
            show_progress_bar=debug and show_progress,
        )

        # Combine binary vectors with text embeddings
        combined_vectors = np.hstack([feature_vectors, text_embeddings])

        return to_tensor(combined_vectors)

    except Exception as e:
        warnings.warn(
            f"Error creating text embeddings: {str(e)}. Returning only binary feature vectors."
        )
        return to_tensor(feature_vectors)
