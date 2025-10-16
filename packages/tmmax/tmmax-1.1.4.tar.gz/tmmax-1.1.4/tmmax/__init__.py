"""TMMax: High-performance modeling of multilayer thin-film structures using transfer matrix method with JAX"""

__version__ = "1.1.4"

description = "tmmax is a high-performance computational library designed for efficient calculation of optical properties in multilayer thin-film structures. Engineered to serve as a Swiss Army knife tool for thin-film optics research, tmmax integrates a comprehensive suite of advanced numerical methods. At its core, tmmax leverages JAX to enable just-in-time (JIT) compilation, vectorization and XLA (Accelerated Linear Algebra) operations, dramatically accelerating the evaluation of optical responses in multilayer coatings. By exploiting these capabilities, tmmax achieves exceptional computational speed, making it the optimal choice for modeling and analyzing complex systems."

from os import path
nk_data_dir = path.join(path.dirname(__file__), 'nk_data')