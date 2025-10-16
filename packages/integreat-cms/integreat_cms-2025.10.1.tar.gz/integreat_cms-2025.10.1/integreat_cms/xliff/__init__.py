"""
This package contains helper classes for the handling of XLIFF files.
It can handle XLIFF files of version 1.2 (see :mod:`~integreat_cms.xliff.xliff1_serializer`) and 2.0 (see
:mod:`~integreat_cms.xliff.xliff2_serializer`).
Additionally, it contains a :mod:`~integreat_cms.xliff.base_serializer` containing shared functionality of both XLIFF versions and a
:mod:`~integreat_cms.xliff.generic_serializer`, which inspects the given XLIFF file and delegates its deserialization to the
respective version's deserializer.

The interface follows Django's standard serialization syntax (see :doc:`django:topics/serialization`)::

    serializers.serialize("xliff", queryset)
    serializers.deserialize("xliff", xliff_file)

To facilitate the handling of XLIFF files in the views, this package also contains utilities in :mod:`~integreat_cms.xliff.utils`.
"""
