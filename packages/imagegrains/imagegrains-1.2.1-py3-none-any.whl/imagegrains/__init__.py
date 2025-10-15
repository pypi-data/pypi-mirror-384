"""A software library for segmenting and measuring of sedimentary particles in images."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("imagegrains")
except PackageNotFoundError:
    __version__ = "uninstalled"

try: 
    __cp_version__ = int(version("cellpose").split('.')[0])
    if __cp_version__ > 3:
        print(f'>> Initializing ImageGrains with CellposeSAM:')
        from cellpose import __init__
    else:
        print(f'>> Initializing ImageGrains with Cellpose legacy release (v{__cp_version__}).')
except PackageNotFoundError: 
    __cp_version__ = "uninstalled" 
    print('>> Cellpose not found - installation information can be found here: https://github.com/dmair1989/imagegrains?tab=readme-ov-file#local-installation ')