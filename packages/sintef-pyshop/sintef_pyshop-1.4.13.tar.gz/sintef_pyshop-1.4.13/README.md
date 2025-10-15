# pyshop

Status:

[![Latest Release](https://gitlab.sintef.no/energy/shop/pyshop/-/badges/release.svg)](https://gitlab.sintef.no/energy/shop/pyshop/-/releases)
[![build status](https://gitlab.sintef.no/energy/shop/pyshop/badges/main/pipeline.svg?key_text=main)](https://gitlab.sintef.no/energy/shop/pyshop/-/commits/main)
[![coverage report](https://gitlab.sintef.no/energy/shop/pyshop/badges/main/coverage.svg)](https://gitlab.sintef.no/energy/shop/pyshop/-/commits/main)

The nicest python interface to SHOP!

SHOP (Short-term Hydro Optimization Program) is a modelling tool for short-term hydro operation planning developed by SINTEF Energy Research in Trondheim, Norway. SHOP is used for both scientific and commercial purposes, please visit the [SHOP home page](https://www.sintef.no/en/software/shop/) for further information and inquiries regarding access and use.

The pyshop package is an open source python wrapper for SHOP, and requires the proper SHOP binaries to function (see step 2).

## 1 Installing pyshop

We currently offer two ways to use pyshop:

1. Install pyshop through pypi (simple and quick)
2. Install pyshop through Sintef's Gitlab Package Registry (useful if you want to avoid public registries)

### Install pyshop using pypi

The pyshop package can be installed using pip, the package installer for python. Please visit the [pip home page](https://pip.pypa.io/en/stable/) for installation and any pip related issues. You can install the official pyshop release through the terminal command:

`pip install sintef-pyshop`

You can also clone this repository and install the latest development version. To do this, open a terminal in the cloned pyshop directory and give the command:

`pip install .`

You should now see pyshop appear in the list of installed python modules when typing:

`pip list`

### Install pyshop using Gitlab Package Registry

Create a [personal access token.](https://gitlab.sintef.no/help/user/profile/personal_access_tokens)

Run the command below with your personal access token:
`pip install sintef-pyshop --index-url https://__token__:<your_personal_token>@gitlab.sintef.no/api/v4/projects/4012/packages/pypi/simple`

## 2 Download the desired SHOP binaries for your system

> NOTE: You may not distribute the CPLEX library as it requires end user license

The SHOP core is separate from the pyshop package, and must be downloaded separately. The latest SHOP binaries are found on the [SHOP Portal](https://shop.sintef.energy/files/). Access to the portal must be granted by SINTEF Energy Research.

The following binaries are required for pyshop to run:

Windows:

- `cplex2010.dll`
- `shop_cplex_interface.dll`
- `shop_utility.dll` (since SHOP 17.2.0)
- `shop_pybind.pyd`

Linux:

- `libcplex2010.so`
- `shop_cplex_interface.so`
- `libshop_utility.so` (since SHOP 17.2.0)
- `shop_pybind.so`

The solver specific binary is listed as cplex2010 here, but will change as new CPLEX versions become available. It is also possible to use the GUROBI and OSI solvers with SHOP. Note that the shop_cplex_interface.so used to contain the CPLEX binaries in the Linux distribution before SHOP version 14.3, and so older SHOP versions do not require the separate libcplex2010.so file.

## 3 Environment and license file

A working SHOP license file, `SHOP_license.dat`, is required to run SHOP through pyshop, and can be generated on the SHOP Portal. The environment variables `SHOP_LICENSE_PATH` and `SHOP_BINARY_PATH` can be used to tell SHOP where the files are located. The old environment variable `ICC_COMMAND_PATH` used for these purposes is now deprecated. Please see the "Environment variables" documentation page in the SHOP documentation on the SHOP Portal for further information. These environment variables can be overridden by manually specifying the `license_path` and `solver_path` input arguments when creating an instance of the ShopSession class, see step 4. Note that all binaries listed in step 2 should be located in the same directory, though SHOP versions older than 14.4.0.5 require libcplex2010.so to be placed in the '/lib' directory when running pyshop in a Linux environment.

## 4 Running SHOP

Now that pyshop is installed, the SHOP binaries are downloaded, and the license file and binary paths are located, it is possible to run SHOP in python using pyshop:

    from pyshop import ShopSession

    shop = ShopSession(license_path="C:/License/File/Path", solver_path="C:/SHOP/versions/latest")

Please visit the SHOP documentation for a detailed guides on how to use [pyshop](https://docs.shop.sintef.energy/examples/pyshop/pyshop.html).
For more in depth examples you should look at the topics within the documentation, since all of the examples in the documentation are written using pyshop. E.g: [Run a standard optimization](https://docs.shop.sintef.energy/examples/best_profit/best_profit_basic.html#run-a-standard-optimization)

## Visual Studio Code Dev Containers

[Visual Studio Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers) lets you run a fully functional development environment using Docker and Visual Studio Code. This might simplify setting up pyshop for new users. Follow the guide below to setup the devcontainer for pyshop.

### Installation

Install the following dependencies:

1. Install the code editor called [Visual Studio Code](https://code.visualstudio.com/Download). Visual Studio Code is free
2. Install a Docker GUI: [Docker desktop](https://www.docker.com/products/docker-desktop/) (might require a paid license depending on your organization), or a free alternative called [Podman](https://podman.io/)

### Setup

1. Create a folder called `.devcontainer` in your root directory with a file called `devcontainer.json`. Your folder structure should look like the example below:

   ![Devcontainer folder setup](docs/images/devcontainer-folder.png)

2. Copy and paste the contents of [devcontainer.json](.devcontainer/devcontainer.json) into your `devcontainer.json` file.
3. Create a folder called `bin` in your root directory and add the following files: `libcplex2010.so`, `shop_cplex_interface.so`, `libshop_utility.so` (since SHOP 17.2.0), your shop license e.g `SHOP_license.dat`, shop pybind e.g `shop_pybind.cpython-312-x86_64-linux-gnu.so`. Your bin folder should now look like:
   ![Binary folder with the required files](docs/images/bin-folder.png)

4. Open your project using the devcontainer config files by running the command:
   ![Searching for devcontainer command](docs/images/dev-containers-reopen.png)

More in depth guides on how to customize devcontainers can be found in the [devcontainer documentation](https://code.visualstudio.com/docs/devcontainers/create-dev-container)
