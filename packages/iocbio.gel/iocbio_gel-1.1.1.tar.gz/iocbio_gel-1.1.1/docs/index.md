# IOCBIO Gel: Software for Gel image analysis

IOCBIO Gel was originally developed for Western Blotting image analysis. However, it can be used
for any sample analysis technique that would result in similar images. This is the case for all gel electrophoresis experiments, where each sample is allocated
a "well" and the application of an electrical field makes the sample run through the gel, forming a lane. Within each lane, molecules within the sample are separated by charge or size. This technique is used in, for example, Western blotting (protein separation by size), Southern blotting (DNA separation by size), Northern blotting (RNA separation by size), and isoelectric focusing (IEF, separation by isoelectric point). After separation, the molecules are typically transferred to a membrane, and the molecules of interest can be detected by protein dyes, labelled antibodies, or labelled nucleic acid probes. In each lane, the intensity of the band(s) correspond to the sample content. 

IOCBIO Gel was designed to fit into the routine lab work by simplifying preprocessing of the images, such as 
background correction, cataloging the results and providing simple access to the analysed data. 
The statistical analysis of the samples is expected to be run by the user through other software. 
For that, either database access can be used, or data can be exported into spreadsheet.

## Links

- [Project page](https://gitlab.com/iocbio/gel)
- [Video tutorials](https://www.youtube.com/playlist?list=PLpBSXtqUd-Rq29Vx3_9B5901i2ov_nGc1)
- [Installation instructions](install.md)
- [Users guide](users.md)
- [Releases](https://gitlab.com/iocbio/gel/-/releases)
- Feature requests and bugs:
    - [How to request features and report bugs](https://iocbio.gitlab.io/gel/users/#bugs-and-feature-requests)
    - [Open feature requests and bugs](https://gitlab.com/iocbio/gel/issues)
- [Development notes](development.md)


## Citations and software description

Software is described in a paper (see below) that gives an overview of
the aims and the overall design of IOCBIO Gel. Please cite this paper
if you use IOCBIO Gel.

Kütt, J., Margus, G., Kask, L., Rätsepso, T., Soodla, K., Bernasconi,
R., Birkedal, R., Järv, P., Laasmaa, M., & Vendelin, M. (2023). Simple
analysis of gel images with IOCBIO Gel. _BMC Biology_, 21(1), 225.
[https://doi.org/10.1186/s12915-023-01734-8](https://doi.org/10.1186/s12915-023-01734-8)

## Copyright

Copyright (C) 2022-2023, Authors of the application as listed in software repository.

Software license: the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.
