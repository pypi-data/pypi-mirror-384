# Integrated Modelling System Infrastructure (IMSI)

[![Documentation Status](https://readthedocs.org/projects/imsi/badge/?version=latest)](https://imsi.readthedocs.io/en/latest/?version=latest)
![Pipeline Status](https://gitlab.com/cccma/imsi/badges/main/pipeline.svg)
![Coverage Status](https://gitlab.com/cccma/imsi/badges/main/coverage.svg)

The **Integrated Modelling System Infrastructure (IMSI)** is a comprehensive Python-based package used to download, configure, build, and run the suite of models in the CCCma Integrated Modelling System.

- **Documentation:** [https://imsi.readthedocs.io](https://imsi.readthedocs.io)

---

## License

- [Open Government License – Canada version 2.0](https://open.canada.ca/en/open-government-licence-canada)

---

## Installation

IMSI is normally pre-installed on support machines by technical staff, and users need only source an environment.

You can install IMSI manually as shown below. It is recommended to install it inside a Python or Conda virtual environment.

```bash
python3 -m venv /path/to/new/virtual/environment 
source /path/to/new/virtual/environment/activate
# conda create -n imsi-test python=3.10

git clone git@gitlab.science.gc.ca:CanESM/imsi.git
cd imsi
pip install .      # for usage
# pip install -e . # for development
```

## Basic usage
```bash
imsi -h # for help

# Setup a CanESM5.1 p1 CMIP6 piControl run
imsi setup --repo=https://gitlab.com/cccma/canesm --ver=develop_canesm --exp=cmip6-piControl --model=canesm51_p1 --runid=imsi-test
imsi build          # compile executables
imsi save-restarts  # save desired restarts
imsi submit         # submit the run
```
