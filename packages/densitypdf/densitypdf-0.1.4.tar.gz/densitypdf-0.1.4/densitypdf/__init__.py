import scipy.stats as st
from statistics import NormalDist
from densitypdf.builtin.builtindensitypdf import builtin_density_pdf


def density_pdf(
    density_dict:dict,
    x: float = 0.0,
    max_depth: int = 3,
    current_depth: int = 0,
    max_mixtures: int = 5,
    mixture_count: int = 0,
) -> float:
    """
    Evaluate a density specification at a given point x, with safeguards:
      1) Recursion limited to 'max_depth' levels (default=3).
      2) At most 'max_mixtures' total mixtures (default=5).

    :param density_dict:  A dictionary describing a density. Possible forms:
        1) Scipy distribution:
           {
             "type": "scipy",
             "name": "norm",
             "params": {"loc": 0, "scale": 1}
           }
        2) Statistics distribution:
           {
             "type": "builtin",
             "name": "normal",
             "params": {"mu": 2.0, "sigma": 1.0}
           }
        3) Builtin distribution:  (same as scipy)
            {
             "type": "builtin",
             "name": "norm",
             "params": {"loc": 0, "scale": 1}
           }

        4) Mixture distribution:
           {
             "type": "mixture",
             "components": [
               {
                 "density": <sub-dict describing density>,
                 "weight": <float>
               },
               ...
             ]
           }
    :param x: The point at which to evaluate the PDF.
    :param max_depth: Maximum recursion depth allowed for nested mixtures.
    :param current_depth: The current recursion level (internal usage).
    :param max_mixtures: Maximum total number of mixtures allowed.
    :param mixture_count: The current count of mixtures encountered (internal usage).
    :return: The PDF value at x (float).
    :raises ValueError: If specification is unknown or if mixture/recursion limits are exceeded.
    :raises RecursionError: If 'max_depth' is exceeded.
    """

    # Check recursion depth
    if current_depth > max_depth:
        raise RecursionError(
            f"Exceeded maximum recursion depth of {max_depth}.\n"
            "Possible nested mixtures beyond allowed depth."
        )

    dist_type = density_dict.get("type")

    # 1) Mixture
    if dist_type == "mixture":
        mixture_count += 1
        if mixture_count > max_mixtures:
            raise ValueError(
                f"Exceeded maximum mixture count of {max_mixtures}.\n"
                "Possible infinite or excessive nesting."
            )

        components = density_dict["components"]
        total_pdf = 0.0
        weights_sum = 0.0
        for comp in components:
            comp_spec = comp["density"]
            weight = abs(comp["weight"])
            weights_sum += weight
            comp_pdf = density_pdf(
                comp_spec,
                x=x,
                max_depth=max_depth,
                current_depth=current_depth + 1,
                max_mixtures=max_mixtures,
                mixture_count=mixture_count,
            )
            total_pdf += weight * comp_pdf
        if weights_sum == 0:
            return 0.0
        return total_pdf / weights_sum

    # 2) Scipy distribution
    elif dist_type == "scipy":
        dist_name = density_dict["name"]
        params = density_dict["params"]
        dist_class = getattr(st, dist_name, None)
        if dist_class is None:
            raise ValueError(f"Unknown scipy distribution name '{dist_name}'.")
        dist_obj = dist_class(**params)
        return dist_obj.pdf(x)

    # 3) Statistics distribution
    elif dist_type == "statistics":
        bname = density_dict["name"]
        bparams = density_dict["params"]
        if bname == "normal":
            mu = bparams.get("mu", bparams.get("loc", 0.0))
            sigma = bparams.get("sigma", 1.0, bparams.get("scale", 1.0))
            dist_obj = NormalDist(mu=mu, sigma=sigma)
            return dist_obj.pdf(x)
        else:
            raise NotImplementedError(f"Unsupported builtin distribution '{bname}'")

    # 3) Builtin distribution
    elif dist_type == "builtin":
        return builtin_density_pdf(density_dict, x)

    else:
        raise ValueError(
            f"Unknown or missing 'type' in density_dict: {density_dict}"
        )
