---
title: 'LabMonitor: Simplified management of decentralized computational resources of Linux machines'
tags:
  - Python
  - astronomy
  - dynamics
  - galactic dynamics
  - milky way
authors:
  - name: José de Anchieta de Oliveira Filho
    orcid: 0000-0002-1904-3786
    corresponding: true
    affiliation: 1 
  - name: Guilherme Ian Spelta
    orcid: 0009-0000-6260-7068
    affiliation: 1 
  - name: Artur Duque Rossi
    orcid: 0000-0002-5717-2116
    affiliation: 1
  - name: Mariana Simões Ferreira
    orcid: 
    affiliation: 1
  - name: Pedro Henrique Monteiro Torres
    orcid: 0000-0002-0945-1495
    affiliation: 1
  - given-names: Pedro Geraldo Pascutti
    orcid: 0000-0002-5454-560X
    affiliation: 1
affiliations:
 - name: Institute of Biophysics Carlos Chagas Filho, Federal University of Rio de Janeiro, Rio de Janeiro, Brazil
   index: 1
date: 16 January 2025
bibliography: paper.bib

---

# Summary

The efficient management of computing resources is a significant challenge, especially in the academic environment, where there are often no professionals dedicated to this task. In many research labs, Linux machines are connected locally or via the internet, creating a decentralized network of computing resources, which may contribute to hardware underutilization, time loss and human resource overload. To facilitate the management and monitoring of these machines, we have developed a Python application that offers a simplified and accessible solution. The application eliminates the need to install software on multiple machines and allows for active and specialized management of computing resources. In addition to the Python library, LabMonitor includes an intuitive dashboard that allows you to view, manage and submit computational jobs centrally. Initial configuration is simple and can be done by filling in the machine information in a spreadsheet and executing a single command. This tool was designed to meet the needs of researchers, providing a user-friendly and efficient interface for managing resources on multiple Linux machines.



# Statement of need

Managing computing resources in academic environments is an essential task, especially when several machines are networked to carry out intensive scientific work. Tools such as SLURM [@Yoo:2003; @Iserte:2014] and HTCondor [@Thain:2005] are widely used to manage work queues and allocate computing cluster resources. SLURM, for instance, is a robust tool designed for managing computer clusters, where the resources are usually centralized and connected by high-speed networks. However, this solution is not ideal for decentralized resources, where machines may be scattered in different locations and sometimes, connected through the internet. On the other hand, HTCondor is known for its flexibility in managing pools of heterogeneous machines, including decentralized resources. Nevertheless, its configuration and operation can be complex, requiring significant technical knowledge to fine-tune the various options available [@Yoo:2003; @Thain:2005; @Iserte:2014].
Although these tools are powerful, the complexity of their configuration and operation can be a barrier for many users in academic environments, where specialized technical support is not always available [@Georgiou:2013; @Varrette:2022]. To fill this gap, we developed LabMonitor, a Python application designed to simplify the management of computing resources in decentralized networks of Linux machines.
LabMonitor is a Python application that is intuitive and easy to use, eliminating the need for complex configurations. Initial configuration can be done by filling in a spreadsheet with information about the machines and, optionally, the users. With the execution of a single command, the system is ready to use, allowing users to manage and monitor resources through a local web platform. Submitting jobs to LabMonitor is done through a simple interface, which also enables e-mail notifications to update users on the status of their jobs. In addition, the system includes a resource scheduling feature, allowing users to reserve machines for specific tasks. This scheduling feature provides a structured way of planning the use of computing resources. By simplifying the process of managing computing resources, LabMonitor becomes a valuable tool for researchers who want to maximize the use of their machines without the need for advanced technical expertise. This allows researchers to devote themselves to the object of their research and not to the difficulties of managing computing resources.


# Acknowledgements

We acknowledge the Laboratory for Molecular Dynamics and Modelling (LMDM) for their contribution by providing access to the computational resources that made this work possible. We also thank the Carlos Chagas Filho Biophysics Institute (IBCCF) and the Federal University of Rio de Janeiro (UFRJ) for their support, as LMDM is a part of IBCCF within UFRJ.

# References
