# Packman

Packman is a service that takes codes and turns them into Docker images in a smart way, using [repo2docker](https://github.com/jupyter/repo2docker/) and [Buildpacks](https://www.heroku.com/elements/buildpacks).

## Table of Contents

- [Install](#install)
- [Configure](#configure)
- [Run](#run)
- [Supported code specifications](#supported-code-specifications)
  - [Dockerfile](#dockerfile)
  - [Custom Run](#custom-run)
  - [Makefile](#makefile)
  - [IPython/Jupyter Notebook](#ipython-jupyter-notebook)
  - [Python](#python)
  - [Java (without build tools)](#java-without-build-tools)
  - [Go](#go)
  - [CMake](#cmake)
  - [C++](#c++)
- [Contributions](#contributions)

## Install

Download the source:

```bash
git clone https://github.com/RoboEpics/packman.git
cd packman
```

## Configure

Put the required config file in the appropriate directory:

```bash
mkdir configs
cp /path/to/config/file configs/production.cfg
```

## Run

Run the main file:

```bash
PRODUCTION=1 python run.py
```

## Supported code specifications

Packman tries to find the best way to build and run your code using some predefined buildpacks.
The buildpacks are tested against the code in a specific order and the first one that accepts the code is selected to build and run the image.

It currently supports the following specifications (written in the order they are tested):

### Dockerfile

If your code has a `Dockerfile` in it's root, Packman simply uses it to build an image and run it.

### Custom Run

We defined a YAML specification to ease the building and running of your code:

```yaml
language: <language name>:<version>
build:
  env:
    <key>: <value>
  commands:
    - <bash commands>
run:
  env:
    <key>: <value>
  command: <bash command>
```

### Makefile

If a `Makefile` exists in the root of your code, a plain `make` command will be run in the root of your project.

It expects an executable file to be created in the path `./bin/out` and to be the run command for the code.

### IPython/Jupyter Notebook
If your code repository contains a single notebook file (.ipynb), the code blocks in your notebook will be executed
sequentially.

Note: To install your dependencies, you need to use IPython magic commands. For example:

```jupyter
%pip install numpy
import numpy as np
```

### Python

This buildpack will be selected if there is a `requirements.txt` or `runtime.txt` file in the root of your project.

For the run phase, it expects exactly one `.py` file in your project repository that contains the Python main file (top-level scope) check:

```python
if __name__ == "__main__":
```

### R

This buildpack expects a `DESCRIPTION` file in the root of your project.

If there is install.R script in the root of your project, it will be executed in the build phase.

For the run phase, it expects exactly one `.r` file in your project repository to be executed.

### Java (without build tools)

This buildpack will be selected if there is at least one `.java` file in your code.

In the build phase, the path of all the `.java` files will be given to the `javac` compiler at once:

```bash
javac -d out <.java file> [<.java file> ...]
```

Note: The JDK used is the latest minor version of OpenJDK 14.

For the run phase, the buildpack will try to find the file with the main method and and will use it's classpath as the argument for the `java` command:

```bash
java -cp out <main classpath>
```

Note: There should exactly be one `.java` file which has the main method. Otherwise, your code will fail to run as we cannot determine the run command.

### Go

This buildpack will be selected if there is at least one `.go` file in your code.

In the build phase, the buildpack will try to find the file with the main method and package and will run following commands:

```bash
go get ./...
go build -o bin/out <main file>
```

Note 1: There should exactly be one `.go` file which has the main method and package. Otherwise, your code will fail to run as we cannot determine the run command.

Note 2: The official Go compiler with the latest patch version of 1.14 is used to build the code.

The output of the build phase will be an executable file with the path `./bin/out` which will be used to run your code.

### CMake

This buildpack does everything the `Makefile` buildpack does with one difference in the build phase.
The command `cmake .` will be run before running the `make` command, which assumes that the output will be the generation of `Makefile`.
It then proceeds with the instructions of `Makefile` buildpack.

### C++

This buildpack will be selected if there is at least one `.cpp` file in your code.

In the build phase, the path of all the `.cpp` files will be given to the `g++` compiler at once:

```bash
g++ -o bin/out <.cpp file> [<.cpp file> ...]
```

Note: The official GCC compiler with the latest patch version of 10 is used to build the code.

The output of the build phase will be an executable file with the path `./bin/out` which will be used to run your code.

### Other

If none of the above buildpacks accept the code, The [Python](#python) buildpack will be used as the default/fallback buildpack.

## Contributions

If you have any suggestions to improve the logic of or add a buildpack, please feel free to open issues and pull requests.

Also, the documentation lacks a lot of explanations since we are under heavy development and so it needs your help to be more informative.
