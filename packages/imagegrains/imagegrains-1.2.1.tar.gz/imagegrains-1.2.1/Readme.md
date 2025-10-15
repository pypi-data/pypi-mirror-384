# ImageGrains  <img src="https://github.com/dmair1989/ImageGrains/blob/main/illustrations/logo_2.png?raw=true" width="100" title="logo" alt="logo" align="left">

![build](https://github.com/dmair1989/imagegrains/actions/workflows/ci.yml/badge.svg)
[![PyPI version](https://badge.fury.io/py/imagegrains.svg)](https://badge.fury.io/py/imagegrains)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/imagegrains)
![PyPI - License](https://img.shields.io/pypi/l/imagegrains?color=green)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/dmair1989/imagegrains)
[![PyPI Downloads](https://static.pepy.tech/badge/imagegrains)](https://pepy.tech/projects/imagegrains)

A software library for segmenting and measuring of sedimentary particles in images. The segmentation is done with [*Cellpose*](https://github.com/mouseland/cellpose), designed for cell and nucleus segmentation in biomedical images. Its segmentation capability is transferred to geoscientific applications throurgh re-training of the model with images of sediment particles. Pretrained [segmentation models](https://doi.org/10.5281/zenodo.15309323) from our [data](https://doi.org/10.5281/zenodo.8005771) are available or custom models can be trained (see [paper](https://doi.org/10.1002/esp.5755) for details).

<img src="https://github.com/dmair1989/ImageGrains/blob/main/illustrations/example.png?raw=true" align="center">
  
## :sparkles: Version 2.0 (in development) :sparkles:

Currently, we prepare a major update, which includes:

* Switching to [*Cellpose-SAM*](https://doi.org/10.1101/2025.04.28.651001) (```4.0.1+```) as default segmentation model, which improves the segmentation accuracy and generalization ***a lot***.
* [New models](https://doi.org/10.5281/zenodo.15309323) trained on a larger dataset (IG2) that includes different types of grains and imagery.
* Including 3D segmentation of CT-scan stacks; see [Notebook](https://github.com/dmair1989/imagegrains/blob/main/notebooks/CT_3D_segmentation.ipynb) and [Schuster et al. (2025)](https://doi.org/10.1111/bor.70023).  
* A [graphical user interface (GUI)](#how-does-it-work).  
  
These features are already available as pre-release, i.e., when [installed](#local-installation) with:
  
```text
pip install git+https://github.com/dmair1989/imagegrains.git
```

## Citation  

If you use software and/or data from here in your research, please cite the following works:

- Mair, D., Witz, G., Do Prado, A.H., Garefalakis, P. & Schlunegger, F. (2023) Automated detecting, segmenting and measuring of grains in images of fluvial sediments: The potential for large and precise data from specialist deep learning models and transfer learning. Earth Surface Processes and Landforms, 1–18. <https://doi.org/10.1002/esp.5755>.

- Pachitariu, M., Rariden, M., Stringer, C.. Cellpose-SAM: superhuman generalization for cellular segmentation. bioRxiv 2025.04.28.651001; <https://doi.org/10.1101/2025.04.28.651001>

If you use legacy versions of Cellpose (e.g., by using Imagegrains `v1.x` models), please cite the Cellpose 1.0 paper:  

- Stringer, C.A., Pachitariu, M., (2021). Cellpose: a generalist algorithm for cellular segmentation. Nat Methods 18, 100–106. <https://doi.org/10.1038/s41592-020-01018-x>.

If you use ImageGrains to calculate percentile uncertainties please also cite:

- Mair, D., Henrique, A., Prado, D., Garefalakis, P., Lechmann, A., Whittaker, A., and Schlunegger, F. (2022): Grain size of fluvial gravel bars from close-range UAV imagery-uncertainty in segmentation-based data, Earth Surf. Dyn., 10,953-973. <https://doi.org/10.5194/esurf-10-953-2022>.

## Local installation  

The easiest way to install the software is by using the conda package manager. If you do not have conda installed, please follow the instructions on the [conda website](https://docs.conda.io/en/latest/miniconda.html). If you encounter problems during installation, have a look [here](https://github.com/dmair1989/imagegrains/blob/main/Readme.md#troubleshooting). If these methods do not solve them, please open an issue.  

To install the software, open an anaconda prompt / command prompt, then create a new environment with:

```text
conda create --name imagegrains -c conda-forge python=3.10  
```

and activate it with:

```text
conda activate imagegrains
```

Then install the package using

```text
pip install imagegrains
```  

### GPU support  

By default, *Cellpose* will run on the CPU. From version `4.0.1` on,  it uses a transformer (*Cellpose-SAM*) as backbone segmentation model, which is much larger than the previous model. **Using a GPU on local machines is strongly recommended**.  
To use a GPU version on Windows or Linux, you will have to make sure you have a GPU compatible PyTorch version. For this:

1. Uninstall the PyTorch version that gets installed by default with Cellpose:

        pip uninstall torch

2. Make sure your have up-to-date drivers for your NVIDIA card installed.

3. Re-install a GPU version of PyTorch via conda using a command that you can find [here](https://pytorch.org/get-started/locally/) (this takes care of the cuda toolkit, cudnn etc. so **no need to install manually anything more than the driver**). The command will look like this:

        pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118  

If you work on a Mac, Cellpose (version `4.0.1` and later) supports   [M1-M3 out-of-the-box](https://cellpose.readthedocs.io/en/latest/installation.html#m1-m3-mac-installation).
Details and more installation options of Cellpose (including GPU versions for Windows and Linux) are also available in the [Cellpose repository](https://github.com/mouseland/cellpose#installation).

## How does it work?

ImageGrains is organised in 3 main modules for [*Segmentation*](#segmentation-of-own-images), [*Grain size measurements*](#grain-size-measurements) and [*Grain size distribution (GSD) analysis*](#grain-size-distribution-gsd-and-uncertainty). There are several ways to use them:  
\
\
**1 - User Interface:** The most convienient option is to use the GUI built as [napari](https://github.com/napari/napari) plugin: <https://github.com/guiwitz/napari-imagegrains>. 
  
<img src="https://github.com/dmair1989/ImageGrains/blob/main/illustrations/gui.png?raw=true" align="center">  
   
You can simply install it with:

```text
pip install git+https://github.com/dmair1989/napari-imagegrains.git
```  

Afterwards, you can start the program by running:
  
```text
napari
```

For instructions, please refer to the [docs](https://guiwitz.github.io/napari-imagegrains/napari_imagegrains.html).
\
\
**2 - Console:** The most basic option is to run ImageGrains from the **console** by first activating the enviromnent:

```text
conda activate imagegrains
```

Then download the pretrained models and demo data by executing:

```text
python -m imagegrains --download_data True
```

To start an analysis from the console run:

```text
python -m imagegrains --img_dir F:/REPLACE_WITH_PATH_TO_FOLDER_OF_IMAGES_(JPEG)
```

This will run the main application with the default settings on images in the provided location. You can use ```--help``` to see all input options.  
\
\
**3 - Notebooks:** Alternatively, you can run the jupyter notebooks in ```/notebooks``` in their order. They offer more options and information for most workflow steps. Of course, any modules and functions can be combined in custom scripts or notebooks.  

### Workflow  

<img src="https://github.com/dmair1989/ImageGrains/blob/main/illustrations/workflow.png?raw=true" width="550" title="wf" alt="wf" align="center">

The main concept of ImageGrains is to first segment grains in images, then to measure and scale them with the respective image resolution before finally estimating the uncertainty on an image base. The whole workflow is designed to use individual images or a set of images in a specific folder. During the processing steps, all intermediate outputs can be stored.

### Segmentation of own images

If you want to segment own images with pre-trained models, simply use the corresponding jupyter notebook ```notebooks/1_image_segmentation.ipynb```. To do so locally, open the console and activate the environment (```conda activate imagegrains```) and start your jupyter instance (e.g., via```jupyter lab```). Then, open the notebook and follow the instructions. You can use any model provied in ```/models``` or train a custom model (see below).

### Grain size measurements

To measure grain sizes, use the jupyter notebook ```notebooks/2_grain_sizes.ipynb```. It will load the segmented images and calculate the grain size for each grain on an image-by-image basis. Several options for outline fitting are available. The grain size is then scaled with the image resolution and stored in an output file. It is also possible to export individual grain outlines for further analysis.

### Grain size distribution (GSD) and uncertainty

To analyze the GSD, use the jupyter notebook ```notebooks/3_gsd_analysis.ipynb```. It will load the grain size measurements and calculate the GSD. Several for the uncertainty estimation are available. The uncertainty by default is calculated for each perecentile as 95% confidence interval. The GSD is then stored in an output file.

### Training of custom models

If you want to train your own models, you can use the jupyter notebook ```notebooks/4_model_training.ipynb```, you can use the [Cellpose GUI](https://www.cellpose.org/) (start it with ```python -m cellpose```) or train via [console](https://cellpose.readthedocs.io/en/latest/train.html) with the full funcitionality of Cellpose. To train custom models, you will first need manually annotated ground truth data ("labels"). This can be done either with the Cellpose GUI or with any dedicated annotation tool. We used the [labkit plugin](https://imagej.net/Labkit) for ImageJ. Please note, that each grain has to have a unique class value.

## Troubleshooting  
  
- If you have problems with the pip installation, you can also install the package directly from the repository. If you have trouble building from the repository, make sure you have ```git``` [installed](https://github.com/git-guides/install-git) and to have it in your path (this can be tricky on [Windows](https://stackoverflow.com/questions/26620312/installing-git-in-path-with-github-client-for-windows)). To install from the repository, use:

```text
pip install git+https://github.com/dmair1989/imagegrains.git
```  

- If you still have trouble, you can install the dependencies manually and use the jupyter notebooks in ```/notebooks``` to run the software and locally import the python files (i.e., by making sure the notebooks and files from ```src/imagegrains/``` are in the same folder and by changing any import statement ```from imagegrains import``` to ```import```). The dependencies are:

```text
cellpose
matplotlib
scikit-image
pandas
scanpy
jupyter lab
```

- If you run into problems with  OpenMP and libiomp5, you can try to create the environment using the ```nomkl``` package (more details [here](https://stackoverflow.com/questions/53014306/error-15-initializing-libiomp5-dylib-but-found-libiomp5-dylib-already-initial)) before installing imagegrains with:

```text
conda create --name imagegrains -c conda-forge python=3.10 imagecodecs nomkl 
```
