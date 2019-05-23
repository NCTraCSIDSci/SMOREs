# Synergistic Medication Organizer for RxNorm and Extras (SMOREs)

SMOREs is a python application designed to assist institutions with mappings local medications to standardized ontologies. Any local information around a medication can be loaded in and SMOREs will attempt to link the provided information to desired ontologies. These links are achieved through the use of available public API's provided by the National Library of Medicine and the Food and Drug Administration.

## Getting Started

These instructions will get you a copy of SMOREs up and running on your local machine.

### Prerequisites
**Python Versions Supported**
```
Python 3.6 or above
```
**Python Libraries Required**
```
PyYAML
tqdm
requests
requests-cache
python-dateutil
pandas
numpy
```
### Installing

#### Option 1 : Download Compiled Standalone Package
For ease of access, NC TraCS provides a standalone package for SMOREs that includes all dependencides, including a built in python virtual environment.
The package can be found at the NC TraCS Institute ShareHub (Registration Required):

https://tracs.unc.edu/index.php/tracs-resources/sharehub/category/2-informatics


#### Option 2 : Download Source Code and Manual Install
All Python library dependencies must be installed. There are a couple of options on how to ensure that all required dependencies.
##### 1. `pipenv` using Pipfile
A pipfile is included in the `install` directory of SMOREs to allow for quick setup of a virtual environment with all necessary dependencies. This does require that `pipenv` is installed.

Instructions on installing `pipenv` are available at: [pipenv.org](https://docs.pipenv.org/en/latest/install/#installing-pipenv)

Once installed running the following command within the `install` directory will perform the necessary steps.
```
pipenv install
pipenv run smores
```

##### 2. `pip` install using requirements.txt
A compiled list of all package requirements is also available to be installed via pip using the requirements.txt file within the `install` directory
```
cd to [smores directory]
pip install -r requirements.txt
```


##### 3. Manually install all requirements
Each required package list in the **Python Libraries Required** section can be installed manually via `pip`. SMOREs will need to be executed via a python interpreter that has all of the modules available.
```
pip install PyYAML
etc..
```


## Verifying Installation

After downloading the source code, installation of all required dependencies and necessary API access can be validated by executing the provided verification program.

```
cd to [smores directory]
python tests\verifyInstall.py
```

## Usage
For more information on available commands, processes and functionality please visit the [SMOREs Wiki]() for up to date descriptions of functionality within the application.

## Contributing

Please contact the development team about making contributions to the source. More detail on contributing to the source will be provided in the future.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Robert Bradford** - *Lead* - [NC Translation and Clinical Sciences Institute](https:tracs.unc.edu)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.


## Academic Citations
If your group uses SMOREs in support of a research project, please include the appropriate citation to help acknowledge SMOREs and it's development.

#### For grant Submissions
> SMOREs is a tool to support institutions by improving semantic relationships to standardized medication ontologies via supported APIs provided by the National Library of Medicine (NLM - RxNav, UMLS) and the US Food and Drug Administration (FDA - openFDA). Standardized ontologies allow a harmonized approach to searching for medications for research, operational, and quality improvement purposes within healthcare. SMOREs was developed at University of North Carolina is supported by the National Center for Advancing Translational Sciences (NCATS), National Institutes of Health, through Grant Award Number UL1TR002489.


#### Acknowledgement of SMOREs in papers and presentations
> SMOREs is a tool to support institutions by improving semantic relationships to standardized medication ontologies via supported APIs provided by the National Library of Medicine (NLM - RxNav, UMLS) and the US Food and Drug Administration (FDA - openFDA). SMOREs was developed at University of North Carolina is supported by the National Center for Advancing Translational Sciences (NCATS), National Institutes of Health, through Grant Award Number UL1TR002489.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

##### RxNav API
>This product uses publicly available data from the U.S. National Library of Medicine (NLM), National Institutes of Health, Department of Health and Human Services; NLM is not responsible for the product and does not endorse or recommend this or any other product.

##### openFDA API
>Data provided by the U.S. Food and Drug Administration (https://open.fda.gov/terms/)

##### UMLS API
>This product uses publicly available data from the U.S. National Library of Medicine (NLM), National Institutes of Health, Department of Health and Human Services; NLM is not responsible for the product and does not endorse or recommend this or any other product.

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc

