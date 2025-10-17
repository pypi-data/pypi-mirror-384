# tifffile/docs/make.py

"""Make documentation for tifffile package using Sphinx."""

import os
import sys

from sphinx.cmd.build import main

here = os.path.dirname(__file__)
sys.path.insert(0, os.path.split(here)[0])
path = os.environ.get('PATH')
if path:
    os.environ['PATH'] = os.path.join(sys.exec_prefix, 'Scripts') + ';' + path

import tifffile  # noqa

members = [
    'imread',
    'imwrite',
    'memmap',
    'TiffWriter',
    'TiffFile',
    # 'TiffFileError',
    'TiffFormat',
    'TiffPage',
    'TiffFrame',
    'TiffPages',
    'TiffTag',
    'TiffTags',
    'TiffTagRegistry',
    'TiffPageSeries',
    'TiffSequence',
    'FileSequence',
    'zarr.ZarrStore',
    'zarr.ZarrTiffStore',
    'zarr.ZarrFileSequenceStore',
    # Constants
    'DATATYPE',
    'SAMPLEFORMAT',
    'PLANARCONFIG',
    'COMPRESSION',
    'PREDICTOR',
    'EXTRASAMPLE',
    'FILETYPE',
    'PHOTOMETRIC',
    'RESUNIT',
    'CHUNKMODE',
    'TIFF',
    # classes
    'FileHandle',
    'OmeXml',
    # 'OmeXmlError',
    'Timer',
    'NullContext',
    'StoredShape',
    'TiledSequence',
    # functions
    'logger',
    'repeat_nd',
    'natural_sorted',
    'parse_filenames',
    'matlabstr2py',
    'strptime',
    'imagej_metadata_tag',
    'imagej_description',
    # 'read_scanimage_metadata',
    'read_micromanager_metadata',
    'read_ndtiff_index',
    'create_output',
    'hexdump',
    'xml2dict',
    'tiffcomment',
    'tiff2fsspec',
    'lsm2bin',
    'validate_jhove',
    'imshow',
    '.geodb',
]

title = f'tifffile {tifffile.__version__}'
underline = '=' * len(title)
members_ = []
for name in members:
    if not name:
        continue
    if '.' in name[1:]:
        name = name.rsplit('.', 1)[-1]
    members_.append(name.replace('.', '').lower())
memberlist = '\n   '.join(members_)

with open(here + '/index.rst', 'w') as fh:
    fh.write(
        f""".. tifffile documentation

.. currentmodule:: tifffile

{title}
{underline}

.. automodule:: tifffile

.. toctree::
   :hidden:
   :maxdepth: 2

   genindex
   license
   revisions
   examples


.. toctree::
   :hidden:
   :maxdepth: 2

   {memberlist}


"""
    )


with open(here + '/genindex.rst', 'w') as fh:
    fh.write(
        """
Index
=====

"""
    )

with open(here + '/license.rst', 'w') as fh:
    fh.write(
        """
License
=======

.. include:: ../LICENSE
"""
    )


with open(here + '/examples.rst', 'w') as fh:
    fh.write(
        """
Examples
========

See `#examples <index.html#examples>`_.
"""
    )


with open(here + '/revisions.rst', 'w') as fh:
    fh.write(""".. include:: ../CHANGES.rst""")


with open('tiff.rst', 'w') as fh:
    fh.write(
        """
.. currentmodule:: tifffile

TIFF
====

.. autoclass:: tifffile.TIFF
    :members:

.. autoclass:: tifffile._TIFF
    :members:
"""
    )


automodule = """.. currentmodule:: {module}

{name}
{size}

.. automodule:: {module}.{name}
    :members:

"""

autoclass = """.. currentmodule:: {module}

{name}
{size}

.. autoclass:: {module}.{name}
    :members:

"""

automethod = """.. currentmodule:: {module}

{name}
{size}

.. autofunction:: {name}

"""

for name in members:
    if not name or name == 'TIFF':
        continue

    if '.' in name[1:]:
        module, name = name.rsplit('.', 1)
        module = f'tifffile.{module}'
    else:
        module = 'tifffile'

    if name[0] == '.':
        template = automodule
        name = name[1:]
    elif name[0].isupper():
        template = autoclass
    else:
        template = automethod
    size = '=' * len(name)

    with open(f'{here}/{name.lower()}.rst', 'w') as fh:
        fh.write(template.format(module=module, name=name, size=size))

main(['-b', 'html', here, here + '/html'])

os.system('start html/index.html')
