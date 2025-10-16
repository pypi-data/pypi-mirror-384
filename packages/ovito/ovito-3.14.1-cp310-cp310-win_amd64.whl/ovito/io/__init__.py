"""
This module provides two high-level functions for reading and data files:

    * :py:func:`import_file`
    * :py:func:`export_file`

Furthermore, it contains the base class for custom :ref:`file readers <writing_custom_file_readers>` and :ref:`file writers <writing_custom_file_writers>`:

    * :py:class:`FileReaderInterface`
    * :py:class:`FileWriterInterface`

"""

__all__ = ['import_file', 'export_file', 'FileReaderInterface', 'FileWriterInterface']