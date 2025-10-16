Getting Started
===============

This guide will help you get started with fastalloc.

Installation
------------

Install fastalloc using pip:

.. code-block:: bash

   pip install fastalloc

Basic Usage
-----------

Creating a Pool
^^^^^^^^^^^^^^^

.. code-block:: python

   from fastalloc import Pool

   # Create a pool of MyObject with capacity 100
   pool = Pool(MyObject, capacity=100)

Getting and Releasing Objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Get an object from the pool
   obj = pool.get()
   
   # Use the object
   obj.do_something()
   
   # Return it to the pool
   pool.release(obj)

Using Context Managers
^^^^^^^^^^^^^^^^^^^^^^

The recommended way to use pools is with context managers:

.. code-block:: python

   with pool.allocate() as obj:
       obj.do_something()
   # Object is automatically released

Using the Decorator
^^^^^^^^^^^^^^^^^^^

Attach a pool directly to your class:

.. code-block:: python

   from fastalloc import pooled

   @pooled(capacity=1000, thread_safe=True)
   class Worker:
       def process(self, data):
           pass

   with Worker.pool.allocate() as worker:
       worker.process(data)

Builder Pattern
^^^^^^^^^^^^^^^

For advanced configuration:

.. code-block:: python

   from fastalloc import Pool, GrowthStrategy

   pool = (Pool.builder()
       .type(Entity)
       .capacity(10_000)
       .max_capacity(100_000)
       .growth_strategy(GrowthStrategy.LINEAR, increment=1000)
       .pre_initialize(True)
       .reset_method('reset')
       .enable_statistics(True)
       .build())

Next Steps
----------

* Learn about different pool types in the :doc:`architecture` guide
* Optimize performance with the :doc:`performance_guide`
* Explore the full :doc:`../api/pool` reference
