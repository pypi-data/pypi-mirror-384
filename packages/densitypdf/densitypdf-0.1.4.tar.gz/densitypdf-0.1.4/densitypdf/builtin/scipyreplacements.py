import math


#
#==============================================================================
# 1) Normal distribution ("norm"): parameters (loc, scale)
#    Domain: x in (-∞, ∞)
#==============================================================================
def norm_pdf_scalar(x, loc=0.0, scale=1.0):
    """
    PDF of Normal(loc, scale) at scalar x.

    Formula:
        pdf(x) = 1 / [scale * sqrt(2π)] * exp(-((x - loc)^2) / (2*scale^2))

    Returns 0.0 if scale <= 0 is given.
    """
    if scale <= 0:
        raise ValueError("scale must be positive for Normal.")
    z = (x - loc) / scale
    return (1.0 / (scale * math.sqrt(2.0 * math.pi))) * math.exp(-0.5 * z * z)


#
#==============================================================================
# 2) Exponential distribution ("expon"): parameters (loc, scale)
#    Domain: x in [loc, ∞)
#==============================================================================
def expon_pdf_scalar(x, loc=0.0, scale=1.0):
    """
    PDF of Exponential with location=loc and scale=scale at scalar x.

    SciPy parameterization:
        If Y ~ Exponential(1/scale) in standard form, then X = loc + Y*scale.
        pdf(x) = (1/scale) * exp( - (x - loc)/scale ),  for x >= loc
                 0, otherwise
    """
    if scale <= 0:
        raise ValueError("scale must be positive for Exponential.")
    if x < loc:
        return 0.0
    z = (x - loc) / scale
    return (1.0 / scale) * math.exp(-z)


#
#==============================================================================
# 3) Student's t distribution ("t"): parameters (df, loc, scale)
#    Domain: x in (-∞, ∞), df>0
#==============================================================================
def t_pdf_scalar(x, df, loc=0.0, scale=1.0):
    """
    PDF of Student's T(df), shifted by loc, scaled by scale, at scalar x.

    Formula (for x in R):
      y = (x - loc)/scale
      pdf(x) = (1/scale) * Gamma((df+1)/2) / [ sqrt(df*pi)*Gamma(df/2) ]
               * [ 1 + (y^2)/df ]^(-(df+1)/2)

    df > 0, scale>0
    """
    if df <= 0:
        raise ValueError("df must be positive for T distribution.")
    if scale <= 0:
        raise ValueError("scale must be positive for T distribution.")
    y = (x - loc) / scale

    # constant factor
    c = math.gamma((df + 1) / 2.0) / (
            math.sqrt(df * math.pi) * math.gamma(df / 2.0)
    )
    return (1.0 / scale) * c * (1 + (y * y) / df) ** (-(df + 1) / 2.0)


#
#==============================================================================
# 4) Weibull minimum ("weibull_min"): parameters (c, loc, scale)
#    Domain: x in [loc, ∞), c>0, scale>0
#==============================================================================
def weibull_min_pdf_scalar(x, c, loc=0.0, scale=1.0):
    """
    PDF of Weibull_min(c), with location=loc, scale=scale, at scalar x.

    Standard form PDF (for y>=0):
      f_0(y) = c * y^(c-1) * exp(-y^c),  y >= 0

    After shifting by loc and scaling by scale:
      y = (x - loc)/scale
      pdf(x) = (c/scale) * [ (x-loc)/scale ]^(c-1) * exp( - [ (x-loc)/scale ]^c )
               for x>=loc; else 0
    """
    if c <= 0:
        raise ValueError("shape c must be positive for weibull_min.")
    if scale <= 0:
        raise ValueError("scale must be positive for weibull_min.")
    if x < loc:
        return 0.0
    y = (x - loc) / scale
    return (c / scale) * (y ** (c - 1)) * math.exp(-(y ** c))


def gamma_pdf_scalar(x, a, loc=0.0, scale=1.0):
    """
    PDF of Gamma(a), with loc, scale at scalar x.

    Matches scipy.stats.gamma(a, loc=loc, scale=scale).

    SciPy parameterization:
      If Y ~ Gamma(shape=a, scale=scale) [i.e. mean = a * scale],
      then X = loc + Y.
      The PDF is:
        f_X(x) = 1 / [Gamma(a) * scale^a] * (x - loc)^(a - 1)
                 * exp(-(x - loc)/scale),  for x >= loc; 0 otherwise.
    """
    import math

    if a <= 0:
        raise ValueError("shape a must be positive for Gamma.")
    if scale <= 0:
        raise ValueError("scale must be positive for Gamma.")
    if x < loc:
        return 0.0

    # Distance above loc
    t = x - loc
    # Gamma PDF formula
    return (
            (t ** (a - 1))
            * math.exp(-t / scale)
            / (math.gamma(a) * (scale ** a))
    )


#
#==============================================================================
# 6) Weibull maximum ("weibull_max"): parameters (c, loc, scale)
#    Domain: x in (-∞, loc], c>0, scale>0
#==============================================================================
def weibull_max_pdf_scalar(x, c, loc=0.0, scale=1.0):
    """
    PDF of Weibull_max(c), with location=loc, scale=scale, at scalar x.

    In SciPy, 'weibull_max' is the "reverse" of Weibull_min.
    Support is x <= loc.

    Standard form PDF (for y>=0):
      f_0(y) = c * y^(c-1) * exp(-y^c), y>=0

    Then X = loc - scale*Y => Y = (loc - x)/scale, (x <= loc).

    pdf(x) = (c/scale) * [ (loc - x)/scale ]^(c-1)
             * exp( - [ (loc - x)/scale ]^c ), for x <= loc; else 0
    """
    if c <= 0:
        raise ValueError("shape c must be positive for weibull_max.")
    if scale <= 0:
        raise ValueError("scale must be positive for weibull_max.")
    if x > loc:
        return 0.0
    y = (loc - x) / scale  # this is >= 0 if x <= loc
    return (c / scale) * (y ** (c - 1)) * math.exp(-(y ** c))


#
#==============================================================================
# 7) Beta distribution ("beta"): parameters (a, b, loc, scale)
#    Domain: x in [loc, loc+scale], a>0, b>0, scale>0
#==============================================================================
def beta_pdf_scalar(x, a, b, loc=0.0, scale=1.0):
    """
    PDF of Beta(a, b), shifted by loc, scaled by scale, at scalar x.

    Standard Beta(α, β) on [0,1]:
      f_0(y) = 1/B(a,b) * y^(a-1)*(1-y)^(b-1),  for 0 <= y <= 1

    After shift and scale => y = (x - loc)/scale in [0,1].
      pdf(x) = 1/scale * f_0( (x-loc)/scale )

    So:
      pdf(x) = 1/[scale * B(a,b)]
               * [ (x-loc)/scale ]^(a-1) * [ 1 - (x-loc)/scale ]^(b-1),
               for loc <= x <= loc+scale, else 0
    """
    if a <= 0 or b <= 0:
        raise ValueError("shape parameters a,b must be > 0 for Beta.")
    if scale <= 0:
        raise ValueError("scale must be positive for Beta.")
    if x < loc or x > loc + scale:
        return 0.0

    # y in [0,1]
    y = (x - loc) / scale
    denom = math.gamma(a) * math.gamma(b) / math.gamma(a + b)
    return (1.0 / (scale * denom)) * (y ** (a - 1)) * ((1 - y) ** (b - 1))


#
#==============================================================================
# 8) Lognormal distribution ("lognorm"): parameters (s, loc, scale)
#    Domain: x in (loc, ∞), s>0, scale>0
#==============================================================================
def lognorm_pdf_scalar(x, s, loc=0.0, scale=1.0):
    """
    PDF of Lognormal(s) with shift=loc, scale=scale, at scalar x.

    SciPy parameterization:
      If Y = ln(X - loc) ~ Normal(mean=ln(scale), std=s), X>loc
      Then pdf(x) = 1/[ (x-loc)*s*sqrt(2π) ]
                    * exp( - [ln((x-loc)/scale)]^2 / (2*s^2) ), for x>loc
      else 0
    """
    if s <= 0:
        raise ValueError("shape s must be positive for lognorm.")
    if scale <= 0:
        raise ValueError("scale must be positive for lognorm.")
    if x <= loc:
        return 0.0

    z = math.log((x - loc) / scale)
    return (1.0 / ((x - loc) * s * math.sqrt(2.0 * math.pi))) * math.exp(
        - (z * z) / (2.0 * s * s)
    )


#
#==============================================================================
# 9) Chi distribution ("chi"): parameters (df, loc, scale)
#    Domain: x in [loc, ∞), df>0, scale>0
#==============================================================================
def chi_pdf_scalar(x, df, loc=0.0, scale=1.0):
    """
    PDF of Chi(df), shifted by loc, scaled by scale, at scalar x.

    Standard Chi(k) pdf for y>0:
      f_0(y) = 2^(1 - k/2) / Gamma(k/2) * y^(k-1) * exp(-y^2/2)

    Then X = loc + scale*Y => pdf(x) = f_0((x-loc)/scale)/scale, for x>loc
    """
    if df <= 0:
        raise ValueError("df must be positive for chi distribution.")
    if scale <= 0:
        raise ValueError("scale must be positive for chi distribution.")
    if x < loc:
        return 0.0

    y = (x - loc) / scale
    c = (2.0 ** (1.0 - 0.5 * df)) / math.gamma(0.5 * df)
    return (1.0 / scale) * c * (y ** (df - 1.0)) * math.exp(-(y * y) / 2.0)


#
#==============================================================================
# 10) Chi-square distribution ("chi2"): parameters (df, loc, scale)
#     Domain: x in [loc, ∞), df>0, scale>0
#==============================================================================
def chi2_pdf_scalar(x, df, loc=0.0, scale=1.0):
    """
    PDF of Chi^2(df), shifted by loc, scaled by scale, at scalar x.

    Standard Chi^2(k) for y>0:
      f_0(y) = 1/[2^(k/2)*Gamma(k/2)] * y^(k/2 -1) * exp(-y/2)

    Then X = loc + scale*Y => pdf(x) = f_0((x-loc)/scale)/scale, for x>loc
    """
    if df <= 0:
        raise ValueError("df must be positive for chi2 distribution.")
    if scale <= 0:
        raise ValueError("scale must be positive for chi2 distribution.")
    if x < loc:
        return 0.0

    y = (x - loc) / scale
    c = 1.0 / (math.pow(2.0, 0.5 * df) * math.gamma(0.5 * df))
    return (1.0 / scale) * c * (y ** (0.5 * df - 1.0)) * math.exp(-0.5 * y)


#
#==============================================================================
# 11) Rayleigh distribution ("rayleigh"): parameters (loc, scale)
#     Domain: x in [loc, ∞), scale>0
#==============================================================================
def rayleigh_pdf_scalar(x, loc=0.0, scale=1.0):
    """
    PDF of Rayleigh(loc, scale) at scalar x.

    Standard Rayleigh (sigma=scale) for r>0:
      f_0(r) = (r / sigma^2) * exp(-r^2/(2 sigma^2))

    Then X=loc + r => pdf(x) = f_0(x-loc)/scale for x>loc
    More explicitly (s=scale):
      pdf(x) = (x-loc)/(s^2) * exp(-((x-loc)^2) / (2*s^2)), for x>=loc
    """
    if scale <= 0:
        raise ValueError("scale must be positive for Rayleigh.")
    if x < loc:
        return 0.0
    z = x - loc
    return (z / (scale * scale)) * math.exp(-0.5 * (z * z) / (scale * scale))


#
#==============================================================================
# 12) Pareto distribution ("pareto"): parameters (b, loc, scale)
#     Domain: x in [loc+scale, ∞), b>0, scale>0
#==============================================================================
def pareto_pdf_scalar(x, b, loc=0.0, scale=1.0):
    """
    PDF of Pareto(b), with loc and scale, at scalar x.

    In SciPy, 'pareto(b, loc, scale)' has support x >= loc + scale.

    Standard Pareto(b) for z>=1:
      f_0(z) = b z^(-b - 1)

    Then let z = (x - loc)/scale. The support means x >= loc + scale => z>=1.
      pdf(x) = (1/scale) * b z^(-b - 1), for z >= 1; else 0
              = b * scale^b / (x-loc)^(b+1), for x >= loc+scale.
    """
    if b <= 0:
        raise ValueError("shape b must be positive for Pareto.")
    if scale <= 0:
        raise ValueError("scale must be positive for Pareto.")
    # The condition x >= loc + scale => (x-loc)/scale >= 1
    if x < loc + scale:
        return 0.0

    z = (x - loc) / scale
    # pdf_0(z) = b * z^(-b - 1) for z>=1
    return (1.0 / scale) * b * (z ** (-b - 1))


#
#==============================================================================
# 13) Cauchy distribution ("cauchy"): parameters (loc, scale)
#     Domain: all real x, scale>0
#==============================================================================
def cauchy_pdf_scalar(x, loc=0.0, scale=1.0):
    """
    PDF of Cauchy(loc, scale) at scalar x.

    Standard Cauchy(0,1):
      f_0(t) = 1/(π * [1 + t^2])

    Then for shift loc, scale => t = (x-loc)/scale:
      pdf(x) = 1/(π*scale) * 1/[1 + ((x-loc)/scale)^2]
    """
    if scale <= 0:
        raise ValueError("scale must be positive for Cauchy.")
    z = (x - loc) / scale
    return 1.0 / (math.pi * scale * (1.0 + z * z))


#
#==============================================================================
# 14) Laplace distribution ("laplace"): parameters (loc, scale)
#     Domain: all real x, scale>0
#==============================================================================
def laplace_pdf_scalar(x, loc=0.0, scale=1.0):
    """
    PDF of Laplace(loc, scale) at scalar x.

    Standard Laplace(0, b):
      f_0(t) = 1/(2b) * exp( -|t|/b )

    With shift=loc, scale=b => t=(x-loc)/b
      pdf(x) = (1/(2*scale)) * exp( -|x-loc| / scale )
    """
    if scale <= 0:
        raise ValueError("scale must be positive for Laplace.")
    return (1.0 / (2.0 * scale)) * math.exp(-abs(x - loc) / scale)


#
#==============================================================================
# 15) F distribution ("f"): parameters (dfn, dfd, loc, scale)
#     Domain: x in [loc, ∞), dfn>0, dfd>0, scale>0
#==============================================================================
def f_pdf_scalar(x, dfn, dfd, loc=0.0, scale=1.0):
    """
    PDF of F(dfn, dfd), with shift=loc, scale=scale, at scalar x.

    Standard F(d1,d2) for y>0:
      f_0(y) = 1 / B(d1/2, d2/2)
               * (d1/d2)^(d1/2)
               * y^(d1/2 - 1)
               * [1 + (d1/d2)*y]^(-(d1+d2)/2)

    Then X = loc + scale*Y => pdf(x) = (1/scale)* f_0((x-loc)/scale), for x>loc.
    """
    if dfn <= 0 or dfd <= 0:
        raise ValueError("dfn, dfd must be positive for F distribution.")
    if scale <= 0:
        raise ValueError("scale must be positive for F distribution.")
    if x < loc:
        return 0.0

    y = (x - loc) / scale

    # standard F(dfn, dfd) pdf at y
    # factor = 1 / Beta(dfn/2, dfd/2)
    #        = 1 / [Gamma(dfn/2)*Gamma(dfd/2) / Gamma((dfn+dfd)/2)]
    # We'll piece it all together carefully
    from math import gamma

    beta_val = gamma(dfn / 2.0) * gamma(dfd / 2.0) / gamma((dfn + dfd) / 2.0)
    c = 1.0 / beta_val
    c *= (dfn / dfd) ** (dfn / 2.0)

    # y^(dfn/2 -1)
    # [1 + (dfn/dfd)* y ]^(-(dfn+dfd)/2)
    return (1.0 / scale) * c * (y ** (dfn / 2.0 - 1.0)) * (
            1.0 + (dfn / dfd) * y
    ) ** (-(dfn + dfd) / 2.0)
