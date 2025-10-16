core-aws
===============================================================================

This project/library contains common elements related
to AWS services...

===============================================================================

.. image:: https://img.shields.io/pypi/pyversions/core-aws.svg
    :target: https://pypi.org/project/core-aws/
    :alt: Python Versions

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target: https://gitlab.com/bytecode-solutions/core/core-aws/-/blob/main/LICENSE
    :alt: License

.. image:: https://gitlab.com/bytecode-solutions/core/core-aws/badges/release/pipeline.svg
    :target: https://gitlab.com/bytecode-solutions/core/core-aws/-/pipelines
    :alt: Pipeline Status

.. image:: https://readthedocs.org/projects/core-aws/badge/?version=latest
    :target: https://readthedocs.org/projects/core-aws/
    :alt: Docs Status

.. image:: https://img.shields.io/badge/security-bandit-yellow.svg
    :target: https://github.com/PyCQA/bandit
    :alt: Security

|

Execution Environment
---------------------------------------

Install libraries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

    pip install --upgrade pip
    pip install virtualenv
..

Create the Python Virtual Environment.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

    virtualenv --python={{python-version}} .venv
    virtualenv --python=python3.11 .venv
..

Activate the Virtual Environment.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

    source .venv/bin/activate
..

Install required libraries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

    pip install .
..

Optional libraries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

    pip install '.[all]'      # For all...
    pip install '.[core-cdc]' # For CDC flows...
    pip install '.[tests]'    # For tests execution...
..

Check tests and coverage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

    python manager.py run-tests
    python manager.py run-tests --test-type integration
    python manager.py run-coverage

    # Having proper AWS credentials...
    python manager.py run-tests --test-type functional --pattern "*.py"
..
