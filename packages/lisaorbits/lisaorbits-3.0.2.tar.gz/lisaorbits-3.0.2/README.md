# LISA Orbits

LISA Orbits is a Python package which generates orbit files compatible with [LISA Instrument](https://gitlab.in2p3.fr/lisa-simulation/instrument), [LISA GW Response](https://gitlab.in2p3.fr/lisa-simulation/orbits), the [LDC Software](https://lisa-ldc.lal.in2p3.fr/code), and [LISANode](https://gitlab.in2p3.fr/j2b.bayle/LISANode). Among others, an orbit file contains the spacecraft state vectors, the light travel times and the proper pseudoranges.

## Contributing

### Report an issue

We use the issue-tracking management system associated with the project provided by Gitlab. If you want to report a bug or request a feature, open an issue at <https://gitlab.in2p3.fr/lisa-simulation/orbits/-/issues>. You may also thumb-up or comment on existing issues.

### Development environment

We strongly recommend to use [Python virtual environments](https://docs.python.org/3/tutorial/venv.html).

To setup the development environment, use the following commands:

```shell
git clone git@gitlab.in2p3.fr:lisa-simulation/orbits.git
cd orbits
poetry install
poetry shell
```

### Workflow

The project's development workflow is based on the issue-tracking system provided by Gitlab, as well as peer-reviewed merge requests. This ensures high-quality standards.

Issues are solved by creating branches and opening merge requests. Only the assignee of the related issue and merge request can push commits on the branch. Once all the changes have been pushed, the "draft" specifier on the merge request is removed, and the merge request is assigned to a reviewer. He can push new changes to the branch, or request changes to the original author by re-assigning the merge request to them. When the merge request is accepted, the branch is merged onto master, deleted, and the associated issue is closed.

### Pylint and unittest

We enforce [PEP 8 (Style Guide for Python Code)](https://www.python.org/dev/peps/pep-0008/) with Pylint syntax checking, and correction of the code using the pytest testing framework. Both are implemented in the continuous integration system.

You can run them locally

```shell
pylint lisaorbits/*.py
python -m pytest
```

## Use policy

The project is distributed under the 3-Clause BSD open-source license to foster open science in our community and share common tools. Please keep in mind that developing and maintaining such a tool takes time and effort. Therefore, we kindly ask you to

* Cite the DOI (see badge above) in any publication
* Acknowledge the authors (below)
* Acknowledge the LISA Simulation Expert Group in any publication

Do not hesitate to send an email to the authors for support. We always appreciate being associated with research projects.

## Authors

* Jean-Baptiste Bayle (<j2b.bayle@gmail.com>)
* Aurélien Hees (<aurelien.hees@obspm.fr>)
* Marc Lilley (<marc.lilley@obspm.fr>)
* Christophe Le Poncin-Lafitte (<christophe.leponcin@obspm.fr>)
* Waldemar Martens (<waldemar.martens@esa.int>)
* Eric Joffre (<eric.joffre@esa.int>)

## Acknowledgements

ESA numerically-optimized orbit files are retreived from the official [ESA Github repository](https://github.com/esa/lisa-orbit-files). They are distributed under the [Creative Commons Attribution 4.0 International license](https://github.com/esa/lisa-orbit-files/blob/main/LICENSE), which permits almost any use subject to providing credit and license notice. Refer to the repository documentation for more information.

* Martens, W., Joffre, E. *Trajectory Design for the ESA LISA Mission*. J Astronaut Sci 68, 402–443 (2021). [arXiv:2101.03040](https://arxiv.org/abs/2101.03040).
