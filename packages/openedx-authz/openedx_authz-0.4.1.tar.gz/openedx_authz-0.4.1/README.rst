openedx-authz
#############

|pypi-badge| |ci-badge| |codecov-badge| |doc-badge| |pyversions-badge|
|license-badge| |status-badge|

Purpose
*******

Open edX AuthZ provides the architecture and foundations of the authorization framework. It implements the core machinery needed to support consistent authorization across the Open edX ecosystem.

This repository centralizes the architecture, design decisions, and reference implementation of a unified model for roles and permissions. It introduces custom roles, flexible scopes, and policy-based evaluation, aiming to replace the fragmented legacy system with a scalable, extensible, and reusable solution.

See the `Product Requirements document for Roles & Permissions`_ for detailed specifications and requirements.

.. _Product Requirements document for Roles & Permissions: https://openedx.atlassian.net/wiki/spaces/OEPM/pages/4724490259/PRD+Roles+Permissions

.. |pypi-badge| image:: https://img.shields.io/pypi/v/openedx-authz.svg
    :target: https://pypi.python.org/pypi/openedx-authz/
    :alt: PyPI

.. |ci-badge| image:: https://github.com/openedx/openedx-authz/actions/workflows/ci.yml/badge.svg?branch=main
    :target: https://github.com/openedx/openedx-authz/actions/workflows/ci.yml
    :alt: CI

.. |codecov-badge| image:: https://codecov.io/github/openedx/openedx-authz/coverage.svg?branch=main
    :target: https://codecov.io/github/openedx/openedx-authz?branch=main
    :alt: Codecov

.. |doc-badge| image:: https://readthedocs.org/projects/openedx-authz/badge/?version=latest
    :target: https://docs.openedx.org/projects/openedx-authz
    :alt: Documentation

.. |pyversions-badge| image:: https://img.shields.io/pypi/pyversions/openedx-authz.svg
    :target: https://pypi.python.org/pypi/openedx-authz/
    :alt: Supported Python versions

.. |license-badge| image:: https://img.shields.io/github/license/openedx/openedx-authz.svg
    :target: https://github.com/openedx/openedx-authz/blob/main/LICENSE.txt
    :alt: License

.. |status-badge| image:: https://img.shields.io/badge/Status-Experimental-yellow
