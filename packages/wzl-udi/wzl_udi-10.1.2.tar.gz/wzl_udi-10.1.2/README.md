[![Build](https://git-ce.rwth-aachen.de/wzl-mq-ms/forschung-lehre/lava/unified-device-interface/python/badges/master/pipeline.svg)](https://git-ce.rwth-aachen.de/wzl-mq-ms/forschung-lehre/lava/unified-device-interface/python/commits/master)

# Python Unified Device Interface
Current stable version: 10.1.2

## Installation
1. Install the WZL-UDI package via pip
```
pip install wzl-udi
```

## Documentation

A full documentation of the entire library does not exist yet and is currently work in progress. 

## Usage
For using the PUDI device interface you need to have a SOIL-Model of your device in JSON-Format.
You can design the model by hand our use the [SOIL-Web-Editor](https://iot.wzl-mq.rwth-aachen.de/soil/), to generate the source code and get a ready-to-run python script for your device server.
Examples of fictional devices using the library can be found [here](https://git-ce.rwth-aachen.de/wzl-mq-public/soil/soil-dummies).

## Citation & References

Scientific background and publications related to the _(Python) Unified Device Interface_ are:

[Bodenbenner, M.](mailto:matthias.bodenbenner@wzl-iqs.rwth-aachen.de); Sanders, M. P.; Montavon, B.; Schmitt, R. H. (2021): 
Domain-Specific Language for Sensors in the Internet of Production. 
In: Bernd-Arno Behrens, Alexander Brosius, Wolfgang Hintze, Steffen Ihlenfeldt und Jens Peter Wulfsberg (Hg.): 
Production at the leading edge of technology. Proceedings of the 10th Congress of the German Academic Association for Production Technology (WGP), Dresden, 23-24 September 2020. Berlin, Heidelberg, 2021. 1st ed. 2021. Berlin, Heidelberg: Springer (Lecture Notes in Production Engineering), S. 448–456, 
http://dx.doi.org/10.1007/978-3-662-62138-7_45

[Bodenbenner, M.](mailto:matthias.bodenbenner@wzl-iqs.rwth-aachen.de); Montavon, B.; Schmitt, R.H. (2021): 
FAIR sensor services - Towards sustainable sensor data management. 
In: Measurement: Sensors 18, S. 100206, 
https://doi.org/10.1016/j.measen.2021.100206

[Bodenbenner, M.](mailto:matthias.bodenbenner@wzl-iqs.rwth-aachen.de); Montavon, B.; Schmitt, R.H. (2022):
Model-driven development of interoperable communication interfaces for FAIR sensor services,
In: Measurement: Sensors, Volume 24, S. 100442,
https://doi.org/10.1016/j.measen.2022.100442

[Montavon, B.](mailto:benjamin.montavon@wzl-iqd.rwth-aachen.de) (2021): 
Virtual Reference Frame Based on Distributed Large-Scale Metrology Providing Coordinates as a Service. 
Aachen: Apprimus Verlag,
https://doi.org/10.18154/RWTH-2021-10238

[Montavon, B.](mailto:benjamin.montavon@wzl-iqd.rwth-aachen.de); Peterek, M.; Schmitt, R. H. (2019): 
Model-based interfacing of large-scale metrology instruments. 
In: Ettore Stella (Hg.): Multimodal Sensing: Technologies and Applications. 26-27 June 2019, Munich, Germany. Multimodal Sensing and Artificial Intelligence: Technologies and Applications. Munich, Germany, 6/24/2019 - 6/27/2019. Bellingham, Washington: SPIE (Proceedings of SPIE. 5200-, volume 11059), S. 11,
https://doi.org/10.1117/12.2527461

## Acknowledgements

The authors acknowledge funding from the LaVA project (Large Volume Applications, contract 17IND03 of the European Metrology Programme for Innovation and Research EMPIR). The EMPIR initiative is co-funded by the European Union’s Horizon 2020 research and innovation programme and the EMPIR Participating States.

Funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under Germany's Excellence Strategy – EXC-2023 Internet of Production – 390621612.

Funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under Project-ID 432233186 -- AIMS. 

## Licenses of third-party libraries used

| Library      | License                               |
|--------------|---------------------------------------|
| aiohttp      | Apache License, Version 2.0           |
| Deprecated   | MIT License                           | 
| nest-asyncio | BSD License                           | 
| pytz         | MIT License                           |
| rdflib       | BSD License                           |
| wzl-mqtt     | MIT License                           |

## Recent changes

**10.1.2** - 2025-10-15
  - updated dependency _aiohttp_ to version 3.13.0

**10.1.1** - 2024-08-16
  - added additional flog to Scheduler to configure semantic publishing correctly and supress unnecessary errors and warnings

**10.1.0** - 2024-04-17
  - added "advertisement", i.e. publishing of metadata via MQTT every x seconds
  - light refactoring of source code for streaming via MQTT
  - bug fix in the streaming scheduler 

**10.0.8** - 2024-03-25
  - fixed missing licences of some semantic resources 
  - changed "schema.org" to http in instead of https

**10.0.7** - 2024-03-22
  - fixed unit handling for the metadata provisioning

**10.0.6** - 2024-03-22
  - fixed validation of rfc3339 datetime strings

**10.0.5** - 2024-03-22
  - bug fix in streaming

**10.0.4** - 2024-03-22
  - increased logging verbosity of streaming class
  - fixed streaming of semantic measurements

**10.0.3** - 2024-03-21
  - added license field to semantic provision of measurement range

**10.0.2** - 2024-03-21
  - bug fix

**10.0.1** - 2024-03-21
  - removed strict-rfc3339 dependency to avoid licensing issues

**10.0.0** - 2024-03-21
  - the getter method of a measurement must always return a tuple of value and uncertainty quantification, if the uncertainty is not applicable None must be returned for the uncertainty
  - semantic path for Observation and MeasurementResults can now be resolved

**9.3.8** - 2024-03-19
  - fixed semantic serialization of integer variables

**9.3.7** - 2024-03-18
  - fixed serialization of semantics

**9.3.6** - 2024-03-18
  - fixed serialization of semantic values

**9.3.5** - 2024-03-18
  - fixed metadata provisioning of arguments and returns

**9.3.4** - 2024-03-16
  - fixed semantic name resolution of range profiles

**9.3.3** - 2024-03-15
  - fixed streaming functions

**9.3.2** - 2024-03-14
  - fixed semantic name resolution (again)

**9.3.1** - 2024-03-14
  - fixed semantic name resolution

**9.3.0** - 2024-03-13
  - implemented semantic features for functions
  - refactoring
    - renamed class Figure to Variable to reflect updated SOIL meta model

**9.2.0** - 2024-02-08
  - functions can be used to publish results via MQTT instead returning the results as response to the POST request
    - if a function is implemented as generator this behaviour is triggered automatically
  - bug fixes
    - the semantic definition of the range of measurements and parameters are properly returned now
    - profiles of base components of a component are properly returned now

**9.1.2** - 2024-01-19
  - added "all" query parameter for semantics, to request complete semantic data model
  - fixed bug when requesting enum or time measurements and parameters

**9.1.1** - 2024-01-18
  - bug fix of subjects of license paths in semantic data packages

**9.1.0** - 2024-01-17
  - the license for profiles, metadata and data is now provided anc can be specified in the config file

**9.0.1** - 2024-01-11
  - bug fix of semantic name resolution

**9.0.0** - 2024-01-10
  - added semantic features
    - the device can return profiles, metadata and data defined and structured according to semantic web standards using RDF and SHACL
  - changed signature of StreamScheduler
    - instead of a list of publishers, only one publisher is allowed no

**8.2.5** - 2023-04-17
  - relaxed required versions of dependencies to avoid conflicts

**8.2.4** - 2023-04-13
  - updated dependency, so that wzl-udi is also compatible with Python 3.11

**8.2.3** - 2023-03-29
  - removed legacy attributes from serialization and streaming

**8.2.2** - 2023-03-29
  - fixed a type hint which depended on windows

**8.2.1** - 2023-03-25 
  - removed utilities dependency, by integrating logger into wzl-udi library

**8.2.0** - 2023-03-16
  - improved FAIRness of streaming
    - published data contains metadata now
  - bug fixes
    - serialization of the complete model

**8.1.1** - 2023-03-15
  - bug fix
    - resolving the methods of the sensor logic for dynamic components

**8.1.0** - 2023-03-15
  - the desired dataformat of the response can be specified with a query parameter now, e.g.,
    - ../MEA-Temperature?format=json
    - ../MEA-Temperature?format=xml

**8.0.1** - 2023-03-14
  - bug fixes
    - fixed DELETE endpoint for dynamic components

**8.0.0** - 2023-03-11
  - changed initialization routine
    - the mapping via a dictionary of encapsulated sensor logic to HTTP-Endpoints is not needed anymore
    - the mapping is now derived automatically because the names of the attributes from the sensor implementation are assumed to be generated from a SOIL-Model
  - code clean-up
    - removed a lot of deprecated source code
  - bug fixes
    - fixed in error of fixed jobs

**7.1.0** - 2023-02-27

- added legacy flag as server parameter (default: false)
  - if set, datatypes are serialized to the old string representation, i.e. "bool" instead of "boolean", and "double" instead of float

**7.0.2** - 2023-02-23

- fixed a bug in update-streams for non-scalar variables


**7.0.1** - 2023-02-23

- minor bugfix

**7.0.0** - 2023-02-23

- aligned the naming of datatypes with *Textual SOIL*
  - "bool" is replaced by "boolean"
  - "double" is replaced by "float"
  - old naming is still accepted when starting the server, but responses of the server use the SOIl-conform naming

**6.3.1** - 2023-02-21

- updated from Python 3.9 to Python 3.11

**6.3.0** - 2022-06-09

- added property "label" for measurements as replacement for "nonce"
- marked usage of keyword "nonce" as deprecated

**6.2.0** - 2022-06-02

- added XML as dataformat for response bodies and published messages
- dataformat can now be chosen between XML and JSON

**6.1.2** - 2022-04-14

- bug fix of loop handling of aiohttp web application

**6.1.1** | 5.2.7 - 2021-05-19

- improved error output for developers

**6.1.0** - 2021-05-18

- refactoring of streaming implementation
  - scheduler classes are reduced to only one for all job types instead of three distinct schedulers

**6.0.3** | 5.2.6 - 2021-05-10

- bug fix
  - fixed serialization to RFC3339 time string
  
**6.0.2** | 5.2.5 - 2021-05-04

- bug fix
  - fixed parsing of parameters and variables/ measurements of type "time" for higher dimensions

**6.0.1**

- bug fix
  - fixed parsing of parameters and measurements of type "time" for higher dimensions
  
**6.0.0** - 2021-05-04

- renamed Object to Component and Variable to Measurement. UUID now starts with COM MEA respectively
- marked Object and Variable as deprecated
- marked docstring parsing as deprecated due to its error-prone behaviour

**5.2.4** - 2021-04-15

- bug fix
  - variables and parameters of type 'enum' and 'time' are now returned correctly

**5.2.3** - 2021-04-07

- minor bug fixes

**5.2.2** - 2021-01-22

- bug fixes of event handling and publishing, caused event handler to crash on the first event to be checked

**5.2.1** - 2021-01-19

- bug fix

**5.2.0** - 2020-11-27

- measurements can now be published automatically on value change

**5.1.2**

- bug fixes

**5.1.1** - 2020-07-13

- bug fixes

**5.1.0** - 2020-06-17

- added method for customizing logging-level
- unprotected the utils-module

**5.0.3** - 2020-06-17

- bug fix

**5.0.2** - 2020-06-17

- bug fix of asynchronous devices

**5.0.1** - 2020-06-10

- fixed erroneous import

**5.0.0** - 2020-06-09

- added events
- changed way of how MQTTPublisher are handled

**4.2.2** - 2020-05-29

- bug fix of MQTT related docstring parsin

**4.2.1** - 2020-05-28

- fixed a bug causing Objects could not be added during runtime

**4.2.0** - 2020-05-26

- improved flexibility of docstring-parsing

**4.1.1** - 2020-05-26

- bug fix

**4.1.0** - 2020-05-25

- From now, the mqtt-callback of Functions accepts only one positional parameter, which is the message data. Thus, it is not required to specify the topic anymore.

**4.0.0** - 2020-05-19

- renamed packages
- changed initialization routine
- bug fixes

**3.1.3** - 2020-04-16

- bug fixes

**3.1.2**

- bug fixes

**3.1.1**

- bug fixes

**3.1**

- moved ScheduledMQTTPublisher into the *wzl-mqtt* package to avoid ambiguity

**3.0** - 2020-04-14

- renamed and restructured packages for the sake of consistency with the C++ UDI

**2.3.1** - 2020-03-26

- bug fix of ScheduledMQTTPublisher

**2.3.0** - 2020-02-26

- instead of using Python-Docstrings one can provide an explicitly defined dictionary for configuration of the scheduled MQTTPublisher
- the publish method of the MQTTPublisher can passed to a function of the device to explicitly publish values within this function
- bug fixes

**2.2.1** - 2020-02-03

- bug fixes

**2.2.0** - 2020-01-27

- instead of using Python-Docstrings one can provide an explicitly defined dictionary with mappings from the model to the implementation

**2.1.0** - 2020-01-21

- the leading *objects* part of all urls is optional now.
- bug fixes

**2.0** - 2020-01-20

- renamed library into *wzl-udi*
- replaced MQTT-part with new *wzl-mqtt* package

**1.5.2** - 2020-01-20

- bug fixes

**1.5.1** - 2020-01-20

- bug fixes

**1.5.0** - 2020-01-20

- changed request for setting parameter values from PUT to PATCH

**1.4.1** - 2020-01-20

- bug fix

**1.4.0** - 2020-01-20

- added optional ontology field to  all elements
- bug fixes

**1.3.0** - 2020-10-09

**1.2.6** - 2020-08-09

- bug fix in docstring parsing

**1.2.5** - 2020-08-09

- bug fix in GET handler

**1.2.4** - 2020-08-01

- bug fixes

**1.2.3** - 2020-08-01

- bug fixes

**1.2.2** - 2020-08-01

- bug fixes

**1.2.1** - 2020-08-01

- bug fixes

**1.2.0** - 2020-08-01

- getters and setters are asynchronous now

**1.1.2** - 2020-07-31

- improved error handling

**1.1.1** - 2020-07-29

- bug fixes

**1.1.0** - 2020-07-29

- enabled asynchronous functions
- bug fixes

**1.0.0** - 2020-07-28

- initial release
