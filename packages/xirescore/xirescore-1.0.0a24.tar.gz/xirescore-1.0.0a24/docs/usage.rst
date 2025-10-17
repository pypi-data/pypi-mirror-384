=====
Usage
=====

xiRESCORE can be used in different ways. First of all, there are different options for data sources and result targets:

* Parquet files
* CSV files
* XiSearch2 databases
* Pandas DataFrames

Secondly there are different ways of calling xiRESCORE: Either as a Python module in code or via CLI (see examples).

To use xiRESCORE in Python code use the XiRescore class:

.. autoclass:: xirescore.XiRescore::XiRescore
   :no-index:

XiRescore accepts an option dictionary as configuration. The passed options will be merged with the default options,
such that all existing default values or arrays are replaces. A special case are ``rescoring.model_params`` which replace the default dictionary if provided.
The available options and default values can be found under :ref:`options`.

.. note::
  The first thing you probably want to configure are the input columns required. Notice that some columns can be derived by others if not provided.
  However, providing them might increase performance.

------
Output
------

After rescoring the result will contain all original columns plus a new score with default name ``rescore`` and
subscores ``rescore_{i}`` for every ``i``'th k-fold cross-validation model. Futhermore, the result will contain a column
``rescore_slice`` that indicates which model has been used for rescoring in case of a training sample, a column
``rescore_top_ranking`` indicating if a match is the top ranking match for the given spectrum and a column
``rescore_rank`` indicating which rank a match has for the according spectrum. The base name ``rescore`` can be
configured in the :ref:`options`.

-----------------
DataFrame example
-----------------

This example shows how to use xiRESCORE directly in code with a DataFrame as input and no file or DB output:

.. code-block:: python

  from xirescore.XiRescore import XiRescore

  # ...

  options = {
      'input': {
          'columns': {
              'features': [
                  'feat_col1',
                  'feat_col2',
                  'feat_col3',
                  # ...
              ]
          }
      },
      # ...
  }

  rescorer = XiRescore(
      input_path=df,
      options=options,
  )

  rescorer.run()

  df_out = rescorer.get_rescored_output()


-------------------
CSV/Parquet example
-------------------

This example shows how to use xiRESCORE with a CSV input and Parquet output:

.. code-block:: python

  from xirescore.XiRescore import XiRescore

  # ...

  options = {
      'input': {
          'columns': {
              'features': [
                  'feat_col1',
                  'feat_col2',
                  'feat_col3',
                  # ...
              ]
          }
      },
      # ...
  }

  rescorer = XiRescore(
      input_path='test_data.csv.gz',
      output_path='result.parquet',
      options=options,
  )

  rescorer.run()


-----------
CLI example
-----------

This example shows how to xiRESCORE from command line:

.. code-block:: bash

  xirescore -i input.parquet -o result.parquet -c options.yaml

The file ``options.yaml`` contains the options you would usually pass to the ``XiRescore``-class:

.. code-block:: yaml

  input:
    columns:
      features:
        - feat_col1
        - feat_col1
        - feat_col2
        # ...

-----------
Schema overrides example
-----------

When loading CSV files, xiRESCORE (or rather `polars <https://docs.pola.rs/>`__) tries to guess the datatypes based on
a sample of the input data. To manually set the datatypes of certain columns use the ``input.schema_overrides`` option:

.. code-block:: yaml

  input:
    schema_overrides:
      columnX: String
      columnY: Int32  # polars datatype name
      columnZ: int    # python datatype name

Valid options for datatypes are `str`, `int`, `float` and `bool` for Python datatypes
or any `Polars datatype <https://docs.pola.rs/api/python/stable/reference/datatypes.html>`__.
