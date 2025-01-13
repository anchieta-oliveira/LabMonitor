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

EN: The efficient management of computing resources is a significant challenge, especially in the academic environment, where there are often no professionals dedicated to this task. In many research labs, Linux machines are connected locally or via the internet, creating a decentralized network of computing resources. To facilitate the management and monitoring of these machines, we have developed a Python application that offers a simplified and accessible solution. The application eliminates the need to install software on multiple machines and allows for active and specialized management of computing resources. In addition to the Python library, LabMonitor includes an intuitive dashboard that allows you to view, manage and submit computational jobs centrally. Initial configuration is simple and can be done by filling in the machine information in a spreadsheet and executing a single command. This tool was designed to meet the needs of researchers, providing a user-friendly and efficient interface for managing resources on multiple Linux machines.

PT: O gerenciamento eficiente de recursos computacionais é um desafio significativo, especialmente no ambiente acadêmico, onde muitas vezes não há profissionais dedicados para essa tarefa. Em muitos laboratórios de pesquisa, máquinas Linux estão conectadas localmente ou via internet, criando uma rede descentralizada de recursos computacionais. Para facilitar o gerenciamento e monitoramento dessas máquinas, desenvolvemos uma aplicação em Python que oferece uma solução simplificada e acessível. A aplicação elimina a necessidade de instalação de software em múltiplas máquinas e permite um gerenciamento ativo e especializado dos recursos computacionais. O LabMonitor, além da biblioteca Python, inclui um Dashboard intuitivo que permite visualizar, gerenciar e submeter trabalhos computacionais de forma centralizada. A configuração inicial é simplificada, podendo ser realizada através do preenchimento de informações das máquinas em uma planilha e a execução de um único comando. Esta ferramenta foi projetada para atender às necessidades de pesquisadores, fornecendo uma interface amigável e eficiente para o gerenciamento de recursos em várias máquinas Linux.


# Statement of need

EN: Managing computing resources in academic environments is an essential task, especially when several machines are networked to carry out intensive scientific work. Tools such as Slurm and HTCondor are widely used to manage work queues and allocate computing cluster resources. Slurm, for example, is a robust tool designed for managing computer clusters, where the machines are usually centralized and connected by high-speed networks. However, this solution is not ideal for decentralized networks, where machines may be scattered in different locations and connected via the internet. On the other hand, HTCondor is known for its flexibility in managing pools of heterogeneous machines, including decentralized networks. However, its configuration and operation can be complex, requiring significant technical knowledge to fine-tune the various options available.
Although these tools are powerful, the complexity of their configuration and operation can be a barrier for many users in academic environments, where specialized technical support is not always available. To fill this gap, we developed LabMonitor, a Python application designed to simplify the management of computing resources in decentralized networks of Linux machines.
LabMonitor, a Python application that is intuitive and easy to use, eliminating the need for complex configurations. Initial configuration can be done by filling in a spreadsheet with information about the machines and, optionally, the users. With the execution of a single command, the system is ready to use, allowing users to manage and monitor resources via a graphical platform. Submitting jobs to LabMonitor is done via a simple interface, which also offers e-mail notifications to update users on the status of their jobs. In addition, the system includes a resource scheduling feature, allowing users to reserve machines for specific tasks. This scheduling feature provides a structured way of planning the use of computing resources. By simplifying the process of managing computing resources, LabMonitor becomes a valuable tool for researchers who want to maximize the use of their machines without the need for advanced technical expertise. This allows researchers to devote themselves to the object of their research and not to the difficulties of managing computing resources.


PT: O gerenciamento de recursos computacionais em ambientes acadêmicos é uma tarefa essencial, especialmente quando diversas máquinas estão conectadas em rede para executar trabalhos científicos intensivos. Ferramentas como Slurm e HTCondor são amplamente utilizadas para gerenciar filas de trabalho e alocar recursos de clusters de computação. O Slurm, por exemplo, é uma ferramenta robusta projetada para o gerenciamento de clusters de computadores, onde as máquinas estão geralmente centralizadas e conectadas por redes de alta velocidade. No entanto, essa solução não é ideal para redes descentralizadas, onde máquinas podem estar espalhadas em diferentes locais e conectadas via internet. Por outro lado, o HTCondor é conhecido por sua flexibilidade em gerenciar pools de máquinas heterogêneas, incluindo redes descentralizadas. Contudo, sua configuração e operação podem ser complexas, exigindo um conhecimento técnico significativo para o ajuste fino das diversas opções disponíveis.
Embora essas ferramentas sejam poderosas, a complexidade de sua configuração e operação pode ser uma barreira para muitos usuários em ambientes acadêmicos, onde o suporte técnico especializado nem sempre está disponível. Para preencher essa lacuna, desenvolvemos o LabMonitor, uma aplicação em Python projetada para simplificar o gerenciamento de recursos computacionais em redes descentralizadas de máquinas Linux.
O LabMonitor, aplicação em Python intuitiva e fácil de usar, eliminando a necessidade de configurações complexas. A configuração inicial pode ser realizada preenchendo uma planilha com informações das máquinas e, opcionalmente, dos usuários. Com a execução de um único comando, o sistema está pronto para uso, permitindo aos usuários gerenciar e monitorar recursos por uma plataforma gráfica. A submissão de trabalhos no LabMonitor é feita por uma interface simples, que também oferece notificações por e-mail para atualizar os usuários sobre o status de seus trabalhos. Além disso, o sistema inclui uma funcionalidade de agendamento de recursos, permitindo que os usuários reservem máquinas para tarefas específicas. Esse recurso de agendamento fornece uma maneira estruturada de planejar o uso de recursos computacionais. Ao simplificar o processo de gerenciamento de recursos computacionais, o LabMonitor torna-se uma ferramenta valiosa para pesquisadores que desejam maximizar a utilização de suas máquinas sem a necessidade de expertise técnica avançada. Isso permite que os pesquisadores possam dedicar-se ao objeto de pesquisa e não às dificuldades de gerenciamento de recursos computacionais.



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