import jax.numpy as jnp # jax's numpy library we will use for all general mathematical operations
from jax.random import split, normal, choice, PRNGKey  # Importing random functions from JAX: PRNGKey for random number generator key, split for splitting keys, normal for normal distribution, and choice for random sampling
from jax.typing import ArrayLike # JAX type hint for array-like objects (supports numpy, JAX arrays, etc.)
from typing import List, Text, Union

from .tmm import tmm

def generate_random_deviated_thicknesses(key: ArrayLike, 
                                         thicknesses: ArrayLike, 
                                         thickness_deviation_list: ArrayLike, 
                                         sensitivity_analysis_sample_num: Union[int, ArrayLike]):
    """
    This function generates a list of deposition thicknesses considering a random deviations from the target thicknesses.
    The deviations are applied within a specified percentage range, and the generated thickness samples are meant for 
    sensitivity optimization in multilayer thin film deposition processes. The function introduces a random deviation 
    in both positive and negative directions for each given thickness value and produces multiple samples based on 
    the specified number (sensitivity_analysis_sample_num).

    Arguments:
        - key (jax.Array): The random key to initialize the random number generation.
        - thicknesses (jax.Array):A 1D array of desired target thickness values for each layer in the thin film.
        - sensitivity_analysis_sample_num (jax.Array): The percentage by which the deposition thicknesses can deviate
            from the target (both positive and negative).
        - sensitivity_analysis_sample_num: (int or jax.Array): The number of deposition thickness samples to generate for 
            sensitivity optimization.

    Return:
        - deviated_samples (jax.Array): A 2D array with shape (sensitivity_analysis_sample_num, len(thicknesses)), 
            where each row corresponds to a set of deposition thicknesses considering the random deviations.
    """
    
    # Split the key for subkey generation to ensure random operations are independent
    key, _ = split(key)
    
    # Generate random deviation samples following a normal distribution. Each deviation is for each thickness value.
    deviation_samples = normal(key, (sensitivity_analysis_sample_num, len(thicknesses)))
    
    # Normalize the deviation samples to the range [0, 1]
    normalized_deviation_samples = (deviation_samples - jnp.min(deviation_samples)) / (jnp.max(deviation_samples) - jnp.min(deviation_samples))
    
    # Generate new subkey to ensure randomness for the next operation
    key, _ = split(key)
    
    # Randomly choose whether the deviation is positive (+1) or negative (-1)
    over_or_under_deposition = choice(key, a=jnp.array([-1, 1]), shape=(sensitivity_analysis_sample_num, len(thicknesses)))
    
    # Calculate the ratio matrix by combining normalized deviations with the direction of deviation and the percentage
    ratio_matrix = 1 + (normalized_deviation_samples * over_or_under_deposition * (thickness_deviation_list/100))
    ratio_matrix = ratio_matrix.at[0,:].set(jnp.ones(len(thicknesses)))

    # Multiply the ratio matrix by the thickness values to generate the final deposition samples
    deviated_samples = ratio_matrix * thicknesses
    
    # Return the final generated deposition samples
    return deviated_samples

def thickness_sensitivity(material_list: List[str],
                          thickness_list: ArrayLike,
                          thickness_deviation_list: ArrayLike,
                          wavelength_arr: ArrayLike,
                          angle_of_incidences: ArrayLike,
                          coherency_list: ArrayLike = None,
                          polarization: Text = 's',
                          sensitivity_analysis_sample_num: Union[int, ArrayLike] = 20,
                          seed: int = 1903):
    """
    Quantifies the sensitivity of the optical response of a multilayer thin-film stack 
    to random deviations in layer thicknesses using the Transfer Matrix Method (TMM).

    This function simulates the impact of thickness variation by introducing stochastic
    perturbations to the nominal thicknesses, then computing the average absolute 
    deviation in reflectance and transmittance across several random samples.

    Parameters
    ----------
    material_list : List[str]
        A list of material names defining the layer sequence from incident medium to substrate.
    
    thickness_list : ArrayLike
        An array specifying the nominal thickness (in nanometers or micrometers) of each layer.

    thickness_deviation_list : ArrayLike
        An array of the same length as `thickness_list`, specifying the standard deviation 
        or maximum deviation allowed for each layer’s thickness during perturbation.

    wavelength_arr : ArrayLike
        A 1D array of wavelengths (in the same unit as used in the optical constants) 
        over which the sensitivity analysis is to be performed.

    angle_of_incidences : ArrayLike
        A 1D array of incidence angles (in degrees or radians) to be evaluated.

    coherency_list : ArrayLike, optional
        Specifies which layers are optically coherent or incoherent. If None, 
        all layers are assumed to be coherent.

    polarization : Text, optional
        Type of polarization for the incoming wave. Must be 's' for s-polarized 
        or 'p' for p-polarized light. Default is 's'.

    sensitivity_analysis_sample_num : Union[int, ArrayLike], optional
        Number of samples to generate for the thickness deviation analysis. 
        Default is 20.

    seed : int, optional
        Random seed used for reproducibility in sampling thickness perturbations. 
        Default is 1903.

    Returns
    -------
    R_deviation : Array
        The average absolute deviation in reflectance due to the thickness perturbations.

    T_deviation : Array
        The average absolute deviation in transmittance due to the thickness perturbations.
    """

    # Initialize random key for reproducible sampling using JAX's PRNG.
    key = PRNGKey(seed)

    # Generate multiple perturbed thickness profiles by applying controlled random noise
    # to the nominal thicknesses, respecting each layer's specified deviation.
    deviated_samples = generate_random_deviated_thicknesses(
        key=key, 
        thicknesses=thickness_list, 
        thickness_deviation_list=thickness_deviation_list, 
        sensitivity_analysis_sample_num=sensitivity_analysis_sample_num
    )

    # Compute the baseline (ground truth) reflectance and transmittance
    # using the nominal thickness values.
    R_gtruth, T_truth = tmm(
        material_list=material_list,
        thickness_list=thickness_list,
        wavelength_arr=wavelength_arr,
        angle_of_incidences=angle_of_incidences,
        coherency_list=coherency_list,
        polarization=polarization
    )

    # Initialize cumulative deviation arrays with zeros.
    R_deviation = jnp.zeros_like(R_gtruth)
    T_deviation = jnp.zeros_like(T_truth)

    # Loop over the generated perturbed samples to assess the sensitivity
    for i in range(sensitivity_analysis_sample_num):
        # Compute reflectance and transmittance for the current perturbed sample.
        R_sample, T_sample = tmm(
            material_list=material_list,
            thickness_list=deviated_samples.at[i].get(),
            wavelength_arr=wavelength_arr,
            angle_of_incidences=angle_of_incidences,
            coherency_list=coherency_list,
            polarization=polarization
        )

        # Accumulate the absolute deviations from the ground truth.
        R_deviation += jnp.abs(R_gtruth - R_sample)
        T_deviation += jnp.abs(T_truth - T_sample)

    # Normalize the cumulative deviations to compute the average over all samples.
    R_deviation = jnp.true_divide(R_deviation, sensitivity_analysis_sample_num)
    T_deviation = jnp.true_divide(T_deviation, sensitivity_analysis_sample_num)

    # Return the averaged reflectance and transmittance deviations.
    return R_deviation, T_deviation