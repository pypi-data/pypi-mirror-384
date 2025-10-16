Pool API
========

This section documents the pool API.

Pool Types
----------

.. autoclass:: fastalloc.FixedPool
   :members:
   :inherited-members:

.. autoclass:: fastalloc.GrowingPool
   :members:
   :inherited-members:

.. autoclass:: fastalloc.ThreadSafePool
   :members:
   :inherited-members:

.. autoclass:: fastalloc.ThreadLocalPool
   :members:
   :inherited-members:

.. autoclass:: fastalloc.AsyncPool
   :members:
   :inherited-members:

Pool Builder
------------

.. autoclass:: fastalloc.PoolBuilder
   :members:

Example Usage
-------------

Basic Pool
^^^^^^^^^^

.. code-block:: python

   from fastalloc import Pool

   pool = Pool(MyObject, capacity=100)
   
   with pool.allocate() as obj:
       obj.process()

Growing Pool
^^^^^^^^^^^^

.. code-block:: python

   from fastalloc import GrowingPool
   from fastalloc.config import linear_growth

   pool = GrowingPool(
       MyObject,
       capacity=100,
       growth_config=linear_growth(increment=50)
   )

Thread-Safe Pool
^^^^^^^^^^^^^^^^

.. code-block:: python

   from fastalloc import ThreadSafePool

   pool = ThreadSafePool(MyObject, capacity=100)
   
   # Safe to use from multiple threads
   obj = pool.get()
   pool.release(obj)
