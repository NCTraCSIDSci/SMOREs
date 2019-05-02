# Synergistic Medication Organizer for RxNorm and Extras (SMOREs)

SMOREs is a python applicationd esigned to assist institutions with mappings local medications to standardized ontologies. Any local information around a medication can be loaded in and SMOREs will attempt to link the provided information to desired ontologies. These links are achieved through the use of available public API's provided by the National Library of Medicine and the Food and Drug Administration.

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
All Python library dependencies must be installed

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

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

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

#####RxNav API
>This product uses publicly available data from the U.S. National Library of Medicine (NLM), National Institutes of Health, Department of Health and Human Services; NLM is not responsible for the product and does not endorse or recommend this or any other product.

#####openFDA API
>Data provided by the U.S. Food and Drug Administration (https://open.fda.gov/terms/)

#####UMLS API
>This product uses publicly available data from the U.S. National Library of Medicine (NLM), National Institutes of Health, Department of Health and Human Services; NLM is not responsible for the product and does not endorse or recommend this or any other product.

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc

