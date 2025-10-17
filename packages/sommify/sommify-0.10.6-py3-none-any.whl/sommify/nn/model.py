import torch
import torch.nn as nn


class Model(nn.Module):
    def __init__(self, wine_encoder, food_encoder):
        super(Model, self).__init__()

        self.wine_encoder = wine_encoder
        self.food_encoder = food_encoder
        # self.temperature = nn.Parameter(torch.tensor(0.07))

    def forward(self, wine_inputs, food_inputs):
        wine_embs = self.wine_encoder(wine_inputs)
        food_embs = self.food_encoder(food_inputs)

        return wine_embs, food_embs


class MLPEncoder(nn.Module):
    def __init__(
        self,
        input_dim,
        output_dim,
        hidden_layer_dims=[128, 64],
        dropout=0,
        gravity=False,
        normalization_layer=nn.LayerNorm,  # either None or some sort of 1d normalization layer
        activation_layer=nn.ReLU,
    ):
        super(MLPEncoder, self).__init__()
        self.output_dim = output_dim

        # Define linear layers
        linear_layers = []

        # if mass, add + 1 to the output dimension
        if gravity:
            output_dim += 1

        # with ReLU activation, normalization and dropout
        for h_output_dim in hidden_layer_dims:
            linear_layers.append(nn.Linear(input_dim, h_output_dim))
            linear_layers.append(activation_layer())
            if normalization_layer is not None:
                linear_layers.append(normalization_layer(h_output_dim))
            if dropout > 0:
                linear_layers.append(nn.Dropout(p=dropout))
            input_dim = h_output_dim

        # Add output layer
        linear_layers.append(nn.Linear(input_dim, output_dim))

        # Combine all layers
        self.fc = nn.Sequential(*linear_layers)

        for layer in self.fc:
            if isinstance(layer, nn.Linear):
                nn.init.kaiming_uniform_(layer.weight, nonlinearity="relu")

    def forward(self, x):
        return self.fc(x)


def build_mlp_encoder(input_dim, embedding_dim, dropout, gravity=0.0, **kwargs):
    return MLPEncoder(
        input_dim=input_dim,
        output_dim=embedding_dim,
        hidden_layer_dims=kwargs.get("hidden_layer_sizes", [256, 128]),
        activation_layer={
            "relu": nn.ReLU,
            "gelu": nn.GELU,
        }.get(kwargs.get("activation", "relu")),
        dropout=dropout,
        gravity=gravity,
    )


def build_model(
    wine_input_dim: int,
    food_input_dim: int,
    embedding_dim: int,
    wine_encoder_params: dict,
    food_encoder_params: dict,
) -> nn.Module:
    wine_encoder = build_mlp_encoder(
        input_dim=wine_input_dim, embedding_dim=embedding_dim, **wine_encoder_params
    )
    food_encoder = build_mlp_encoder(
        input_dim=food_input_dim, embedding_dim=embedding_dim, **food_encoder_params
    )

    return Model(wine_encoder, food_encoder)


def load_model(
    path, wine_input_dim=577, food_input_dim=1172, device="cpu", random=False
):
    # Load the checkpoint
    checkpoint = torch.load(path, map_location=device)

    # Extract the configuration
    config = checkpoint["config"]

    # Build the model using the saved configuration
    model = build_model(
        embedding_dim=config["embedding_dim"],
        wine_input_dim=wine_input_dim,
        food_input_dim=food_input_dim,
        wine_encoder_params=config["wine_encoder"],
        food_encoder_params=config["food_encoder"],
    )

    # Load the model state
    # load the model state dict
    try:
        if not random:
            model.load_state_dict(checkpoint["model_state_dict"])
    except RuntimeError:
        # If there is a size mismatch, try to load the state dict with strict=False
        print("Size mismatch in model state dict")
        return None

    # Move the model to the specified device
    model.to(device)

    print(f"Model loaded from {path}")
    return model
