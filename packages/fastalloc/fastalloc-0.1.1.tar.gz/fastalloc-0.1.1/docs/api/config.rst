Configuration API
=================

Configuration for pool behavior.

Growth Strategies
-----------------

.. autoclass:: fastalloc.config.GrowthStrategy
   :members:

.. autoclass:: fastalloc.config.GrowthConfig
   :members:

.. autofunction:: fastalloc.config.linear_growth

.. autofunction:: fastalloc.config.exponential_growth

Initialization Strategies
-------------------------

.. autoclass:: fastalloc.config.InitializationStrategy
   :members:

Statistics
----------

.. autoclass:: fastalloc.StatsCollector
   :members:

.. autoclass:: fastalloc.StatsReporter
   :members:

Example Usage
-------------

Growth Configuration
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from fastalloc import GrowingPool
   from fastalloc.config import linear_growth

   pool = GrowingPool(
       MyObject,
       capacity=100,
       growth_config=linear_growth(increment=50, max_capacity=1000)
   )

Statistics Collection
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from fastalloc import Pool
   from fastalloc.stats import StatsReporter

   pool = Pool(MyObject, capacity=100, enable_statistics=True)
   
   # Use pool...
   
   reporter = StatsReporter(pool.stats())
   reporter.print_report()
