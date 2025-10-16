Handle API
==========

Handles manage the lifetime of pooled objects.

Handle Types
------------

.. autoclass:: fastalloc.handle.ContextHandle
   :members:

.. autoclass:: fastalloc.handle.OwnedHandle
   :members:

.. autoclass:: fastalloc.handle.WeakHandle
   :members:

Usage Examples
--------------

Context Handle
^^^^^^^^^^^^^^

.. code-block:: python

   from fastalloc import Pool

   pool = Pool(MyObject, capacity=10)
   
   # Context handle auto-releases
   with pool.allocate() as obj:
       obj.process()

Owned Handle
^^^^^^^^^^^^

.. code-block:: python

   from fastalloc.handle import OwnedHandle

   pool = Pool(MyObject, capacity=10)
   obj = pool.get()
   
   handle = OwnedHandle(obj, pool.release)
   
   # Use object
   handle.get().process()
   
   # Explicit release
   handle.release()

Weak Handle
^^^^^^^^^^^

.. code-block:: python

   from fastalloc.handle import WeakHandle

   pool = Pool(MyObject, capacity=10)
   obj = pool.get()
   
   handle = WeakHandle(obj, pool.release)
   
   # Check if object still alive
   if handle.is_alive():
       handle.get().process()
