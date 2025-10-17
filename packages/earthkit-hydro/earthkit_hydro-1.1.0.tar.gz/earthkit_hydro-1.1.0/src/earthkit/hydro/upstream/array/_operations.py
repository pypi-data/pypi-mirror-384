from earthkit.hydro._core.online import calculate_online_metric
from earthkit.hydro._utils.decorators import mask, multi_backend


def calculate_upstream_metric(
    xp,
    river_network,
    field,
    metric,
    node_weights,
    edge_weights,
):
    return calculate_online_metric(
        xp,
        river_network,
        field,
        metric,
        node_weights,
        edge_weights,
        flow_direction="down",
    )


@multi_backend(jax_static_args=["xp", "river_network", "return_type"])
def var(xp, river_network, field, node_weights, edge_weights, return_type):
    return_type = river_network.return_type if return_type is None else return_type
    if return_type not in ["gridded", "masked"]:
        raise ValueError("return_type must be either 'gridded' or 'masked'.")
    decorated_calculate_upstream_metric = mask(return_type == "gridded")(
        calculate_upstream_metric
    )
    return decorated_calculate_upstream_metric(
        xp,
        river_network,
        field,
        "var",
        node_weights,
        edge_weights,
    )


@multi_backend(jax_static_args=["xp", "river_network", "return_type"])
def std(
    xp,
    river_network,
    field,
    node_weights,
    edge_weights,
    return_type,
):
    return_type = river_network.return_type if return_type is None else return_type
    if return_type not in ["gridded", "masked"]:
        raise ValueError("return_type must be either 'gridded' or 'masked'.")
    decorated_calculate_upstream_metric = mask(return_type == "gridded")(
        calculate_upstream_metric
    )
    return decorated_calculate_upstream_metric(
        xp,
        river_network,
        field,
        "std",
        node_weights,
        edge_weights,
    )


@multi_backend(jax_static_args=["xp", "river_network", "return_type"])
def mean(xp, river_network, field, node_weights, edge_weights, return_type):
    return_type = river_network.return_type if return_type is None else return_type
    if return_type not in ["gridded", "masked"]:
        raise ValueError("return_type must be either 'gridded' or 'masked'.")
    decorated_calculate_upstream_metric = mask(return_type == "gridded")(
        calculate_upstream_metric
    )
    return decorated_calculate_upstream_metric(
        xp,
        river_network,
        field,
        "mean",
        node_weights,
        edge_weights,
    )


@multi_backend(jax_static_args=["xp", "river_network", "return_type"])
def sum(xp, river_network, field, node_weights, edge_weights, return_type):
    return_type = river_network.return_type if return_type is None else return_type
    if return_type not in ["gridded", "masked"]:
        raise ValueError("return_type must be either 'gridded' or 'masked'.")
    decorated_calculate_upstream_metric = mask(return_type == "gridded")(
        calculate_upstream_metric
    )
    return decorated_calculate_upstream_metric(
        xp,
        river_network,
        field,
        "sum",
        node_weights,
        edge_weights,
    )


@multi_backend(jax_static_args=["xp", "river_network", "return_type"])
def min(xp, river_network, field, node_weights, edge_weights, return_type):
    return_type = river_network.return_type if return_type is None else return_type
    if return_type not in ["gridded", "masked"]:
        raise ValueError("return_type must be either 'gridded' or 'masked'.")
    decorated_calculate_upstream_metric = mask(return_type == "gridded")(
        calculate_upstream_metric
    )
    return decorated_calculate_upstream_metric(
        xp,
        river_network,
        field,
        "min",
        node_weights,
        edge_weights,
    )


@multi_backend(jax_static_args=["xp", "river_network", "return_type"])
def max(xp, river_network, field, node_weights, edge_weights, return_type):
    return_type = river_network.return_type if return_type is None else return_type
    if return_type not in ["gridded", "masked"]:
        raise ValueError("return_type must be either 'gridded' or 'masked'.")
    decorated_calculate_upstream_metric = mask(return_type == "gridded")(
        calculate_upstream_metric
    )
    return decorated_calculate_upstream_metric(
        xp,
        river_network,
        field,
        "max",
        node_weights,
        edge_weights,
    )
