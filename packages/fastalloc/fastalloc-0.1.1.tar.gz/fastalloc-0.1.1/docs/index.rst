fastalloc Documentation
=======================

Welcome to fastalloc's documentation!

fastalloc is a high-performance Python memory pool library providing pre-allocated
object pools for frequently created and destroyed objects. It reduces allocation
overhead, minimizes garbage collection pressure, and eliminates memory fragmentation.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   guides/getting_started
   guides/architecture
   guides/performance_guide
   api/pool
   api/handle
   api/config

Features
--------

* **Multiple Pool Types**: Fixed-size, growing, thread-safe, thread-local, and async pools
* **High Performance**: < 50ns object acquisition, 80%+ reduction in GC cycles
* **Thread Safety**: Built-in thread-safe and thread-local pool variants
* **Async Support**: First-class async/await integration
* **Type Safe**: Full type hints with mypy strict mode support
* **Easy to Use**: Context managers, decorators, and builder patterns
* **Statistics**: Built-in performance monitoring and reporting

Quick Start
-----------

.. code-block:: python

   from fastalloc import Pool

   pool = Pool(MyObject, capacity=1000)

   with pool.allocate() as obj:
       obj.do_something()
       result = obj.get_result()

Installation
------------

.. code-block:: bash

   pip install fastalloc

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
