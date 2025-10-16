# Electrolyte Machine

`Sea Urchin` is a set of Python tools to post-process trajectories from AIMD, MD and metadynamics simulations to extract and analyze local structure around atomic species. The outcome of the algorithm is a quantitative mapping of the multiple coordination environments present in the MD data.

Details on the `Sea Urchin` algorithm are presented in the paper:

Roncoroni, F., Sanz-Matias, A., Sundararaman, S., & Prendergast, D. **Unsupervised learning of representative local atomic arrangements in molecular dynamics data**. Phys. Chem. Chem. Phys., 25, 13741-13754 (2023) (https://doi.org/10.1039/D3CP00525A);
arXiv preprint [arXiv:2302.01465](https://arxiv.org/abs/2302.01465).

Applications of the `Sea Urchin` algorithm:

Sanz-Matias, A., Roncoroni, F., Sundararaman, S., & Prendergast, D. **Ca-dimers, solvent layering, and dominant electrochemically active species in Ca(BH$_4$)$_2$ in THF** Nature Communications 15, 1397 (2024) (https://doi.org/10.1038/s41467-024-45672-7)
arXiv preprint [https://arxiv.org/pdf/2303.08261]

-------

## Requirements

Check the file [requirements.txt](requirements.txt) to see which packages are needed. Installing the package using `pip` should already take care of all dependencies.

## Installation

### Basic Installation

The easiest way to install `sea_urchin` is using pip:

```bash
pip install sea_urchin
```

This will install the package with all core dependencies needed for basic functionality.

### Python Environment Setup (Recommended)

For a clean installation, we recommend creating a dedicated Python environment:

```bash
# Using conda
conda create -n sea_urchin python=3.11
conda activate sea_urchin
pip install sea_urchin

# Using venv
python -m venv sea_urchin_env
source sea_urchin_env/bin/activate  # On Windows: sea_urchin_env\Scripts\activate
pip install sea_urchin
```

### Development Installation

For development or to get the latest features from the repository:

```bash
git clone git@gitlab.com:electrolyte-machine/sea_urchin.git
cd sea_urchin
pip install -e .
```


### Manual Dependency Installation (Alternative)

If you prefer to manage dependencies manually:

```bash
git clone git@gitlab.com:electrolyte-machine/sea_urchin.git
cd sea_urchin
conda install -c conda-forge --file requirements.txt
pip install -e .
```

**Note**: GitLab uses SSH for access. You'll need to set up a public key through your GitLab account as described [here](https://docs.gitlab.com/ee/user/ssh.html).

### Use alignment and clustering algorithm

To use the clustering algorithm and perform alignment of structures, you will need to install and compile some optional additional packages.

#### Fastoverlap

The original repository developed by M. Griffiths can be found on GitHub. Here, we will use a tweaked forked repository so that it is compatible with newer Python versions and with the alignment routines defined in the `sea_urchin`. The package can be found at [https://gitlab.com/roncofaber/fastoverlap](https://gitlab.com/roncofaber/fastoverlap).

**Attention**: If you want to use `FASTOVERLAP`, you will need to follow those instructions:

- Install `fftw` and `lapack`, e.g.: `conda install -c conda-forge fftw lapack`
- Compile the fortran modules (not strictly necessary, but suggested):

    ```bash
    git clone https://gitlab.com/roncofaber/fastoverlap
    cd fastoverlap/
    python setup.py build_ext -i
    ```

- Add package to Python path:

    ```bash
    conda develop .
    ```

- Occasionally, if you update the conda environment stuff might break and you will have to rebuild the Fortran modules with `python setup.py build_ext -i`. You can always check if `FASTOVERLAP` can be run using Fortran by doing:
  
    ```python
    import fastoverlap
    fastoverlap.f90.have_fortran
    ```

    If the answer is `False`, try reinstalling the Python `fftw` implementation with: `conda install -c conda-forge fftw` and proceeding again with `python setup.py build_ext -i`. The Fortran implementation is not strictly necessary, but improves the alignment performance a lot.

#### IterativeRotationsAssignments

Iterative Rotations and Assignments (IRA) is a shape matching algorithm that can be found at: [https://github.com/mammasmias/IterativeRotationsAssignments](https://github.com/mammasmias/IterativeRotationsAssignments)

Visit the links above for details about its installation. To add the package to your Python path, do the following with your conda environment activated:

```bash
cd IterativeRotationsAssignments/interface
conda develop .
```

## Usage - tutorial

A tutorial to introduce how to use the `Sea Urchin` for trajectory post-processing and structure clustering can be found in the folder [sea_urchin/tutorial](sea_urchin/tutorial). For the scope of the tutorial you will need to download some additional files that you can find [here](https://drive.google.com/drive/folders/1H-RVB34yQd6fisYsTVMr-6ANG1ogiA2l?usp). Download them (unzip if you downloaded as a zip) and change the path of the Jupyter Notebook accordingly to point to the folder.

### Jupyter Notebooks - Open on demand

To use the `sea_urchin` functionalities within the *lrc-ondemand* service, follow those steps:

1) Load the precompiled environment on your terminal (connected to the hpc-cluster):

    ```bash
    module load python/3.7
    source activate /global/home/groups/nano/share/software/electrolyte_machine/conda_environment/elemac 
    ```

2) Install the IPython kernels:

    ```bash
    python -m ipykernel install --user --name=elemac
    ```

3) Connect to a Jupyter Notebook through: https://lrc-ondemand.lbl.gov/ &rarr; interactive apps &rarr; Jupyter Notebook &rarr; compute mode ..... 

4) Open a new notebook, make sure to select the `elemac` kernel.

You are ready to go! To start, check the Jupyter Notebook in [sea_urchin/tutorial](sea_urchin/tutorial). 

## Contact

Feel free to create Merge Requests and Issues on our GitLab page: [https://gitlab.com/electrolyte-machine/sea_urchin](https://gitlab.com/electrolyte-machine/sea_urchin).

If you want to contact the authors, please write to D. Prendergast at <dgprendergast@lbl.gov>.

## References

If you use this code please cite the paper:

**Sea Urchin**

Roncoroni, F., Sanz-Matias, A., Sundararaman, S., & Prendergast, D. **Unsupervised learning of representative local atomic arrangements in molecular dynamics data**. <i>Phys. Chem. Chem. Phys.</i>, 25, 13741-13754 (2023). doi:[10.1039/D3CP00525A](https://doi.org/10.1039/D3CP00525A);

Additionally, if you use any of the packages the `Sea Urchin` relies on, please cite their work accordingly. Notably:

**ASE**

Hjorth Larsen, A., JØrgen Mortensen, J., Blomqvist, J., Castelli, I. E., Christensen, R., Dułak, M., Friis, J., Groves, M. N., Hammer, B., Hargus, C., Hermes, E. D., Jennings, P. C., Bjerre Jensen, P., Kermode, J., Kitchin, J. R., Leonhard Kolsbjerg, E., Kubal, J., Kaasbjerg, K., Lysgaard, S., … Jacobsen, K. W. (2017). **The atomic simulation environment - a Python library for working with atoms**. <i>Journal of Physics: Condensed Matter</i>, <i>29</i>(27), 273002. doi:[10.1088/1361-648X/AA680E](https://doi.org/10.1088/1361-648X/AA680E)

**FASTOVERLAP**

Griffiths, M., Niblett, S. P., & Wales, D. J. (2017). **Optimal Alignment of Structures for Finite and Periodic Systems**. <i>Journal of Chemical Theory and Computation</i>, <i>13</i>(10), 4914–4931. doi:[10.1021/acs.jctc.7b00543](http://dx.doi.org/10.1021/acs.jctc.7b00543)

**IRA**

Gunde M., Salles N., Hemeryck A., Martin Samos L. **IRA: A shape matching approach for recognition and comparison of generic atomic patterns**. <i>Journal of Chemical Information and Modeling</i> (2021), doi:[10.1021/acs.jcim.1c00567](https://doi.org/10.1021/acs.jcim.1c00567)

**Molalign**

J. M. Vasquez-Perez, L. A. Zarate-Hernandez, C. Z. Gomez-Castro, U. A. Nolasco-Hernandez. **A Practical Algorithm to Solve the Near-Congruence Problem for Rigid Molecules and Clusters**. <i>Journal of Chemical Information and Modeling</i> (2023), doi:[10.1021/acs.jcim.2c01187](https://doi.org/10.1021/acs.jcim.2c01187)