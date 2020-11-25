# Initial implementation courtesy of https://github.com/roee30/datargs
# under the MIT license - maintained in this repository at LICENSE-datargs

# import classes to register it in RecordClass._implementors
import datargs.records.dataclass

try:
    import datargs.records.attrs
except ImportError:
    pass
