# Use case

You've created a conda environment for your python project, which you would like to reuse with a different version of python.
* Example: You have a current python 3.10 conda environment used for GIS applications. When you learn that there is a package that does exactly what you had planned to do, you want to install it ASAP... Except that package is using python 3.9.  
Note: From here on end, I assume you have python 3.9 & 3.10 installed on your computer.

## Issues
1. Using the usual `conda env export > environment.yml` command fixes all packages dependencies, so that will not work.
2. Using the `--from-history` flag, e.g.: `conda env export --from-history > environment.yml` will not always (or never?) include the python version under the _dependencies_ section. Yet, it is close to what you need!
3. Packages installed using pip should be listed in the dependency list (both as an item and a mapping), but are not.

# Manual workaround: Create a "minimal" `environment.yml` file from an existing, activate environment using the `--from-history` flag.

### What's yaml (yml)?
>"YAML is a data serialization format designed for human readability and interaction with scripting languages"

#### More about [yaml](https://github.com/yaml/yaml-spec/blob/main/spec/1.2.2/spec.md) and [pyyaml](https://pypi.org/project/PyYAML/)

1. Use the `from-history` flag to export the environment to a yaml file
Create a minimal yaml file of your favorite environment and save it. Note: the example uses a hypothetical "geo310" environment created with python 3.10 on Windows 10, e.g.:
```
(base)>conda activate geo310
(geo310)>conda env export --from-history > env_hist_from_geo310.yml (Pattern 1: "env_hist_from_"+<env_name>+".yml")
(geo310)>conda deactivate
```
1.2 (Optional) Inspect `env_hist_from_geo310.yml`
  - The first line is "name: geo310";
  - The dependencies list does not have an entry for python; [to be confirmed]
  - The last line is the 'prefix' line: "prefix: C:\Users\<you>\<Anaconda3 | Miniconda>\envs\geo310"

2. Whenever you want a similar environment but for a different version of python, amend `generic_from_geo31.yml` with the appropriate substitutions for the name and prefix values, insert "python=3.xx[.xx]" as the first entry in the dependencies key list of values and save under a meaningful name.
* Example: Change the value of the name key to geo309, which is reused in the prefix key value; Insert "python=3.9" as the first item in the dependencies list; SaveAs `env_hist_from_geo310.yml` to `env_geo309_from_geo31_hist.yml` (that's meaningful to me).

3. Create the new environment:
```
(base)>conda create -y -f env_geo309_from_geo31_hist.yml  # -y::install after download without asking
#...long download of packages...
(base)>conda env list
# geo309 should be listed
(base)>conda activate geo309 # install the 3.9 package you need!
(geo309)>pip install new_py39_package

```
---
# Automated workaround
This project automate the process!

## User supplied data:
1. The name of the conda env to "minimize", `env_ini`
2. The (new) version of python to use, `new_ver`
3. A name for the new yaml file to use a custom name
