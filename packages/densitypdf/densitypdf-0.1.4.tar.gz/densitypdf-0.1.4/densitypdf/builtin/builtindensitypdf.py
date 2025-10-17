from densitypdf.builtin.scipyreplacements import (
    norm_pdf_scalar,
    expon_pdf_scalar,
    t_pdf_scalar,
    weibull_min_pdf_scalar,
    gamma_pdf_scalar,
    weibull_max_pdf_scalar,
    beta_pdf_scalar,
    lognorm_pdf_scalar,
    chi_pdf_scalar,
    chi2_pdf_scalar,
    rayleigh_pdf_scalar,
    pareto_pdf_scalar,
    cauchy_pdf_scalar,
    laplace_pdf_scalar,
    f_pdf_scalar,
)


def builtin_density_pdf(density_dict, x):
    """
    Calculate the PDF of a builtin distribution.

    Dispatches to the built-in replacements for scipy.stats functions.
    This version does NOT provide defaults:
    if a required param is missing in density_dict["params"],
    a KeyError will be raised immediately.

    Example of density_dict:
        {
          "name": "norm",
          "params": {
             "mu": 0.0,
             "sigma": 1.0
          }
        }
    """

    bname = density_dict["name"]
    bparams = density_dict["params"]

    if bname == "norm":
        mu = bparams['loc']         # one must exist
        sigma = bparams['scale']  # one must exist
        return norm_pdf_scalar(x, loc=mu, scale=sigma)

    elif bname == "lognorm":
        s = bparams["s"]  # must exist
        loc = bparams["loc"]  # must exist
        scale = bparams["scale"]  # must exist
        return lognorm_pdf_scalar(x, s, loc, scale)

    elif bname == "expon":
        loc = bparams["loc"]
        scale = bparams["scale"]
        return expon_pdf_scalar(x, loc, scale)

    elif bname == "t":
        df = bparams["df"]
        loc = bparams["loc"]
        scale = bparams["scale"]
        return t_pdf_scalar(x, df, loc, scale)

    elif bname == "weibull_min":
        c = bparams["c"]
        loc = bparams["loc"]
        scale = bparams["scale"]
        return weibull_min_pdf_scalar(x, c, loc, scale)

    elif bname == "gamma":
        a = bparams["a"]
        loc = bparams["loc"]
        scale = bparams["scale"]
        return gamma_pdf_scalar(x, a, loc, scale)

    elif bname == "weibull_max":
        c = bparams["c"]
        loc = bparams["loc"]
        scale = bparams["scale"]
        return weibull_max_pdf_scalar(x, c, loc, scale)

    elif bname == "beta":
        a = bparams["a"]
        b_ = bparams["b"]
        loc = bparams["loc"]
        scale = bparams["scale"]
        return beta_pdf_scalar(x, a, b_, loc, scale)

    elif bname == "chi":
        df = bparams["df"]
        loc = bparams["loc"]
        scale = bparams["scale"]
        return chi_pdf_scalar(x, df, loc, scale)

    elif bname == "chi2":
        df = bparams["df"]
        loc = bparams["loc"]
        scale = bparams["scale"]
        return chi2_pdf_scalar(x, df, loc, scale)

    elif bname == "rayleigh":
        loc = bparams["loc"]
        scale = bparams["scale"]
        return rayleigh_pdf_scalar(x, loc, scale)

    elif bname == "pareto":
        b_ = bparams["b"]
        loc = bparams["loc"]
        scale = bparams["scale"]
        return pareto_pdf_scalar(x, b_, loc, scale)

    elif bname == "cauchy":
        loc_ = bparams["loc"]
        scale_ = bparams["scale"]
        return cauchy_pdf_scalar(x, loc_, scale_)

    elif bname == "laplace":
        loc_ = bparams["loc"]
        scale_ = bparams["scale"]
        return laplace_pdf_scalar(x, loc_, scale_)

    elif bname == "f":
        dfn = bparams["dfn"]
        dfd = bparams["dfd"]
        loc = bparams["loc"]
        scale = bparams["scale"]
        return f_pdf_scalar(x, dfn, dfd, loc, scale)

    else:
        raise NotImplementedError(f"Unsupported builtin distribution '{bname}'")
