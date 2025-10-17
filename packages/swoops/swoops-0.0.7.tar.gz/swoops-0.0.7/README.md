
# SWOOPS Optimization GUI

## Setup, Workflows, Orchestrate, Optimize, Plot, Surrogates

#### Author: Jason Krist

#### Date: October 1st, 2025

## Description

SWOOPS is an in-progress Graphical User Interface (GUI) designed for parametric optimization. Each letter of SWOOPS stands for a feature set that is within the scope of the tool. [Swoops](https://www.mariowiki.com/Swoop) are also the name for the bats in super mario, hence the mascot for the tool is a swoop named Zippy, which is an homage to the Microsoft Office Assistance [Clippy](https://en.wikipedia.org/wiki/Office_Assistant).

<h2 id="table-of-contents">Table of Contents</h2>

1. [Why Create Swoops?](#why-create-swoops)
1. [Core Tenets](#core-tenets)
1. [Feature Sets](#feature-sets)
1. [Architectural Choices](#architectural-choices)
1. [Target Uses](#target-uses)
1. [Install](#install)
1. [Usage (Incomplete)](#usage-incomplete)
1. [Roadmap](#roadmap)

<h2 id="why-create-swoops">Why Create Swoops?</h2>

SWOOPS is a culmination of everything I want in an optimization GUI. Below are my grievances with the state of current optimization interfaces:

- COTS (Commercial Off The Shelf) tools are expensive, lack necessary configurability, and prioritize supporting tools within their own ecosystem
- COTS tools have architectures which make interoperability with open source optimization frameworks difficult
- Open source frameworks have little to no GUIs, with [DAKOTA](https://github.com/snl-dakota) being the exception
- Custom tools have high [tech debt](https://en.wikipedia.org/wiki/Technical_debt) and steep learning curves
- Unfriendly user experience across the board

Therefore, I have developed SWOOPS with the "Core Tenets" below in mind.

<h2 id="core-tenets">Core Tenets</h2>

[Table of Contents](#table-of-contents)

1. Democratize Optimization
1. Prioritize User Experience
1. Seamless Automation
1. Free and Open Source Core Program
1. Modularity is a Must
1. Encourage Community Collaboration
1. Make Lasting Contributions

<h2 id="feature-sets">Feature Sets</h2>

[Table of Contents](#table-of-contents)

1. Setup - prepare files or processes for optimization, which includes file parsers and workflow templates
1. Workflows - specify tasks, inputs, outputs, and dependencies of a workflow
1. Orchestrate - export and execute a workflow. See progress as it completes
1. Optimize - specify constraints, objectives, algorithms, and check ongoing optimization progress
1. Plot - create user-defined plots from existing data sets or optimization results
1. Surrogates - create and test surrogate models for utilizing in multi-fidelity optimization

<h2 id="architectural-choices">Architectural Choices</h2>

[Table of Contents](#table-of-contents)

- Written in Python due to the breadth of experience for develops in this field, and because it is the language of choice for existing frameworks
- Primarily target desktop platform for architectural simplicity
- [QT](https://www.qt.io/) ([Pyside6](https://doc.qt.io/qtforpython-6/)) chosen for being the most robust, feature rich, and cross-platform Desktop GUI Framework in Python

<h2 id="target-uses">Target Uses</h2>

[Table of Contents](#table-of-contents)

- Generic workflow automation
- DOE (Design of Experiments) and analyzing interaction effects
- Early conceptual design optimization with derivatives and tightly coupled variables
- Gradient free, multi-fidelity optimization for design tuning
- Multi-objective optimization for pareto optimal solutions

<h2 id="install">Install</h2>

[Table of Contents](#table-of-contents)

```
pip install swoops
```

<h2 id="usage-incomplete">Usage (Incomplete)</h2>

[Table of Contents](#table-of-contents)

python test_app.py

![Dark Mode](https://raw.githubusercontent.com/jkrist2696/swoops/refs/heads/master/images/gui_example.png)

![Light Mode](https://raw.githubusercontent.com/jkrist2696/swoops/refs/heads/master/images/gui_example_light.png)

![Video Test](https://raw.githubusercontent.com/jkrist2696/swoops/refs/heads/master/images/smaller.gif)

Add more GUI usage steps and images here.

### Python In-Line Usage (Incomplete)

Probably don't need this section.

### Command Line Usage (Incomplete)

swoops [-h] [-file FILE] [-b] 

<h2 id="roadmap">Roadmap</h2>

[Table of Contents](#table-of-contents)

#### Complete

1. Backend data structures which can represent most optimization setups
1. Widgets
    1. Docked windows - each widget is nested in a dockable window
    1. Tree View - visualize nested data structures or file system
    1. Edit Window - visualize and edit all attributes of a data structure
    1. Table View - visualize and edit a large set of entities and their attributes in a table
    1. Web View - load local HTML files (Plotly, N2 Diagram) or online web pages
    1. Plot View - load interactive Matplotlib plots
    1. Python Code Editor - text edit python scripts
1. Undoablility for Data Structure and Widget related changes (new, delete, edit)
1. Tabs which can contain different widgets and layouts
1. Rudimentary export script for swoops data structures to GEMSEO optimization format

#### In Progress

1. Block Diagram Viewer - visualize Workflow, Dependencies, and data flow
1. Get App fully functional for simple demos. This encompasses many small To-Do's
1. Python Command Window - run python commands in-session and see results

#### Future Plans

1. File Parser for defining variable locations in input or output files
1. Workflow "Templates" can be created with Empty values which are highlighted to user to complete
1. Create a "Library" of common tasks with drag-and-drop functionality
1. User-friendly, Documented Python API
1. Custom optimization orchestrator with modular optimizer interface
1. "Zippy" button opens a helper overlay for tutorials and trainings
1. Out-of-the-Box interoperability with [GEMSEO](https://gemseo.readthedocs.io/en/stable/index.html), [OpenMDAO](https://openmdao.org/newdocs/versions/latest/main.html#), and [Pymoo](https://pymoo.org/). Potentially work on supporting [Philote](https://mdo-standards.github.io/Philote-MDO/intro.html), [CSDL](https://lsdolab.github.io/csdl/), and [SUAVE](https://suave.stanford.edu/).

[Table of Contents](#table-of-contents)

## Read The Docs (Incomplete)

Download "docs" folder or [check preview](https://www.google.com).

## Contributing

Message me on Github.

## License

[GNU GPLv3](https://choosealicense.com/licenses/gpl-3.0/)

## Copyright:

(c) 2025, Jason Krist
