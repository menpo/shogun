# Initial implementation courtesy of https://github.com/roee30/datargs
# under the MIT license - maintained in this repository at LICENSE-datargs

# import classes to register it in RecordClass._implementors
import shogun.records.dataclass

try:
    import shogun.records.attrs
except ImportError:
    pass
