# What is `new_conda_env`?
This (future) conda-forge package performs a "quick-clone" of an existing conda environment when one is needed with a different kernel version.  
* **Caveat:**
  - At the moment, python is the first (& only) kernel considered.
  - There is no guarantee that the new environment is satisfiable e.g. some packages in envA using python 3.x may not exist in envB using python 3.y. The statisfiability check is done by conda at the moment of installation.

# Use case (python kernel)

You've created a conda environment, which you would like to re-create with a different version of python.
* Example: You have a current python 3.10 conda environment for GIS applications, geo310. When you learn that there is a package that does exactly what you had planned to do, you want to install it... Except, that package is using python 3.9, so you need to reproduce the python 3.10 environment to work with the lower version.

# Issues
1. Using the usual `conda env export > environment.yml` or  `conda env export --no-builds > environment.yml` command fixes all packages dependencies, so that will not work with another python version.
2. Using the `--from-history` option, e.g.: `conda env export --from-history > environment.yml` is closer to what's needed because it lists all the packages you installed at the command line, but __it excludes all pip installations__!

# Manual workaround
 1. Create a "minimal" `env_hist.yml` file from an existing environment using the `--from-history` option
 2. Create a "complete" `env_nobld.yml` file using the `--no-builds` option
 3. Edit `env_hist.yml`:    
   3.1 Change `name` to that of the new environment  
   3.2 Insert the missing pip installations (minus version numbers) listed in `env_nobld.yml` in the dependencies list & change the python version to the new one (or insert a line for python if missing)  
   3.3 Change the prefix line so that the path uses the new `name`  
 4. Save `env_hist.yml`, or 'save as' a better name hinting at the creation process, e.g. `env_39_from_geo310.yml`

# Solution implemented in `new_conda_env`:
The package automates the manual workaround.
![wanted](./wanted_venn.drawio.svg)

![C1 view](./c1_view.drawio.svg)
# User-supplied data:
1. The name of the conda env to "quick-clone", `env_ini`
2. The name of the kernel, i.e. 'python'
2. The name for the new environment
2. The new version of the kernel to use, `new_ver`
3. Optional: A name for the new yaml file (to overwrite default name: `env_{kernal}{new_ver}_from_{env_ini}.yml`)

# TODO
 [ ] Create all needed processing functions & tests  
 [ ] Create cli & test  
 [ ] Upload to conda-forge  
 
---

### What's yaml (yml)?
>"YAML is a data serialization format designed for human readability and interaction with scripting languages"
#### More about [yaml](https://github.com/yaml/yaml-spec/blob/main/spec/1.2.2/spec.md) and [pyyaml](https://pypi.org/project/PyYAML/)
