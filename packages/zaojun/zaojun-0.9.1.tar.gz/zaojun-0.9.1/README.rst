""""""""""""""""""""""""""
zaojun
""""""""""""""""""""""""""

|Repo| |CI| |Checked with|

|AGPL|



zaojun is a command line (CLI) tool to check versions of your dependencies as defined in `pyproject.toml`
file against the latest version published on `PyPi`_

Install and run from `Source <https://codeberg.org/marvin8/zaojun>`_
==============================================================================================

Alternatively you can run zaojun from source by cloning the repository using the following command line::

    git clone https://codeberg.org/marvin8/zaojun.git

zaojun uses `uv`_ for dependency control, please install UV before proceeding further.

Before running, make sure you have all required python modules installed. With uv this is as easy as::

    uv sync

Run zaojun with the command `uv run zaojun`

As a `pre-commit`_ hook
=========================

To run zaojun as a `pre-commit`_ hook, just add the below snippet into your `.pre-commit-config.yaml` file:

.. code-block:: yaml

   - repo: https://codeberg.org/marvin8/zaojun
   rev: 0.9.0
   hooks:
     - id: zaojun
       args:
       - "--groups"


Significance of Name zaojun
===========================

Zao Jun is the Chinese god that acts as a household guardian, overseeing domestic harmony and reporting family conduct to the heavens—reinforcing moral behavior within the kin unit.
This tool tries to keep your project and its dependencies in harmony. It doesn't do any reporting to third parties though :)

I know is a little far fetched, but I like it, so there :)

If you'd like to go down the rabbit hole of learning more about Zao Jun, the Chinese kitchen god, you can follow these links:

   - `Wikipedia`_
   - `Columbia University`_

.. _Wikipedia: https://en.wikipedia.org/wiki/Kitchen_God
.. _Columbia University: https://afe.easia.columbia.edu/cosmos/prb/earthly.htm


Licensing
=========
zaojun is licensed under the `GNU Affero General Public License v3.0 <http://www.gnu.org/licenses/agpl-3.0.html>`_

Supporting zaojun
==============================

There are a number of ways you can support fedibooster:

- Create an issue with problems or ideas you have with/for zaojun
- Create a pull request if you are more of a hands on person.
- You can `buy me a coffee <https://www.buymeacoffee.com/marvin8>`_.
- You can send me small change in Monero to the address below:

Monero donation address
-----------------------
``89g4QvoWjuEYeLURNZfQwr4XWWYE36U15ZgKzunwxHiUd78vGWy6wxKCet6KF9ij4fEMs7WP4mtPRa4xj6rGneceTnDMN2X``


.. _uv: https://docs.astral.sh/uv/

.. _pre-commit: https://pre-commit.com

.. _PyPi: https://pypi.org

.. |AGPL| image:: https://www.gnu.org/graphics/agplv3-with-text-162x68.png
    :alt: AGLP 3 or later
    :target:  https://codeberg.org/marvin8/zaojun/src/branch/main/LICENSE.md

.. |Repo| image:: https://img.shields.io/badge/repo-Codeberg.org-blue
    :alt: Repo at Codeberg.org
    :target: https://codeberg.org/marvin8/zaojun

.. |Checked with| image:: https://img.shields.io/badge/pip--audit-Checked-green
    :alt: Checked with pip-audit
    :target: https://pypi.org/project/pip-audit/

.. |CI| image:: https://ci.codeberg.org/api/badges/13971/status.svg
    :alt: CI / Woodpecker
    :target: https://ci.codeberg.org/repos/13971
