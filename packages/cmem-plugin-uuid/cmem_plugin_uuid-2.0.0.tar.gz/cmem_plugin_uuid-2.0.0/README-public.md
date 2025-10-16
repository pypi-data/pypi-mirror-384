# cmem-plugin-uuid

Create universally unique identifiers (UUIDs) versions 1, 3, 4, 5, 6, 7 and 8 in transformations.


[![eccenca Corporate Memory][cmem-shield]][cmem-link]

This is a plugin for [eccenca](https://eccenca.com) [Corporate Memory](https://documentation.eccenca.com). You can install it with the [cmemc](https://eccenca.com/go/cmemc) command line client like this:

```
cmemc admin workspace python install cmem-plugin-uuid
```
[![workflow](https://github.com/eccenca/cmem-plugin-uuid/actions/workflows/check.yml/badge.svg)](https://github.com/eccenca/cmem-plugin-uuid/actions) [![pypi version](https://img.shields.io/pypi/v/cmem-plugin-uuid)](https://pypi.org/project/cmem-plugin-uuid) [![license](https://img.shields.io/pypi/l/cmem-plugin-uuid)](https://pypi.org/project/cmem-plugin-uuid)
[![poetry][poetry-shield]][poetry-link] [![ruff][ruff-shield]][ruff-link] [![mypy][mypy-shield]][mypy-link] [![copier][copier-shield]][copier] 

[cmem-link]: https://documentation.eccenca.com
[cmem-shield]: https://img.shields.io/endpoint?url=https://dev.documentation.eccenca.com/badge.json
[poetry-link]: https://python-poetry.org/
[poetry-shield]: https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json
[ruff-link]: https://docs.astral.sh/ruff/
[ruff-shield]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&label=Code%20Style
[mypy-link]: https://mypy-lang.org/
[mypy-shield]: https://www.mypy-lang.org/static/mypy_badge.svg
[copier]: https://copier.readthedocs.io/
[copier-shield]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-purple.json


UUID1 version is generated from a host ID, sequence number, and the current time.

### Parameters

#### Node

Node value in the form "01:23:45:67:89:AB", "01-23-45-67-89-AB", or "0123456789AB".
If not given, [`uuid.getnode()`](https://docs.python.org/3/library/uuid.html#uuid.getnode) is used to 
attempt to obtain the hardware address. If this is unsuccessful a random 48-bit number is chosen.

Default value: _None_  
ID: `node`

#### Clock sequence

If clock sequence is given, it is used as the sequence number, otherwise a random 14-bit sequence number is chosen.

Default value: _None_  
ID: `clock_seq`

<br>

## UUID3

UUID version 3 is a reproducible UUID based on the MD5 hash of a namespace identifier (which is a UUID) and a name
(which is a string).


### Parameters

#### Namespace

The namespace can be entered manually or selected from the namespace UUIDs defined in
[RFC 4122](https://www.rfc-editor.org/rfc/rfc4122):

- Namespace DNS: 6ba7b810-9dad-11d1-80b4-00c04fd430c8 (*namespace_dns*)
- Namespace URL: 6ba7b811-9dad-11d1-80b4-00c04fd430c8 (*namespace_url*)
- Namespace OID: 6ba7b812-9dad-11d1-80b4-00c04fd430c8 (*namespace_oid*)
- Namespace X500: 6ba7b814-9dad-11d1-80b4-00c04fd430c8 (*namespace_x500*)

If none of the predefined namespace UUIDs is selected, the input namespace is either directly
interpreted as a UUID, or used to derive a UUID (see parameter _Namespace as UUID_). If no namespace is given,
the output is the same as that of the standard CMEM UUID operator with input value.

Default value: _none_  
ID: `namespace`

#### Use input as namespace

If enabled, the input value is used for the namespace.

Default value: _False_  
ID: `input_as_namespace`

#### Namespace as UUID

Applies only if none of the pre-defined namespaces is selected. If enabled, the namespace string
needs to be a valid UUID. Otherwise, the namespace UUID is a UUIDv1 derived from the MD5 
hash of the namespace string.

Default value: _False_  
ID: `namespace_as_uuid`

<br>


## UUID4

UUID version 4 specifies a random UUID. This plugin is equivalent to the standard CMEM UUID operator without input value.

<br>


## UUID5

UUID version 5 is a reproducible UUID based on the SHA1 hash of a namespace identifier (which is a UUID) and a
name (which is a string).

### Parameters

#### Namespace

The namespace can be entered manually or selected from the namespace UUIDs defined in
[RFC 4122](https://www.rfc-editor.org/rfc/rfc4122):

- Namespace DNS: 6ba7b810-9dad-11d1-80b4-00c04fd430c8 (*namespace_dns*)
- Namespace URL: 6ba7b811-9dad-11d1-80b4-00c04fd430c8 (*namespace_url*)
- Namespace OID: 6ba7b812-9dad-11d1-80b4-00c04fd430c8 (*namespace_oid*)
- Namespace X500: 6ba7b814-9dad-11d1-80b4-00c04fd430c8 (*namespace_x500*)

If none of the predefined namespace UUIDs is selected, the input namespace is either directly
interpreted as a UUID, or used to derive a UUID (see parameter _Namespace as UUID_).

Default value: _none_  
ID: `namespace`

#### Namespace as UUID

Applies only if none of the pre-defined namespaces is selected. If enabled, the namespace string
needs to be a valid UUID. Otherwise, the namespace UUID is a UUIDv1 derived from the SHA1 
hash of the namespace string.

Default value: _False_  
ID: `namespace_as_uuid`

<br>

## UUID6

UUID6 version is generated from a host ID, sequence number, and the current time.
UUID version 6 is a field-compatible version of UUIDv1, reordered for improved DB locality. 

### Parameters

#### Node

Node value in the form "01:23:45:67:89:AB", "01-23-45-67-89-AB", or "0123456789AB".
If not given, a random 48-bit sequence number is chosen.

Default value: _None_  
ID: `node`

#### Clock sequence

If clock sequence is given, it is used as the sequence number, otherwise a random 14-bit number is chosen.

Default value: _None_  
ID: `clock_seq`

<br>

## UUID7

UUID version 7 features a time-ordered value field derived from the
widely implemented and well known Unix Epoch timestamp source, the
number of milliseconds since midnight 1 Jan 1970 UTC, leap seconds
excluded, as well as improved entropy characteristics over versions
1 or 6.

<br>

## UUID8

UUID version 8 features a time-ordered value field derived from the
widely implemented and well known Unix Epoch timestamp source, the
number of nanoseconds since midnight 1 Jan 1970 UTC, leap seconds
excluded.

<br>

## UUID1 to UUID6

Generate a UUID version 6 from a UUID version 1. The input needs to be a valid UUIDv1
hexdecimal string.

<br>

## UUID Version

Outputs the UUID version from a UUID input string.

<br>

## UUID Convert

Convert a UUID from one format to another. The plugin accepts strings in the correct format, however, the log will show
a warning if the input does not comply with the standard specified in [RFC 4122](https://www.rfc-editor.org/rfc/rfc4122) and the 
[proposed updates](https://www.ietf.org/archive/id/draft-peabody-dispatch-new-uuid-format-01.html).

### Parameters

#### From

The input format

Options:

- **UUID/32-character hexadecimal string** (*uuid_hex*):

  A standard UUID or a UUID as a 32-character lowercase hexadecimal string.
- **128-bit integer** (_int_):

  The UUID as a 128-bit integer.
- **URN** (_urn_):

  The UUID as a URN.

Default value: _UUID/32-character lowercase hexadecimal string_   
ID: `from_format`

#### To

The output format

Options:

- **UUID** (_uuid_):

  A standard UUID.
- **32-character lowercase hexadecimal string** (_hex_):

  The UUID as a 32-character lowercase hexadecimal string.
- **128-bit integer** (_int_):

  The UUID as a 128-bit integer.
- **URN** (_urn_):

  The UUID as a URN as specified in [RFC 4122](https://www.rfc-editor.org/rfc/rfc4122).

Default value: _32-character lowercase hexadecimal string_  
ID: `to_format`
