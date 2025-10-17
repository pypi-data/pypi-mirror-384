.. _Installation instructions:

Installation instructions
=========================

..
    SPDX-License-Identifier: CC-BY-SA-4.0
    Copyright Tumult Labs 2025

This guide will help you set up Tumult Core on your local machine.

Prerequisites
^^^^^^^^^^^^^

Tumult Core is built in `Python <https://www.python.org/>`__, so a Python installation is required to use it.
It is compatible with Python 3.10 through 3.11, and has experimental support for Python 3.12.
Because Tumult Analytics uses PySpark for computation, it also `requires Java 8 or 11 <https://archive.apache.org/dist/spark/docs/3.1.1/#downloading>`__, or Java 17 if PySpark 3.4 or later is used.

Tumult Core supports the ``x86_64`` processor architecture, as well as Apple silicon.

Below are instructions for installing these prerequisites on several common platforms.
If none of these apply to you, install Python 3 and Java from your OS package manager.
If you encounter any issues during the installation process, please `let us know <https://gitlab.com/tumult-labs/core/-/issues>`__!

.. tab-set::

   .. tab-item:: Linux (Debian-based)

       Python and ``pip``, Python's package manager, are likely already installed.
       If they are not, install them with:

       .. code-block:: bash

           apt install python3 python3-pip

       Java may already be installed as well.
       If it is not, install the Java Runtime Environment with:

       .. code-block:: bash

           apt install default-jre-headless


   .. tab-item:: Linux (Red Hat-based)

       Python and ``pip``, Python's package manager, may already be installed.
       On some releases, Python 2 may be installed by default, but not Python 3.
       To install Python 3, run:

       .. code-block:: bash

           yum install python3 python3-pip

       To install Java, run:

       .. code-block:: bash

           yum install java-1.8.0-openjdk-headless

       Note that despite the package name, this will install Java 8.


   .. tab-item:: macOS

       The below instructions assume the use of `Homebrew <https://brew.sh/>`__ for managing packages.
       If you do not already have Homebrew, it can be installed with:

       .. code-block:: bash

           /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

       Python may be installed with:

       .. code-block:: bash

           brew install python@3.11

       And Java may be installed with:

       .. code-block:: bash

           brew install openjdk@11

       For the system Java wrappers to find this JDK you may need to symlink it by following the instructions that Homebrew provides upon installation.
       The command will look similar to the following, but will differ depending on your CPU architecture:

       .. code-block:: bash

           sudo ln -sfn /opt/homebrew/opt/openjdk@11/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-11.jdk

       If you have more than one Java version installed on your system, use Java 11 by setting ``JAVA_HOME`` to ``$(/usr/libexec/java_home -v11)``.
       This can be done by, for example, adding ``export JAVA_HOME=$(/usr/libexec/java_home -v11)`` to ``.bashrc`` and then restarting your shell.

   .. tab-item:: Windows

       The only supported way to install Tumult Core on Windows is using the `Windows Subsystem for Linux (WSL) <https://docs.microsoft.com/en-us/windows/wsl/about>`__.
       Once you have installed your preferred Linux distribution with WSL, follow the corresponding Linux installation instructions to get Tumult Core set up.


Installation
^^^^^^^^^^^^

Once the above prerequisites are installed, Tumult Core can be installed using ``pip3`` with:

.. code-block:: bash

    pip3 install tmlt.core

This will automatically install all of its Python dependencies as well.

It is recommended, though not required, to install Tumult Core in a `virtual environment <https://packaging.python.org/en/latest/tutorials/installing-packages/#creating-virtual-environments>`__ to minimize interactions with your system Python environment.
