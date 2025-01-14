---
title: 'Gala: A Python package for galactic dynamics'
tags:
  - Python
  - astronomy
  - dynamics
  - galactic dynamics
  - milky way
authors:
  - name: Adrian M. Price-Whelan
    orcid: 0000-0000-0000-0000
    equal-contrib: true
    affiliation: "1, 2" # (Multiple affiliations must be quoted)
  - name: Author Without ORCID
    equal-contrib: true # (This is how you can denote equal contributions between multiple authors)
    affiliation: 2
  - name: Author with no affiliation
    corresponding: true # (This is how to denote the corresponding author)
    affiliation: 3
  - given-names: Ludwig
    dropping-particle: van
    surname: Beethoven
    affiliation: 3
affiliations:
 - name: Lyman Spitzer, Jr. Fellow, Princeton University, United States
   index: 1
   ror: 00hx57361
 - name: Institution Name, Country
   index: 2
 - name: Independent Researcher, Country
   index: 3
date: 13 August 2017
bibliography: paper.bib

# Optional fields if submitting to a AAS journal too, see this blog post:
# https://blog.joss.theoj.org/2018/12/a-new-collaboration-with-aas-publishing
aas-doi: 10.3847/xxxxx <- update this with the DOI from AAS once you know it.
aas-journal: Astrophysical Journal <- The name of the AAS journal.
---

# Summary

The efficient management of computing resources is a significant challenge, especially in the academic environment, where there are often no professionals dedicated to this task. In many research labs, Linux machines are connected locally or via the internet, creating a decentralized network of computing resources, which may contribute to hardware underutilization, time loss and human resource overload. To facilitate the management and monitoring of these machines, we have developed a Python application that offers a simplified and accessible solution. The application eliminates the need to install software on multiple machines and allows for active and specialized management of computing resources. In addition to the Python library, LabMonitor includes an intuitive dashboard that allows you to view, manage and submit computational jobs centrally. Initial configuration is simple and can be done by filling in the machine information in a spreadsheet and executing a single command. This tool was designed to meet the needs of researchers, providing a user-friendly and efficient interface for managing resources on multiple Linux machines.



# Statement of need

Managing computing resources in academic environments is an essential task, especially when several machines are networked to carry out intensive scientific work. Tools such as Slurm`[Yoo:2003; Iserte:2014]` and HTCondor`[Thain:2005]` are widely used to manage work queues and allocate computing cluster resources. Slurm, for example, is a robust tool designed for managing computer clusters, where the machines are usually centralized and connected by high-speed networks. However, this solution is not ideal for decentralized networks, where machines may be scattered in different locations and connected via the internet. On the other hand, HTCondor is known for its flexibility in managing pools of heterogeneous machines, including decentralized networks. However, its configuration and operation can be complex, requiring significant technical knowledge to fine-tune the various options available `[Yoo:2003; Thain:2005; Iserte:2014]`.
Although these tools are powerful, the complexity of their configuration and operation can be a barrier for many users in academic environments, where specialized technical support is not always available`[Georgiou:2013; Varrette:2022]`. To fill this gap, we developed LabMonitor, a Python application designed to simplify the management of computing resources in decentralized networks of Linux machines.
LabMonitor, a Python application that is intuitive and easy to use, eliminating the need for complex configurations. Initial configuration can be done by filling in a spreadsheet with information about the machines and, optionally, the users. With the execution of a single command, the system is ready to use, allowing users to manage and monitor resources via a graphical platform. Submitting jobs to LabMonitor is done via a simple interface, which also offers e-mail notifications to update users on the status of their jobs. In addition, the system includes a resource scheduling feature, allowing users to reserve machines for specific tasks. This scheduling feature provides a structured way of planning the use of computing resources. By simplifying the process of managing computing resources, LabMonitor becomes a valuable tool for researchers who want to maximize the use of their machines without the need for advanced technical expertise. This allows researchers to devote themselves to the object of their research and not to the difficulties of managing computing resources.


# Citations

Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:
- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)"

# Figures

Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)
and referenced from text using \autoref{fig:example}.

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% }

# Acknowledgements

We acknowledge contributions from Brigitta Sipocz, Syrtis Major, and Semyeong
Oh, and support from Kathryn Johnston during the genesis of this project.

# References