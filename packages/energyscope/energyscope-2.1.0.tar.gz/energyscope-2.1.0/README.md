# EnergyScope Library

## Overview

This library is part of the EnergyScope project, designed for energy system modeling and analysis. It includes the following core functionalities:

1.  **Model Setup and Documentation**: A set of energy models tailored to specific scenarios, along with comprehensive documentation.
2.  **Pre-Calculation**: Tools for preparing and processing input data.
3.  **Model Solving**: Optimization tools for running simulations based on the pre-calculated input.
4.  **KPI Calculation and Plotting**: Tools to compute Key Performance Indicators (KPIs) and visualize results.

For more detailed information, please refer to the full [documentation](https://library.energyscope.ch).

------------------------------------------------------------------------

## Installation

For detailed installation instructions, please refer to the [Getting Started Guide](https://library.energyscope.ch).

To install the EnergyScope library, use the following command:

``` bash
pip install energyscope
```

Alternatively, you may clone the repository and install the package manually:

``` bash
git clone <repo-url>
cd <project-directory>
pip install .
```

------------------------------------------------------------------------

## Acknowledging Authorship

In the academic spirit of collaboration, please acknowledge the authorship of this library in any scientific dissemination. Cite the EnergyScope project as follows:

-   For reference to the origins of the EnergyScope project or the first online version, cite \[2\].
-   For the EnergyScope MILP framework, cite \[2\].
-   For Typical Day version, cite \[3\].
-   For the carbon flows model, cite \[4\]
-   For the mobility framework, cite \[5\] & \[6\]
-   For the transition pathway models, cite \[7\] (Belgium) and \[8\] (Switzerland)
-   For the multicell model, cite \[9\]
-   For the non-energy demand integration, cite \[10\]
-   For the infrastructure model, cite \[11\]
-   For the decentralization model, cite \[12\]
-   For the LCA model, cite \[13\]

The **main contributors** includes:

-   [Stefano Moret](mailto:morets@ethz.ch) (EnergyScope Creator)
-   [Gauthier Limpens](mailto:gauthier.limpens@uclouvain.be) (EnergyScope Improver)
-   [Jonas Schnidrig](mailto:jonas.schnidrig@hevs.ch) (Library, Plotting, Documentation, Development)
-   [Xavier Rixhon](mailto:xavier.rixhon@uclouvain.be) (EnergyScope Developer, Documentation)
-   [Arthur Chuat](mailto:arthur.chuat@epfl.ch) (Library, Plotting, Documentation, Development)
-   [Gabriel Wiest](mailto:gwiest@ethz.ch) (Library, Plotting, Documentation, Development)
-   [Cyrille Platteau](mailto:cyrille.platteau@epfl.ch) (IT)

Refer to the [Releases file](./Releases.rst) for additional contributors and acknowledgments.

------------------------------------------------------------------------

## Documentation

Full documentation, including a model overview, releases, publications, model formulation, data sources, and exercises, can be found at [library.energyscope.ch](https://library.energyscope.ch).

------------------------------------------------------------------------

## Bug Reporting and Support

-   For bug reports or feature requests, please use the GitLab issue tracker.
-   For general inquiries or simple questions, join our [Discourse forum](https://forum.energyscope.net/).

------------------------------------------------------------------------

## Release Process

To release a new version of the library, follow these steps:

1.  Ensure that the pipeline on the `main` branch is successful.
2.  Update the version of the library in the file `src/energyscope/__init__.py` on the `main` branch:
    -   For a bug fix, increase the digit on the right (e.g., from `0.4.1` to `0.4.2`).
    -   For new features, increase the middle digit and reset the bug fix digit (e.g., from `0.4.1` to `0.5.0`).
    -   For a major release or breaking changes, increase the digit on the left and reset the others (e.g., from `0.4.1` to `1.0.0`).
3.  [Create a tag](https://www.gitlab.com/energyscope/energyscope/-/tags) `vx.y.z` from the `main` branch:
    -   The tag should be a `v` followed by the version `x.y.z`, matching the version specified earlier.
    -   Example tags: `v0.4.2`, `v0.5.0`, or `v1.0.0`, based on the previous versioning examples.

------------------------------------------------------------------------

## References

\[1\] V. Codina Gironès, S. Moret, F. Maréchal, D. Favrat
(2015). Strategic energy planning for large-scale energy systems: A
modelling framework to aid decision-making. Energy, 90(PA1), 173–186. <https://doi.org/10.1016/j.energy.2015.06.008>

\[2\] S. Moret, M. Bierlaire, F. Maréchal (2016). Strategic
Energy Planning under Uncertainty: a Mixed-Integer Linear Programming
Modeling Framework for Large-Scale Energy Systems. <https://doi.org/10.1016/B978-0-444-63428-3.50321-0>

\[3\] G. Limpens, S . Moret, H. Jeanmart, F. Maréchal (2019). EnergyScope TD:
a novel open-source model for regional energy systems and its
application to the case of Switzerland. <https://doi.org/10.1016/j.apenergy.2019.113729>

\[4\] X. Li, T. Damartzis, Z. Stadler, S. Moeret, B. Meier, M. Friedli, F. Maréchal (2020). Decarbonization in Complex Energy Systems: A Study on the Feasibility of Carbon Neutrality for Switzerland in 2050. Front. Energy Res. Volume 8, <https://doi.org/10.3389/fenrg.2020.549615>

\[5\] J. Schnidrig, T.-V. Nguyen, X. Li, F. Maréchal (2021). A modelling framework for assessing the impact of green mobility technologies on energy systems. ECOS <https://infoscience.epfl.ch/entities/publication/d521fe41-b873-46da-b4b3-8d31938d3df5>

\[6\] T.-V. Nguyen, J. Schnidrig, An analysis of the impacts of green mobility strategies and technologies on different European energy system F. Maréchal (2021). https://infoscience.epfl.ch/entities/publication/bf57ffc4-51fb-4f31-822c-ee51ceb79e39

\[7\] Limpens, G., Rixhon, X., Contino, F., & Jeanmart, H. (2024). EnergyScope Pathway: An open-source model to optimise the energy transition pathways of a regional whole-energy system. Applied Energy, 358, 122501, https://doi.org/10.1016/j.apenergy.2023.122501.

\[8\] X. Li, J. Schnidrig, M. Souttre, F. Maréchal (2022). A dynamic methodology for analyzing energy transitional pathways. IEEE PESGM <https://doi.org/10.1109/PESGM48719.2022.9916902>

\[9\] J. Schnidrig, X. Li, A. Slaymaker, T.-V. Nguyen, F. Maréchal (2022). Regionalisation in high share renewable energy system modelling. IEEE PESGM <https://doi.org/10.1109/PESGM48719.2022.9917062>

\[10\] X. Rixhon, D. Tonelli, M. Colla, K. Verleysen, G. Limpens, H. Jeanmart, F. Contino (2022). Integration of non-energy among the end-use demands of bottom-up whole-energy system models. Front. Energy Res. Volume 10. <https://doi.org/10.3389/fenrg.2022.904777>

\[11\] J. Schnidrig, R. Cherkaoui, Y. Calisesi, M. Margni, F. Maréchal (2023). On the role of energy infrastructure in the energy transition. Case study of an energy independent and CO2 neutral energy system for Switzerland. Front. Energy Res. Volume 11, <https://doi.org/10.3389/fenrg.2023.1164813>

\[12\]  J. Schnidrig*, M. Souttre*, A. Chuat*, F. Maréchal, M. Margni (2023). Between Green Hills and Green Bills: Unveiling the Green Shades of Sustainability and Burden Shifting through Multi-Objective Optimization in Swiss Energy System Planning, JEMA, <https://arxiv.org/abs/2402.12973>

\[13\] J. Schnidrig, A. Chuat, C. Terrier, F. Maréchal, M. Margni (2024). Power to the People: On the Role of Districts in Decentralized Energy Systems. Energies, Vol 17, Issue 7. <https://www.mdpi.com/1996-1073/17/7/1718#>
