# mgktools
Python Package using marginalized graph kernel (MGK) to predict molecular properties.

## Installation
Suggested Package Versions:
Python>=3.9, GCC==11.2, CUDA==11.7.
```
pip install git+https://gitlab.com/Xiangyan93/graphdot.git@feature/xy
pip install mgktools
```

## QuickStart with Google Colab
GPU is required to compute graph kernel. 
- [Interpretability Marginalized Graph Kernel](https://colab.research.google.com/drive/1Z6tx4_3FBhZB9SwOvxex9jIP-XZ40hi9?usp=sharing)

## Hyperparameters
[hyperparameters](https://github.com/Xiangyan93/mgktools/tree/main/mgktools/hyperparameters) contains the JSON files that
define the hyperparameters for MGK.

## Related work
* [Predicting Single-Substance Phase Diagrams: A Kernel Approach on Graph Representations of Molecules](https://pubs.acs.org/doi/full/10.1021/acs.jpca.1c02391)
* [A Comparative Study of Marginalized Graph Kernel and Message-Passing Neural Network](https://pubs.acs.org/doi/full/10.1021/acs.jcim.1c01118)
* [Interpretable Molecular Property Predictions Using Marginalized Graph Kernels](https://pubs.acs.org/doi/full/10.1021/acs.jcim.3c00396)
