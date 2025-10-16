# Hestia Data Utils

Utils library to manipulate distributions on the Hestia platform

## Install

1. `pip install hestia_earth.distribution`
2. Optional: to generate distribution files, please install [pymc 4](https://pypi.org/project/pymc/).

## Usage

By default, all output files will be stored under _./data_ folder.
You can set the env variable `DISTRIBUTION_DATA_FOLDER` to store in a different folder.

### To get univariate posterior distribution:
```python
from hestia_earth.distribution.posterior_yield import get_post_ensemble, get_post

# get a single posterior distribution, run:
mu_ensemble, sd_ensemble = get_post_ensemble('GADM-GBR', 'wheatGrain')

# Or, if only instrested in the mean of the mu and sd values, run:
mu, sd = get_post('GADM-GBR', 'wheatGrain')
```

### To calculate the probability of a set of values using bivariate distribution:
```python
from hestia_earth.distribution.utils.MCMC_bivariate import calculate_fit_2d

# get the likelihood of a candidate based on the bivariate distribution between Grain
# yield and Nitrogen fertiliser usage of a given country and a given product, run:
yield_value = 8500
n_use = 200
likelihood = calculate_fit_2d([n_use, yield_value], 'GADM-GBR', 'wheatGrain')
```

## Advance Usage

You can clone this repository to use the commands below.

### Generate prior distribution

To generate yield prior file for all products:
```
python generate_prior_yield.py --overwrite
```

For more information, run `python generate_prior_yield.py --help`.

### Generate likelihood data

In order to generate likelihood data (a spreadsheet of crop yield and fertiliser data) for a specific product and a specific country, run:
```
python generate_likelihood.py --product-id="wheatGrain" --country-id="GADM-GBR" --limit=1000
```

For more information, run `python generate_likelihood.py --help`.

### Generate posterior distribution

* In order to generate posterior distribution (for Bayesian statistics) for a specific country, run:
```
python generate_posterior_yield.py --country-id="GADM-GBR"
```

or to generate the fertiliser usage:
```
python generate_posterior_fert.py --country-id="GADM-GBR"
```

or to generate the pesticide usage:
```
python generate_posterior_pest.py --country-id="GADM-GBR"
```

Note: all commands above will update the same CSV file so they must not be run **at the same time**.


### Generate multivariate distribution

* In order to generate multivariate distribution (between yield and N, P, K fetiliser inputs) for a specific country and product, run:
```
python generate_MCMC_mv.py --country-id="GADM-GBR" --product-id="wheatGrain" --sample-size=10
```

### Plotting

#### Prior Yield

To plot prior distribution by product by country:

```
python plot_prior_yield.py --country-id='GADM-GBR' --product-id='wheatGrain' --output-file='prior.png'
```

To plot FAO annual yield data, change `--type` parameter to one of the four options: `fao_per_country`, `fao_per_product`, `fao_per_country_per_product`, `world_mu_signma`. Example:
```
python plot_prior_yield.py --country-id='GADM-GBR' --output-file='fao-yield-gbr-allProducts.png' --type='fao_per_country'
```

For more information, run `python plot_prior_yield.py --help`.

#### Cycle Yield

To plot the bivariate distribution of yield data for [Wheat, grain](https://hestia.earth/term/wheatGrain) in [United Kingdom](https://hestia.earth/term/GADM-GBR):

```
python plot_cycle_yield.py --product-id=wheatGrain" --country-id="GADM-GBR" --limit=100
```

This will take a sample size of `100` and create a `result.png` file with the distribution.

For more information, run `python plot_cycle_yield.py --help`.

#### Posterior Yield

In order to plot the posterior distribution for a specific product and a specific country, run:
```
python plot_posterior_yield.py --country-id="GADM-GBR" --product-id="wheatGrain" --output-file="post.png"
```

For more information, run `python plot_posterior_yield.py --help`.

#### Plot bivariate distribution between Yield and fetiliser use

In order to plot the bivariate distribution between Yield and N, P or K fetiliser use for a specific product and a specific country, run:
```
python plot_MCMC_bivariate.py --y=8500 --n=200 --country-id='GADM-GBR' --product-id='wheatGrain' --output='gbr-yield-vs-nitrogen.png'
```

Or

```
python plot_MCMC_mv.py --y=8500 --n=200 --p=50 --k=50  --pest=5  --country-id='GADM-GBR' --product-id='wheatGrain' --output='gbr-yield-vs-nitrogen-on-demand.png'
```

Or

```
python plot_MCMC_mv.py --y=8500 --n=200 --p=50 --k=50  --country-id='GADM-GBR' --product-id='wheatGrain' --output='gbr-yield-vs-nitrogen-static.png'
```

For more information, run `python plot_MCMC_bivariate.py --help`.
