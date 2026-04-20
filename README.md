# Gravitational Wave and Numerical Relativity Tutorials
Welcome friends! In this repository you can find two tutorials that I've given over the years.

One is focused more on simulations and building waveform models:
* a brief introduction to numerical relativity, i.e., what it means to simulate a binary black hole coalescence,
* how to interact with SXS Collaboration's catalog of NR simulations, i.e., how to load waveforms and plot them,
* and then we'll conclude by building our very own waveform surrogate model using some of the more simple numerical relativity waveforms for the SXS Collaboration's catalog!
  
and one is focused more on gravitational wave theory and black hole perturbation theory:
* the BMS symmetries and how they can be used to express waveforms in terms of BMS charges and fluxes,
* and how to fit the ringdown phase of gravitational waves from binary black holes with quasi-normal modes.

### Getting started (Google Colab)

If you don't want to download anything locally, feel free to use [Google Colab](https://colab.research.google.com/) instead!

Just 
1. Go to [Google Colab](https://colab.research.google.com/)
2. Click `File`, and then `Upload Notebook`, and then `GitHub`
3. Paste the following url
    ```
    https://github.com/keefemitman/ResearchTutorials
    ```
    into the search bar, and  <ins>then click off the search bar</ins>

4. Click `Tutorial_SXSAndSurrogates.ipynb` (this will open the notebook)
5. Or click `Tutorial_BMSAndQNMs.ipynb` (this will open the notebook)
6. Click `Run all`
7. Wait for the notebook to crash
8. Click `Run all` again
9. Enjoy! 🌊

### Getting started (running locally)
To start this tutorial, you'll first need to clone the repository and `cd` into it

(feel free to change `my_copy_of_the_tutorial` to whatever you want):

```
git clone git@github.com:keefemitman/ResearchTutorials.git my_copy_of_the_tutorial | cd my_copy_of_the_tutorial
```

Then, you'll need to install the relevant packages. If you are already one of the cool kids and are using `uv` (https://docs.astral.sh/uv/),
then running this installation is as easy as 

```
uv sync
```

Otherwise you can install via `pip` with

```
pip install .
```

or create a `conda` environment with

```
conda env create --name research-tutorials --file=environments.yml | conda activate research-tutorials
```

### Loading the tutorial
Everything for the tutorial can be found in the `Tutorial*.ipynb` notebooks.

If you're using `uv`, this is again trivial by running
```
uv run ipython kernel install --user --env VIRTUAL_ENV $(pwd)/.venv --name=research-tutorials
uv run --with jupyter jupyter lab
```
and then opening the notebook and select the kernel `research-tutorials`.

If instead you've activated your conda environment, then this should also just be as simple as running
```
jupyter notebook Tutorial_SXSAndSurrogates.ipynb
```
or
```
jupyter notebook Tutorial_BMSAndQNMs.ipynb
```

If you don't want to activate your conda environment, but would rather creater a jupyter kernel, just run
```
python -m ipykernel install --user --name=research-tutorials
```
and then load it in the notebook after starting it up.

🌈 **Happy Tutorial-ing!** 🎉
