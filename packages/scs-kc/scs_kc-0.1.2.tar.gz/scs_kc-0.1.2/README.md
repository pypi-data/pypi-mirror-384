# Supercoefficients for Kerr-cat

This project is a python package that demonstrates supercoefficient approach for the analysis of the 
parametrically driven single-degree-of-freedom circuits, based on the theory presented 
in the paper [**"Exact amplitudes of parametric processes in driven Josephson circuits"**](https://arxiv.org/abs/2501.07784).

Supercoefficent approach allows to calculate the amplitudes of various parametric processes present
in a circuit Hamiltonian. the bookkeeping is made systematic by coefficients which appropriately
keep track of the order of each parametric process. The main advantage of the approach that it is
agnostic to the system Hamiltonian, reminiscent to a Taylor series of a function:

$$
\hat{{H}}=\omega_0\hat{a}^\dagger\hat{a}+\sum\limits_{ n,l,p=0}{C}_{nl,p}(\hat{a}^{\dagger n}\hat{a}^{n+l}+\hat{a}^{\dagger n+l}\hat{a}^{n})(e^{ip(\omega_d{t}{+}\gamma)}+e^{-ip(\omega_d{t}{+}\gamma)})
$$

The concrete coeffcients, $C_{nl,p}$, contain comprehensive information about the circuit and make it easier to distinguish 
and track how different properties—such as drive power, circuit topology, and zero-point fluctuations—contribute 
to the various parametric processes.



# installation instructions

The project requires the following packages:

- numpy (mandatory)
- sympy (mandatory)
- scipy (mandatory)
- swg (Schrieffer-Wolff procedure generator which is currently under the development and distributed as a wheel only. Downloadadle from https://dl.cloudsmith.io/public/cs-x033/swg/python/simple/)
- [ninatool](https://github.com/sandromiano/ninatool)
- jupyter (for examples)
- matplotlib (for examples)


To install project, execute "pip install -r requirements.txt" in the package directory.

The package could be rebuilt locally with "python -m build" and installed with pip from dist directory 
but still requires "pip install swg --index-url https://dl.cloudsmith.io/public/cs-x033/swg/python/simple/" before swg package is made public.

# Examples

You can start exploring project's functionality by running the .ipynb files in 'examples'. The examples include:

- General guide for the optimization of circuit designs (example for a Kerr-cat).
- Full scale simulation to benchmark the Kerr-cat circuit designs for the case of SNAIL- and SQUID-based driven circuits
- Agnostic Schrieffer-Wolff procedure for the case of multiple drives in single-degree-of-freedom circuits.

# citing 

If you use the project for your research, please cite [**this article**](https://arxiv.org/abs/2501.07784).

# contacts

For inquiries, comments, suggestions etc. you can contact the authors at **supercoefficients@gmail.com**.

# acknowledgements

The project uses some functionality from [ninatool](https://github.com/sandromiano/ninatool) repo. The main functionality of NINA is 
to compute the Taylor expansion coefficient of the effective potential energy function of an arbitrary flux-biased 
superconducting loop. The loop can host any combination of Josephson junctions (JJs) and linear inductances. NINA can also
 compute the Hamiltonian series expansion of an arbitrary Josephson nonlinear oscillator (limited for now to a single mode).

