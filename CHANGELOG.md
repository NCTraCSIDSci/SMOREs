# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

#### [Unreleased] 
- Command Functions to UMLS API: lookup, crosswalk
- SNOMED-CT input and output Support

#### [0.10.6] - 2019-05-23
```
- Minor bug fix for csv processing
- Minor bug fix for workflow escaping
- Added some color highlighting in console for better visibility
- Minor cleanups for PEP standards
- Updated requirements.txt and Pipfile
```
#### [0.10.5] - 2019-05-22
```
- Added basic workflow process for automating multiple tasks
```
#### [0.10.4] - 2019-05-20
```
- Bugfix for issue #4 - YAML Loader warning
```

#### [0.10.3] - 2019-05-20
```
- Added Pipfile, requirements.txt for easy install
- Bugfix for issue #2 - Pathing Error on Cli Start
```
#### [0.10.2] - 2019-05-02
```
- Added API Key definitions to config.ini and supporting call functions 
- Typos in ReadMe
```

#### [0.10.1] - 2019-04-24
*Initial Public Release Version for Testing*
```
- Basic Command Line Interface
- Supports API calls to RxNav and FDA
- Supports Searches by RxNorm and NDC
- Exports CSV
- Exports FHIR Json Objects
- Session saves
- 48 Hour API Cache'ing
- Basic input config settings
```