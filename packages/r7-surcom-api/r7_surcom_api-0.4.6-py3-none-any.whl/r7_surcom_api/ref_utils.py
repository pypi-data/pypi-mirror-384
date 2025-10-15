"""
helpers for working with $ref in jsonschema
"""

from copy import deepcopy
from furl import furl

from r7_surcom_api import helpers


class SchemaError(Exception):
    """
    Represents an error that occurred while creating types.  These errors should
    be returned to the caller.
    """

    def __init__(self, message: str, code: str = None, type_name: str = None):
        super().__init__(
            f"Schema error for type {type_name}; failure code = {code}; message = {message}"
        )

        self.code = code
        self.type_name = type_name
        self.message = message


def bare_portion(url: str) -> str:
    """
    >>> bare_portion("https://foo")
    'https://foo'
    >>> bare_portion("https://foo#1/2/3")
    'https://foo'
    >>> bare_portion(None)
    ''
    """
    # TODO: make these pytest
    return furl(url).remove(fragment=True).url


def path_portion(url: str) -> str:
    """
    >>> path_portion("https://foo")
    ''
    >>> path_portion("https://foo#")
    ''
    >>> path_portion("https://foo#abc")
    '#abc'
    >>> path_portion(None)
    ''
    """
    # TODO: make these pytest
    frag = str(furl(url).fragment)
    if frag == "":
        return frag
    return "#" + frag


def absolute_ref_url(baseurl: str, url: str) -> str:
    """
    Return the 'absolute' resolved URL from a $ref value

    >>> absolute_ref_url('http://example.com/abc/def.json', '#/components/schemas/xyz')
    'http://example.com/abc/def.json#/components/schemas/xyz'

    >>> absolute_ref_url('http://example.com/abc/def.json', '/xyz/bar.json')
    'http://example.com/xyz/bar.json'

    >>> absolute_ref_url('http://example.com/abc/def.json#zzz', 'ghi.json')
    'http://example.com/abc/ghi.json'

    >>> absolute_ref_url('http://example.com/abc/def.json#zzz', None)
    'http://example.com/abc/def.json#zzz'

    >>> absolute_ref_url('http://example.com/abc/def.json#zzz', 'http://foo')
    'http://foo'

    >>> absolute_ref_url('http://example.com/abc/def.json', 'http://foo#/components/schemas/xyz')
    'http://foo#/components/schemas/xyz'

    >>> absolute_ref_url('http://example.com/abc/def/ghi.json#zzz', '../in/out.json')
    'http://example.com/abc/in/out.json'

    """
    # TODO: make these pytest
    if url is None:
        return baseurl
    return furl(baseurl).join(url).url


def bare_ref_url(baseurl: str, url: str = None) -> str:
    """
    Return the 'bare' resolved URL from a $ref value

    >>> bare_ref_url('http://example.com/abc/def.json', '#/components/schemas/xyz')
    'http://example.com/abc/def.json'

    >>> bare_ref_url('http://example.com/abc/def.json', None)
    'http://example.com/abc/def.json'

    >>> bare_ref_url('http://example.com/abc/def.json#zzz', 'ghi.json')
    'http://example.com/abc/ghi.json'

    >>> bare_ref_url('http://example.com/abc/def.json#zzz', 'http://foo')
    'http://foo'

    >>> bare_ref_url('http://example.com/abc/def.json', 'http://foo#/components/schemas/xyz')
    'http://foo'

    >>> bare_ref_url('http://example.com/abc/def/ghi.json#zzz', '../in/out.json')
    'http://example.com/abc/in/out.json'

    """
    # TODO: make these pytest
    if url is None:
        return furl(baseurl).remove(fragment=True).url
    return furl(baseurl).join(url).remove(fragment=True).url


def subschemas(schema: dict):
    """
    Enumerate the contents of the schema, looking for subschemas with '$id' or '$anchor'
    """
    for _, value in schema.items():
        if isinstance(value, dict):
            if "$id" in value:
                yield value["$id"], value
            if "$anchor" in value:
                yield "#" + value["$anchor"], value
            yield from subschemas(value)


def get_element(doc: dict, ref: str):
    """
    get a (copy) leaf element using a JSON-schema-style path

    Regular paths and fragments:
    >>> get_element({"one":1, "two":{"three":3}}, "#")
    {'one': 1, 'two': {'three': 3}}
    >>> get_element({"one":1, "two":{"three":3}}, "#/one")
    1
    >>> get_element({"one":1, "two":{"three":3, "four":4}}, "#/two/three")
    3

    Anchors identified by '$anchor':
    (from https://json-schema.org/draft/2020-12/json-schema-core.html#idExamples)

    >>> get_element({"$defs": {"A": { "$anchor": "foo" }}}, "#/$defs/A")
    {'$anchor': 'foo'}

    >>> get_element({"$defs": {"A": { "$anchor": "foo" }}}, "#foo")
    {'$anchor': 'foo'}

    Anchors identified by '$id' with "#" as the id:
    (like the OSCAL usage)

    >>> get_element({"$defs": {"B": { "$id": "#bar" }}}, "#/$defs/B")
    {'$id': '#bar'}

    >>> get_element({"$defs": {"B": { "$id": "#bar" }}}, "#bar")
    {'$id': '#bar'}

    >>> get_element({"$id": "#baz", "C": "val" }, "#baz")
    {'$id': '#baz', 'C': 'val'}

    """
    # TODO: make these pytest
    base = doc
    ref = path_portion(ref)
    if ref in ("#", ""):
        # Want the main schema from the document, but *excluding* any components
        ret = deepcopy(doc)
        ret.pop("components", None)
        ret.pop("definitions", None)
        return ret
    refs = ref.split("/")
    for path in refs:
        if path == "#":
            continue
        # JSONPointer escape sequences https://tools.ietf.org/html/rfc6901#section-3
        path = path.replace("~1", "/")
        path = path.replace("~0", "~")
        doc = doc.get(path, {})
        if doc is None:
            return {}
    if doc:
        return deepcopy(doc)

    # The whole document can be addressed by its id, if you like
    if "$id" in base and base["$id"] == ref:
        return deepcopy(base)

    # Scan the document for any $id and $anchor definitions, and return if exact match
    for key, element in subschemas(base):
        if ref == key:
            return deepcopy(element)

    # Not found
    return {}


def get_ref_element(doc: dict, ref: str) -> dict:
    """
    Get `ref` from `doc`
    and return a (copy) dictionary that includes it with the appropriate prefixes.
    This only uses the #<anchor> portion of the 'ref' url, ignoring the base.

    Root element:
    >>> get_ref_element({"one":1, "two":{"three":3}}, "#")
    {'one': 1, 'two': {'three': 3}}

    >>> get_ref_element({"one":1, "two":{"three":3}}, "")
    {'one': 1, 'two': {'three': 3}}

    # Anchor with a path:
    >>> get_ref_element({"one":1, "two":{"three":3}}, "#/one")
    {'one': 1}
    >>> get_ref_element({"one":1, "two":{"three":3, "four":4}}, "#/two/three")
    {'two': {'three': 3}}

    # Anchor without a path:
    >>> get_ref_element({"one":1, "two":{"three":3}}, "#ident")
    {}
    >>> get_ref_element({"one":1, "two":{"$id": "#ident", "three":3}}, "#ident")
    {'$id': '#ident', 'three': 3}

    """
    # TODO: make these pytest
    result = {}
    out = result
    ret = result
    if ref is None:
        return None
    ref = path_portion(ref)
    if ref in ("#", ""):
        # Want the main schema from the document, but *excluding* any components
        # (those will be pulled in if they are referenced)
        ret = deepcopy(doc)
        ret.pop("components", None)
        ret.pop("definitions", None)
        return ret

    if "/" in ref:
        refs = ref.split("/")
        path = "#"
        for path in refs:
            if path == "#":
                continue
            # JSONPointer escape sequences https://tools.ietf.org/html/rfc6901#section-3
            path = path.replace("~1", "/")
            path = path.replace("~0", "~")
            out[path] = {}
            ret = out
            out = out[path]
        ret[path] = deepcopy(get_element(doc, ref))
        return result

    return deepcopy(get_element(doc, ref))


def resolve_internal_refs(typename: str, doc: dict, baseurl: str = None) -> dict:
    """
    Resolve (expand in place) all the "internal" (same-document) references in the document.

    Note: we don't handle dereferencing in recursive cases, and will raise an exception
    where a fragment references itself or an outer portion of the same schema.

    :param doc: The document to resolve
    :param baseurl: The "base URL" of this document (optional)
    """

    def resolve_ref(
        typename: str, outerdoc: dict, doc: dict, baseurl: str, recursiontrap: list
    ):
        if "$ref" not in doc:
            return doc
        val = doc["$ref"]
        if val is None:
            # Marker to remove a troublesome ref (e.g. to squelch recursion)
            doc.pop("$ref")
            return doc
        if not isinstance(val, str):
            raise SchemaError(
                "Value of $ref must be a string.", code="InvalidRef", type_name=typename
            )

        if (baseurl or "") != bare_ref_url(baseurl, val):
            # This is a reference to a different document.  Leave it unresolved.
            return doc
        # Get (a copy of) the value of the reference
        ref = get_element(outerdoc, val)
        if not ref:
            # Found nothing.  Leave it unresolved.
            return doc
        ref.pop("$id", None)
        ref.pop("$schema", None)
        # Resolve any $refs within that
        recursiontrap.append(val)
        if len(recursiontrap) > 30:
            # Don't print after the list repeats
            loop = []
            for idx, ref in enumerate(recursiontrap):
                loop.append(ref)
                if recursiontrap.index(ref) < idx:
                    break
            trap = " -> ".join(loop) + "..."
            raise SchemaError(
                f"$ref cannot be resolved due to recursion: {trap}",
                code="RecursiveRef",
                type_name=typename,
            )
        ref = resolve_recurse(typename, outerdoc, ref, baseurl, val, recursiontrap)
        recursiontrap.pop()
        # Replace '$ref' with the reference (not recursively)
        ret = deepcopy(doc)
        ret.pop("$ref", None)
        return helpers.dict_merge(ret, ref)

    def resolve_recurse(
        typename: str,
        outerdoc: dict,
        doc: dict,
        baseurl: str,
        refurl: str,
        recursiontrap: list,
    ):
        if isinstance(doc, list):
            return [
                resolve_recurse(
                    typename, outerdoc, value, baseurl, refurl, recursiontrap
                )
                for value in doc
            ]
        if isinstance(doc, dict):
            doc2 = resolve_ref(typename, outerdoc, doc, baseurl, recursiontrap)
            return {
                key: resolve_recurse(
                    typename, outerdoc, value, baseurl, refurl, recursiontrap
                )
                for key, value in doc2.items()
            }
        return doc

    recursiontrap = []
    return resolve_recurse(typename, doc, doc, baseurl, None, recursiontrap)
