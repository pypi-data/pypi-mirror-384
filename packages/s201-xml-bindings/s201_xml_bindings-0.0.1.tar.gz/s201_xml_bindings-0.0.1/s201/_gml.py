# ./_gml.py
# -*- coding: utf-8 -*-
# PyXB bindings for NM:c4f74fce23a2f49d6da683416eb2980bfced7e33
# Generated 2025-10-13 15:57:18.382584 by PyXB version 1.2.6 using Python 3.12.3.final.0
# Namespace http://www.opengis.net/gml/3.2 [xmlns:gml]

from __future__ import unicode_literals
import pyxb
import pyxb.binding
import pyxb.binding.saxer
import io
import pyxb.utils.utility
import pyxb.utils.domutils
import sys
import pyxb.utils.six as _six
# Unique identifier for bindings created at the same time
_GenerationUID = pyxb.utils.utility.UniqueIdentifier('urn:uuid:60b60e42-201d-4bd9-8d99-8405dbc0d811')

# Version of PyXB used to generate the bindings
_PyXBVersion = '1.2.6'

# A holder for module-level binding classes so we can access them from
# inside class definitions where property names may conflict.
_module_typeBindings = pyxb.utils.utility.Object()

# Import bindings for namespaces imported into schema
import _xlink as _ImportedBinding__xlink
import pyxb.binding.datatypes

# NOTE: All namespace declarations are reserved within the binding
Namespace = pyxb.namespace.NamespaceForURI('http://www.opengis.net/gml/3.2', create_if_missing=True)
Namespace.configureCategories(['typeBinding', 'elementBinding'])
_Namespace_xlink = _ImportedBinding__xlink.Namespace
_Namespace_xlink.configureCategories(['typeBinding', 'elementBinding'])

def CreateFromDocument (xml_text, fallback_namespace=None, location_base=None, default_namespace=None):
    """Parse the given XML and use the document element to create a
    Python instance.

    @param xml_text An XML document.  This should be data (Python 2
    str or Python 3 bytes), or a text (Python 2 unicode or Python 3
    str) in the L{pyxb._InputEncoding} encoding.

    @keyword fallback_namespace An absent L{pyxb.Namespace} instance
    to use for unqualified names when there is no default namespace in
    scope.  If unspecified or C{None}, the namespace of the module
    containing this function will be used, if it is an absent
    namespace.

    @keyword location_base: An object to be recorded as the base of all
    L{pyxb.utils.utility.Location} instances associated with events and
    objects handled by the parser.  You might pass the URI from which
    the document was obtained.

    @keyword default_namespace An alias for @c fallback_namespace used
    in PyXB 1.1.4 through 1.2.6.  It behaved like a default namespace
    only for absent namespaces.
    """

    if pyxb.XMLStyle_saxer != pyxb._XMLStyle:
        dom = pyxb.utils.domutils.StringToDOM(xml_text)
        return CreateFromDOM(dom.documentElement)
    if fallback_namespace is None:
        fallback_namespace = default_namespace
    if fallback_namespace is None:
        fallback_namespace = Namespace.fallbackNamespace()
    saxer = pyxb.binding.saxer.make_parser(fallback_namespace=fallback_namespace, location_base=location_base)
    handler = saxer.getContentHandler()
    xmld = xml_text
    if isinstance(xmld, _six.text_type):
        xmld = xmld.encode(pyxb._InputEncoding)
    saxer.parse(io.BytesIO(xmld))
    instance = handler.rootObject()
    return instance

def CreateFromDOM (node, fallback_namespace=None, default_namespace=None):
    """Create a Python instance from the given DOM node.
    The node tag must correspond to an element declaration in this module.

    @deprecated: Forcing use of DOM interface is unnecessary; use L{CreateFromDocument}."""
    if fallback_namespace is None:
        fallback_namespace = default_namespace
    if fallback_namespace is None:
        fallback_namespace = Namespace.fallbackNamespace()
    return pyxb.binding.basis.element.AnyCreateFromDOM(node, fallback_namespace)


# Atomic simple type: {http://www.opengis.net/gml/3.2}AggregationType
class AggregationType (pyxb.binding.datatypes.string, pyxb.binding.basis.enumeration_mixin):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AggregationType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 311, 1)
    _Documentation = None
AggregationType._CF_enumeration = pyxb.binding.facets.CF_enumeration(enum_prefix=None, value_datatype=AggregationType)
AggregationType.set_ = AggregationType._CF_enumeration.addEnumeration(unicode_value='set', tag='set_')
AggregationType.bag = AggregationType._CF_enumeration.addEnumeration(unicode_value='bag', tag='bag')
AggregationType.sequence = AggregationType._CF_enumeration.addEnumeration(unicode_value='sequence', tag='sequence')
AggregationType.array = AggregationType._CF_enumeration.addEnumeration(unicode_value='array', tag='array')
AggregationType.record = AggregationType._CF_enumeration.addEnumeration(unicode_value='record', tag='record')
AggregationType.table = AggregationType._CF_enumeration.addEnumeration(unicode_value='table', tag='table')
AggregationType._InitializeFacetMap(AggregationType._CF_enumeration)
Namespace.addCategoryObject('typeBinding', 'AggregationType', AggregationType)
_module_typeBindings.AggregationType = AggregationType

# Atomic simple type: {http://www.opengis.net/gml/3.2}CurveInterpolationType
class CurveInterpolationType (pyxb.binding.datatypes.string, pyxb.binding.basis.enumeration_mixin):

    """gml:CurveInterpolationType is a list of codes that may be used to identify the interpolation mechanisms specified by an applicationschema.S-100 3.1 note: The list has been extended by adding the S-100 3.1 interpolations, given that the new draft of ISO 19107 explicitly says "As a codelist, there is no intention of limiting the potential values ofCurveInterpolation." """

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'CurveInterpolationType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 946, 1)
    _Documentation = 'gml:CurveInterpolationType is a list of codes that may be used to identify the interpolation mechanisms specified by an applicationschema.S-100 3.1 note: The list has been extended by adding the S-100 3.1 interpolations, given that the new draft of ISO 19107 explicitly says "As a codelist, there is no intention of limiting the potential values ofCurveInterpolation."'
CurveInterpolationType._CF_enumeration = pyxb.binding.facets.CF_enumeration(enum_prefix=None, value_datatype=CurveInterpolationType)
CurveInterpolationType.none = CurveInterpolationType._CF_enumeration.addEnumeration(unicode_value='none', tag='none')
CurveInterpolationType.linear = CurveInterpolationType._CF_enumeration.addEnumeration(unicode_value='linear', tag='linear')
CurveInterpolationType.geodesic = CurveInterpolationType._CF_enumeration.addEnumeration(unicode_value='geodesic', tag='geodesic')
CurveInterpolationType.circularArc3Points = CurveInterpolationType._CF_enumeration.addEnumeration(unicode_value='circularArc3Points', tag='circularArc3Points')
CurveInterpolationType.loxodromic = CurveInterpolationType._CF_enumeration.addEnumeration(unicode_value='loxodromic', tag='loxodromic')
CurveInterpolationType.elliptical = CurveInterpolationType._CF_enumeration.addEnumeration(unicode_value='elliptical', tag='elliptical')
CurveInterpolationType.conic = CurveInterpolationType._CF_enumeration.addEnumeration(unicode_value='conic', tag='conic')
CurveInterpolationType.circularArcCenterPointWithRadius = CurveInterpolationType._CF_enumeration.addEnumeration(unicode_value='circularArcCenterPointWithRadius', tag='circularArcCenterPointWithRadius')
CurveInterpolationType.polynomialSpline = CurveInterpolationType._CF_enumeration.addEnumeration(unicode_value='polynomialSpline', tag='polynomialSpline')
CurveInterpolationType.bezierSpline = CurveInterpolationType._CF_enumeration.addEnumeration(unicode_value='bezierSpline', tag='bezierSpline')
CurveInterpolationType.bSpline = CurveInterpolationType._CF_enumeration.addEnumeration(unicode_value='bSpline', tag='bSpline')
CurveInterpolationType.cubicSpline = CurveInterpolationType._CF_enumeration.addEnumeration(unicode_value='cubicSpline', tag='cubicSpline')
CurveInterpolationType.rationalSpline = CurveInterpolationType._CF_enumeration.addEnumeration(unicode_value='rationalSpline', tag='rationalSpline')
CurveInterpolationType.blendedParabolic = CurveInterpolationType._CF_enumeration.addEnumeration(unicode_value='blendedParabolic', tag='blendedParabolic')
CurveInterpolationType._InitializeFacetMap(CurveInterpolationType._CF_enumeration)
Namespace.addCategoryObject('typeBinding', 'CurveInterpolationType', CurveInterpolationType)
_module_typeBindings.CurveInterpolationType = CurveInterpolationType

# Atomic simple type: {http://www.opengis.net/gml/3.2}SurfaceInterpolationType
class SurfaceInterpolationType (pyxb.binding.datatypes.string, pyxb.binding.basis.enumeration_mixin):

    """gml:SurfaceInterpolationType is a list of codes that may be used to
				identify the interpolation mechanisms specified by an application
			schema."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'SurfaceInterpolationType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1154, 1)
    _Documentation = 'gml:SurfaceInterpolationType is a list of codes that may be used to\n\t\t\t\tidentify the interpolation mechanisms specified by an application\n\t\t\tschema.'
SurfaceInterpolationType._CF_enumeration = pyxb.binding.facets.CF_enumeration(enum_prefix=None, value_datatype=SurfaceInterpolationType)
SurfaceInterpolationType.none = SurfaceInterpolationType._CF_enumeration.addEnumeration(unicode_value='none', tag='none')
SurfaceInterpolationType.planar = SurfaceInterpolationType._CF_enumeration.addEnumeration(unicode_value='planar', tag='planar')
SurfaceInterpolationType.spherical = SurfaceInterpolationType._CF_enumeration.addEnumeration(unicode_value='spherical', tag='spherical')
SurfaceInterpolationType.elliptical = SurfaceInterpolationType._CF_enumeration.addEnumeration(unicode_value='elliptical', tag='elliptical')
SurfaceInterpolationType.conic = SurfaceInterpolationType._CF_enumeration.addEnumeration(unicode_value='conic', tag='conic')
SurfaceInterpolationType.tin = SurfaceInterpolationType._CF_enumeration.addEnumeration(unicode_value='tin', tag='tin')
SurfaceInterpolationType.parametricCurve = SurfaceInterpolationType._CF_enumeration.addEnumeration(unicode_value='parametricCurve', tag='parametricCurve')
SurfaceInterpolationType.polynomialSpline = SurfaceInterpolationType._CF_enumeration.addEnumeration(unicode_value='polynomialSpline', tag='polynomialSpline')
SurfaceInterpolationType.rationalSpline = SurfaceInterpolationType._CF_enumeration.addEnumeration(unicode_value='rationalSpline', tag='rationalSpline')
SurfaceInterpolationType.triangulatedSpline = SurfaceInterpolationType._CF_enumeration.addEnumeration(unicode_value='triangulatedSpline', tag='triangulatedSpline')
SurfaceInterpolationType._InitializeFacetMap(SurfaceInterpolationType._CF_enumeration)
Namespace.addCategoryObject('typeBinding', 'SurfaceInterpolationType', SurfaceInterpolationType)
_module_typeBindings.SurfaceInterpolationType = SurfaceInterpolationType

# Atomic simple type: {http://www.opengis.net/gml/3.2}SignType
class SignType (pyxb.binding.datatypes.string, pyxb.binding.basis.enumeration_mixin):

    """gml:SignType is a convenience type with values "+" (plus) and "-"
				(minus)."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'SignType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1263, 1)
    _Documentation = 'gml:SignType is a convenience type with values "+" (plus) and "-"\n\t\t\t\t(minus).'
SignType._CF_enumeration = pyxb.binding.facets.CF_enumeration(enum_prefix=None, value_datatype=SignType)
SignType.emptyString = SignType._CF_enumeration.addEnumeration(unicode_value='-', tag='emptyString')
SignType.emptyString_ = SignType._CF_enumeration.addEnumeration(unicode_value='+', tag='emptyString_')
SignType._InitializeFacetMap(SignType._CF_enumeration)
Namespace.addCategoryObject('typeBinding', 'SignType', SignType)
_module_typeBindings.SignType = SignType

# Atomic simple type: [anonymous]
class STD_ANON (pyxb.binding.datatypes.string, pyxb.binding.basis.enumeration_mixin):

    """An atomic simple type."""

    _ExpandedName = None
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1296, 3)
    _Documentation = None
STD_ANON._CF_enumeration = pyxb.binding.facets.CF_enumeration(enum_prefix=None, value_datatype=STD_ANON)
STD_ANON.inapplicable = STD_ANON._CF_enumeration.addEnumeration(unicode_value='inapplicable', tag='inapplicable')
STD_ANON.missing = STD_ANON._CF_enumeration.addEnumeration(unicode_value='missing', tag='missing')
STD_ANON.template = STD_ANON._CF_enumeration.addEnumeration(unicode_value='template', tag='template')
STD_ANON.unknown = STD_ANON._CF_enumeration.addEnumeration(unicode_value='unknown', tag='unknown')
STD_ANON.withheld = STD_ANON._CF_enumeration.addEnumeration(unicode_value='withheld', tag='withheld')
STD_ANON._InitializeFacetMap(STD_ANON._CF_enumeration)
_module_typeBindings.STD_ANON = STD_ANON

# Atomic simple type: [anonymous]
class STD_ANON_ (pyxb.binding.datatypes.string):

    """An atomic simple type."""

    _ExpandedName = None
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1305, 3)
    _Documentation = None
STD_ANON_._CF_pattern = pyxb.binding.facets.CF_pattern()
STD_ANON_._CF_pattern.addPattern(pattern='other:/w{2,}')
STD_ANON_._InitializeFacetMap(STD_ANON_._CF_pattern)
_module_typeBindings.STD_ANON_ = STD_ANON_

# Atomic simple type: [anonymous]
class STD_ANON_2 (pyxb.binding.datatypes.string):

    """An atomic simple type."""

    _ExpandedName = None
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1358, 1)
    _Documentation = None
STD_ANON_2._InitializeFacetMap()
_module_typeBindings.STD_ANON_2 = STD_ANON_2

# Atomic simple type: {http://www.opengis.net/gml/3.2}UomSymbol
class UomSymbol (pyxb.binding.datatypes.string):

    """This type specifies a character string of length at least one, and
				restricted such that it must not contain any of the following characters: ":"
				(colon), " " (space), (newline), (carriage return), (tab). This allows values
				corresponding to familiar abbreviations, such as "kg", "m/s", etc. It is recommended
				that the symbol be an identifier for a unit of measure as specified in the "Unified
				Code of Units of Measure" (UCUM) (http://aurora.regenstrief.org/UCUM). This provides
				a set of symbols and a grammar for constructing identifiers for units of measure
				that are unique, and may be easily entered with a keyboard supporting the limited
				character set known as 7-bit ASCII. ISO 2955 formerly provided a specification with
				this scope, but was withdrawn in 2001. UCUM largely follows ISO 2955 with
				modifications to remove ambiguities and other problems."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'UomSymbol')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1389, 1)
    _Documentation = 'This type specifies a character string of length at least one, and\n\t\t\t\trestricted such that it must not contain any of the following characters: ":"\n\t\t\t\t(colon), " " (space), (newline), (carriage return), (tab). This allows values\n\t\t\t\tcorresponding to familiar abbreviations, such as "kg", "m/s", etc. It is recommended\n\t\t\t\tthat the symbol be an identifier for a unit of measure as specified in the "Unified\n\t\t\t\tCode of Units of Measure" (UCUM) (http://aurora.regenstrief.org/UCUM). This provides\n\t\t\t\ta set of symbols and a grammar for constructing identifiers for units of measure\n\t\t\t\tthat are unique, and may be easily entered with a keyboard supporting the limited\n\t\t\t\tcharacter set known as 7-bit ASCII. ISO 2955 formerly provided a specification with\n\t\t\t\tthis scope, but was withdrawn in 2001. UCUM largely follows ISO 2955 with\n\t\t\t\tmodifications to remove ambiguities and other problems.'
UomSymbol._CF_pattern = pyxb.binding.facets.CF_pattern()
UomSymbol._CF_pattern.addPattern(pattern='[^: /n/r/t]+')
UomSymbol._InitializeFacetMap(UomSymbol._CF_pattern)
Namespace.addCategoryObject('typeBinding', 'UomSymbol', UomSymbol)
_module_typeBindings.UomSymbol = UomSymbol

# Atomic simple type: {http://www.opengis.net/gml/3.2}UomURI
class UomURI (pyxb.binding.datatypes.anyURI):

    """This type specifies a URI, restricted such that it must start with one of
				the following sequences: "#", "./", "../", or a string of characters followed by a
				":". These patterns ensure that the most common URI forms are supported, including
				absolute and relative URIs and URIs that are simple fragment identifiers, but
				prohibits certain forms of relative URI that could be mistaken for unit of measure
				symbol . NOTE It is possible to re-write such a relative URI to conform to the
				restriction (e.g. "./m/s"). In an instance document, on elements of type
				gml:MeasureType the mandatory uom attribute shall carry a value corresponding to
				either - a conventional unit of measure symbol, - a link to a definition of a unit
				of measure that does not have a conventional symbol, or when it is desired to
				indicate a precise or variant definition."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'UomURI')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1407, 1)
    _Documentation = 'This type specifies a URI, restricted such that it must start with one of\n\t\t\t\tthe following sequences: "#", "./", "../", or a string of characters followed by a\n\t\t\t\t":". These patterns ensure that the most common URI forms are supported, including\n\t\t\t\tabsolute and relative URIs and URIs that are simple fragment identifiers, but\n\t\t\t\tprohibits certain forms of relative URI that could be mistaken for unit of measure\n\t\t\t\tsymbol . NOTE It is possible to re-write such a relative URI to conform to the\n\t\t\t\trestriction (e.g. "./m/s"). In an instance document, on elements of type\n\t\t\t\tgml:MeasureType the mandatory uom attribute shall carry a value corresponding to\n\t\t\t\teither - a conventional unit of measure symbol, - a link to a definition of a unit\n\t\t\t\tof measure that does not have a conventional symbol, or when it is desired to\n\t\t\t\tindicate a precise or variant definition.'
UomURI._CF_pattern = pyxb.binding.facets.CF_pattern()
UomURI._CF_pattern.addPattern(pattern='([a-zA-Z][a-zA-Z0-9/-/+/.]*:|/././|/./|#).*')
UomURI._InitializeFacetMap(UomURI._CF_pattern)
Namespace.addCategoryObject('typeBinding', 'UomURI', UomURI)
_module_typeBindings.UomURI = UomURI

# List simple type: {http://www.opengis.net/gml/3.2}doubleList
# superclasses pyxb.binding.datatypes.anySimpleType
class doubleList (pyxb.binding.basis.STD_list):

    """A type for a list of values of the respective simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'doubleList')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1425, 1)
    _Documentation = 'A type for a list of values of the respective simple type.'

    _ItemType = pyxb.binding.datatypes.double
doubleList._InitializeFacetMap()
Namespace.addCategoryObject('typeBinding', 'doubleList', doubleList)
_module_typeBindings.doubleList = doubleList

# Union simple type: {http://www.opengis.net/gml/3.2}NilReasonType
# superclasses pyxb.binding.datatypes.anySimpleType
class NilReasonType (pyxb.binding.basis.STD_union):

    """gml:NilReasonType defines a content model that allows recording of an
				explanation for a void value or other exception. gml:NilReasonType is a union of the
				following enumerated values: - inapplicable there is no value - missing the correct
				value is not readily available to the sender of this data. Furthermore, a correct
				value may not exist - template the value will be available later - unknown the
				correct value is not known to, and not computable by, the sender of this data.
				However, a correct value probably exists - withheld the value is not divulged -
				other:text other brief explanation, where text is a string of two or more characters
				with no included spaces and - anyURI which should refer to a resource which
				describes the reason for the exception A particular community may choose to assign
				more detailed semantics to the standard values provided. Alternatively, the URI
				method enables a specific or more complete explanation for the absence of a value to
				be provided elsewhere and indicated by-reference in an instance document.
				gml:NilReasonType is used as a member of a union in a number of simple content types
				where it is necessary to permit a value from the NilReasonType union as an
				alternative to the primary type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'NilReasonType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1273, 1)
    _Documentation = 'gml:NilReasonType defines a content model that allows recording of an\n\t\t\t\texplanation for a void value or other exception. gml:NilReasonType is a union of the\n\t\t\t\tfollowing enumerated values: - inapplicable there is no value - missing the correct\n\t\t\t\tvalue is not readily available to the sender of this data. Furthermore, a correct\n\t\t\t\tvalue may not exist - template the value will be available later - unknown the\n\t\t\t\tcorrect value is not known to, and not computable by, the sender of this data.\n\t\t\t\tHowever, a correct value probably exists - withheld the value is not divulged -\n\t\t\t\tother:text other brief explanation, where text is a string of two or more characters\n\t\t\t\twith no included spaces and - anyURI which should refer to a resource which\n\t\t\t\tdescribes the reason for the exception A particular community may choose to assign\n\t\t\t\tmore detailed semantics to the standard values provided. Alternatively, the URI\n\t\t\t\tmethod enables a specific or more complete explanation for the absence of a value to\n\t\t\t\tbe provided elsewhere and indicated by-reference in an instance document.\n\t\t\t\tgml:NilReasonType is used as a member of a union in a number of simple content types\n\t\t\t\twhere it is necessary to permit a value from the NilReasonType union as an\n\t\t\t\talternative to the primary type.'

    _MemberTypes = ( STD_ANON, STD_ANON_, pyxb.binding.datatypes.anyURI, )
NilReasonType._CF_enumeration = pyxb.binding.facets.CF_enumeration(value_datatype=NilReasonType)
NilReasonType._CF_pattern = pyxb.binding.facets.CF_pattern()
NilReasonType.inapplicable = 'inapplicable'       # originally STD_ANON.inapplicable
NilReasonType.missing = 'missing'                 # originally STD_ANON.missing
NilReasonType.template = 'template'               # originally STD_ANON.template
NilReasonType.unknown = 'unknown'                 # originally STD_ANON.unknown
NilReasonType.withheld = 'withheld'               # originally STD_ANON.withheld
NilReasonType._InitializeFacetMap(NilReasonType._CF_enumeration,
   NilReasonType._CF_pattern)
Namespace.addCategoryObject('typeBinding', 'NilReasonType', NilReasonType)
_module_typeBindings.NilReasonType = NilReasonType

# Union simple type: {http://www.opengis.net/gml/3.2}NilReasonEnumeration
# superclasses pyxb.binding.datatypes.anySimpleType
class NilReasonEnumeration (pyxb.binding.basis.STD_union):

    """Simple type that is a union of STD_ANON, STD_ANON_."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'NilReasonEnumeration')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1294, 1)
    _Documentation = None

    _MemberTypes = ( STD_ANON, STD_ANON_, )
NilReasonEnumeration._CF_enumeration = pyxb.binding.facets.CF_enumeration(value_datatype=NilReasonEnumeration)
NilReasonEnumeration._CF_pattern = pyxb.binding.facets.CF_pattern()
NilReasonEnumeration.inapplicable = 'inapplicable'# originally STD_ANON.inapplicable
NilReasonEnumeration.missing = 'missing'          # originally STD_ANON.missing
NilReasonEnumeration.template = 'template'        # originally STD_ANON.template
NilReasonEnumeration.unknown = 'unknown'          # originally STD_ANON.unknown
NilReasonEnumeration.withheld = 'withheld'        # originally STD_ANON.withheld
NilReasonEnumeration._InitializeFacetMap(NilReasonEnumeration._CF_enumeration,
   NilReasonEnumeration._CF_pattern)
Namespace.addCategoryObject('typeBinding', 'NilReasonEnumeration', NilReasonEnumeration)
_module_typeBindings.NilReasonEnumeration = NilReasonEnumeration

# Union simple type: {http://www.opengis.net/gml/3.2}booleanOrNilReason
# superclasses pyxb.binding.datatypes.anySimpleType
class booleanOrNilReason (pyxb.binding.basis.STD_union):

    """Extension to the respective XML Schema built-in simple type to allow a choice of either a value of the built-in simple type or a reason for a nil value."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'booleanOrNilReason')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1315, 1)
    _Documentation = 'Extension to the respective XML Schema built-in simple type to allow a choice of either a value of the built-in simple type or a reason for a nil value.'

    _MemberTypes = ( STD_ANON, STD_ANON_, pyxb.binding.datatypes.boolean, )
booleanOrNilReason._CF_enumeration = pyxb.binding.facets.CF_enumeration(value_datatype=booleanOrNilReason)
booleanOrNilReason._CF_pattern = pyxb.binding.facets.CF_pattern()
booleanOrNilReason.inapplicable = 'inapplicable'  # originally STD_ANON.inapplicable
booleanOrNilReason.missing = 'missing'            # originally STD_ANON.missing
booleanOrNilReason.template = 'template'          # originally STD_ANON.template
booleanOrNilReason.unknown = 'unknown'            # originally STD_ANON.unknown
booleanOrNilReason.withheld = 'withheld'          # originally STD_ANON.withheld
booleanOrNilReason._InitializeFacetMap(booleanOrNilReason._CF_enumeration,
   booleanOrNilReason._CF_pattern)
Namespace.addCategoryObject('typeBinding', 'booleanOrNilReason', booleanOrNilReason)
_module_typeBindings.booleanOrNilReason = booleanOrNilReason

# Union simple type: {http://www.opengis.net/gml/3.2}doubleOrNilReason
# superclasses pyxb.binding.datatypes.anySimpleType
class doubleOrNilReason (pyxb.binding.basis.STD_union):

    """Extension to the respective XML Schema built-in simple type to allow a choice of either a value of the built-in simple type or a reason for a nil value."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'doubleOrNilReason')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1321, 1)
    _Documentation = 'Extension to the respective XML Schema built-in simple type to allow a choice of either a value of the built-in simple type or a reason for a nil value.'

    _MemberTypes = ( STD_ANON, STD_ANON_, pyxb.binding.datatypes.double, )
doubleOrNilReason._CF_enumeration = pyxb.binding.facets.CF_enumeration(value_datatype=doubleOrNilReason)
doubleOrNilReason._CF_pattern = pyxb.binding.facets.CF_pattern()
doubleOrNilReason.inapplicable = 'inapplicable'   # originally STD_ANON.inapplicable
doubleOrNilReason.missing = 'missing'             # originally STD_ANON.missing
doubleOrNilReason.template = 'template'           # originally STD_ANON.template
doubleOrNilReason.unknown = 'unknown'             # originally STD_ANON.unknown
doubleOrNilReason.withheld = 'withheld'           # originally STD_ANON.withheld
doubleOrNilReason._InitializeFacetMap(doubleOrNilReason._CF_enumeration,
   doubleOrNilReason._CF_pattern)
Namespace.addCategoryObject('typeBinding', 'doubleOrNilReason', doubleOrNilReason)
_module_typeBindings.doubleOrNilReason = doubleOrNilReason

# Union simple type: {http://www.opengis.net/gml/3.2}integerOrNilReason
# superclasses pyxb.binding.datatypes.anySimpleType
class integerOrNilReason (pyxb.binding.basis.STD_union):

    """Extension to the respective XML Schema built-in simple type to allow a choice of either a value of the built-in simple type or a reason for a nil value."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'integerOrNilReason')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1327, 1)
    _Documentation = 'Extension to the respective XML Schema built-in simple type to allow a choice of either a value of the built-in simple type or a reason for a nil value.'

    _MemberTypes = ( STD_ANON, STD_ANON_, pyxb.binding.datatypes.integer, )
integerOrNilReason._CF_enumeration = pyxb.binding.facets.CF_enumeration(value_datatype=integerOrNilReason)
integerOrNilReason._CF_pattern = pyxb.binding.facets.CF_pattern()
integerOrNilReason.inapplicable = 'inapplicable'  # originally STD_ANON.inapplicable
integerOrNilReason.missing = 'missing'            # originally STD_ANON.missing
integerOrNilReason.template = 'template'          # originally STD_ANON.template
integerOrNilReason.unknown = 'unknown'            # originally STD_ANON.unknown
integerOrNilReason.withheld = 'withheld'          # originally STD_ANON.withheld
integerOrNilReason._InitializeFacetMap(integerOrNilReason._CF_enumeration,
   integerOrNilReason._CF_pattern)
Namespace.addCategoryObject('typeBinding', 'integerOrNilReason', integerOrNilReason)
_module_typeBindings.integerOrNilReason = integerOrNilReason

# Union simple type: {http://www.opengis.net/gml/3.2}NameOrNilReason
# superclasses pyxb.binding.datatypes.anySimpleType
class NameOrNilReason (pyxb.binding.basis.STD_union):

    """Extension to the respective XML Schema built-in simple type to allow a choice of either a value of the built-in simple type or a reason for a nil value."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'NameOrNilReason')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1333, 1)
    _Documentation = 'Extension to the respective XML Schema built-in simple type to allow a choice of either a value of the built-in simple type or a reason for a nil value.'

    _MemberTypes = ( STD_ANON, STD_ANON_, pyxb.binding.datatypes.Name, )
NameOrNilReason._CF_enumeration = pyxb.binding.facets.CF_enumeration(value_datatype=NameOrNilReason)
NameOrNilReason._CF_pattern = pyxb.binding.facets.CF_pattern()
NameOrNilReason.inapplicable = 'inapplicable'     # originally STD_ANON.inapplicable
NameOrNilReason.missing = 'missing'               # originally STD_ANON.missing
NameOrNilReason.template = 'template'             # originally STD_ANON.template
NameOrNilReason.unknown = 'unknown'               # originally STD_ANON.unknown
NameOrNilReason.withheld = 'withheld'             # originally STD_ANON.withheld
NameOrNilReason._InitializeFacetMap(NameOrNilReason._CF_enumeration,
   NameOrNilReason._CF_pattern)
Namespace.addCategoryObject('typeBinding', 'NameOrNilReason', NameOrNilReason)
_module_typeBindings.NameOrNilReason = NameOrNilReason

# Union simple type: {http://www.opengis.net/gml/3.2}stringOrNilReason
# superclasses pyxb.binding.datatypes.anySimpleType
class stringOrNilReason (pyxb.binding.basis.STD_union):

    """Extension to the respective XML Schema built-in simple type to allow a choice of either a value of the built-in simple type or a reason for a nil value."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'stringOrNilReason')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1339, 1)
    _Documentation = 'Extension to the respective XML Schema built-in simple type to allow a choice of either a value of the built-in simple type or a reason for a nil value.'

    _MemberTypes = ( STD_ANON, STD_ANON_, pyxb.binding.datatypes.string, )
stringOrNilReason._CF_enumeration = pyxb.binding.facets.CF_enumeration(value_datatype=stringOrNilReason)
stringOrNilReason._CF_pattern = pyxb.binding.facets.CF_pattern()
stringOrNilReason.inapplicable = 'inapplicable'   # originally STD_ANON.inapplicable
stringOrNilReason.missing = 'missing'             # originally STD_ANON.missing
stringOrNilReason.template = 'template'           # originally STD_ANON.template
stringOrNilReason.unknown = 'unknown'             # originally STD_ANON.unknown
stringOrNilReason.withheld = 'withheld'           # originally STD_ANON.withheld
stringOrNilReason._InitializeFacetMap(stringOrNilReason._CF_enumeration,
   stringOrNilReason._CF_pattern)
Namespace.addCategoryObject('typeBinding', 'stringOrNilReason', stringOrNilReason)
_module_typeBindings.stringOrNilReason = stringOrNilReason

# Union simple type: {http://www.opengis.net/gml/3.2}UomIdentifier
# superclasses pyxb.binding.datatypes.anySimpleType
class UomIdentifier (pyxb.binding.basis.STD_union):

    """The simple type gml:UomIdentifer defines the syntax and value space of
				the unit of measure identifier."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'UomIdentifier')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1382, 1)
    _Documentation = 'The simple type gml:UomIdentifer defines the syntax and value space of\n\t\t\t\tthe unit of measure identifier.'

    _MemberTypes = ( UomSymbol, UomURI, )
UomIdentifier._CF_enumeration = pyxb.binding.facets.CF_enumeration(value_datatype=UomIdentifier)
UomIdentifier._CF_pattern = pyxb.binding.facets.CF_pattern()
UomIdentifier._InitializeFacetMap(UomIdentifier._CF_enumeration,
   UomIdentifier._CF_pattern)
Namespace.addCategoryObject('typeBinding', 'UomIdentifier', UomIdentifier)
_module_typeBindings.UomIdentifier = UomIdentifier

# Complex type {http://www.opengis.net/gml/3.2}AbstractGMLType with content type EMPTY
class AbstractGMLType (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://www.opengis.net/gml/3.2}AbstractGMLType with content type EMPTY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_EMPTY
    _Abstract = True
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractGMLType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 183, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Attribute {http://www.opengis.net/gml/3.2}id uses Python identifier id
    __id = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'id'), 'id', '__httpwww_opengis_netgml3_2_AbstractGMLType_httpwww_opengis_netgml3_2id', pyxb.binding.datatypes.ID, required=True)
    __id._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 274, 1)
    __id._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 184, 2)
    
    id = property(__id.value, __id.set, None, 'The attribute gml:id supports provision of a handle for the XML element\n\t\t\t\trepresenting a GML Object. Its use is mandatory for all GML objects. It is of XML\n\t\t\t\ttype ID, so is constrained to be unique in the XML document within which it\n\t\t\toccurs.')

    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __id.name() : __id
    })
_module_typeBindings.AbstractGMLType = AbstractGMLType
Namespace.addCategoryObject('typeBinding', 'AbstractGMLType', AbstractGMLType)


# Complex type {http://www.opengis.net/gml/3.2}InlinePropertyType with content type ELEMENT_ONLY
class InlinePropertyType (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://www.opengis.net/gml/3.2}InlinePropertyType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'InlinePropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 258, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Attribute owns uses Python identifier owns
    __owns = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'owns'), 'owns', '__httpwww_opengis_netgml3_2_InlinePropertyType_owns', pyxb.binding.datatypes.boolean, unicode_default='false')
    __owns._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    __owns._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    
    owns = property(__owns.value, __owns.set, None, None)

    _HasWildcardElement = True
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __owns.name() : __owns
    })
_module_typeBindings.InlinePropertyType = InlinePropertyType
Namespace.addCategoryObject('typeBinding', 'InlinePropertyType', InlinePropertyType)


# Complex type {http://www.opengis.net/gml/3.2}AbstractMemberType with content type EMPTY
class AbstractMemberType (pyxb.binding.basis.complexTypeDefinition):
    """To create a collection of GML Objects that are not all features, a
				property type shall be derived by extension from gml:AbstractMemberType. This
				abstract property type is intended to be used only in object types where software
				shall be able to identify that an instance of such an object type is to be
				interpreted as a collection of objects. By default, this abstract property type does
				not imply any ownership of the objects in the collection. The owns attribute of
				gml:OwnershipAttributeGroup may be used on a property element instance to assert
				ownership of an object in the collection. A collection shall not own an object
				already owned by another object. """
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_EMPTY
    _Abstract = True
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractMemberType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 282, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Attribute owns uses Python identifier owns
    __owns = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'owns'), 'owns', '__httpwww_opengis_netgml3_2_AbstractMemberType_owns', pyxb.binding.datatypes.boolean, unicode_default='false')
    __owns._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    __owns._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    
    owns = property(__owns.value, __owns.set, None, None)

    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __owns.name() : __owns
    })
_module_typeBindings.AbstractMemberType = AbstractMemberType
Namespace.addCategoryObject('typeBinding', 'AbstractMemberType', AbstractMemberType)


# Complex type {http://www.opengis.net/gml/3.2}AbstractMetadataPropertyType with content type EMPTY
class AbstractMetadataPropertyType (pyxb.binding.basis.complexTypeDefinition):
    """To associate metadata described by any XML Schema with a GML object, a
				property element shall be defined whose content model is derived by extension from
				gml:AbstractMetadataPropertyType. The value of such a property shall be metadata.
				The content model of such a property type, i.e. the metadata application schema
				shall be specified by the GML Application Schema. By default, this abstract property
				type does not imply any ownership of the metadata. The owns attribute of
				gml:OwnershipAttributeGroup may be used on a metadata property element instance to
				assert ownership of the metadata. If metadata following the conceptual model of ISO
				19115 is to be encoded in a GML document, the corresponding Implementation
				Specification specified in ISO/TS 19139 shall be used to encode the metadata
				information. """
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_EMPTY
    _Abstract = True
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractMetadataPropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 321, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Attribute owns uses Python identifier owns
    __owns = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'owns'), 'owns', '__httpwww_opengis_netgml3_2_AbstractMetadataPropertyType_owns', pyxb.binding.datatypes.boolean, unicode_default='false')
    __owns._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    __owns._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    
    owns = property(__owns.value, __owns.set, None, None)

    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __owns.name() : __owns
    })
_module_typeBindings.AbstractMetadataPropertyType = AbstractMetadataPropertyType
Namespace.addCategoryObject('typeBinding', 'AbstractMetadataPropertyType', AbstractMetadataPropertyType)


# Complex type {http://www.opengis.net/gml/3.2}AbstractFeatureMemberType with content type EMPTY
class AbstractFeatureMemberType (pyxb.binding.basis.complexTypeDefinition):
    """To create a collection of GML features, a property type shall be derived
				by extension from gml:AbstractFeatureMemberType. By default, this abstract property
				type does not imply any ownership of the features in the collection. The owns
				attribute of gml:OwnershipAttributeGroup may be used on a property element instance
				to assert ownership of a feature in the collection. A collection shall not own a
				feature already owned by another object."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_EMPTY
    _Abstract = True
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractFeatureMemberType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 396, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Attribute owns uses Python identifier owns
    __owns = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'owns'), 'owns', '__httpwww_opengis_netgml3_2_AbstractFeatureMemberType_owns', pyxb.binding.datatypes.boolean, unicode_default='false')
    __owns._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    __owns._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    
    owns = property(__owns.value, __owns.set, None, None)

    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __owns.name() : __owns
    })
_module_typeBindings.AbstractFeatureMemberType = AbstractFeatureMemberType
Namespace.addCategoryObject('typeBinding', 'AbstractFeatureMemberType', AbstractFeatureMemberType)


# Complex type {http://www.opengis.net/gml/3.2}EnvelopeType with content type ELEMENT_ONLY
class EnvelopeType (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://www.opengis.net/gml/3.2}EnvelopeType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'EnvelopeType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 423, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.opengis.net/gml/3.2}lowerCorner uses Python identifier lowerCorner
    __lowerCorner = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'lowerCorner'), 'lowerCorner', '__httpwww_opengis_netgml3_2_EnvelopeType_httpwww_opengis_netgml3_2lowerCorner', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 425, 3), )

    
    lowerCorner = property(__lowerCorner.value, __lowerCorner.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}upperCorner uses Python identifier upperCorner
    __upperCorner = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'upperCorner'), 'upperCorner', '__httpwww_opengis_netgml3_2_EnvelopeType_httpwww_opengis_netgml3_2upperCorner', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 426, 3), )

    
    upperCorner = property(__upperCorner.value, __upperCorner.set, None, None)

    
    # Attribute srsName uses Python identifier srsName
    __srsName = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'srsName'), 'srsName', '__httpwww_opengis_netgml3_2_EnvelopeType_srsName', pyxb.binding.datatypes.anyURI)
    __srsName._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 468, 2)
    __srsName._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 468, 2)
    
    srsName = property(__srsName.value, __srsName.set, None, None)

    
    # Attribute srsDimension uses Python identifier srsDimension
    __srsDimension = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'srsDimension'), 'srsDimension', '__httpwww_opengis_netgml3_2_EnvelopeType_srsDimension', pyxb.binding.datatypes.positiveInteger)
    __srsDimension._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 469, 2)
    __srsDimension._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 469, 2)
    
    srsDimension = property(__srsDimension.value, __srsDimension.set, None, None)

    _ElementMap.update({
        __lowerCorner.name() : __lowerCorner,
        __upperCorner.name() : __upperCorner
    })
    _AttributeMap.update({
        __srsName.name() : __srsName,
        __srsDimension.name() : __srsDimension
    })
_module_typeBindings.EnvelopeType = EnvelopeType
Namespace.addCategoryObject('typeBinding', 'EnvelopeType', EnvelopeType)


# Complex type {http://www.opengis.net/gml/3.2}AbstractRingType with content type EMPTY
class AbstractRingType (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://www.opengis.net/gml/3.2}AbstractRingType with content type EMPTY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_EMPTY
    _Abstract = True
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractRingType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 729, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.AbstractRingType = AbstractRingType
Namespace.addCategoryObject('typeBinding', 'AbstractRingType', AbstractRingType)


# Complex type {http://www.opengis.net/gml/3.2}AbstractRingPropertyType with content type ELEMENT_ONLY
class AbstractRingPropertyType (pyxb.binding.basis.complexTypeDefinition):
    """A property with the content model of gml:AbstractRingPropertyType
				encapsulates a ring to represent the surface boundary property of a
			surface."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractRingPropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 732, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.opengis.net/gml/3.2}AbstractRing uses Python identifier AbstractRing
    __AbstractRing = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'AbstractRing'), 'AbstractRing', '__httpwww_opengis_netgml3_2_AbstractRingPropertyType_httpwww_opengis_netgml3_2AbstractRing', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 722, 1), )

    
    AbstractRing = property(__AbstractRing.value, __AbstractRing.set, None, 'An abstraction of a ring to support surface boundaries of different\n\t\t\t\tcomplexity. The AbstractRing element is the abstract head of the substituition group\n\t\t\t\tfor all closed boundaries of a surface patch.')

    _ElementMap.update({
        __AbstractRing.name() : __AbstractRing
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.AbstractRingPropertyType = AbstractRingPropertyType
Namespace.addCategoryObject('typeBinding', 'AbstractRingPropertyType', AbstractRingPropertyType)


# Complex type {http://www.opengis.net/gml/3.2}LinearRingPropertyType with content type ELEMENT_ONLY
class LinearRingPropertyType (pyxb.binding.basis.complexTypeDefinition):
    """A property with the content model of gml:LinearRingPropertyType
				encapsulates a linear ring to represent a component of a surface
			boundary."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'LinearRingPropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 775, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.opengis.net/gml/3.2}LinearRing uses Python identifier LinearRing
    __LinearRing = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'LinearRing'), 'LinearRing', '__httpwww_opengis_netgml3_2_LinearRingPropertyType_httpwww_opengis_netgml3_2LinearRing', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 742, 1), )

    
    LinearRing = property(__LinearRing.value, __LinearRing.set, None, 'A LinearRing is defined by four or more coordinate tuples, with linear\n\t\t\t\tinterpolation between them; the first and last coordinates shall be coincident. The\n\t\t\t\tnumber of direct positions in the list shall be at least four.')

    _ElementMap.update({
        __LinearRing.name() : __LinearRing
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.LinearRingPropertyType = LinearRingPropertyType
Namespace.addCategoryObject('typeBinding', 'LinearRingPropertyType', LinearRingPropertyType)


# Complex type {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType with content type EMPTY
class AbstractCurveSegmentType (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType with content type EMPTY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_EMPTY
    _Abstract = True
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractCurveSegmentType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 855, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Attribute numDerivativesAtStart uses Python identifier numDerivativesAtStart
    __numDerivativesAtStart = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'numDerivativesAtStart'), 'numDerivativesAtStart', '__httpwww_opengis_netgml3_2_AbstractCurveSegmentType_numDerivativesAtStart', pyxb.binding.datatypes.integer, unicode_default='0')
    __numDerivativesAtStart._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 856, 2)
    __numDerivativesAtStart._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 856, 2)
    
    numDerivativesAtStart = property(__numDerivativesAtStart.value, __numDerivativesAtStart.set, None, None)

    
    # Attribute numDerivativesAtEnd uses Python identifier numDerivativesAtEnd
    __numDerivativesAtEnd = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'numDerivativesAtEnd'), 'numDerivativesAtEnd', '__httpwww_opengis_netgml3_2_AbstractCurveSegmentType_numDerivativesAtEnd', pyxb.binding.datatypes.integer, unicode_default='0')
    __numDerivativesAtEnd._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 857, 2)
    __numDerivativesAtEnd._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 857, 2)
    
    numDerivativesAtEnd = property(__numDerivativesAtEnd.value, __numDerivativesAtEnd.set, None, None)

    
    # Attribute numDerivativeInterior uses Python identifier numDerivativeInterior
    __numDerivativeInterior = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'numDerivativeInterior'), 'numDerivativeInterior', '__httpwww_opengis_netgml3_2_AbstractCurveSegmentType_numDerivativeInterior', pyxb.binding.datatypes.integer, unicode_default='0')
    __numDerivativeInterior._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 858, 2)
    __numDerivativeInterior._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 858, 2)
    
    numDerivativeInterior = property(__numDerivativeInterior.value, __numDerivativeInterior.set, None, None)

    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __numDerivativesAtStart.name() : __numDerivativesAtStart,
        __numDerivativesAtEnd.name() : __numDerivativesAtEnd,
        __numDerivativeInterior.name() : __numDerivativeInterior
    })
_module_typeBindings.AbstractCurveSegmentType = AbstractCurveSegmentType
Namespace.addCategoryObject('typeBinding', 'AbstractCurveSegmentType', AbstractCurveSegmentType)


# Complex type {http://www.opengis.net/gml/3.2}CurveSegmentArrayPropertyType with content type ELEMENT_ONLY
class CurveSegmentArrayPropertyType (pyxb.binding.basis.complexTypeDefinition):
    """gml:CurveSegmentArrayPropertyType is a container for an array of curve
				segments."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'CurveSegmentArrayPropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 860, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.opengis.net/gml/3.2}AbstractCurveSegment uses Python identifier AbstractCurveSegment
    __AbstractCurveSegment = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'AbstractCurveSegment'), 'AbstractCurveSegment', '__httpwww_opengis_netgml3_2_CurveSegmentArrayPropertyType_httpwww_opengis_netgml3_2AbstractCurveSegment', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 842, 1), )

    
    AbstractCurveSegment = property(__AbstractCurveSegment.value, __AbstractCurveSegment.set, None, 'A curve segment defines a homogeneous segment of a curve. The attributes\n\t\t\t\tnumDerivativesAtStart, numDerivativesAtEnd and numDerivativesInterior specify the\n\t\t\t\ttype of continuity as specified in ISO 19107:2003, 6.4.9.3. The AbstractCurveSegment\n\t\t\t\telement is the abstract head of the substituition group for all curve segment\n\t\t\t\telements, i.e. continuous segments of the same interpolation mechanism. All curve\n\t\t\t\tsegments shall have an attribute interpolation with type gml:CurveInterpolationType\n\t\t\t\tspecifying the curve interpolation mechanism used for this segment. This mechanism\n\t\t\t\tuses the control points and control parameters to determine the position of this\n\t\t\t\tcurve segment.')

    _ElementMap.update({
        __AbstractCurveSegment.name() : __AbstractCurveSegment
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.CurveSegmentArrayPropertyType = CurveSegmentArrayPropertyType
Namespace.addCategoryObject('typeBinding', 'CurveSegmentArrayPropertyType', CurveSegmentArrayPropertyType)


# Complex type {http://www.opengis.net/gml/3.2}SurfacePatchArrayPropertyType with content type ELEMENT_ONLY
class SurfacePatchArrayPropertyType (pyxb.binding.basis.complexTypeDefinition):
    """gml:SurfacePatchArrayPropertyType is a container for a sequence of
				surface patches."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'SurfacePatchArrayPropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1113, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.opengis.net/gml/3.2}AbstractSurfacePatch uses Python identifier AbstractSurfacePatch
    __AbstractSurfacePatch = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'AbstractSurfacePatch'), 'AbstractSurfacePatch', '__httpwww_opengis_netgml3_2_SurfacePatchArrayPropertyType_httpwww_opengis_netgml3_2AbstractSurfacePatch', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1122, 1), )

    
    AbstractSurfacePatch = property(__AbstractSurfacePatch.value, __AbstractSurfacePatch.set, None, 'A surface patch defines a homogenuous portion of a surface. The\n\t\t\t\tAbstractSurfacePatch element is the abstract head of the substituition group for all\n\t\t\t\tsurface patch elements describing a continuous portion of a surface. All surface\n\t\t\t\tpatches shall have an attribute interpolation (declared in the types derived from\n\t\t\t\tgml:AbstractSurfacePatchType) specifying the interpolation mechanism used for the\n\t\t\t\tpatch using gml:SurfaceInterpolationType.')

    _ElementMap.update({
        __AbstractSurfacePatch.name() : __AbstractSurfacePatch
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.SurfacePatchArrayPropertyType = SurfacePatchArrayPropertyType
Namespace.addCategoryObject('typeBinding', 'SurfacePatchArrayPropertyType', SurfacePatchArrayPropertyType)


# Complex type {http://www.opengis.net/gml/3.2}AbstractSurfacePatchType with content type EMPTY
class AbstractSurfacePatchType (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://www.opengis.net/gml/3.2}AbstractSurfacePatchType with content type EMPTY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_EMPTY
    _Abstract = True
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractSurfacePatchType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1132, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.AbstractSurfacePatchType = AbstractSurfacePatchType
Namespace.addCategoryObject('typeBinding', 'AbstractSurfacePatchType', AbstractSurfacePatchType)


# Complex type {http://www.opengis.net/gml/3.2}CodeType with content type SIMPLE
class CodeType (pyxb.binding.basis.complexTypeDefinition):
    """gml:CodeType is a generalized type to be used for a term, keyword or
				name. It adds a XML attribute codeSpace to a term, where the value of the codeSpace
				attribute (if present) shall indicate a dictionary, thesaurus, classification
				scheme, authority, or pattern for the term."""
    _TypeDefinition = pyxb.binding.datatypes.string
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_SIMPLE
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'CodeType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1345, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.string
    
    # Attribute codeSpace uses Python identifier codeSpace
    __codeSpace = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'codeSpace'), 'codeSpace', '__httpwww_opengis_netgml3_2_CodeType_codeSpace', pyxb.binding.datatypes.anyURI)
    __codeSpace._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1354, 4)
    __codeSpace._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1354, 4)
    
    codeSpace = property(__codeSpace.value, __codeSpace.set, None, None)

    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __codeSpace.name() : __codeSpace
    })
_module_typeBindings.CodeType = CodeType
Namespace.addCategoryObject('typeBinding', 'CodeType', CodeType)


# Complex type {http://www.opengis.net/gml/3.2}AbstractFeatureType with content type ELEMENT_ONLY
class AbstractFeatureType (AbstractGMLType):
    """The basic feature model is given by the gml:AbstractFeatureType. The
				content model for gml:AbstractFeatureType adds two specific properties suitable for
				geographic features to the content model defined in gml:AbstractGMLType. The value
				of the gml:boundedBy property describes an envelope that encloses the entire feature
				instance, and is primarily useful for supporting rapid searching for features that
				occur in a particular location. The value of the gml:location property describes the
				extent, position or relative location of the feature."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = True
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractFeatureType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 357, 1)
    _ElementMap = AbstractGMLType._ElementMap.copy()
    _AttributeMap = AbstractGMLType._AttributeMap.copy()
    # Base type is AbstractGMLType
    
    # Element {http://www.opengis.net/gml/3.2}boundedBy uses Python identifier boundedBy
    __boundedBy = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'boundedBy'), 'boundedBy', '__httpwww_opengis_netgml3_2_AbstractFeatureType_httpwww_opengis_netgml3_2boundedBy', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 382, 1), )

    
    boundedBy = property(__boundedBy.value, __boundedBy.set, None, 'This property describes the minimum bounding box or rectangle that\n\t\t\t\tencloses the entire feature.')

    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    _ElementMap.update({
        __boundedBy.name() : __boundedBy
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.AbstractFeatureType = AbstractFeatureType
Namespace.addCategoryObject('typeBinding', 'AbstractFeatureType', AbstractFeatureType)


# Complex type {http://www.opengis.net/gml/3.2}AbstractGeometryType with content type EMPTY
class AbstractGeometryType (AbstractGMLType):
    """All geometry elements are derived directly or indirectly from this
				abstract supertype. A geometry element may have an identifying attribute (gml:id),
				one or more names (elements identifier and name) and a description (elements
				description and descriptionReference) . It may be associated with a spatial
				reference system (attribute group gml:SRSReferenceGroup). The following rules shall
				be adhered to: - Every geometry type shall derive from this abstract type. - Every
				geometry element (i.e. an element of a geometry type) shall be directly or
				indirectly in the substitution group of AbstractGeometry."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_EMPTY
    _Abstract = True
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractGeometryType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 440, 1)
    _ElementMap = AbstractGMLType._ElementMap.copy()
    _AttributeMap = AbstractGMLType._AttributeMap.copy()
    # Base type is AbstractGMLType
    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute srsName uses Python identifier srsName
    __srsName = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'srsName'), 'srsName', '__httpwww_opengis_netgml3_2_AbstractGeometryType_srsName', pyxb.binding.datatypes.anyURI)
    __srsName._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 468, 2)
    __srsName._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 468, 2)
    
    srsName = property(__srsName.value, __srsName.set, None, None)

    
    # Attribute srsDimension uses Python identifier srsDimension
    __srsDimension = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'srsDimension'), 'srsDimension', '__httpwww_opengis_netgml3_2_AbstractGeometryType_srsDimension', pyxb.binding.datatypes.positiveInteger)
    __srsDimension._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 469, 2)
    __srsDimension._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 469, 2)
    
    srsDimension = property(__srsDimension.value, __srsDimension.set, None, None)

    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __srsName.name() : __srsName,
        __srsDimension.name() : __srsDimension
    })
_module_typeBindings.AbstractGeometryType = AbstractGeometryType
Namespace.addCategoryObject('typeBinding', 'AbstractGeometryType', AbstractGeometryType)


# Complex type {http://www.opengis.net/gml/3.2}DirectPositionType with content type SIMPLE
class DirectPositionType (pyxb.binding.basis.complexTypeDefinition):
    """Direct position instances hold the coordinates for a position within some
				coordinate reference system (CRS). Since direct positions, as data types, will often
				be included in larger objects (such as geometry elements) that have references to
				CRS, the srsName attribute will in general be missing, if this particular direct
				position is included in a larger element with such a reference to a CRS. In this
				case, the CRS is implicitly assumed to take on the value of the containing object's
				CRS. if no srsName attribute is given, the CRS shall be specified as part of the
				larger context this geometry element is part of, typically a geometric object like a
				point, curve, etc."""
    _TypeDefinition = doubleList
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_SIMPLE
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'DirectPositionType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 472, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is doubleList
    
    # Attribute srsName uses Python identifier srsName
    __srsName = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'srsName'), 'srsName', '__httpwww_opengis_netgml3_2_DirectPositionType_srsName', pyxb.binding.datatypes.anyURI)
    __srsName._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 468, 2)
    __srsName._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 468, 2)
    
    srsName = property(__srsName.value, __srsName.set, None, None)

    
    # Attribute srsDimension uses Python identifier srsDimension
    __srsDimension = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'srsDimension'), 'srsDimension', '__httpwww_opengis_netgml3_2_DirectPositionType_srsDimension', pyxb.binding.datatypes.positiveInteger)
    __srsDimension._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 469, 2)
    __srsDimension._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 469, 2)
    
    srsDimension = property(__srsDimension.value, __srsDimension.set, None, None)

    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __srsName.name() : __srsName,
        __srsDimension.name() : __srsDimension
    })
_module_typeBindings.DirectPositionType = DirectPositionType
Namespace.addCategoryObject('typeBinding', 'DirectPositionType', DirectPositionType)


# Complex type {http://www.opengis.net/gml/3.2}DirectPositionListType with content type SIMPLE
class DirectPositionListType (pyxb.binding.basis.complexTypeDefinition):
    """posList instances (and other instances with the content model specified
				by DirectPositionListType) hold the coordinates for a sequence of direct positions
				within the same coordinate reference system (CRS). if no srsName attribute is given,
				the CRS shall be specified as part of the larger context this geometry element is
				part of, typically a geometric object like a point, curve, etc. The optional
				attribute count specifies the number of direct positions in the list. If the
				attribute count is present then the attribute srsDimension shall be present, too.
				The number of entries in the list is equal to the product of the dimensionality of
				the coordinate reference system (i.e. it is a derived value of the coordinate
				reference system definition) and the number of direct positions."""
    _TypeDefinition = doubleList
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_SIMPLE
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'DirectPositionListType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 491, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is doubleList
    
    # Attribute srsName uses Python identifier srsName
    __srsName = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'srsName'), 'srsName', '__httpwww_opengis_netgml3_2_DirectPositionListType_srsName', pyxb.binding.datatypes.anyURI)
    __srsName._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 468, 2)
    __srsName._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 468, 2)
    
    srsName = property(__srsName.value, __srsName.set, None, None)

    
    # Attribute srsDimension uses Python identifier srsDimension
    __srsDimension = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'srsDimension'), 'srsDimension', '__httpwww_opengis_netgml3_2_DirectPositionListType_srsDimension', pyxb.binding.datatypes.positiveInteger)
    __srsDimension._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 469, 2)
    __srsDimension._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 469, 2)
    
    srsDimension = property(__srsDimension.value, __srsDimension.set, None, None)

    
    # Attribute count uses Python identifier count
    __count = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'count'), 'count', '__httpwww_opengis_netgml3_2_DirectPositionListType_count', pyxb.binding.datatypes.positiveInteger)
    __count._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 507, 4)
    __count._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 507, 4)
    
    count = property(__count.value, __count.set, None, None)

    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __srsName.name() : __srsName,
        __srsDimension.name() : __srsDimension,
        __count.name() : __count
    })
_module_typeBindings.DirectPositionListType = DirectPositionListType
Namespace.addCategoryObject('typeBinding', 'DirectPositionListType', DirectPositionListType)


# Complex type {http://www.opengis.net/gml/3.2}LinearRingType with content type ELEMENT_ONLY
class LinearRingType (AbstractRingType):
    """S-100 XML supports two different ways to specify the control points of a
				linear ring. 1. A sequence of "pos" (DirectPositionType) or "pointProperty"
				(PointPropertyType) elements. "pos" elements are control points that are only part
				of this ring, "pointProperty" elements contain a point that may be referenced from
				other geometry elements or reference another point defined outside of this ring
				(reuse of existing points). 2. The "posList" element allows for a compact way to
				specifiy the coordinates of the control points, if all control points are in the
				same coordinate reference systems and belong to this ring only. The number of direct
				positions in the list must be at least four."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'LinearRingType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 749, 1)
    _ElementMap = AbstractRingType._ElementMap.copy()
    _AttributeMap = AbstractRingType._AttributeMap.copy()
    # Base type is AbstractRingType
    
    # Element {http://www.opengis.net/gml/3.2}pos uses Python identifier pos
    __pos = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'pos'), 'pos', '__httpwww_opengis_netgml3_2_LinearRingType_httpwww_opengis_netgml3_2pos', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1), )

    
    pos = property(__pos.value, __pos.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}posList uses Python identifier posList
    __posList = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'posList'), 'posList', '__httpwww_opengis_netgml3_2_LinearRingType_httpwww_opengis_netgml3_2posList', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 490, 1), )

    
    posList = property(__posList.value, __posList.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}pointProperty uses Python identifier pointProperty
    __pointProperty = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'pointProperty'), 'pointProperty', '__httpwww_opengis_netgml3_2_LinearRingType_httpwww_opengis_netgml3_2pointProperty', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1), )

    
    pointProperty = property(__pointProperty.value, __pointProperty.set, None, 'This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.')

    _ElementMap.update({
        __pos.name() : __pos,
        __posList.name() : __posList,
        __pointProperty.name() : __pointProperty
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.LinearRingType = LinearRingType
Namespace.addCategoryObject('typeBinding', 'LinearRingType', LinearRingType)


# Complex type {http://www.opengis.net/gml/3.2}LineStringSegmentType with content type ELEMENT_ONLY
class LineStringSegmentType (AbstractCurveSegmentType):
    """GML supports two different ways to specify the control points of a line
				string. 1. A sequence of "pos" (DirectPositionType) or "pointProperty"
				(PointPropertyType) elements. "pos" elements are control points that are only part
				of this curve, "pointProperty" elements contain a point that may be referenced from
				other geometry elements or reference another point defined outside of this curve
				(reuse of existing points). 2. The "posList" element allows for a compact way to
				specifiy the coordinates of the control points, if all control points are in the
				same coordinate reference systems and belong to this curve only. The number of
				direct positions in the list must be at least two."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'LineStringSegmentType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 893, 1)
    _ElementMap = AbstractCurveSegmentType._ElementMap.copy()
    _AttributeMap = AbstractCurveSegmentType._AttributeMap.copy()
    # Base type is AbstractCurveSegmentType
    
    # Element {http://www.opengis.net/gml/3.2}pos uses Python identifier pos
    __pos = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'pos'), 'pos', '__httpwww_opengis_netgml3_2_LineStringSegmentType_httpwww_opengis_netgml3_2pos', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1), )

    
    pos = property(__pos.value, __pos.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}posList uses Python identifier posList
    __posList = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'posList'), 'posList', '__httpwww_opengis_netgml3_2_LineStringSegmentType_httpwww_opengis_netgml3_2posList', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 490, 1), )

    
    posList = property(__posList.value, __posList.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}pointProperty uses Python identifier pointProperty
    __pointProperty = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'pointProperty'), 'pointProperty', '__httpwww_opengis_netgml3_2_LineStringSegmentType_httpwww_opengis_netgml3_2pointProperty', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1), )

    
    pointProperty = property(__pointProperty.value, __pointProperty.set, None, 'This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.')

    
    # Attribute numDerivativesAtStart inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute numDerivativesAtEnd inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute numDerivativeInterior inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute interpolation uses Python identifier interpolation
    __interpolation = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'interpolation'), 'interpolation', '__httpwww_opengis_netgml3_2_LineStringSegmentType_interpolation', _module_typeBindings.CurveInterpolationType, fixed=True, unicode_default='linear')
    __interpolation._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 919, 4)
    __interpolation._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 919, 4)
    
    interpolation = property(__interpolation.value, __interpolation.set, None, None)

    _ElementMap.update({
        __pos.name() : __pos,
        __posList.name() : __posList,
        __pointProperty.name() : __pointProperty
    })
    _AttributeMap.update({
        __interpolation.name() : __interpolation
    })
_module_typeBindings.LineStringSegmentType = LineStringSegmentType
Namespace.addCategoryObject('typeBinding', 'LineStringSegmentType', LineStringSegmentType)


# Complex type {http://www.opengis.net/gml/3.2}GeodesicStringType with content type ELEMENT_ONLY
class GeodesicStringType (AbstractCurveSegmentType):
    """Complex type {http://www.opengis.net/gml/3.2}GeodesicStringType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'GeodesicStringType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1072, 1)
    _ElementMap = AbstractCurveSegmentType._ElementMap.copy()
    _AttributeMap = AbstractCurveSegmentType._AttributeMap.copy()
    # Base type is AbstractCurveSegmentType
    
    # Element {http://www.opengis.net/gml/3.2}pos uses Python identifier pos
    __pos = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'pos'), 'pos', '__httpwww_opengis_netgml3_2_GeodesicStringType_httpwww_opengis_netgml3_2pos', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1), )

    
    pos = property(__pos.value, __pos.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}posList uses Python identifier posList
    __posList = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'posList'), 'posList', '__httpwww_opengis_netgml3_2_GeodesicStringType_httpwww_opengis_netgml3_2posList', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 490, 1), )

    
    posList = property(__posList.value, __posList.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}pointProperty uses Python identifier pointProperty
    __pointProperty = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'pointProperty'), 'pointProperty', '__httpwww_opengis_netgml3_2_GeodesicStringType_httpwww_opengis_netgml3_2pointProperty', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1), )

    
    pointProperty = property(__pointProperty.value, __pointProperty.set, None, 'This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.')

    
    # Attribute numDerivativesAtStart inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute numDerivativesAtEnd inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute numDerivativeInterior inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute interpolation uses Python identifier interpolation
    __interpolation = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'interpolation'), 'interpolation', '__httpwww_opengis_netgml3_2_GeodesicStringType_interpolation', _module_typeBindings.CurveInterpolationType, fixed=True, unicode_default='geodesic')
    __interpolation._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1079, 4)
    __interpolation._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1079, 4)
    
    interpolation = property(__interpolation.value, __interpolation.set, None, None)

    _ElementMap.update({
        __pos.name() : __pos,
        __posList.name() : __posList,
        __pointProperty.name() : __pointProperty
    })
    _AttributeMap.update({
        __interpolation.name() : __interpolation
    })
_module_typeBindings.GeodesicStringType = GeodesicStringType
Namespace.addCategoryObject('typeBinding', 'GeodesicStringType', GeodesicStringType)


# Complex type {http://www.opengis.net/gml/3.2}PolygonPatchType with content type ELEMENT_ONLY
class PolygonPatchType (AbstractSurfacePatchType):
    """Complex type {http://www.opengis.net/gml/3.2}PolygonPatchType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'PolygonPatchType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1143, 1)
    _ElementMap = AbstractSurfacePatchType._ElementMap.copy()
    _AttributeMap = AbstractSurfacePatchType._AttributeMap.copy()
    # Base type is AbstractSurfacePatchType
    
    # Element {http://www.opengis.net/gml/3.2}exterior uses Python identifier exterior
    __exterior = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'exterior'), 'exterior', '__httpwww_opengis_netgml3_2_PolygonPatchType_httpwww_opengis_netgml3_2exterior', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 707, 1), )

    
    exterior = property(__exterior.value, __exterior.set, None, 'A boundary of a surface consists of a number of rings. In the normal 2D\n\t\t\t\tcase, one of these rings is distinguished as being the exterior boundary. In a\n\t\t\t\tgeneral manifold this is not always possible, in which case all boundaries shall be\n\t\t\t\tlisted as interior boundaries, and the exterior will be empty.')

    
    # Element {http://www.opengis.net/gml/3.2}interior uses Python identifier interior
    __interior = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'interior'), 'interior', '__httpwww_opengis_netgml3_2_PolygonPatchType_httpwww_opengis_netgml3_2interior', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 715, 1), )

    
    interior = property(__interior.value, __interior.set, None, 'A boundary of a surface consists of a number of rings. The "interior"\n\t\t\t\trings separate the surface / surface patch from the area enclosed by the\n\t\t\trings.')

    
    # Attribute interpolation uses Python identifier interpolation
    __interpolation = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'interpolation'), 'interpolation', '__httpwww_opengis_netgml3_2_PolygonPatchType_interpolation', _module_typeBindings.SurfaceInterpolationType, fixed=True, unicode_default='planar')
    __interpolation._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1150, 4)
    __interpolation._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1150, 4)
    
    interpolation = property(__interpolation.value, __interpolation.set, None, None)

    _ElementMap.update({
        __exterior.name() : __exterior,
        __interior.name() : __interior
    })
    _AttributeMap.update({
        __interpolation.name() : __interpolation
    })
_module_typeBindings.PolygonPatchType = PolygonPatchType
Namespace.addCategoryObject('typeBinding', 'PolygonPatchType', PolygonPatchType)


# Complex type {http://www.opengis.net/gml/3.2}RingType with content type ELEMENT_ONLY
class RingType (AbstractRingType):
    """Complex type {http://www.opengis.net/gml/3.2}RingType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'RingType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1183, 1)
    _ElementMap = AbstractRingType._ElementMap.copy()
    _AttributeMap = AbstractRingType._AttributeMap.copy()
    # Base type is AbstractRingType
    
    # Element {http://www.opengis.net/gml/3.2}curveMember uses Python identifier curveMember
    __curveMember = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'curveMember'), 'curveMember', '__httpwww_opengis_netgml3_2_RingType_httpwww_opengis_netgml3_2curveMember', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1193, 1), )

    
    curveMember = property(__curveMember.value, __curveMember.set, None, None)

    
    # Attribute aggregationType uses Python identifier aggregationType
    __aggregationType = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'aggregationType'), 'aggregationType', '__httpwww_opengis_netgml3_2_RingType_aggregationType', _module_typeBindings.AggregationType)
    __aggregationType._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 309, 2)
    __aggregationType._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 309, 2)
    
    aggregationType = property(__aggregationType.value, __aggregationType.set, None, None)

    _ElementMap.update({
        __curveMember.name() : __curveMember
    })
    _AttributeMap.update({
        __aggregationType.name() : __aggregationType
    })
_module_typeBindings.RingType = RingType
Namespace.addCategoryObject('typeBinding', 'RingType', RingType)


# Complex type {http://www.opengis.net/gml/3.2}CodeWithAuthorityType with content type SIMPLE
class CodeWithAuthorityType (CodeType):
    """gml:CodeWithAuthorityType requires that the codeSpace attribute is
				provided in an instance."""
    _TypeDefinition = STD_ANON_2
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_SIMPLE
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'CodeWithAuthorityType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1358, 1)
    _ElementMap = CodeType._ElementMap.copy()
    _AttributeMap = CodeType._AttributeMap.copy()
    # Base type is CodeType
    
    # Attribute codeSpace is restricted from parent
    
    # Attribute codeSpace uses Python identifier codeSpace
    __codeSpace = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'codeSpace'), 'codeSpace', '__httpwww_opengis_netgml3_2_CodeType_codeSpace', pyxb.binding.datatypes.anyURI, required=True)
    __codeSpace._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1365, 4)
    __codeSpace._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1365, 4)
    
    codeSpace = property(__codeSpace.value, __codeSpace.set, None, None)

    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __codeSpace.name() : __codeSpace
    })
_module_typeBindings.CodeWithAuthorityType = CodeWithAuthorityType
Namespace.addCategoryObject('typeBinding', 'CodeWithAuthorityType', CodeWithAuthorityType)


# Complex type {http://www.opengis.net/gml/3.2}AssociationRoleType with content type ELEMENT_ONLY
class AssociationRoleType (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://www.opengis.net/gml/3.2}AssociationRoleType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AssociationRoleType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 207, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Attribute nilReason uses Python identifier nilReason
    __nilReason = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'nilReason'), 'nilReason', '__httpwww_opengis_netgml3_2_AssociationRoleType_nilReason', _module_typeBindings.NilReasonType)
    __nilReason._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    __nilReason._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    
    nilReason = property(__nilReason.value, __nilReason.set, None, None)

    
    # Attribute owns uses Python identifier owns
    __owns = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'owns'), 'owns', '__httpwww_opengis_netgml3_2_AssociationRoleType_owns', pyxb.binding.datatypes.boolean, unicode_default='false')
    __owns._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    __owns._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    
    owns = property(__owns.value, __owns.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'type'), 'type', '__httpwww_opengis_netgml3_2_AssociationRoleType_httpwww_w3_org1999xlinktype', _ImportedBinding__xlink.typeType, fixed=True, unicode_default='simple')
    __type._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 52, 1)
    __type._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 135, 2)
    
    type = property(__type.value, __type.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}href uses Python identifier href
    __href = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'href'), 'href', '__httpwww_opengis_netgml3_2_AssociationRoleType_httpwww_w3_org1999xlinkhref', _ImportedBinding__xlink.hrefType)
    __href._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 65, 1)
    __href._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 136, 2)
    
    href = property(__href.value, __href.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}role uses Python identifier role
    __role = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'role'), 'role', '__httpwww_opengis_netgml3_2_AssociationRoleType_httpwww_w3_org1999xlinkrole', _ImportedBinding__xlink.roleType)
    __role._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 71, 1)
    __role._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 137, 2)
    
    role = property(__role.value, __role.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}arcrole uses Python identifier arcrole
    __arcrole = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'arcrole'), 'arcrole', '__httpwww_opengis_netgml3_2_AssociationRoleType_httpwww_w3_org1999xlinkarcrole', _ImportedBinding__xlink.arcroleType)
    __arcrole._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 79, 1)
    __arcrole._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 138, 2)
    
    arcrole = property(__arcrole.value, __arcrole.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'title'), 'title', '__httpwww_opengis_netgml3_2_AssociationRoleType_httpwww_w3_org1999xlinktitle', _ImportedBinding__xlink.titleAttrType)
    __title._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 87, 1)
    __title._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 139, 2)
    
    title = property(__title.value, __title.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}show uses Python identifier show
    __show = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'show'), 'show', '__httpwww_opengis_netgml3_2_AssociationRoleType_httpwww_w3_org1999xlinkshow', _ImportedBinding__xlink.showType)
    __show._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 93, 1)
    __show._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 140, 2)
    
    show = property(__show.value, __show.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}actuate uses Python identifier actuate
    __actuate = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'actuate'), 'actuate', '__httpwww_opengis_netgml3_2_AssociationRoleType_httpwww_w3_org1999xlinkactuate', _ImportedBinding__xlink.actuateType)
    __actuate._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 105, 1)
    __actuate._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 141, 2)
    
    actuate = property(__actuate.value, __actuate.set, None, None)

    _HasWildcardElement = True
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __nilReason.name() : __nilReason,
        __owns.name() : __owns,
        __type.name() : __type,
        __href.name() : __href,
        __role.name() : __role,
        __arcrole.name() : __arcrole,
        __title.name() : __title,
        __show.name() : __show,
        __actuate.name() : __actuate
    })
_module_typeBindings.AssociationRoleType = AssociationRoleType
Namespace.addCategoryObject('typeBinding', 'AssociationRoleType', AssociationRoleType)


# Complex type {http://www.opengis.net/gml/3.2}ReferenceType with content type EMPTY
class ReferenceType (pyxb.binding.basis.complexTypeDefinition):
    """gml:ReferenceType is intended to be used in application schemas directly,
				if a property element shall use a "by-reference only" encoding."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_EMPTY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'ReferenceType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 243, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Attribute nilReason uses Python identifier nilReason
    __nilReason = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'nilReason'), 'nilReason', '__httpwww_opengis_netgml3_2_ReferenceType_nilReason', _module_typeBindings.NilReasonType)
    __nilReason._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    __nilReason._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    
    nilReason = property(__nilReason.value, __nilReason.set, None, None)

    
    # Attribute owns uses Python identifier owns
    __owns = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'owns'), 'owns', '__httpwww_opengis_netgml3_2_ReferenceType_owns', pyxb.binding.datatypes.boolean, unicode_default='false')
    __owns._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    __owns._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    
    owns = property(__owns.value, __owns.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'type'), 'type', '__httpwww_opengis_netgml3_2_ReferenceType_httpwww_w3_org1999xlinktype', _ImportedBinding__xlink.typeType, fixed=True, unicode_default='simple')
    __type._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 52, 1)
    __type._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 135, 2)
    
    type = property(__type.value, __type.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}href uses Python identifier href
    __href = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'href'), 'href', '__httpwww_opengis_netgml3_2_ReferenceType_httpwww_w3_org1999xlinkhref', _ImportedBinding__xlink.hrefType)
    __href._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 65, 1)
    __href._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 136, 2)
    
    href = property(__href.value, __href.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}role uses Python identifier role
    __role = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'role'), 'role', '__httpwww_opengis_netgml3_2_ReferenceType_httpwww_w3_org1999xlinkrole', _ImportedBinding__xlink.roleType)
    __role._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 71, 1)
    __role._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 137, 2)
    
    role = property(__role.value, __role.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}arcrole uses Python identifier arcrole
    __arcrole = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'arcrole'), 'arcrole', '__httpwww_opengis_netgml3_2_ReferenceType_httpwww_w3_org1999xlinkarcrole', _ImportedBinding__xlink.arcroleType)
    __arcrole._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 79, 1)
    __arcrole._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 138, 2)
    
    arcrole = property(__arcrole.value, __arcrole.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'title'), 'title', '__httpwww_opengis_netgml3_2_ReferenceType_httpwww_w3_org1999xlinktitle', _ImportedBinding__xlink.titleAttrType)
    __title._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 87, 1)
    __title._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 139, 2)
    
    title = property(__title.value, __title.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}show uses Python identifier show
    __show = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'show'), 'show', '__httpwww_opengis_netgml3_2_ReferenceType_httpwww_w3_org1999xlinkshow', _ImportedBinding__xlink.showType)
    __show._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 93, 1)
    __show._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 140, 2)
    
    show = property(__show.value, __show.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}actuate uses Python identifier actuate
    __actuate = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'actuate'), 'actuate', '__httpwww_opengis_netgml3_2_ReferenceType_httpwww_w3_org1999xlinkactuate', _ImportedBinding__xlink.actuateType)
    __actuate._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 105, 1)
    __actuate._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 141, 2)
    
    actuate = property(__actuate.value, __actuate.set, None, None)

    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __nilReason.name() : __nilReason,
        __owns.name() : __owns,
        __type.name() : __type,
        __href.name() : __href,
        __role.name() : __role,
        __arcrole.name() : __arcrole,
        __title.name() : __title,
        __show.name() : __show,
        __actuate.name() : __actuate
    })
_module_typeBindings.ReferenceType = ReferenceType
Namespace.addCategoryObject('typeBinding', 'ReferenceType', ReferenceType)


# Complex type {http://www.opengis.net/gml/3.2}FeaturePropertyType with content type ELEMENT_ONLY
class FeaturePropertyType (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://www.opengis.net/gml/3.2}FeaturePropertyType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'FeaturePropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 375, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.opengis.net/gml/3.2}AbstractFeature uses Python identifier AbstractFeature
    __AbstractFeature = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'AbstractFeature'), 'AbstractFeature', '__httpwww_opengis_netgml3_2_FeaturePropertyType_httpwww_opengis_netgml3_2AbstractFeature', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 345, 1), )

    
    AbstractFeature = property(__AbstractFeature.value, __AbstractFeature.set, None, 'This abstract element serves as the head of a substitution group which\n\t\t\t\tmay contain any elements whose content model is derived from\n\t\t\t\tgml:AbstractFeatureType. This may be used as a variable in the construction of\n\t\t\t\tcontent models. gml:AbstractFeature may be thought of as "anything that is a GML\n\t\t\t\tfeature" and may be used to define variables or templates in which the value of a\n\t\t\t\tGML property is "any feature". This occurs in particular in a GML feature collection\n\t\t\t\twhere the feature member properties contain one or multiple copies of\n\t\t\t\tgml:AbstractFeature respectively.')

    
    # Attribute nilReason uses Python identifier nilReason
    __nilReason = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'nilReason'), 'nilReason', '__httpwww_opengis_netgml3_2_FeaturePropertyType_nilReason', _module_typeBindings.NilReasonType)
    __nilReason._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    __nilReason._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    
    nilReason = property(__nilReason.value, __nilReason.set, None, None)

    
    # Attribute owns uses Python identifier owns
    __owns = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'owns'), 'owns', '__httpwww_opengis_netgml3_2_FeaturePropertyType_owns', pyxb.binding.datatypes.boolean, unicode_default='false')
    __owns._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    __owns._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    
    owns = property(__owns.value, __owns.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'type'), 'type', '__httpwww_opengis_netgml3_2_FeaturePropertyType_httpwww_w3_org1999xlinktype', _ImportedBinding__xlink.typeType, fixed=True, unicode_default='simple')
    __type._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 52, 1)
    __type._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 135, 2)
    
    type = property(__type.value, __type.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}href uses Python identifier href
    __href = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'href'), 'href', '__httpwww_opengis_netgml3_2_FeaturePropertyType_httpwww_w3_org1999xlinkhref', _ImportedBinding__xlink.hrefType)
    __href._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 65, 1)
    __href._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 136, 2)
    
    href = property(__href.value, __href.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}role uses Python identifier role
    __role = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'role'), 'role', '__httpwww_opengis_netgml3_2_FeaturePropertyType_httpwww_w3_org1999xlinkrole', _ImportedBinding__xlink.roleType)
    __role._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 71, 1)
    __role._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 137, 2)
    
    role = property(__role.value, __role.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}arcrole uses Python identifier arcrole
    __arcrole = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'arcrole'), 'arcrole', '__httpwww_opengis_netgml3_2_FeaturePropertyType_httpwww_w3_org1999xlinkarcrole', _ImportedBinding__xlink.arcroleType)
    __arcrole._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 79, 1)
    __arcrole._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 138, 2)
    
    arcrole = property(__arcrole.value, __arcrole.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'title'), 'title', '__httpwww_opengis_netgml3_2_FeaturePropertyType_httpwww_w3_org1999xlinktitle', _ImportedBinding__xlink.titleAttrType)
    __title._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 87, 1)
    __title._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 139, 2)
    
    title = property(__title.value, __title.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}show uses Python identifier show
    __show = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'show'), 'show', '__httpwww_opengis_netgml3_2_FeaturePropertyType_httpwww_w3_org1999xlinkshow', _ImportedBinding__xlink.showType)
    __show._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 93, 1)
    __show._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 140, 2)
    
    show = property(__show.value, __show.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}actuate uses Python identifier actuate
    __actuate = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'actuate'), 'actuate', '__httpwww_opengis_netgml3_2_FeaturePropertyType_httpwww_w3_org1999xlinkactuate', _ImportedBinding__xlink.actuateType)
    __actuate._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 105, 1)
    __actuate._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 141, 2)
    
    actuate = property(__actuate.value, __actuate.set, None, None)

    _ElementMap.update({
        __AbstractFeature.name() : __AbstractFeature
    })
    _AttributeMap.update({
        __nilReason.name() : __nilReason,
        __owns.name() : __owns,
        __type.name() : __type,
        __href.name() : __href,
        __role.name() : __role,
        __arcrole.name() : __arcrole,
        __title.name() : __title,
        __show.name() : __show,
        __actuate.name() : __actuate
    })
_module_typeBindings.FeaturePropertyType = FeaturePropertyType
Namespace.addCategoryObject('typeBinding', 'FeaturePropertyType', FeaturePropertyType)


# Complex type {http://www.opengis.net/gml/3.2}BoundingShapeType with content type ELEMENT_ONLY
class BoundingShapeType (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://www.opengis.net/gml/3.2}BoundingShapeType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'BoundingShapeType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 388, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.opengis.net/gml/3.2}Envelope uses Python identifier Envelope
    __Envelope = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'Envelope'), 'Envelope', '__httpwww_opengis_netgml3_2_BoundingShapeType_httpwww_opengis_netgml3_2Envelope', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 411, 1), )

    
    Envelope = property(__Envelope.value, __Envelope.set, None, 'Envelope defines an extent using a pair of positions defining opposite\n\t\t\t\tcorners in arbitrary dimensions. The first direct position is the "lower corner" (a\n\t\t\t\tcoordinate position consisting of all the minimal ordinates for each dimension for\n\t\t\t\tall points within the envelope), the second one the "upper corner" (a coordinate\n\t\t\t\tposition consisting of all the maximal ordinates for each dimension for all points\n\t\t\t\twithin the envelope). The use of the properties "coordinates" and "pos" has been\n\t\t\t\tdeprecated. The explicitly named properties "lowerCorner" and "upperCorner" shall be\n\t\t\t\tused instead.')

    
    # Attribute nilReason uses Python identifier nilReason
    __nilReason = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'nilReason'), 'nilReason', '__httpwww_opengis_netgml3_2_BoundingShapeType_nilReason', _module_typeBindings.NilReasonType)
    __nilReason._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 394, 2)
    __nilReason._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 394, 2)
    
    nilReason = property(__nilReason.value, __nilReason.set, None, None)

    _ElementMap.update({
        __Envelope.name() : __Envelope
    })
    _AttributeMap.update({
        __nilReason.name() : __nilReason
    })
_module_typeBindings.BoundingShapeType = BoundingShapeType
Namespace.addCategoryObject('typeBinding', 'BoundingShapeType', BoundingShapeType)


# Complex type {http://www.opengis.net/gml/3.2}AbstractGeometricPrimitiveType with content type EMPTY
class AbstractGeometricPrimitiveType (AbstractGeometryType):
    """gml:AbstractGeometricPrimitiveType is the abstract root type of the
				geometric primitives. A geometric primitive is a geometric object that is not
				decomposed further into other primitives in the system. All primitives are oriented
				in the direction implied by the sequence of their coordinate tuples."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_EMPTY
    _Abstract = True
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractGeometricPrimitiveType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 518, 1)
    _ElementMap = AbstractGeometryType._ElementMap.copy()
    _AttributeMap = AbstractGeometryType._AttributeMap.copy()
    # Base type is AbstractGeometryType
    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.AbstractGeometricPrimitiveType = AbstractGeometricPrimitiveType
Namespace.addCategoryObject('typeBinding', 'AbstractGeometricPrimitiveType', AbstractGeometricPrimitiveType)


# Complex type {http://www.opengis.net/gml/3.2}GeometricPrimitivePropertyType with content type ELEMENT_ONLY
class GeometricPrimitivePropertyType (pyxb.binding.basis.complexTypeDefinition):
    """A property that has a geometric primitive as its value domain may either
				be an appropriate geometry element encapsulated in an element of this type or an
				XLink reference to a remote geometry element (where remote includes geometry
				elements located elsewhere in the same document). Either the reference or the
				contained element shall be given, but neither both nor none."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'GeometricPrimitivePropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 529, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.opengis.net/gml/3.2}AbstractGeometricPrimitive uses Python identifier AbstractGeometricPrimitive
    __AbstractGeometricPrimitive = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'AbstractGeometricPrimitive'), 'AbstractGeometricPrimitive', '__httpwww_opengis_netgml3_2_GeometricPrimitivePropertyType_httpwww_opengis_netgml3_2AbstractGeometricPrimitive', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 511, 1), )

    
    AbstractGeometricPrimitive = property(__AbstractGeometricPrimitive.value, __AbstractGeometricPrimitive.set, None, 'The AbstractGeometricPrimitive element is the abstract head of the\n\t\t\t\tsubstitution group for all (pre- and user-defined) geometric\n\t\t\tprimitives.')

    
    # Attribute nilReason uses Python identifier nilReason
    __nilReason = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'nilReason'), 'nilReason', '__httpwww_opengis_netgml3_2_GeometricPrimitivePropertyType_nilReason', _module_typeBindings.NilReasonType)
    __nilReason._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    __nilReason._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    
    nilReason = property(__nilReason.value, __nilReason.set, None, None)

    
    # Attribute owns uses Python identifier owns
    __owns = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'owns'), 'owns', '__httpwww_opengis_netgml3_2_GeometricPrimitivePropertyType_owns', pyxb.binding.datatypes.boolean, unicode_default='false')
    __owns._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    __owns._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    
    owns = property(__owns.value, __owns.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'type'), 'type', '__httpwww_opengis_netgml3_2_GeometricPrimitivePropertyType_httpwww_w3_org1999xlinktype', _ImportedBinding__xlink.typeType, fixed=True, unicode_default='simple')
    __type._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 52, 1)
    __type._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 135, 2)
    
    type = property(__type.value, __type.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}href uses Python identifier href
    __href = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'href'), 'href', '__httpwww_opengis_netgml3_2_GeometricPrimitivePropertyType_httpwww_w3_org1999xlinkhref', _ImportedBinding__xlink.hrefType)
    __href._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 65, 1)
    __href._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 136, 2)
    
    href = property(__href.value, __href.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}role uses Python identifier role
    __role = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'role'), 'role', '__httpwww_opengis_netgml3_2_GeometricPrimitivePropertyType_httpwww_w3_org1999xlinkrole', _ImportedBinding__xlink.roleType)
    __role._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 71, 1)
    __role._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 137, 2)
    
    role = property(__role.value, __role.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}arcrole uses Python identifier arcrole
    __arcrole = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'arcrole'), 'arcrole', '__httpwww_opengis_netgml3_2_GeometricPrimitivePropertyType_httpwww_w3_org1999xlinkarcrole', _ImportedBinding__xlink.arcroleType)
    __arcrole._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 79, 1)
    __arcrole._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 138, 2)
    
    arcrole = property(__arcrole.value, __arcrole.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'title'), 'title', '__httpwww_opengis_netgml3_2_GeometricPrimitivePropertyType_httpwww_w3_org1999xlinktitle', _ImportedBinding__xlink.titleAttrType)
    __title._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 87, 1)
    __title._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 139, 2)
    
    title = property(__title.value, __title.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}show uses Python identifier show
    __show = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'show'), 'show', '__httpwww_opengis_netgml3_2_GeometricPrimitivePropertyType_httpwww_w3_org1999xlinkshow', _ImportedBinding__xlink.showType)
    __show._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 93, 1)
    __show._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 140, 2)
    
    show = property(__show.value, __show.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}actuate uses Python identifier actuate
    __actuate = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'actuate'), 'actuate', '__httpwww_opengis_netgml3_2_GeometricPrimitivePropertyType_httpwww_w3_org1999xlinkactuate', _ImportedBinding__xlink.actuateType)
    __actuate._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 105, 1)
    __actuate._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 141, 2)
    
    actuate = property(__actuate.value, __actuate.set, None, None)

    _ElementMap.update({
        __AbstractGeometricPrimitive.name() : __AbstractGeometricPrimitive
    })
    _AttributeMap.update({
        __nilReason.name() : __nilReason,
        __owns.name() : __owns,
        __type.name() : __type,
        __href.name() : __href,
        __role.name() : __role,
        __arcrole.name() : __arcrole,
        __title.name() : __title,
        __show.name() : __show,
        __actuate.name() : __actuate
    })
_module_typeBindings.GeometricPrimitivePropertyType = GeometricPrimitivePropertyType
Namespace.addCategoryObject('typeBinding', 'GeometricPrimitivePropertyType', GeometricPrimitivePropertyType)


# Complex type {http://www.opengis.net/gml/3.2}PointPropertyType with content type ELEMENT_ONLY
class PointPropertyType (pyxb.binding.basis.complexTypeDefinition):
    """A property that has a point as its value domain may either be an
				appropriate geometry element encapsulated in an element of this type or an XLink
				reference to a remote geometry element (where remote includes geometry elements
				located elsewhere in the same document). Either the reference or the contained
				element shall be given, but neither both nor none."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'PointPropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 579, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.opengis.net/gml/3.2}Point uses Python identifier Point
    __Point = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'Point'), 'Point', '__httpwww_opengis_netgml3_2_PointPropertyType_httpwww_opengis_netgml3_2Point', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 558, 1), )

    
    Point = property(__Point.value, __Point.set, None, 'A Point is defined by a single coordinate tuple. The direct position of a\n\t\t\t\tpoint is specified by the pos element which is of type\n\t\t\tDirectPositionType.')

    
    # Attribute nilReason uses Python identifier nilReason
    __nilReason = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'nilReason'), 'nilReason', '__httpwww_opengis_netgml3_2_PointPropertyType_nilReason', _module_typeBindings.NilReasonType)
    __nilReason._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    __nilReason._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    
    nilReason = property(__nilReason.value, __nilReason.set, None, None)

    
    # Attribute owns uses Python identifier owns
    __owns = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'owns'), 'owns', '__httpwww_opengis_netgml3_2_PointPropertyType_owns', pyxb.binding.datatypes.boolean, unicode_default='false')
    __owns._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    __owns._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    
    owns = property(__owns.value, __owns.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'type'), 'type', '__httpwww_opengis_netgml3_2_PointPropertyType_httpwww_w3_org1999xlinktype', _ImportedBinding__xlink.typeType, fixed=True, unicode_default='simple')
    __type._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 52, 1)
    __type._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 135, 2)
    
    type = property(__type.value, __type.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}href uses Python identifier href
    __href = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'href'), 'href', '__httpwww_opengis_netgml3_2_PointPropertyType_httpwww_w3_org1999xlinkhref', _ImportedBinding__xlink.hrefType)
    __href._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 65, 1)
    __href._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 136, 2)
    
    href = property(__href.value, __href.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}role uses Python identifier role
    __role = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'role'), 'role', '__httpwww_opengis_netgml3_2_PointPropertyType_httpwww_w3_org1999xlinkrole', _ImportedBinding__xlink.roleType)
    __role._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 71, 1)
    __role._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 137, 2)
    
    role = property(__role.value, __role.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}arcrole uses Python identifier arcrole
    __arcrole = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'arcrole'), 'arcrole', '__httpwww_opengis_netgml3_2_PointPropertyType_httpwww_w3_org1999xlinkarcrole', _ImportedBinding__xlink.arcroleType)
    __arcrole._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 79, 1)
    __arcrole._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 138, 2)
    
    arcrole = property(__arcrole.value, __arcrole.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'title'), 'title', '__httpwww_opengis_netgml3_2_PointPropertyType_httpwww_w3_org1999xlinktitle', _ImportedBinding__xlink.titleAttrType)
    __title._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 87, 1)
    __title._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 139, 2)
    
    title = property(__title.value, __title.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}show uses Python identifier show
    __show = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'show'), 'show', '__httpwww_opengis_netgml3_2_PointPropertyType_httpwww_w3_org1999xlinkshow', _ImportedBinding__xlink.showType)
    __show._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 93, 1)
    __show._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 140, 2)
    
    show = property(__show.value, __show.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}actuate uses Python identifier actuate
    __actuate = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'actuate'), 'actuate', '__httpwww_opengis_netgml3_2_PointPropertyType_httpwww_w3_org1999xlinkactuate', _ImportedBinding__xlink.actuateType)
    __actuate._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 105, 1)
    __actuate._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 141, 2)
    
    actuate = property(__actuate.value, __actuate.set, None, None)

    _ElementMap.update({
        __Point.name() : __Point
    })
    _AttributeMap.update({
        __nilReason.name() : __nilReason,
        __owns.name() : __owns,
        __type.name() : __type,
        __href.name() : __href,
        __role.name() : __role,
        __arcrole.name() : __arcrole,
        __title.name() : __title,
        __show.name() : __show,
        __actuate.name() : __actuate
    })
_module_typeBindings.PointPropertyType = PointPropertyType
Namespace.addCategoryObject('typeBinding', 'PointPropertyType', PointPropertyType)


# Complex type {http://www.opengis.net/gml/3.2}CurvePropertyType with content type ELEMENT_ONLY
class CurvePropertyType (pyxb.binding.basis.complexTypeDefinition):
    """A property that has a curve as its value domain may either be an
				appropriate geometry element encapsulated in an element of this type or an XLink
				reference to a remote geometry element (where remote includes geometry elements
				located elsewhere in the same document). Either the reference or the contained
				element shall be given, but neither both nor none."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'CurvePropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 617, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.opengis.net/gml/3.2}AbstractCurve uses Python identifier AbstractCurve
    __AbstractCurve = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'AbstractCurve'), 'AbstractCurve', '__httpwww_opengis_netgml3_2_CurvePropertyType_httpwww_opengis_netgml3_2AbstractCurve', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 601, 1), )

    
    AbstractCurve = property(__AbstractCurve.value, __AbstractCurve.set, None, 'The AbstractCurve element is the abstract head of the substitution group\n\t\t\t\tfor all (continuous) curve elements.')

    
    # Attribute nilReason uses Python identifier nilReason
    __nilReason = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'nilReason'), 'nilReason', '__httpwww_opengis_netgml3_2_CurvePropertyType_nilReason', _module_typeBindings.NilReasonType)
    __nilReason._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    __nilReason._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    
    nilReason = property(__nilReason.value, __nilReason.set, None, None)

    
    # Attribute owns uses Python identifier owns
    __owns = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'owns'), 'owns', '__httpwww_opengis_netgml3_2_CurvePropertyType_owns', pyxb.binding.datatypes.boolean, unicode_default='false')
    __owns._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    __owns._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    
    owns = property(__owns.value, __owns.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'type'), 'type', '__httpwww_opengis_netgml3_2_CurvePropertyType_httpwww_w3_org1999xlinktype', _ImportedBinding__xlink.typeType, fixed=True, unicode_default='simple')
    __type._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 52, 1)
    __type._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 135, 2)
    
    type = property(__type.value, __type.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}href uses Python identifier href
    __href = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'href'), 'href', '__httpwww_opengis_netgml3_2_CurvePropertyType_httpwww_w3_org1999xlinkhref', _ImportedBinding__xlink.hrefType)
    __href._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 65, 1)
    __href._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 136, 2)
    
    href = property(__href.value, __href.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}role uses Python identifier role
    __role = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'role'), 'role', '__httpwww_opengis_netgml3_2_CurvePropertyType_httpwww_w3_org1999xlinkrole', _ImportedBinding__xlink.roleType)
    __role._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 71, 1)
    __role._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 137, 2)
    
    role = property(__role.value, __role.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}arcrole uses Python identifier arcrole
    __arcrole = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'arcrole'), 'arcrole', '__httpwww_opengis_netgml3_2_CurvePropertyType_httpwww_w3_org1999xlinkarcrole', _ImportedBinding__xlink.arcroleType)
    __arcrole._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 79, 1)
    __arcrole._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 138, 2)
    
    arcrole = property(__arcrole.value, __arcrole.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'title'), 'title', '__httpwww_opengis_netgml3_2_CurvePropertyType_httpwww_w3_org1999xlinktitle', _ImportedBinding__xlink.titleAttrType)
    __title._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 87, 1)
    __title._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 139, 2)
    
    title = property(__title.value, __title.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}show uses Python identifier show
    __show = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'show'), 'show', '__httpwww_opengis_netgml3_2_CurvePropertyType_httpwww_w3_org1999xlinkshow', _ImportedBinding__xlink.showType)
    __show._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 93, 1)
    __show._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 140, 2)
    
    show = property(__show.value, __show.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}actuate uses Python identifier actuate
    __actuate = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'actuate'), 'actuate', '__httpwww_opengis_netgml3_2_CurvePropertyType_httpwww_w3_org1999xlinkactuate', _ImportedBinding__xlink.actuateType)
    __actuate._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 105, 1)
    __actuate._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 141, 2)
    
    actuate = property(__actuate.value, __actuate.set, None, None)

    _ElementMap.update({
        __AbstractCurve.name() : __AbstractCurve
    })
    _AttributeMap.update({
        __nilReason.name() : __nilReason,
        __owns.name() : __owns,
        __type.name() : __type,
        __href.name() : __href,
        __role.name() : __role,
        __arcrole.name() : __arcrole,
        __title.name() : __title,
        __show.name() : __show,
        __actuate.name() : __actuate
    })
_module_typeBindings.CurvePropertyType = CurvePropertyType
Namespace.addCategoryObject('typeBinding', 'CurvePropertyType', CurvePropertyType)


# Complex type {http://www.opengis.net/gml/3.2}SurfacePropertyType with content type ELEMENT_ONLY
class SurfacePropertyType (pyxb.binding.basis.complexTypeDefinition):
    """A property that has a surface as its value domain may either be an
				appropriate geometry element encapsulated in an element of this type or an XLink
				reference to a remote geometry element (where remote includes geometry elements
				located elsewhere in the same document). Either the reference or the contained
				element shall be given, but neither both nor none."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'SurfacePropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 675, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.opengis.net/gml/3.2}AbstractSurface uses Python identifier AbstractSurface
    __AbstractSurface = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'AbstractSurface'), 'AbstractSurface', '__httpwww_opengis_netgml3_2_SurfacePropertyType_httpwww_opengis_netgml3_2AbstractSurface', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 659, 1), )

    
    AbstractSurface = property(__AbstractSurface.value, __AbstractSurface.set, None, 'The AbstractSurface element is the abstract head of the substitution\n\t\t\t\tgroup for all (continuous) surface elements.')

    
    # Attribute nilReason uses Python identifier nilReason
    __nilReason = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'nilReason'), 'nilReason', '__httpwww_opengis_netgml3_2_SurfacePropertyType_nilReason', _module_typeBindings.NilReasonType)
    __nilReason._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    __nilReason._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    
    nilReason = property(__nilReason.value, __nilReason.set, None, None)

    
    # Attribute owns uses Python identifier owns
    __owns = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'owns'), 'owns', '__httpwww_opengis_netgml3_2_SurfacePropertyType_owns', pyxb.binding.datatypes.boolean, unicode_default='false')
    __owns._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    __owns._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 226, 2)
    
    owns = property(__owns.value, __owns.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'type'), 'type', '__httpwww_opengis_netgml3_2_SurfacePropertyType_httpwww_w3_org1999xlinktype', _ImportedBinding__xlink.typeType, fixed=True, unicode_default='simple')
    __type._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 52, 1)
    __type._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 135, 2)
    
    type = property(__type.value, __type.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}href uses Python identifier href
    __href = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'href'), 'href', '__httpwww_opengis_netgml3_2_SurfacePropertyType_httpwww_w3_org1999xlinkhref', _ImportedBinding__xlink.hrefType)
    __href._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 65, 1)
    __href._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 136, 2)
    
    href = property(__href.value, __href.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}role uses Python identifier role
    __role = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'role'), 'role', '__httpwww_opengis_netgml3_2_SurfacePropertyType_httpwww_w3_org1999xlinkrole', _ImportedBinding__xlink.roleType)
    __role._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 71, 1)
    __role._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 137, 2)
    
    role = property(__role.value, __role.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}arcrole uses Python identifier arcrole
    __arcrole = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'arcrole'), 'arcrole', '__httpwww_opengis_netgml3_2_SurfacePropertyType_httpwww_w3_org1999xlinkarcrole', _ImportedBinding__xlink.arcroleType)
    __arcrole._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 79, 1)
    __arcrole._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 138, 2)
    
    arcrole = property(__arcrole.value, __arcrole.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'title'), 'title', '__httpwww_opengis_netgml3_2_SurfacePropertyType_httpwww_w3_org1999xlinktitle', _ImportedBinding__xlink.titleAttrType)
    __title._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 87, 1)
    __title._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 139, 2)
    
    title = property(__title.value, __title.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}show uses Python identifier show
    __show = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'show'), 'show', '__httpwww_opengis_netgml3_2_SurfacePropertyType_httpwww_w3_org1999xlinkshow', _ImportedBinding__xlink.showType)
    __show._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 93, 1)
    __show._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 140, 2)
    
    show = property(__show.value, __show.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}actuate uses Python identifier actuate
    __actuate = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'actuate'), 'actuate', '__httpwww_opengis_netgml3_2_SurfacePropertyType_httpwww_w3_org1999xlinkactuate', _ImportedBinding__xlink.actuateType)
    __actuate._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 105, 1)
    __actuate._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 141, 2)
    
    actuate = property(__actuate.value, __actuate.set, None, None)

    _ElementMap.update({
        __AbstractSurface.name() : __AbstractSurface
    })
    _AttributeMap.update({
        __nilReason.name() : __nilReason,
        __owns.name() : __owns,
        __type.name() : __type,
        __href.name() : __href,
        __role.name() : __role,
        __arcrole.name() : __arcrole,
        __title.name() : __title,
        __show.name() : __show,
        __actuate.name() : __actuate
    })
_module_typeBindings.SurfacePropertyType = SurfacePropertyType
Namespace.addCategoryObject('typeBinding', 'SurfacePropertyType', SurfacePropertyType)


# Complex type {http://www.opengis.net/gml/3.2}GeodesicType with content type ELEMENT_ONLY
class GeodesicType (GeodesicStringType):
    """Complex type {http://www.opengis.net/gml/3.2}GeodesicType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'GeodesicType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1084, 1)
    _ElementMap = GeodesicStringType._ElementMap.copy()
    _AttributeMap = GeodesicStringType._AttributeMap.copy()
    # Base type is GeodesicStringType
    
    # Element pos ({http://www.opengis.net/gml/3.2}pos) inherited from {http://www.opengis.net/gml/3.2}GeodesicStringType
    
    # Element posList ({http://www.opengis.net/gml/3.2}posList) inherited from {http://www.opengis.net/gml/3.2}GeodesicStringType
    
    # Element pointProperty ({http://www.opengis.net/gml/3.2}pointProperty) inherited from {http://www.opengis.net/gml/3.2}GeodesicStringType
    
    # Attribute numDerivativesAtStart inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute numDerivativesAtEnd inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute numDerivativeInterior inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute interpolation inherited from {http://www.opengis.net/gml/3.2}GeodesicStringType
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.GeodesicType = GeodesicType
Namespace.addCategoryObject('typeBinding', 'GeodesicType', GeodesicType)


# Complex type {http://www.opengis.net/gml/3.2}AbstractGeometricAggregateType with content type EMPTY
class AbstractGeometricAggregateType (AbstractGeometryType):
    """Complex type {http://www.opengis.net/gml/3.2}AbstractGeometricAggregateType with content type EMPTY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_EMPTY
    _Abstract = True
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractGeometricAggregateType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1226, 1)
    _ElementMap = AbstractGeometryType._ElementMap.copy()
    _AttributeMap = AbstractGeometryType._AttributeMap.copy()
    # Base type is AbstractGeometryType
    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute aggregationType uses Python identifier aggregationType
    __aggregationType = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'aggregationType'), 'aggregationType', '__httpwww_opengis_netgml3_2_AbstractGeometricAggregateType_aggregationType', _module_typeBindings.AggregationType)
    __aggregationType._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 309, 2)
    __aggregationType._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 309, 2)
    
    aggregationType = property(__aggregationType.value, __aggregationType.set, None, None)

    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __aggregationType.name() : __aggregationType
    })
_module_typeBindings.AbstractGeometricAggregateType = AbstractGeometricAggregateType
Namespace.addCategoryObject('typeBinding', 'AbstractGeometricAggregateType', AbstractGeometricAggregateType)


# Complex type {http://www.opengis.net/gml/3.2}MeasureType with content type SIMPLE
class MeasureType (pyxb.binding.basis.complexTypeDefinition):
    """gml:MeasureType supports recording an amount encoded as a value of XML
				Schema double, together with a units of measure indicated by an attribute uom, short
				for "units Of measure". The value of the uom attribute identifies a reference system
				for the amount, usually a ratio or interval scale."""
    _TypeDefinition = pyxb.binding.datatypes.double
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_SIMPLE
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'MeasureType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1369, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.double
    
    # Attribute uom uses Python identifier uom
    __uom = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'uom'), 'uom', '__httpwww_opengis_netgml3_2_MeasureType_uom', _module_typeBindings.UomIdentifier, required=True)
    __uom._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1378, 4)
    __uom._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1378, 4)
    
    uom = property(__uom.value, __uom.set, None, None)

    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __uom.name() : __uom
    })
_module_typeBindings.MeasureType = MeasureType
Namespace.addCategoryObject('typeBinding', 'MeasureType', MeasureType)


# Complex type [anonymous] with content type SIMPLE
class CTD_ANON (pyxb.binding.basis.complexTypeDefinition):
    """Complex type [anonymous] with content type SIMPLE"""
    _TypeDefinition = pyxb.binding.datatypes.boolean
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_SIMPLE
    _Abstract = False
    _ExpandedName = None
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1453, 2)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.boolean
    
    # Attribute nilReason uses Python identifier nilReason
    __nilReason = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'nilReason'), 'nilReason', '__httpwww_opengis_netgml3_2_CTD_ANON_nilReason', _module_typeBindings.NilReasonType)
    __nilReason._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1456, 5)
    __nilReason._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1456, 5)
    
    nilReason = property(__nilReason.value, __nilReason.set, None, None)

    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __nilReason.name() : __nilReason
    })
_module_typeBindings.CTD_ANON = CTD_ANON


# Complex type {http://www.opengis.net/gml/3.2}PointType with content type ELEMENT_ONLY
class PointType (AbstractGeometricPrimitiveType):
    """S-100 XML supports two different ways to specify the direct positon of a
				point. 1. The "pos" element is of type DirectPositionType."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'PointType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 565, 1)
    _ElementMap = AbstractGeometricPrimitiveType._ElementMap.copy()
    _AttributeMap = AbstractGeometricPrimitiveType._AttributeMap.copy()
    # Base type is AbstractGeometricPrimitiveType
    
    # Element {http://www.opengis.net/gml/3.2}pos uses Python identifier pos
    __pos = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'pos'), 'pos', '__httpwww_opengis_netgml3_2_PointType_httpwww_opengis_netgml3_2pos', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1), )

    
    pos = property(__pos.value, __pos.set, None, None)

    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        __pos.name() : __pos
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.PointType = PointType
Namespace.addCategoryObject('typeBinding', 'PointType', PointType)


# Complex type {http://www.opengis.net/gml/3.2}AbstractCurveType with content type EMPTY
class AbstractCurveType (AbstractGeometricPrimitiveType):
    """gml:AbstractCurveType is an abstraction of a curve to support the
				different levels of complexity. The curve may always be viewed as a geometric
				primitive, i.e. is continuous."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_EMPTY
    _Abstract = True
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractCurveType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 607, 1)
    _ElementMap = AbstractGeometricPrimitiveType._ElementMap.copy()
    _AttributeMap = AbstractGeometricPrimitiveType._AttributeMap.copy()
    # Base type is AbstractGeometricPrimitiveType
    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.AbstractCurveType = AbstractCurveType
Namespace.addCategoryObject('typeBinding', 'AbstractCurveType', AbstractCurveType)


# Complex type {http://www.opengis.net/gml/3.2}AbstractSurfaceType with content type EMPTY
class AbstractSurfaceType (AbstractGeometricPrimitiveType):
    """gml:AbstractSurfaceType is an abstraction of a surface to support the
				different levels of complexity. A surface is always a continuous region of a
			plane."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_EMPTY
    _Abstract = True
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractSurfaceType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 665, 1)
    _ElementMap = AbstractGeometricPrimitiveType._ElementMap.copy()
    _AttributeMap = AbstractGeometricPrimitiveType._AttributeMap.copy()
    # Base type is AbstractGeometricPrimitiveType
    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.AbstractSurfaceType = AbstractSurfaceType
Namespace.addCategoryObject('typeBinding', 'AbstractSurfaceType', AbstractSurfaceType)


# Complex type {http://www.opengis.net/gml/3.2}MultiPointType with content type ELEMENT_ONLY
class MultiPointType (AbstractGeometricAggregateType):
    """Complex type {http://www.opengis.net/gml/3.2}MultiPointType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'MultiPointType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1241, 1)
    _ElementMap = AbstractGeometricAggregateType._ElementMap.copy()
    _AttributeMap = AbstractGeometricAggregateType._AttributeMap.copy()
    # Base type is AbstractGeometricAggregateType
    
    # Element {http://www.opengis.net/gml/3.2}pointMember uses Python identifier pointMember
    __pointMember = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'pointMember'), 'pointMember', '__httpwww_opengis_netgml3_2_MultiPointType_httpwww_opengis_netgml3_2pointMember', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1250, 1), )

    
    pointMember = property(__pointMember.value, __pointMember.set, None, 'This property element either references a Point via the XLink-attributes\n\t\t\t\tor contains the Point element.')

    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute aggregationType inherited from {http://www.opengis.net/gml/3.2}AbstractGeometricAggregateType
    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        __pointMember.name() : __pointMember
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.MultiPointType = MultiPointType
Namespace.addCategoryObject('typeBinding', 'MultiPointType', MultiPointType)


# Complex type {http://www.opengis.net/gml/3.2}LengthType with content type SIMPLE
class LengthType (MeasureType):
    """This is a prototypical definition for a specific measure type defined as
				a vacuous extension (i.e. aliases) of gml:MeasureType. In this case, the content
				model supports the description of a length (or distance) quantity, with its units.
				The unit of measure referenced by uom shall be suitable for a length, such as metres
				or feet."""
    _TypeDefinition = pyxb.binding.datatypes.double
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_SIMPLE
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'LengthType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1469, 1)
    _ElementMap = MeasureType._ElementMap.copy()
    _AttributeMap = MeasureType._AttributeMap.copy()
    # Base type is MeasureType
    
    # Attribute uom inherited from {http://www.opengis.net/gml/3.2}MeasureType
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.LengthType = LengthType
Namespace.addCategoryObject('typeBinding', 'LengthType', LengthType)


# Complex type {http://www.opengis.net/gml/3.2}AngleType with content type SIMPLE
class AngleType (MeasureType):
    """Complex type {http://www.opengis.net/gml/3.2}AngleType with content type SIMPLE"""
    _TypeDefinition = pyxb.binding.datatypes.double
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_SIMPLE
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AngleType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1487, 1)
    _ElementMap = MeasureType._ElementMap.copy()
    _AttributeMap = MeasureType._AttributeMap.copy()
    # Base type is MeasureType
    
    # Attribute uom inherited from {http://www.opengis.net/gml/3.2}MeasureType
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.AngleType = AngleType
Namespace.addCategoryObject('typeBinding', 'AngleType', AngleType)


# Complex type {http://www.opengis.net/gml/3.2}VolumeType with content type SIMPLE
class VolumeType (MeasureType):
    """Complex type {http://www.opengis.net/gml/3.2}VolumeType with content type SIMPLE"""
    _TypeDefinition = pyxb.binding.datatypes.double
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_SIMPLE
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'VolumeType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1492, 1)
    _ElementMap = MeasureType._ElementMap.copy()
    _AttributeMap = MeasureType._AttributeMap.copy()
    # Base type is MeasureType
    
    # Attribute uom inherited from {http://www.opengis.net/gml/3.2}MeasureType
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.VolumeType = VolumeType
Namespace.addCategoryObject('typeBinding', 'VolumeType', VolumeType)


# Complex type {http://www.opengis.net/gml/3.2}LineStringType with content type ELEMENT_ONLY
class LineStringType (AbstractCurveType):
    """Complex type {http://www.opengis.net/gml/3.2}LineStringType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'LineStringType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 639, 1)
    _ElementMap = AbstractCurveType._ElementMap.copy()
    _AttributeMap = AbstractCurveType._AttributeMap.copy()
    # Base type is AbstractCurveType
    
    # Element {http://www.opengis.net/gml/3.2}pos uses Python identifier pos
    __pos = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'pos'), 'pos', '__httpwww_opengis_netgml3_2_LineStringType_httpwww_opengis_netgml3_2pos', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1), )

    
    pos = property(__pos.value, __pos.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}posList uses Python identifier posList
    __posList = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'posList'), 'posList', '__httpwww_opengis_netgml3_2_LineStringType_httpwww_opengis_netgml3_2posList', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 490, 1), )

    
    posList = property(__posList.value, __posList.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}pointProperty uses Python identifier pointProperty
    __pointProperty = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'pointProperty'), 'pointProperty', '__httpwww_opengis_netgml3_2_LineStringType_httpwww_opengis_netgml3_2pointProperty', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1), )

    
    pointProperty = property(__pointProperty.value, __pointProperty.set, None, 'This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.')

    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        __pos.name() : __pos,
        __posList.name() : __posList,
        __pointProperty.name() : __pointProperty
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.LineStringType = LineStringType
Namespace.addCategoryObject('typeBinding', 'LineStringType', LineStringType)


# Complex type {http://www.opengis.net/gml/3.2}PolygonType with content type ELEMENT_ONLY
class PolygonType (AbstractSurfaceType):
    """Complex type {http://www.opengis.net/gml/3.2}PolygonType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'PolygonType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 697, 1)
    _ElementMap = AbstractSurfaceType._ElementMap.copy()
    _AttributeMap = AbstractSurfaceType._AttributeMap.copy()
    # Base type is AbstractSurfaceType
    
    # Element {http://www.opengis.net/gml/3.2}exterior uses Python identifier exterior
    __exterior = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'exterior'), 'exterior', '__httpwww_opengis_netgml3_2_PolygonType_httpwww_opengis_netgml3_2exterior', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 707, 1), )

    
    exterior = property(__exterior.value, __exterior.set, None, 'A boundary of a surface consists of a number of rings. In the normal 2D\n\t\t\t\tcase, one of these rings is distinguished as being the exterior boundary. In a\n\t\t\t\tgeneral manifold this is not always possible, in which case all boundaries shall be\n\t\t\t\tlisted as interior boundaries, and the exterior will be empty.')

    
    # Element {http://www.opengis.net/gml/3.2}interior uses Python identifier interior
    __interior = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'interior'), 'interior', '__httpwww_opengis_netgml3_2_PolygonType_httpwww_opengis_netgml3_2interior', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 715, 1), )

    
    interior = property(__interior.value, __interior.set, None, 'A boundary of a surface consists of a number of rings. The "interior"\n\t\t\t\trings separate the surface / surface patch from the area enclosed by the\n\t\t\trings.')

    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        __exterior.name() : __exterior,
        __interior.name() : __interior
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.PolygonType = PolygonType
Namespace.addCategoryObject('typeBinding', 'PolygonType', PolygonType)


# Complex type {http://www.opengis.net/gml/3.2}CurveType with content type ELEMENT_ONLY
class CurveType (AbstractCurveType):
    """Complex type {http://www.opengis.net/gml/3.2}CurveType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'CurveType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 799, 1)
    _ElementMap = AbstractCurveType._ElementMap.copy()
    _AttributeMap = AbstractCurveType._AttributeMap.copy()
    # Base type is AbstractCurveType
    
    # Element {http://www.opengis.net/gml/3.2}segments uses Python identifier segments
    __segments = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'segments'), 'segments', '__httpwww_opengis_netgml3_2_CurveType_httpwww_opengis_netgml3_2segments', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 835, 1), )

    
    segments = property(__segments.value, __segments.set, None, 'This property element contains a list of curve segments. The order of the\n\t\t\t\telements is significant and shall be preserved when processing the\n\t\t\tarray.')

    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        __segments.name() : __segments
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.CurveType = CurveType
Namespace.addCategoryObject('typeBinding', 'CurveType', CurveType)


# Complex type {http://www.opengis.net/gml/3.2}OrientableCurveType with content type ELEMENT_ONLY
class OrientableCurveType (AbstractCurveType):
    """Complex type {http://www.opengis.net/gml/3.2}OrientableCurveType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'OrientableCurveType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 808, 1)
    _ElementMap = AbstractCurveType._ElementMap.copy()
    _AttributeMap = AbstractCurveType._AttributeMap.copy()
    # Base type is AbstractCurveType
    
    # Element {http://www.opengis.net/gml/3.2}baseCurve uses Python identifier baseCurve
    __baseCurve = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'baseCurve'), 'baseCurve', '__httpwww_opengis_netgml3_2_OrientableCurveType_httpwww_opengis_netgml3_2baseCurve', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 818, 1), )

    
    baseCurve = property(__baseCurve.value, __baseCurve.set, None, 'The property baseCurve references or contains the base curve, i.e. it\n\t\t\t\teither references the base curve via the XLink-attributes or contains the curve\n\t\t\t\telement. A curve element is any element which is substitutable for AbstractCurve.\n\t\t\t\tThe base curve has positive orientation.')

    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute orientation uses Python identifier orientation
    __orientation = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'orientation'), 'orientation', '__httpwww_opengis_netgml3_2_OrientableCurveType_orientation', _module_typeBindings.SignType, unicode_default='+')
    __orientation._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 814, 4)
    __orientation._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 814, 4)
    
    orientation = property(__orientation.value, __orientation.set, None, None)

    _ElementMap.update({
        __baseCurve.name() : __baseCurve
    })
    _AttributeMap.update({
        __orientation.name() : __orientation
    })
_module_typeBindings.OrientableCurveType = OrientableCurveType
Namespace.addCategoryObject('typeBinding', 'OrientableCurveType', OrientableCurveType)


# Complex type {http://www.opengis.net/gml/3.2}SurfaceType with content type ELEMENT_ONLY
class SurfaceType (AbstractSurfaceType):
    """Complex type {http://www.opengis.net/gml/3.2}SurfaceType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'SurfaceType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1097, 1)
    _ElementMap = AbstractSurfaceType._ElementMap.copy()
    _AttributeMap = AbstractSurfaceType._AttributeMap.copy()
    # Base type is AbstractSurfaceType
    
    # Element {http://www.opengis.net/gml/3.2}patches uses Python identifier patches
    __patches = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'patches'), 'patches', '__httpwww_opengis_netgml3_2_SurfaceType_httpwww_opengis_netgml3_2patches', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1106, 1), )

    
    patches = property(__patches.value, __patches.set, None, 'The patches property element contains the sequence of surface patches.\n\t\t\t\tThe order of the elements is significant and shall be preserved when processing the\n\t\t\t\tarray.')

    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        __patches.name() : __patches
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.SurfaceType = SurfaceType
Namespace.addCategoryObject('typeBinding', 'SurfaceType', SurfaceType)


# Complex type {http://www.opengis.net/gml/3.2}CompositeCurveType with content type ELEMENT_ONLY
class CompositeCurveType (AbstractCurveType):
    """Complex type {http://www.opengis.net/gml/3.2}CompositeCurveType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'CompositeCurveType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1197, 1)
    _ElementMap = AbstractCurveType._ElementMap.copy()
    _AttributeMap = AbstractCurveType._AttributeMap.copy()
    # Base type is AbstractCurveType
    
    # Element {http://www.opengis.net/gml/3.2}curveMember uses Python identifier curveMember
    __curveMember = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'curveMember'), 'curveMember', '__httpwww_opengis_netgml3_2_CompositeCurveType_httpwww_opengis_netgml3_2curveMember', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1193, 1), )

    
    curveMember = property(__curveMember.value, __curveMember.set, None, None)

    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute aggregationType uses Python identifier aggregationType
    __aggregationType = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'aggregationType'), 'aggregationType', '__httpwww_opengis_netgml3_2_CompositeCurveType_aggregationType', _module_typeBindings.AggregationType)
    __aggregationType._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 309, 2)
    __aggregationType._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 309, 2)
    
    aggregationType = property(__aggregationType.value, __aggregationType.set, None, None)

    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        __curveMember.name() : __curveMember
    })
    _AttributeMap.update({
        __aggregationType.name() : __aggregationType
    })
_module_typeBindings.CompositeCurveType = CompositeCurveType
Namespace.addCategoryObject('typeBinding', 'CompositeCurveType', CompositeCurveType)


AbstractObject = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractObject'), pyxb.binding.datatypes.anyType, abstract=pyxb.binding.datatypes.boolean(1), documentation='This element has no type defined, and is therefore implicitly (according\n\t\t\t\tto the rules of W3C XML Schema) an XML Schema anyType. It is used as the head of an\n\t\t\t\tXML Schema substitution group which unifies complex content and certain simple\n\t\t\t\tcontent elements used for datatypes in GML, including the gml:AbstractGML\n\t\t\t\tsubstitution group.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 165, 1))
Namespace.addCategoryObject('elementBinding', AbstractObject.name().localName(), AbstractObject)

reversePropertyName = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'reversePropertyName'), pyxb.binding.datatypes.string, documentation='If the value of an object property is another object and that object\n\t\t\t\tcontains also a property for the association between the two objects, then this name\n\t\t\t\tof the reverse property may be encoded in a gml:reversePropertyName element in an\n\t\t\t\tappinfo annotation of the property element to document the constraint between the\n\t\t\t\ttwo properties. The value of the element shall contain the qualified name of the\n\t\t\t\tproperty element.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 264, 1))
Namespace.addCategoryObject('elementBinding', reversePropertyName.name().localName(), reversePropertyName)

targetElement = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'targetElement'), pyxb.binding.datatypes.string, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 338, 1))
Namespace.addCategoryObject('elementBinding', targetElement.name().localName(), targetElement)

associationName = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'associationName'), pyxb.binding.datatypes.string, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 339, 1))
Namespace.addCategoryObject('elementBinding', associationName.name().localName(), associationName)

defaultCodeSpace = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'defaultCodeSpace'), pyxb.binding.datatypes.anyURI, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 340, 1))
Namespace.addCategoryObject('elementBinding', defaultCodeSpace.name().localName(), defaultCodeSpace)

gmlProfileSchema = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'gmlProfileSchema'), pyxb.binding.datatypes.anyURI, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 341, 1))
Namespace.addCategoryObject('elementBinding', gmlProfileSchema.name().localName(), gmlProfileSchema)

AbstractValue = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractValue'), pyxb.binding.datatypes.anyType, abstract=pyxb.binding.datatypes.boolean(1), documentation='gml:AbstractValue is an abstract element which acts as the head of a\n\t\t\t\tsubstitution group which contains gml:AbstractScalarValue,\n\t\t\t\tgml:AbstractScalarValueList, gml:CompositeValue and gml:ValueExtent, and\n\t\t\t\t(transitively) the elements in their substitution groups. These elements may be used\n\t\t\t\tin an application schema as variables, so that in an XML instance document any\n\t\t\t\tmember of its substitution group may occur.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1434, 1))
Namespace.addCategoryObject('elementBinding', AbstractValue.name().localName(), AbstractValue)

AbstractScalarValue = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractScalarValue'), pyxb.binding.datatypes.anyType, abstract=pyxb.binding.datatypes.boolean(1), documentation='gml:AbstractScalarValue is an abstract element which acts as the head of\n\t\t\t\ta substitution group which contains gml:Boolean, gml:Category, gml:Count and\n\t\t\t\tgml:Quantity, and (transitively) the elements in their substitution\n\t\t\tgroups.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1444, 1))
Namespace.addCategoryObject('elementBinding', AbstractScalarValue.name().localName(), AbstractScalarValue)

AbstractGML = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractGML'), AbstractGMLType, abstract=pyxb.binding.datatypes.boolean(1), documentation='The abstract element gml:AbstractGML is "any GML object having identity".\n\t\t\t\tIt acts as the head of an XML Schema substitution group, which may include any\n\t\t\t\telement which is a GML feature, or other object, with identity. This is used as a\n\t\t\t\tvariable in content models in GML core and application schemas. It is effectively an\n\t\t\t\tabstract superclass for all GML objects.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 174, 1))
Namespace.addCategoryObject('elementBinding', AbstractGML.name().localName(), AbstractGML)

abstractInlineProperty = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'abstractInlineProperty'), InlinePropertyType, abstract=pyxb.binding.datatypes.boolean(1), documentation='gml:abstractInlineProperty may be used as the head of a subtitution group\n\t\t\t\tof more specific elements providing a value inline.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 252, 1))
Namespace.addCategoryObject('elementBinding', abstractInlineProperty.name().localName(), abstractInlineProperty)

Envelope = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Envelope'), EnvelopeType, documentation='Envelope defines an extent using a pair of positions defining opposite\n\t\t\t\tcorners in arbitrary dimensions. The first direct position is the "lower corner" (a\n\t\t\t\tcoordinate position consisting of all the minimal ordinates for each dimension for\n\t\t\t\tall points within the envelope), the second one the "upper corner" (a coordinate\n\t\t\t\tposition consisting of all the maximal ordinates for each dimension for all points\n\t\t\t\twithin the envelope). The use of the properties "coordinates" and "pos" has been\n\t\t\t\tdeprecated. The explicitly named properties "lowerCorner" and "upperCorner" shall be\n\t\t\t\tused instead.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 411, 1))
Namespace.addCategoryObject('elementBinding', Envelope.name().localName(), Envelope)

exterior = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'exterior'), AbstractRingPropertyType, documentation='A boundary of a surface consists of a number of rings. In the normal 2D\n\t\t\t\tcase, one of these rings is distinguished as being the exterior boundary. In a\n\t\t\t\tgeneral manifold this is not always possible, in which case all boundaries shall be\n\t\t\t\tlisted as interior boundaries, and the exterior will be empty.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 707, 1))
Namespace.addCategoryObject('elementBinding', exterior.name().localName(), exterior)

interior = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'interior'), AbstractRingPropertyType, documentation='A boundary of a surface consists of a number of rings. The "interior"\n\t\t\t\trings separate the surface / surface patch from the area enclosed by the\n\t\t\trings.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 715, 1))
Namespace.addCategoryObject('elementBinding', interior.name().localName(), interior)

AbstractRing = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractRing'), AbstractRingType, abstract=pyxb.binding.datatypes.boolean(1), documentation='An abstraction of a ring to support surface boundaries of different\n\t\t\t\tcomplexity. The AbstractRing element is the abstract head of the substituition group\n\t\t\t\tfor all closed boundaries of a surface patch.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 722, 1))
Namespace.addCategoryObject('elementBinding', AbstractRing.name().localName(), AbstractRing)

segments = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'segments'), CurveSegmentArrayPropertyType, documentation='This property element contains a list of curve segments. The order of the\n\t\t\t\telements is significant and shall be preserved when processing the\n\t\t\tarray.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 835, 1))
Namespace.addCategoryObject('elementBinding', segments.name().localName(), segments)

AbstractCurveSegment = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractCurveSegment'), AbstractCurveSegmentType, abstract=pyxb.binding.datatypes.boolean(1), documentation='A curve segment defines a homogeneous segment of a curve. The attributes\n\t\t\t\tnumDerivativesAtStart, numDerivativesAtEnd and numDerivativesInterior specify the\n\t\t\t\ttype of continuity as specified in ISO 19107:2003, 6.4.9.3. The AbstractCurveSegment\n\t\t\t\telement is the abstract head of the substituition group for all curve segment\n\t\t\t\telements, i.e. continuous segments of the same interpolation mechanism. All curve\n\t\t\t\tsegments shall have an attribute interpolation with type gml:CurveInterpolationType\n\t\t\t\tspecifying the curve interpolation mechanism used for this segment. This mechanism\n\t\t\t\tuses the control points and control parameters to determine the position of this\n\t\t\t\tcurve segment.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 842, 1))
Namespace.addCategoryObject('elementBinding', AbstractCurveSegment.name().localName(), AbstractCurveSegment)

patches = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'patches'), SurfacePatchArrayPropertyType, documentation='The patches property element contains the sequence of surface patches.\n\t\t\t\tThe order of the elements is significant and shall be preserved when processing the\n\t\t\t\tarray.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1106, 1))
Namespace.addCategoryObject('elementBinding', patches.name().localName(), patches)

AbstractSurfacePatch = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractSurfacePatch'), AbstractSurfacePatchType, abstract=pyxb.binding.datatypes.boolean(1), documentation='A surface patch defines a homogenuous portion of a surface. The\n\t\t\t\tAbstractSurfacePatch element is the abstract head of the substituition group for all\n\t\t\t\tsurface patch elements describing a continuous portion of a surface. All surface\n\t\t\t\tpatches shall have an attribute interpolation (declared in the types derived from\n\t\t\t\tgml:AbstractSurfacePatchType) specifying the interpolation mechanism used for the\n\t\t\t\tpatch using gml:SurfaceInterpolationType.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1122, 1))
Namespace.addCategoryObject('elementBinding', AbstractSurfacePatch.name().localName(), AbstractSurfacePatch)

AbstractFeature = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractFeature'), AbstractFeatureType, abstract=pyxb.binding.datatypes.boolean(1), documentation='This abstract element serves as the head of a substitution group which\n\t\t\t\tmay contain any elements whose content model is derived from\n\t\t\t\tgml:AbstractFeatureType. This may be used as a variable in the construction of\n\t\t\t\tcontent models. gml:AbstractFeature may be thought of as "anything that is a GML\n\t\t\t\tfeature" and may be used to define variables or templates in which the value of a\n\t\t\t\tGML property is "any feature". This occurs in particular in a GML feature collection\n\t\t\t\twhere the feature member properties contain one or multiple copies of\n\t\t\t\tgml:AbstractFeature respectively.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 345, 1))
Namespace.addCategoryObject('elementBinding', AbstractFeature.name().localName(), AbstractFeature)

AbstractGeometry = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractGeometry'), AbstractGeometryType, abstract=pyxb.binding.datatypes.boolean(1), documentation='The AbstractGeometry element is the abstract head of the substitution\n\t\t\t\tgroup for all geometry elements of GML. This includes pre-defined and user-defined\n\t\t\t\tgeometry elements. Any geometry element shall be a direct or indirect\n\t\t\t\textension/restriction of AbstractGeometryType and shall be directly or indirectly in\n\t\t\t\tthe substitution group of AbstractGeometry.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 431, 1))
Namespace.addCategoryObject('elementBinding', AbstractGeometry.name().localName(), AbstractGeometry)

pos = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'pos'), DirectPositionType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1))
Namespace.addCategoryObject('elementBinding', pos.name().localName(), pos)

posList = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'posList'), DirectPositionListType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 490, 1))
Namespace.addCategoryObject('elementBinding', posList.name().localName(), posList)

LinearRing = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'LinearRing'), LinearRingType, documentation='A LinearRing is defined by four or more coordinate tuples, with linear\n\t\t\t\tinterpolation between them; the first and last coordinates shall be coincident. The\n\t\t\t\tnumber of direct positions in the list shall be at least four.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 742, 1))
Namespace.addCategoryObject('elementBinding', LinearRing.name().localName(), LinearRing)

LineStringSegment = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'LineStringSegment'), LineStringSegmentType, documentation='A LineStringSegment is a curve segment that is defined by two or more\n\t\t\t\tcontrol points including the start and end point, with linear interpolation between\n\t\t\t\tthem. The content model follows the general pattern for the encoding of curve\n\t\t\t\tsegments.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 885, 1))
Namespace.addCategoryObject('elementBinding', LineStringSegment.name().localName(), LineStringSegment)

GeodesicString = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'GeodesicString'), GeodesicStringType, documentation='A sequence of geodesic segments. The number of control points shall be at\n\t\t\t\tleast two. interpolation is fixed as "geodesic". The content model follows the\n\t\t\t\tgeneral pattern for the encoding of curve segments.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1065, 1))
Namespace.addCategoryObject('elementBinding', GeodesicString.name().localName(), GeodesicString)

PolygonPatch = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'PolygonPatch'), PolygonPatchType, documentation='A gml:PolygonPatch is a surface patch that is defined by a set of\n\t\t\t\tboundary curves and an underlying surface to which these curves adhere. The curves\n\t\t\t\tshall be coplanar and the polygon uses planar interpolation in its interior.\n\t\t\t\tinterpolation is fixed to "planar", i.e. an interpolation shall return points on a\n\t\t\t\tsingle plane. The boundary of the patch shall be contained within that\n\t\t\tplane.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1133, 1))
Namespace.addCategoryObject('elementBinding', PolygonPatch.name().localName(), PolygonPatch)

Ring = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Ring'), RingType, documentation='A ring is used to represent a single connected component of a surface\n\t\t\t\tboundary as specified in ISO 19107:2003, 6.3.6. Every gml:curveMember references or\n\t\t\t\tcontains one curve, i.e. any element which is substitutable for gml:AbstractCurve.\n\t\t\t\tIn the context of a ring, the curves describe the boundary of the surface. The\n\t\t\t\tsequence of curves shall be contiguous and connected in a cycle. If provided, the\n\t\t\t\taggregationType attribute shall have the value "sequence".', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1173, 1))
Namespace.addCategoryObject('elementBinding', Ring.name().localName(), Ring)

abstractAssociationRole = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'abstractAssociationRole'), AssociationRoleType, abstract=pyxb.binding.datatypes.boolean(1), documentation='Applying this pattern shall restrict the multiplicity of objects in a\n\t\t\t\tproperty element using this content model to exactly one. An instance of this type\n\t\t\t\tshall contain an element representing an object, or serve as a pointer to a remote\n\t\t\t\tobject. Applying the pattern to define an application schema specific property type\n\t\t\t\tallows to restrict - the inline object to specified object types, - the encoding to\n\t\t\t\t"by-reference only" (see 7.2.3.7), - the encoding to "inline only" (see 7.2.3.8).', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 197, 1))
Namespace.addCategoryObject('elementBinding', abstractAssociationRole.name().localName(), abstractAssociationRole)

abstractReference = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'abstractReference'), ReferenceType, abstract=pyxb.binding.datatypes.boolean(1), documentation='gml:abstractReference may be used as the head of a subtitution group of\n\t\t\t\tmore specific elements providing a value by-reference.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 237, 1))
Namespace.addCategoryObject('elementBinding', abstractReference.name().localName(), abstractReference)

boundedBy = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'boundedBy'), BoundingShapeType, nillable=pyxb.binding.datatypes.boolean(1), documentation='This property describes the minimum bounding box or rectangle that\n\t\t\t\tencloses the entire feature.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 382, 1))
Namespace.addCategoryObject('elementBinding', boundedBy.name().localName(), boundedBy)

AbstractGeometricPrimitive = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractGeometricPrimitive'), AbstractGeometricPrimitiveType, abstract=pyxb.binding.datatypes.boolean(1), documentation='The AbstractGeometricPrimitive element is the abstract head of the\n\t\t\t\tsubstitution group for all (pre- and user-defined) geometric\n\t\t\tprimitives.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 511, 1))
Namespace.addCategoryObject('elementBinding', AbstractGeometricPrimitive.name().localName(), AbstractGeometricPrimitive)

pointProperty = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'pointProperty'), PointPropertyType, documentation='This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1))
Namespace.addCategoryObject('elementBinding', pointProperty.name().localName(), pointProperty)

baseCurve = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'baseCurve'), CurvePropertyType, documentation='The property baseCurve references or contains the base curve, i.e. it\n\t\t\t\teither references the base curve via the XLink-attributes or contains the curve\n\t\t\t\telement. A curve element is any element which is substitutable for AbstractCurve.\n\t\t\t\tThe base curve has positive orientation.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 818, 1))
Namespace.addCategoryObject('elementBinding', baseCurve.name().localName(), baseCurve)

Geodesic = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Geodesic'), GeodesicType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1083, 1))
Namespace.addCategoryObject('elementBinding', Geodesic.name().localName(), Geodesic)

curveMember = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'curveMember'), CurvePropertyType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1193, 1))
Namespace.addCategoryObject('elementBinding', curveMember.name().localName(), curveMember)

AbstractGeometricAggregate = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractGeometricAggregate'), AbstractGeometricAggregateType, abstract=pyxb.binding.datatypes.boolean(1), documentation='gml:AbstractGeometricAggregate is the abstract head of the substitution\n\t\t\t\tgroup for all geometric aggregates.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1220, 1))
Namespace.addCategoryObject('elementBinding', AbstractGeometricAggregate.name().localName(), AbstractGeometricAggregate)

pointMember = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'pointMember'), PointPropertyType, documentation='This property element either references a Point via the XLink-attributes\n\t\t\t\tor contains the Point element.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1250, 1))
Namespace.addCategoryObject('elementBinding', pointMember.name().localName(), pointMember)

Boolean = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Boolean'), CTD_ANON, nillable=pyxb.binding.datatypes.boolean(1), location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1452, 1))
Namespace.addCategoryObject('elementBinding', Boolean.name().localName(), Boolean)

measure = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'measure'), MeasureType, documentation='The value of a physical quantity, together with its unit.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1464, 1))
Namespace.addCategoryObject('elementBinding', measure.name().localName(), measure)

Point = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Point'), PointType, documentation='A Point is defined by a single coordinate tuple. The direct position of a\n\t\t\t\tpoint is specified by the pos element which is of type\n\t\t\tDirectPositionType.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 558, 1))
Namespace.addCategoryObject('elementBinding', Point.name().localName(), Point)

AbstractCurve = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractCurve'), AbstractCurveType, abstract=pyxb.binding.datatypes.boolean(1), documentation='The AbstractCurve element is the abstract head of the substitution group\n\t\t\t\tfor all (continuous) curve elements.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 601, 1))
Namespace.addCategoryObject('elementBinding', AbstractCurve.name().localName(), AbstractCurve)

AbstractSurface = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractSurface'), AbstractSurfaceType, abstract=pyxb.binding.datatypes.boolean(1), documentation='The AbstractSurface element is the abstract head of the substitution\n\t\t\t\tgroup for all (continuous) surface elements.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 659, 1))
Namespace.addCategoryObject('elementBinding', AbstractSurface.name().localName(), AbstractSurface)

MultiPoint = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'MultiPoint'), MultiPointType, documentation='A gml:MultiPoint consists of one or more gml:Points. The members of the\n\t\t\t\tgeometric aggregate may be specified either using the "standard" property\n\t\t\t\t(gml:pointMember) or the array property (gml:pointMembers). It is also valid to use\n\t\t\t\tboth the "standard" and the array properties in the same collection.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1233, 1))
Namespace.addCategoryObject('elementBinding', MultiPoint.name().localName(), MultiPoint)

angle = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'angle'), AngleType, documentation='The gml:angle property element is used to record the value of an angle\n\t\t\t\tquantity as a single number, with its units.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1481, 1))
Namespace.addCategoryObject('elementBinding', angle.name().localName(), angle)

LineString = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'LineString'), LineStringType, documentation='A LineString is a special curve that consists of a single segment with\n\t\t\t\tlinear interpolation. It is defined by two or more coordinate tuples, with linear\n\t\t\t\tinterpolation between them. The number of direct positions in the list shall be at\n\t\t\t\tleast two.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 631, 1))
Namespace.addCategoryObject('elementBinding', LineString.name().localName(), LineString)

Polygon = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Polygon'), PolygonType, documentation='A Polygon is a special surface that is defined by a single surface patch\n\t\t\t\t(see D.3.6). The boundary of this patch is coplanar and the polygon uses planar\n\t\t\t\tinterpolation in its interior. The elements exterior and interior describe the\n\t\t\t\tsurface boundary of the polygon.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 689, 1))
Namespace.addCategoryObject('elementBinding', Polygon.name().localName(), Polygon)

Curve = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Curve'), CurveType, documentation='A curve is a 1-dimensional primitive. Curves are continuous, connected,\n\t\t\t\tand have a measurable length in terms of the coordinate system. A curve is composed\n\t\t\t\tof one or more curve segments. Each curve segment within a curve may be defined\n\t\t\t\tusing a different interpolation method. The curve segments are connected to one\n\t\t\t\tanother, with the end point of each segment except the last being the start point of\n\t\t\t\tthe next segment in the segment list. The orientation of the curve is positive. The\n\t\t\t\telement segments encapsulates the segments of the curve.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 788, 1))
Namespace.addCategoryObject('elementBinding', Curve.name().localName(), Curve)

OrientableCurve = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'OrientableCurve'), OrientableCurveType, documentation='OrientableCurve consists of a curve and an orientation. If the\n\t\t\t\torientation is "+", then the OrientableCurve is identical to the baseCurve. If the\n\t\t\t\torientation is "-", then the OrientableCurve is related to another AbstractCurve\n\t\t\t\twith a parameterization that reverses the sense of the curve\n\t\t\ttraversal.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 826, 1))
Namespace.addCategoryObject('elementBinding', OrientableCurve.name().localName(), OrientableCurve)

Surface = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Surface'), SurfaceType, documentation='A Surface is a 2-dimensional primitive and is composed of one or more\n\t\t\t\tsurface patches as specified in ISO 19107:2003, 6.3.17.1. The surface patches are\n\t\t\t\tconnected to one another. patches encapsulates the patches of the\n\t\t\tsurface.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1089, 1))
Namespace.addCategoryObject('elementBinding', Surface.name().localName(), Surface)

CompositeCurve = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'CompositeCurve'), CompositeCurveType, documentation='A gml:CompositeCurve is represented by a sequence of (orientable) curves\n\t\t\t\tsuch that each curve in the sequence terminates at the start point of the subsequent\n\t\t\t\tcurve in the list. curveMember references or contains inline one curve in the\n\t\t\t\tcomposite curve. The curves are contiguous, the collection of curves is ordered.\n\t\t\t\tTherefore, if provided, the aggregationType attribute shall have the value\n\t\t\t\t"sequence".', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1207, 1))
Namespace.addCategoryObject('elementBinding', CompositeCurve.name().localName(), CompositeCurve)



def _BuildAutomaton ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton
    del _BuildAutomaton
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = set()
    symbol = pyxb.binding.content.WildcardUse(pyxb.binding.content.Wildcard(process_contents=pyxb.binding.content.Wildcard.PC_strict, namespace_constraint=pyxb.binding.content.Wildcard.NC_any), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 260, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
InlinePropertyType._Automaton = _BuildAutomaton()




EnvelopeType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'lowerCorner'), DirectPositionType, scope=EnvelopeType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 425, 3)))

EnvelopeType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'upperCorner'), DirectPositionType, scope=EnvelopeType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 426, 3)))

def _BuildAutomaton_ ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_
    del _BuildAutomaton_
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = None
    symbol = pyxb.binding.content.ElementUse(EnvelopeType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'lowerCorner')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 425, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(EnvelopeType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'upperCorner')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 426, 3))
    st_1 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    transitions = []
    transitions.append(fac.Transition(st_1, [
         ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    st_1._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
EnvelopeType._Automaton = _BuildAutomaton_()




AbstractRingPropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractRing'), AbstractRingType, abstract=pyxb.binding.datatypes.boolean(1), scope=AbstractRingPropertyType, documentation='An abstraction of a ring to support surface boundaries of different\n\t\t\t\tcomplexity. The AbstractRing element is the abstract head of the substituition group\n\t\t\t\tfor all closed boundaries of a surface patch.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 722, 1)))

def _BuildAutomaton_2 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_2
    del _BuildAutomaton_2
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(AbstractRingPropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'AbstractRing')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 739, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
AbstractRingPropertyType._Automaton = _BuildAutomaton_2()




LinearRingPropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'LinearRing'), LinearRingType, scope=LinearRingPropertyType, documentation='A LinearRing is defined by four or more coordinate tuples, with linear\n\t\t\t\tinterpolation between them; the first and last coordinates shall be coincident. The\n\t\t\t\tnumber of direct positions in the list shall be at least four.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 742, 1)))

def _BuildAutomaton_3 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_3
    del _BuildAutomaton_3
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(LinearRingPropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'LinearRing')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 782, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
LinearRingPropertyType._Automaton = _BuildAutomaton_3()




CurveSegmentArrayPropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractCurveSegment'), AbstractCurveSegmentType, abstract=pyxb.binding.datatypes.boolean(1), scope=CurveSegmentArrayPropertyType, documentation='A curve segment defines a homogeneous segment of a curve. The attributes\n\t\t\t\tnumDerivativesAtStart, numDerivativesAtEnd and numDerivativesInterior specify the\n\t\t\t\ttype of continuity as specified in ISO 19107:2003, 6.4.9.3. The AbstractCurveSegment\n\t\t\t\telement is the abstract head of the substituition group for all curve segment\n\t\t\t\telements, i.e. continuous segments of the same interpolation mechanism. All curve\n\t\t\t\tsegments shall have an attribute interpolation with type gml:CurveInterpolationType\n\t\t\t\tspecifying the curve interpolation mechanism used for this segment. This mechanism\n\t\t\t\tuses the control points and control parameters to determine the position of this\n\t\t\t\tcurve segment.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 842, 1)))

def _BuildAutomaton_4 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_4
    del _BuildAutomaton_4
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 865, 2))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(CurveSegmentArrayPropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'AbstractCurveSegment')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 866, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
CurveSegmentArrayPropertyType._Automaton = _BuildAutomaton_4()




SurfacePatchArrayPropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractSurfacePatch'), AbstractSurfacePatchType, abstract=pyxb.binding.datatypes.boolean(1), scope=SurfacePatchArrayPropertyType, documentation='A surface patch defines a homogenuous portion of a surface. The\n\t\t\t\tAbstractSurfacePatch element is the abstract head of the substituition group for all\n\t\t\t\tsurface patch elements describing a continuous portion of a surface. All surface\n\t\t\t\tpatches shall have an attribute interpolation (declared in the types derived from\n\t\t\t\tgml:AbstractSurfacePatchType) specifying the interpolation mechanism used for the\n\t\t\t\tpatch using gml:SurfaceInterpolationType.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1122, 1)))

def _BuildAutomaton_5 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_5
    del _BuildAutomaton_5
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1118, 2))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(SurfacePatchArrayPropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'AbstractSurfacePatch')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1119, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
SurfacePatchArrayPropertyType._Automaton = _BuildAutomaton_5()




AbstractFeatureType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'boundedBy'), BoundingShapeType, nillable=pyxb.binding.datatypes.boolean(1), scope=AbstractFeatureType, documentation='This property describes the minimum bounding box or rectangle that\n\t\t\t\tencloses the entire feature.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 382, 1)))

def _BuildAutomaton_6 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_6
    del _BuildAutomaton_6
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 370, 5))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(AbstractFeatureType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'boundedBy')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 370, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
AbstractFeatureType._Automaton = _BuildAutomaton_6()




LinearRingType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'pos'), DirectPositionType, scope=LinearRingType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1)))

LinearRingType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'posList'), DirectPositionListType, scope=LinearRingType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 490, 1)))

LinearRingType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'pointProperty'), PointPropertyType, scope=LinearRingType, documentation='This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1)))

def _BuildAutomaton_7 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_7
    del _BuildAutomaton_7
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=4, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 765, 6))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(LinearRingType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'pos')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 766, 7))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(LinearRingType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'pointProperty')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 767, 7))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(LinearRingType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'posList')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 769, 6))
    st_2 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    st_2._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
LinearRingType._Automaton = _BuildAutomaton_7()




LineStringSegmentType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'pos'), DirectPositionType, scope=LineStringSegmentType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1)))

LineStringSegmentType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'posList'), DirectPositionListType, scope=LineStringSegmentType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 490, 1)))

LineStringSegmentType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'pointProperty'), PointPropertyType, scope=LineStringSegmentType, documentation='This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1)))

def _BuildAutomaton_8 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_8
    del _BuildAutomaton_8
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=2, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 909, 6))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(LineStringSegmentType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'pos')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 910, 7))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(LineStringSegmentType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'pointProperty')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 911, 7))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(LineStringSegmentType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'posList')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 913, 6))
    st_2 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    st_2._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
LineStringSegmentType._Automaton = _BuildAutomaton_8()




GeodesicStringType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'pos'), DirectPositionType, scope=GeodesicStringType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1)))

GeodesicStringType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'posList'), DirectPositionListType, scope=GeodesicStringType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 490, 1)))

GeodesicStringType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'pointProperty'), PointPropertyType, scope=GeodesicStringType, documentation='This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1)))

def _BuildAutomaton_9 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_9
    del _BuildAutomaton_9
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=2, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1077, 5))
    counters.add(cc_0)
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(GeodesicStringType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'posList')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1076, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(GeodesicStringType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'pos')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 553, 3))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(GeodesicStringType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'pointProperty')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 554, 3))
    st_2 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    transitions = []
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_2._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
GeodesicStringType._Automaton = _BuildAutomaton_9()




PolygonPatchType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'exterior'), AbstractRingPropertyType, scope=PolygonPatchType, documentation='A boundary of a surface consists of a number of rings. In the normal 2D\n\t\t\t\tcase, one of these rings is distinguished as being the exterior boundary. In a\n\t\t\t\tgeneral manifold this is not always possible, in which case all boundaries shall be\n\t\t\t\tlisted as interior boundaries, and the exterior will be empty.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 707, 1)))

PolygonPatchType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'interior'), AbstractRingPropertyType, scope=PolygonPatchType, documentation='A boundary of a surface consists of a number of rings. The "interior"\n\t\t\t\trings separate the surface / surface patch from the area enclosed by the\n\t\t\trings.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 715, 1)))

def _BuildAutomaton_10 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_10
    del _BuildAutomaton_10
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1147, 5))
    counters.add(cc_0)
    cc_1 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1148, 5))
    counters.add(cc_1)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(PolygonPatchType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'exterior')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1147, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(PolygonPatchType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'interior')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1148, 5))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, False) ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_1, True) ]))
    st_1._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
PolygonPatchType._Automaton = _BuildAutomaton_10()




RingType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'curveMember'), CurvePropertyType, scope=RingType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1193, 1)))

def _BuildAutomaton_11 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_11
    del _BuildAutomaton_11
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(RingType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'curveMember')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1187, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
         ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
RingType._Automaton = _BuildAutomaton_11()




def _BuildAutomaton_12 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_12
    del _BuildAutomaton_12
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 208, 2))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.WildcardUse(pyxb.binding.content.Wildcard(process_contents=pyxb.binding.content.Wildcard.PC_strict, namespace_constraint=pyxb.binding.content.Wildcard.NC_any), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 209, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
AssociationRoleType._Automaton = _BuildAutomaton_12()




FeaturePropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractFeature'), AbstractFeatureType, abstract=pyxb.binding.datatypes.boolean(1), scope=FeaturePropertyType, documentation='This abstract element serves as the head of a substitution group which\n\t\t\t\tmay contain any elements whose content model is derived from\n\t\t\t\tgml:AbstractFeatureType. This may be used as a variable in the construction of\n\t\t\t\tcontent models. gml:AbstractFeature may be thought of as "anything that is a GML\n\t\t\t\tfeature" and may be used to define variables or templates in which the value of a\n\t\t\t\tGML property is "any feature". This occurs in particular in a GML feature collection\n\t\t\t\twhere the feature member properties contain one or multiple copies of\n\t\t\t\tgml:AbstractFeature respectively.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 345, 1)))

def _BuildAutomaton_13 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_13
    del _BuildAutomaton_13
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 376, 2))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(FeaturePropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'AbstractFeature')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 377, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
FeaturePropertyType._Automaton = _BuildAutomaton_13()




BoundingShapeType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Envelope'), EnvelopeType, scope=BoundingShapeType, documentation='Envelope defines an extent using a pair of positions defining opposite\n\t\t\t\tcorners in arbitrary dimensions. The first direct position is the "lower corner" (a\n\t\t\t\tcoordinate position consisting of all the minimal ordinates for each dimension for\n\t\t\t\tall points within the envelope), the second one the "upper corner" (a coordinate\n\t\t\t\tposition consisting of all the maximal ordinates for each dimension for all points\n\t\t\t\twithin the envelope). The use of the properties "coordinates" and "pos" has been\n\t\t\t\tdeprecated. The explicitly named properties "lowerCorner" and "upperCorner" shall be\n\t\t\t\tused instead.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 411, 1)))

def _BuildAutomaton_14 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_14
    del _BuildAutomaton_14
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(BoundingShapeType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'Envelope')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 391, 4))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
BoundingShapeType._Automaton = _BuildAutomaton_14()




GeometricPrimitivePropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractGeometricPrimitive'), AbstractGeometricPrimitiveType, abstract=pyxb.binding.datatypes.boolean(1), scope=GeometricPrimitivePropertyType, documentation='The AbstractGeometricPrimitive element is the abstract head of the\n\t\t\t\tsubstitution group for all (pre- and user-defined) geometric\n\t\t\tprimitives.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 511, 1)))

def _BuildAutomaton_15 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_15
    del _BuildAutomaton_15
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 537, 2))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(GeometricPrimitivePropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'AbstractGeometricPrimitive')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 538, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
GeometricPrimitivePropertyType._Automaton = _BuildAutomaton_15()




PointPropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Point'), PointType, scope=PointPropertyType, documentation='A Point is defined by a single coordinate tuple. The direct position of a\n\t\t\t\tpoint is specified by the pos element which is of type\n\t\t\tDirectPositionType.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 558, 1)))

def _BuildAutomaton_16 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_16
    del _BuildAutomaton_16
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 587, 2))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(PointPropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'Point')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 588, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
PointPropertyType._Automaton = _BuildAutomaton_16()




CurvePropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractCurve'), AbstractCurveType, abstract=pyxb.binding.datatypes.boolean(1), scope=CurvePropertyType, documentation='The AbstractCurve element is the abstract head of the substitution group\n\t\t\t\tfor all (continuous) curve elements.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 601, 1)))

def _BuildAutomaton_17 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_17
    del _BuildAutomaton_17
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 625, 2))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(CurvePropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'AbstractCurve')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 626, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
CurvePropertyType._Automaton = _BuildAutomaton_17()




SurfacePropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'AbstractSurface'), AbstractSurfaceType, abstract=pyxb.binding.datatypes.boolean(1), scope=SurfacePropertyType, documentation='The AbstractSurface element is the abstract head of the substitution\n\t\t\t\tgroup for all (continuous) surface elements.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 659, 1)))

def _BuildAutomaton_18 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_18
    del _BuildAutomaton_18
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 683, 2))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(SurfacePropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'AbstractSurface')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 684, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
SurfacePropertyType._Automaton = _BuildAutomaton_18()




def _BuildAutomaton_19 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_19
    del _BuildAutomaton_19
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=2, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1077, 5))
    counters.add(cc_0)
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(GeodesicType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'posList')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1076, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(GeodesicType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'pos')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 553, 3))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(GeodesicType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'pointProperty')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 554, 3))
    st_2 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    transitions = []
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_2._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
GeodesicType._Automaton = _BuildAutomaton_19()




PointType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'pos'), DirectPositionType, scope=PointType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1)))

def _BuildAutomaton_20 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_20
    del _BuildAutomaton_20
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(PointType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'pos')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 573, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
PointType._Automaton = _BuildAutomaton_20()




MultiPointType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'pointMember'), PointPropertyType, scope=MultiPointType, documentation='This property element either references a Point via the XLink-attributes\n\t\t\t\tor contains the Point element.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1250, 1)))

def _BuildAutomaton_21 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_21
    del _BuildAutomaton_21
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1245, 5))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(MultiPointType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'pointMember')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1245, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
MultiPointType._Automaton = _BuildAutomaton_21()




LineStringType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'pos'), DirectPositionType, scope=LineStringType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1)))

LineStringType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'posList'), DirectPositionListType, scope=LineStringType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 490, 1)))

LineStringType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'pointProperty'), PointPropertyType, scope=LineStringType, documentation='This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1)))

def _BuildAutomaton_22 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_22
    del _BuildAutomaton_22
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=2, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 644, 6))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(LineStringType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'pos')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 645, 7))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(LineStringType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'pointProperty')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 646, 7))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(LineStringType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'posList')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 648, 6))
    st_2 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    st_2._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
LineStringType._Automaton = _BuildAutomaton_22()




PolygonType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'exterior'), AbstractRingPropertyType, scope=PolygonType, documentation='A boundary of a surface consists of a number of rings. In the normal 2D\n\t\t\t\tcase, one of these rings is distinguished as being the exterior boundary. In a\n\t\t\t\tgeneral manifold this is not always possible, in which case all boundaries shall be\n\t\t\t\tlisted as interior boundaries, and the exterior will be empty.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 707, 1)))

PolygonType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'interior'), AbstractRingPropertyType, scope=PolygonType, documentation='A boundary of a surface consists of a number of rings. The "interior"\n\t\t\t\trings separate the surface / surface patch from the area enclosed by the\n\t\t\trings.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 715, 1)))

def _BuildAutomaton_23 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_23
    del _BuildAutomaton_23
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 701, 5))
    counters.add(cc_0)
    cc_1 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 702, 5))
    counters.add(cc_1)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(PolygonType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'exterior')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 701, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(PolygonType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'interior')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 702, 5))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, False) ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_1, True) ]))
    st_1._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
PolygonType._Automaton = _BuildAutomaton_23()




CurveType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'segments'), CurveSegmentArrayPropertyType, scope=CurveType, documentation='This property element contains a list of curve segments. The order of the\n\t\t\t\telements is significant and shall be preserved when processing the\n\t\t\tarray.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 835, 1)))

def _BuildAutomaton_24 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_24
    del _BuildAutomaton_24
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(CurveType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'segments')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 803, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
CurveType._Automaton = _BuildAutomaton_24()




OrientableCurveType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'baseCurve'), CurvePropertyType, scope=OrientableCurveType, documentation='The property baseCurve references or contains the base curve, i.e. it\n\t\t\t\teither references the base curve via the XLink-attributes or contains the curve\n\t\t\t\telement. A curve element is any element which is substitutable for AbstractCurve.\n\t\t\t\tThe base curve has positive orientation.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 818, 1)))

def _BuildAutomaton_25 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_25
    del _BuildAutomaton_25
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(OrientableCurveType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'baseCurve')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 812, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
OrientableCurveType._Automaton = _BuildAutomaton_25()




SurfaceType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'patches'), SurfacePatchArrayPropertyType, scope=SurfaceType, documentation='The patches property element contains the sequence of surface patches.\n\t\t\t\tThe order of the elements is significant and shall be preserved when processing the\n\t\t\t\tarray.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1106, 1)))

def _BuildAutomaton_26 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_26
    del _BuildAutomaton_26
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(SurfaceType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'patches')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1101, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
SurfaceType._Automaton = _BuildAutomaton_26()




CompositeCurveType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'curveMember'), CurvePropertyType, scope=CompositeCurveType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1193, 1)))

def _BuildAutomaton_27 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_27
    del _BuildAutomaton_27
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(CompositeCurveType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'curveMember')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1201, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
         ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
CompositeCurveType._Automaton = _BuildAutomaton_27()


AbstractValue._setSubstitutionGroup(AbstractObject)

AbstractScalarValue._setSubstitutionGroup(AbstractValue)

AbstractGML._setSubstitutionGroup(AbstractObject)

Envelope._setSubstitutionGroup(AbstractObject)

AbstractRing._setSubstitutionGroup(AbstractObject)

AbstractCurveSegment._setSubstitutionGroup(AbstractObject)

AbstractFeature._setSubstitutionGroup(AbstractGML)

AbstractGeometry._setSubstitutionGroup(AbstractGML)

LinearRing._setSubstitutionGroup(AbstractRing)

LineStringSegment._setSubstitutionGroup(AbstractCurveSegment)

GeodesicString._setSubstitutionGroup(AbstractCurveSegment)

PolygonPatch._setSubstitutionGroup(AbstractSurfacePatch)

Ring._setSubstitutionGroup(AbstractRing)

AbstractGeometricPrimitive._setSubstitutionGroup(AbstractGeometry)

Geodesic._setSubstitutionGroup(GeodesicString)

AbstractGeometricAggregate._setSubstitutionGroup(AbstractGeometry)

Boolean._setSubstitutionGroup(AbstractScalarValue)

Point._setSubstitutionGroup(AbstractGeometricPrimitive)

AbstractCurve._setSubstitutionGroup(AbstractGeometricPrimitive)

AbstractSurface._setSubstitutionGroup(AbstractGeometricPrimitive)

MultiPoint._setSubstitutionGroup(AbstractGeometricAggregate)

LineString._setSubstitutionGroup(AbstractCurve)

Polygon._setSubstitutionGroup(AbstractSurface)

Curve._setSubstitutionGroup(AbstractCurve)

OrientableCurve._setSubstitutionGroup(AbstractCurve)

Surface._setSubstitutionGroup(AbstractSurface)

CompositeCurve._setSubstitutionGroup(AbstractCurve)
