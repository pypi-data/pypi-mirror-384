'''
Flexible classes to represent tables, records & links in the data request,
as obtained from the Airtable json "raw export" of data request content.

The purpose is to create generic objects allowing intuitive navigation/coding
of the data request "network" (i.e., linked records). While the dict variables from
the export can be used directly for this, manipulating them is more complex and
error-prone.

Each record from a table is represented as a DreqRecord object.
The object's attribute names are determined automatically from the Airtable field
names, which are the names of table columns in Airtable, following simple formatting
rules (e.g. change space to underscore). Original names of Airtable fields
are stored as well, allowing unambiguous comparison with Airtable content.
'''

from dataclasses import dataclass
from dataclasses import field as dataclass_field  # "field" is used often for Airtable column names, so need a different name here

import sys
PYTHON_VERSION = (sys.version_info.major, sys.version_info.minor)
if PYTHON_VERSION < (3, 9):
    from typing import Set


PRIORITY_LEVELS = ('core', 'high', 'medium', 'low')  # names of priority levels, ordered from highest to lowest priority


def format_attribute_name(k):
    '''
    Adjust input string so that it's suitable for use as an object attribute name using the dot syntax (object.attribute).
    '''
    k = k.strip()
    k = k.lower()
    substitute = {
        # replacement character(s) : [characters to replace with the replacement character]
        '_': list(' .-+=?!@#$%^*:;') + ['_&_', '/', '\\'],
        '': list('(){}[]<>|,"~'),
        # Note: list(str) = [single chars in the string], example: list('ab') = ['a', 'b']
    }
    for replacement in substitute:
        for s in substitute[replacement]:
            k = k.replace(s, replacement)
    check_for_invalid_chars = ['&', '/', '-']
    for s in check_for_invalid_chars:
        assert s not in k, f'{s} is invalid character for attribute {k}'
    return k


###############################################################################
# Generic classes
# (not specific to different data request tables)

@dataclass
class DreqLink:
    '''
    Generic class to represent a link to a record in a table.

    The table_id, record_id reference the record. They are used to locate a record.
    '''
    table_id: str
    record_id: str
    table_name: str  # useful as a human-readable lable
    # record_name : str  # not all tables have a "name" attribute, so would need to choose this based on table

    def __repr__(self):
        # return self.record_id
        return f'link: table={self.table_name}, record={self.record_id}'


class DreqRecord:
    '''
    Generic class to represent a single record from a table.
    '''

    def __init__(self, record, field_info):
        # Loop over fields in the record
        for field_name, value in record.items():

            # Check if the field contains links to records in other tables
            if 'linked_table_id' in field_info[field_name]:
                assert isinstance(value, list), 'links should be a list of record identifiers'
                for m, record_id in enumerate(value):
                    # Change the record_id str into a more informative object representing the link
                    d = {
                        'table_id': field_info[field_name]['linked_table_id'],
                        'table_name': field_info[field_name]['linked_table_name'],
                        'record_id': record_id,
                        # 'record_name' : '', # fill this in later if desired (finding it here would require access to whole base)
                    }
                    value[m] = DreqLink(**d)

            # Adjust the field name so that it's accessible as an object attribute using the dot syntax (object.attribute)
            key = field_info[field_name]['attribute_name']
            assert not hasattr(self, key), f'for field {field_name}, key already exists: {key}'
            setattr(self, key, value)

    def __repr__(self):
        # return pprint.pformat(vars(self))
        l = []
        show_list_entries = 2
        for k, v in self.__dict__.items():
            s = f'  {k}: '
            if isinstance(v, list):
                # If attribute is a list of links, show only show_list_entries of them.
                # This makes it easier to view records that contain very long lists of links.
                indent = ' ' * len(s)
                n = len(v)
                s += f'{v[0]}'
                for m in range(1, min(show_list_entries, n)):
                    s += '\n' + indent + f'{v[m]}'
                if n > show_list_entries:
                    # s += '\n' + indent + f'... ({n} entries)'
                    s += '\n' + indent + f'... ({n} in list, first {show_list_entries} shown)'
            else:
                # Attribute is just a regular string or number.
                s = f'{s}{v}'
            l.append(s)
        return '\n' + '\n'.join(l)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class DreqTable:
    '''
    Generic class to represent an table from the data request Airtable raw export json file (dict).

    Here both "field" and "attribute" are used to refer to the columns in the table.
    "field"  refers to the name of a column as it appears in Airtable.
    "attribute" refers to the name of the column converted to the name of a record object attribute.
    '''

    def __init__(self, table, table_id2name):

        # Set attributes that describe the table
        self.table_id = table['id']
        self.table_name = table['name']
        self.base_id = table['base_id']
        self.base_name = table['base_name']
        self.description = table['description']

        # Get info about fields (columns) in the table records, which are used below when creating record objects
        fields = table['fields']  # dict giving info on each field, keyed by field_id (example: 'fld61d8b5mzI45H8F')
        field_info = {field['name']: field for field in fields.values()}  # as fields dict, but use field name as the key
        assert len(fields) == len(field_info), 'field names are not unique!'
        # (since field names are keys in record dicts, their names should be unique)
        attr2field = {}
        links = {}
        for field_name, field in field_info.items():
            # Determine an attribute name for the field.
            # The field name is the name from Airtable, but it may include spaces or other forbidden characters.
            attr = format_attribute_name(field_name)
            field['attribute_name'] = attr
            attr2field[attr] = field_name  # remember the Airtable name, in case useful later
            # If field is a link, add the name of the linked table to field_info.
            if 'linked_table_id' in field:
                field['linked_table_name'] = table_id2name[field['linked_table_id']]
                links[attr] = field['linked_table_name']

        # Loop over records to create a record object representing each one
        records = table['records']  # dict giving info on each record, keyed by record_id (example: 'reczyxsKbAseqCisA')
        for record_id, record in records.items():
            if len(record) == 0:
                # don't allow empty records!
                # print(f'skipping empty record {record_id} in table {self.table_name}')
                continue
            # Replace record dict with a record object
            records[record_id] = DreqRecord(record, field_info)

        # attributes for the collection of records (table rows)
        self.records = records
        self.record_ids = sorted(self.records.keys(), key=str.lower)
        self.nrec = len(self.record_ids)

        # attributes describing the attributes (columns) in each individual record
        self.field_info = field_info
        self.attr2field = attr2field
        self.links = links

    def rename_attr(self, old, new):
        if old in self.attr2field:
            assert new not in self.attr2field, 'Record attribute already exists: ' + new

            field_name = self.attr2field[old]
            self.field_info[field_name]['attribute_name'] = new

            self.attr2field[new] = self.attr2field[old]
            self.attr2field.pop(old)

            if old in self.links:
                self.links[new] = self.links[old]
                self.links.pop(old)

            for record in self.records.values():
                if not hasattr(record, old):
                    continue
                setattr(record, new, getattr(record, old))
                delattr(record, old)

    def __repr__(self):
        # return f'Table: {self.table_name}, records: {self.nrec}'
        s = f'table: {self.table_name}'
        s += f'\ndescription: {self.description}'
        s += f'\nrecords (rows): {self.nrec}'
        s += '\nattributes (columns): ' + ', '.join(sorted(self.attr2field))
        if len(self.links) > 0:
            s += '\nlinks to other tables:'  # ({}):'.format(len(self.links))
            for attr, target in sorted(self.links.items()):
                s += f'\n  {attr} -> {target}'
        return s

    def get_record(self, m):
        if isinstance(m, int):
            # argument is index of the record in the list of record_ids
            return self.records[self.record_ids[m]]
        elif isinstance(m, str):
            # argument is a record id string
            return self.records[m]
        elif isinstance(m, DreqLink):
            # argument is DreqLink instance, which contains a record id
            return self.records[m.record_id]
        else:
            raise TypeError(f'Error specifying record to retrieve from table {self.table_name}')

    def get_attr_record(self, attr, value, unique=True):
        if attr in self.attr2field:
            records = [record for record in self.records.values() if getattr(record, attr) == value]
            if len(records) == 0:
                raise ValueError(f'No record found for {attr}={value}')
            if unique:
                if len(records) != 1:
                    raise ValueError(f'{attr}={value} is not unique (identified {len(records)} records)')
                return records[0]
            else:
                return records
        else:
            raise Exception(f'Record attribute does not exist: {attr}')

    def get_record_id(self, record):
        # In case we need to get a record_id when we only have the record.
        # For example, to use delete_record() to remove the record.
        l = [record_id for record_id, rec in self.records.items() if rec == record]
        if len(l) == 1:
            return l[0]
        else:
            raise Exception('Could not find record_id matching the record')

    def delete_record(self, record_id):
        self.records.pop(record_id)
        self.record_ids.remove(record_id)
        self.nrec -= 1

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


###############################################################################
# Non-generic classes, i.e. they have a specific function in the data request

@dataclass
class ExptRequest:
    '''
    Object to store variables requested for an experiment.
    Variable names are stored in seperate sets for different priority levels.
    '''
    experiment: str
    if PYTHON_VERSION < (3, 9):
        # Required for python versions before 3.9, see:
        #   https://stackoverflow.com/questions/75202610/typeerror-type-object-is-not-subscriptable-python
        # Should remove this if we decide not to support versions before 3.9.
        core: Set[str] = dataclass_field(default_factory=set)
        high: Set[str] = dataclass_field(default_factory=set)
        medium: Set[str] = dataclass_field(default_factory=set)
        low: Set[str] = dataclass_field(default_factory=set)
    else:
        core: set[str] = dataclass_field(default_factory=set)
        high: set[str] = dataclass_field(default_factory=set)
        medium: set[str] = dataclass_field(default_factory=set)
        low: set[str] = dataclass_field(default_factory=set)

    def __post_init__(self):
        for p in PRIORITY_LEVELS:
            assert hasattr(self, p), 'ExptRequest object missing priority level: ' + p
        self.consistency_check()

    def add_vars(self, var_names, priority_level):
        '''
        Add variables to output from the experiment, at the specified priority level.
        Removes overlaps between priority levels (e.g., if adding a variable at high
        priority that is already requested at medium priority, it is removed from the
        medium priority list).

        Parameters
        ----------
        var_names : set
            Set of unique variable names to be added.
        priority_level : str
            Priority level at which to add them.
            Not case sensitive (will be rendered as lower case).

        Returns
        -------
        ExptRequest object is updated with the new variables, and any overlaps removed.
        '''
        priority_level = priority_level.lower()
        current_vars = getattr(self, priority_level)
        current_vars.update(var_names)
        # Remove any overlaps by ensuring a variable only appears at its highest
        # requested priority level.
        self.high = self.high.difference(self.core)

        self.medium = self.medium.difference(self.core)
        self.medium = self.medium.difference(self.high)  # remove any high priority vars from medium priority group

        self.low = self.low.difference(self.core)
        self.low = self.low.difference(self.high)  # remove any high priority vars from low priority group
        self.low = self.low.difference(self.medium)  # remove any medium priority vars from low priority group

        self.consistency_check()

    def consistency_check(self):
        # Confirm that priority sets don't overlap
        # assert self.high.intersection(self.medium.union(self.low)) == set()
        # assert self.medium.intersection(self.high.union(self.low)) == set()
        # assert self.low.intersection(self.high.union(self.medium)) == set()
        for this_p in PRIORITY_LEVELS:
            other_p = [p for p in PRIORITY_LEVELS if p != this_p]
            for p in other_p:
                assert getattr(self, this_p).intersection(getattr(self, p)) == set()

        # Also confirm object contains the expected priority levels
        pl = list(vars(self))
        pl.remove('experiment')
        assert set(pl) == set(PRIORITY_LEVELS)

    def __repr__(self):
        self.consistency_check()
        break_up_varname_for_display = False
        l = [f'Variables (by priority) for experiment: {self.experiment}']
        for p in PRIORITY_LEVELS:
            req = getattr(self, p)
            if len(req) == 0:
                continue
            n = len(req)
            s = f'  {p} ({n}): '
            indent = ' ' * len(s)
            sortby = str.lower
            req = sorted(req, key=sortby)
            if break_up_varname_for_display:
                # for better readability, show all vars in each cmor table on one line
                # TO DO: remove this option? probably not ever used
                separator = '.'
                lt = [tuple(varname.split(separator)) for varname in req]
                tables = sorted(set([t[0] for t in lt]), key=sortby)
                req = []
                for table in tables:
                    varnames = sorted(set([t[1] for t in lt if t[0] == table]), key=sortby)
                    n = len(varnames)
                    req.append(f'{table} ({n}): ' + ', '.join(varnames))
            s += req[0]
            for varname in req[1:]:
                s += '\n' + indent + varname
            l.append(s)
        return '\n'.join(l)

    def to_dict(self):
        '''
        Return dict equivalent of the object, suitable to write to json.
        '''
        sortby = str.lower
        return {
            self.experiment: {
                'Core': sorted(self.core, key=sortby),
                'High': sorted(self.high, key=sortby),
                'Medium': sorted(self.medium, key=sortby),
                'Low': sorted(self.low, key=sortby),
            }
        }
