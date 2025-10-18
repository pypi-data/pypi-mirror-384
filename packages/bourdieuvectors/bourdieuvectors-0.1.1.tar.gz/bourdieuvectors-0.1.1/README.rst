Python Library bourdieuvectors
========================================

`bourdieuvectors` is a library that allows to inferr bourdieuvectors. Usage see https://bourdieuvectors.com/.

Installation
~~~~~~~~~~~~

Install this library using pip.

Supported Python Versions
^^^^^^^^^^^^^^^^^^^^^^^^^
Python >= 3.6

Mac/Linux
^^^^^^^^^

.. code-block:: console

    pip install virtualenv
    virtualenv <your-env>
    source <your-env>/bin/activate
    <your-env>/bin/pip install bourdieuvectors


Windows
^^^^^^^

.. code-block:: console

    pip install virtualenv
    virtualenv <your-env>
    <your-env>\Scripts\activate
    <your-env>\Scripts\pip.exe install bourdieuvectors


Example Usage
~~~~~~~~~~~~~

Extends a Pandas DataFrame with the vectors.

.. code:: python

    import pandas as pd
    from bourdieuvectors import get_bourdieu_vector

    data = pd.DataFrame({
        "cultural_event": ["american football"]
    })

    vector_df = data["cultural_event"].apply(get_bourdieu_vector).apply(pd.Series)
    data_with_vectors = pd.concat([data, vector_df], axis=1)

    print(data_with_vectors)
    data_with_vectors.to_csv("bourdieuvectors_data.csv")
