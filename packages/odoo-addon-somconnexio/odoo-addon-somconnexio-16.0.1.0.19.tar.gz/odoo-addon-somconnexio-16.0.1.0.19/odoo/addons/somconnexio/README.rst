##########################
 SomConnexio - ERP System
##########################

.. |badge1| image:: https://codecov.io/gl/coopdevs/odoo-somconnexio/branch/master/graph/badge.svg?token=ZfxYjFpQBz
   :alt: codecov
   :target: https://codecov.io/gl/coopdevs/odoo-somconnexio

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html

.. |badge3| image:: https://img.shields.io/badge/maturity-Mature-brightgreen.png
   :alt: Mature
   :target: https://odoo-community.org/page/development-status

|badge1| |badge2| |badge3|

This project provides an ERP system for `Som Connexio
<https://somosconexion.coop/>`_ telecommunication users cooperative.

**************
 Installation
**************

This package requires Odoo v12.0 installed.

You can install this module using ``pip``:

.. code:: bash

   $ pip install odoo-addon-somconnexio

More info in: https://pypi.org/project/odoo-addon-somconnexio/

*************
 Development
*************

Configure local development environment
=======================================

First of all, to start development, we need to create a virtualenv in
our local machine to install the pre-commit dependencies. Using a
virtualenv with Python 3.7, we install the pre-commit hooks to execute
the linters (and in the future the formatter).

In your local environment, where you execute the ``git commit ...``
command, run:

#. Install ``pyenv``

.. code:: bash

   curl https://pyenv.run | bash

2. Build the Python version

.. code:: bash

   pyenv install 3.7.7

3. Create a virtualenv

.. code:: bash

   pyenv virtualenv 3.7.7 odoo-somconnexio

4. Activate the virtualenv

.. code:: bash

   pyenv activate odoo-somconnexio

5. Install dependencies

.. code:: bash

   pip install pre-commit

6. Install pre-commit hooks

.. code:: bash

   pyenv exec pre-commit install

Create development environment (LXC Container)
==============================================

Create the ``devenv`` container with the ``somconnexio`` module mounted
and provision it. Follow the `instructions
<https://gitlab.com/coopdevs/odoo-somconnexio-inventory#requirements>`_
in `odoo-somconnexio-inventory
<https://gitlab.com/coopdevs/odoo-somconnexio-inventory>`_.

Once created, we can stop or start our ``odoo-sc`` lxc container as
indicated here:

.. code:: bash

   $ sudo systemctl start lxc@odoo-sc
   $ sudo systemctl stop lxc@odoo-sc

To check our local lxc containers and their status, run:

.. code:: bash

   $ sudo lxc-ls -f

Start the ODOO application
==========================

Enter to your local machine as the user ``odoo``, activate the python
environment first and run the odoo bin:

.. code:: bash

   $ ssh odoo@odoo-sc.local
   $ pyenv activate odoo
   $ cd /opt/odoo
   $ set -a && source /etc/default/odoo && set +a
   $ ./odoo-bin -c /etc/odoo/odoo.conf -u somconnexio -d odoo --workers 0

To use the local somconnexio module (development version) instead of the
PyPI published one, you need to upgrade the `version in the manifest
<https://gitlab.com/coopdevs/odoo-somconnexio/-/blob/master/somconnexio/__manifest__.py#L3>`_
and then update the module with ``-u`` in the Odoo CLI.

Restart ODOO database from scratch
==================================

Enter to your local machine as the user ``odoo``, activate the python
environment first, drop the DB, and run the odoo bin to create it again:

.. code:: bash

   $ ssh odoo@odoo-sc.local
   $ pyenv activate odoo
   $ dropdb odoo
   $ cd /opt/odoo
   $ ./odoo-bin -c /etc/odoo/odoo.conf -i somconnexio -d odoo --stop-after-init

Deploy branch
=============

For tests purposes, we might want to deploy a given branch (``BRANCH``)
into a server (staging), instead of publishing a new package release
just to test some fix or new feature.

To do so, we need to enter into the server with an authorized user
(``<USER>``), and then switch to ``odoo`` user to install with pip the
package version found in the git branch.

.. code:: bash

   $ ssh <USER>@staging-odoo.somconnexio.coop
   $ sudo su - odoo
   $ cd /opt/odoo
   $ pyenv activate odoo
   $ pip install -e git+https://gitlab.com/coopdevs/odoo-somconnexio@<BRANCH>#egg=odoo12-addon-somconnexio\&subdirectory=setup/somconnexio

At this point we need to restart Odoo to load the new installed module
version.

.. code:: bash

   $ sudo systemctl stop odoo
   $ ./odoo-bin -c /etc/odoo/odoo.conf -u somconnexio -d odoo --stop-after-init --logfile /dev/stdout
   $ sudo systemctl start odoo

To restart the odoo service it is better to stop it, execute odoo with
the upgrade (``-u``) option and start it again, rather that just
``restart`` it, in case there are changes in views within the deployed
branch.

Run tests
=========

You can run the tests with this command:

.. code:: bash

   $ ./odoo-bin -c /etc/odoo/odoo.conf -u somconnexio -d odoo --stop-after-init --test-enable --workers 0

The company data is rewritten every module upgrade

Run tests with coverage
=======================

You can run the tests with a coverage report following the next steps:

#. Copy the `coveragerc
   <https://github.com/coopdevs/maintainer-quality-tools/blob/master/cfg/.coveragerc>`_
   file in your ``odoo`` base path (``/opt/odoo``) changing the
   ``include`` option to the ``somconnexio`` module path
   (``/opt/odoo_modules/somconnexio/*``).

#. Go to ``/opt/odoo``

#. Run:

.. code:: bash

   $ coverage run odoo-bin -c /etc/odoo/odoo.conf -u somconnexio -d odoo --stop-after-init --test-enable --workers 0 && coverage report --show-missing

Update CHANGELOG without running pipeline
=========================================

If you need to update the CHANGELOG but you don't need to wait for the
pipeline to end, you can put ``[skip ci]`` in your commit message and
the pipeline will be skipped. More info in
https://docs.gitlab.com/ee/ci/yaml/#skip-pipeline

**************
 Contributors
**************

-  ``Som Connexió SCCL <https://somconnexio.coop/>``

   -  Gerard Funonsas gerard.funosas@somconnexio.coop
   -  Borja Gimeno borja.gimeno@somconnexio.coop

-  ``Coopdevs Treball SCCL <https://coopdevs.coop/>``

   -  Daniel Palomar daniel.palomar@coopdevs.org
   -  César López cesar.lopez@coopdevs.org
