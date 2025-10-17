
# Density PDF 
Evaluation of univariate density functions defined in the `density` package.


## Install

    pip install densitypdf 


## Usage 

    from densitypdf import density_pdf

    # Example mixture with one scipy normal and one builtin normal

    mixture_spec = {
        "type": "mixture",
        "components": [
            {
                "density": {
                    "type": "scipy",
                    "name": "norm",
                    "params": {"loc": 0, "scale": 1}
                },
                "weight": 0.6
            },
            {
                "density": {
                    "type": "builtin",
                    "name": "norm",
                    "params": {"loc": 2.0, "scale": 1.0}
                },
                "weight": 0.4
            }
        ]
    }

    val = density_pdf(mixture_spec, x=0.0)

The `builtin` options are replacements for scipy.stats distributions should you wish to use them. 

## Specifying densities or mixtures of the same
One is limited to a finite set of continuous distributions, and mixtures of the same. 

See [examples](https://github.com/microprediction/density/tree/main/examples) of specifying densities. 

See the [Scipy manifest](https://github.com/microprediction/density/blob/main/density/schemachecker/scipydensitymanifest.py) for a list of densities. 

