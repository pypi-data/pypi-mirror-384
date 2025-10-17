# ./_S100.py
# -*- coding: utf-8 -*-
# PyXB bindings for NM:39d4dfdf577f986e5d6b149536ddd6947cc5643f
# Generated 2025-10-13 15:57:18.382739 by PyXB version 1.2.6 using Python 3.12.3.final.0
# Namespace http://www.iho.int/s100gml/5.0 [xmlns:S100]

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
import _gml as _ImportedBinding__gml
import _xlink as _ImportedBinding__xlink
import pyxb.binding.datatypes

# NOTE: All namespace declarations are reserved within the binding
Namespace = pyxb.namespace.NamespaceForURI('http://www.iho.int/s100gml/5.0', create_if_missing=True)
Namespace.configureCategories(['typeBinding', 'elementBinding'])
_Namespace_gml = _ImportedBinding__gml.Namespace
_Namespace_gml.configureCategories(['typeBinding', 'elementBinding'])
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


# Atomic simple type: {http://www.iho.int/s100gml/5.0}ISO-639-2
class ISO_639_2 (pyxb.binding.datatypes.string):

    """Stub for ISO 639-2 language codes. Further validation via XSLT or Schematron rules?"""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'ISO-639-2')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 56, 4)
    _Documentation = 'Stub for ISO 639-2 language codes. Further validation via XSLT or Schematron rules?'
ISO_639_2._CF_pattern = pyxb.binding.facets.CF_pattern()
ISO_639_2._CF_pattern.addPattern(pattern='\\w{3}')
ISO_639_2._InitializeFacetMap(ISO_639_2._CF_pattern)
Namespace.addCategoryObject('typeBinding', 'ISO-639-2', ISO_639_2)
_module_typeBindings.ISO_639_2 = ISO_639_2

# Atomic simple type: {http://www.iho.int/s100gml/5.0}BearingType
class BearingType (pyxb.binding.datatypes.decimal):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'BearingType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 66, 4)
    _Documentation = None
BearingType._CF_fractionDigits = pyxb.binding.facets.CF_fractionDigits(value=pyxb.binding.datatypes.nonNegativeInteger(1))
BearingType._CF_maxInclusive = pyxb.binding.facets.CF_maxInclusive(value=pyxb.binding.datatypes.decimal('360.0'), value_datatype=BearingType)
BearingType._CF_minInclusive = pyxb.binding.facets.CF_minInclusive(value=pyxb.binding.datatypes.decimal('0.0'), value_datatype=BearingType)
BearingType._InitializeFacetMap(BearingType._CF_fractionDigits,
   BearingType._CF_maxInclusive,
   BearingType._CF_minInclusive)
Namespace.addCategoryObject('typeBinding', 'BearingType', BearingType)
_module_typeBindings.BearingType = BearingType

# Atomic simple type: {http://www.iho.int/s100gml/5.0}PlusOrMinus360Degrees
class PlusOrMinus360Degrees (pyxb.binding.datatypes.decimal):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'PlusOrMinus360Degrees')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 73, 4)
    _Documentation = None
PlusOrMinus360Degrees._CF_fractionDigits = pyxb.binding.facets.CF_fractionDigits(value=pyxb.binding.datatypes.nonNegativeInteger(1))
PlusOrMinus360Degrees._CF_maxInclusive = pyxb.binding.facets.CF_maxInclusive(value=pyxb.binding.datatypes.decimal('360.0'), value_datatype=PlusOrMinus360Degrees)
PlusOrMinus360Degrees._CF_minInclusive = pyxb.binding.facets.CF_minInclusive(value=pyxb.binding.datatypes.decimal('-360.0'), value_datatype=PlusOrMinus360Degrees)
PlusOrMinus360Degrees._InitializeFacetMap(PlusOrMinus360Degrees._CF_fractionDigits,
   PlusOrMinus360Degrees._CF_maxInclusive,
   PlusOrMinus360Degrees._CF_minInclusive)
Namespace.addCategoryObject('typeBinding', 'PlusOrMinus360Degrees', PlusOrMinus360Degrees)
_module_typeBindings.PlusOrMinus360Degrees = PlusOrMinus360Degrees

# Atomic simple type: {http://www.iho.int/s100gml/5.0}MD_TopicCategoryCode
class MD_TopicCategoryCode (pyxb.binding.datatypes.string, pyxb.binding.basis.enumeration_mixin):

    """Topic categories in S-100 Edition 1.0.0 and gmxCodelists.xml from OGC ISO 19139 XML schemas - see MD_TopicCategoryCode.
            Alternatives to this enumeration: (1) Add the ISO 19139 schemas to this profile and use the codelist MD_TopicCategoryCode instead.
            (2) Ise numeric codes for literals instead of labels, e.g., "1" instead of "farming"."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'MD_TopicCategoryCode')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 84, 4)
    _Documentation = 'Topic categories in S-100 Edition 1.0.0 and gmxCodelists.xml from OGC ISO 19139 XML schemas - see MD_TopicCategoryCode.\n            Alternatives to this enumeration: (1) Add the ISO 19139 schemas to this profile and use the codelist MD_TopicCategoryCode instead.\n            (2) Ise numeric codes for literals instead of labels, e.g., "1" instead of "farming".'
MD_TopicCategoryCode._CF_enumeration = pyxb.binding.facets.CF_enumeration(enum_prefix=None, value_datatype=MD_TopicCategoryCode)
MD_TopicCategoryCode.farming = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='farming', tag='farming')
MD_TopicCategoryCode.biota = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='biota', tag='biota')
MD_TopicCategoryCode.boundaries = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='boundaries', tag='boundaries')
MD_TopicCategoryCode.climatologyMeteorologyAtmosphere = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='climatologyMeteorologyAtmosphere', tag='climatologyMeteorologyAtmosphere')
MD_TopicCategoryCode.economy = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='economy', tag='economy')
MD_TopicCategoryCode.elevation = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='elevation', tag='elevation')
MD_TopicCategoryCode.environment = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='environment', tag='environment')
MD_TopicCategoryCode.geoscientificInformation = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='geoscientificInformation', tag='geoscientificInformation')
MD_TopicCategoryCode.health = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='health', tag='health')
MD_TopicCategoryCode.imageryBaseMapsEarthCover = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='imageryBaseMapsEarthCover', tag='imageryBaseMapsEarthCover')
MD_TopicCategoryCode.intelligenceMilitary = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='intelligenceMilitary', tag='intelligenceMilitary')
MD_TopicCategoryCode.inlandWaters = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='inlandWaters', tag='inlandWaters')
MD_TopicCategoryCode.location = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='location', tag='location')
MD_TopicCategoryCode.oceans = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='oceans', tag='oceans')
MD_TopicCategoryCode.planningCadastre = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='planningCadastre', tag='planningCadastre')
MD_TopicCategoryCode.society = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='society', tag='society')
MD_TopicCategoryCode.structure = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='structure', tag='structure')
MD_TopicCategoryCode.transportation = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='transportation', tag='transportation')
MD_TopicCategoryCode.utilitiesCommunication = MD_TopicCategoryCode._CF_enumeration.addEnumeration(unicode_value='utilitiesCommunication', tag='utilitiesCommunication')
MD_TopicCategoryCode._InitializeFacetMap(MD_TopicCategoryCode._CF_enumeration)
Namespace.addCategoryObject('typeBinding', 'MD_TopicCategoryCode', MD_TopicCategoryCode)
_module_typeBindings.MD_TopicCategoryCode = MD_TopicCategoryCode

# Atomic simple type: {http://www.iho.int/s100gml/5.0}datasetPurposeType
class datasetPurposeType (pyxb.binding.datatypes.string, pyxb.binding.basis.enumeration_mixin):

    """New type introduced in S-100 Ed 5 to distinguish between a Base dataset and an Update."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'datasetPurposeType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 189, 4)
    _Documentation = 'New type introduced in S-100 Ed 5 to distinguish between a Base dataset and an Update.'
datasetPurposeType._CF_enumeration = pyxb.binding.facets.CF_enumeration(enum_prefix=None, value_datatype=datasetPurposeType)
datasetPurposeType.base = datasetPurposeType._CF_enumeration.addEnumeration(unicode_value='base', tag='base')
datasetPurposeType.update = datasetPurposeType._CF_enumeration.addEnumeration(unicode_value='update', tag='update')
datasetPurposeType._InitializeFacetMap(datasetPurposeType._CF_enumeration)
Namespace.addCategoryObject('typeBinding', 'datasetPurposeType', datasetPurposeType)
_module_typeBindings.datasetPurposeType = datasetPurposeType

# Atomic simple type: {http://www.iho.int/s100gml/5.0}S100_GM_KnotTypeType
class S100_GM_KnotTypeType (pyxb.binding.datatypes.string, pyxb.binding.basis.enumeration_mixin):

    """This enumeration type specifies values for the knots' type (see ISO 19107:2003, 6.4.25).The S-100 3.1 type extends it with "nonUniform" in keeping with the 2017 draft of 19107 """

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'S100_GM_KnotTypeType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 596, 4)
    _Documentation = 'This enumeration type specifies values for the knots\' type (see ISO 19107:2003, 6.4.25).The S-100 3.1 type extends it with "nonUniform" in keeping with the 2017 draft of 19107 '
S100_GM_KnotTypeType._CF_enumeration = pyxb.binding.facets.CF_enumeration(enum_prefix=None, value_datatype=S100_GM_KnotTypeType)
S100_GM_KnotTypeType.uniform = S100_GM_KnotTypeType._CF_enumeration.addEnumeration(unicode_value='uniform', tag='uniform')
S100_GM_KnotTypeType.quasiUniform = S100_GM_KnotTypeType._CF_enumeration.addEnumeration(unicode_value='quasiUniform', tag='quasiUniform')
S100_GM_KnotTypeType.piecewiseBezier = S100_GM_KnotTypeType._CF_enumeration.addEnumeration(unicode_value='piecewiseBezier', tag='piecewiseBezier')
S100_GM_KnotTypeType.nonUniform = S100_GM_KnotTypeType._CF_enumeration.addEnumeration(unicode_value='nonUniform', tag='nonUniform')
S100_GM_KnotTypeType._InitializeFacetMap(S100_GM_KnotTypeType._CF_enumeration)
Namespace.addCategoryObject('typeBinding', 'S100_GM_KnotTypeType', S100_GM_KnotTypeType)
_module_typeBindings.S100_GM_KnotTypeType = S100_GM_KnotTypeType

# Atomic simple type: [anonymous]
class STD_ANON (pyxb.binding.datatypes.integer, pyxb.binding.basis.enumeration_mixin):

    """An atomic simple type."""

    _ExpandedName = None
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 800, 2)
    _Documentation = None
STD_ANON._CF_enumeration = pyxb.binding.facets.CF_enumeration(enum_prefix=None, value_datatype=STD_ANON)
STD_ANON._CF_enumeration.addEnumeration(unicode_value='1', tag=None)
STD_ANON._CF_enumeration.addEnumeration(unicode_value='2', tag=None)
STD_ANON._InitializeFacetMap(STD_ANON._CF_enumeration)
_module_typeBindings.STD_ANON = STD_ANON

# Atomic simple type: [anonymous]
class STD_ANON_ (PlusOrMinus360Degrees, pyxb.binding.basis.enumeration_mixin):

    """An atomic simple type."""

    _ExpandedName = None
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 574, 24)
    _Documentation = None
STD_ANON_._CF_enumeration = pyxb.binding.facets.CF_enumeration(enum_prefix=None, value_datatype=STD_ANON_)
STD_ANON_._CF_enumeration.addEnumeration(unicode_value='360.0', tag=None)
STD_ANON_._CF_enumeration.addEnumeration(unicode_value='-360.0', tag=None)
STD_ANON_._InitializeFacetMap(STD_ANON_._CF_enumeration)
_module_typeBindings.STD_ANON_ = STD_ANON_

# Complex type {http://www.iho.int/s100gml/5.0}DataSetIdentificationType with content type ELEMENT_ONLY
class DataSetIdentificationType (pyxb.binding.basis.complexTypeDefinition):
    """S-100 Data Set Identification. The fields correspond to S-100 10a-5.1.2.1 fields.
            Attributes encodingSpecification and encodingSpecificationEdition are actually redundant here because in an XML schema the encoding specification and encoding specification edition are usually implicit in the namespace URI."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'DataSetIdentificationType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 208, 4)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.iho.int/s100gml/5.0}encodingSpecification uses Python identifier encodingSpecification
    __encodingSpecification = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'encodingSpecification'), 'encodingSpecification', '__httpwww_iho_ints100gml5_0_DataSetIdentificationType_httpwww_iho_ints100gml5_0encodingSpecification', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 214, 12), )

    
    encodingSpecification = property(__encodingSpecification.value, __encodingSpecification.set, None, 'Encoding specification that defines the encoding.')

    
    # Element {http://www.iho.int/s100gml/5.0}encodingSpecificationEdition uses Python identifier encodingSpecificationEdition
    __encodingSpecificationEdition = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'encodingSpecificationEdition'), 'encodingSpecificationEdition', '__httpwww_iho_ints100gml5_0_DataSetIdentificationType_httpwww_iho_ints100gml5_0encodingSpecificationEdition', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 219, 12), )

    
    encodingSpecificationEdition = property(__encodingSpecificationEdition.value, __encodingSpecificationEdition.set, None, 'Edition of the encoding specification')

    
    # Element {http://www.iho.int/s100gml/5.0}productIdentifier uses Python identifier productIdentifier
    __productIdentifier = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'productIdentifier'), 'productIdentifier', '__httpwww_iho_ints100gml5_0_DataSetIdentificationType_httpwww_iho_ints100gml5_0productIdentifier', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 224, 12), )

    
    productIdentifier = property(__productIdentifier.value, __productIdentifier.set, None, 'Unique identifier of the data product as specified in the product specification')

    
    # Element {http://www.iho.int/s100gml/5.0}productEdition uses Python identifier productEdition
    __productEdition = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'productEdition'), 'productEdition', '__httpwww_iho_ints100gml5_0_DataSetIdentificationType_httpwww_iho_ints100gml5_0productEdition', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 229, 12), )

    
    productEdition = property(__productEdition.value, __productEdition.set, None, 'Edition of the product specification')

    
    # Element {http://www.iho.int/s100gml/5.0}applicationProfile uses Python identifier applicationProfile
    __applicationProfile = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'applicationProfile'), 'applicationProfile', '__httpwww_iho_ints100gml5_0_DataSetIdentificationType_httpwww_iho_ints100gml5_0applicationProfile', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 234, 12), )

    
    applicationProfile = property(__applicationProfile.value, __applicationProfile.set, None, 'Identifier that specifies a profile within the data product')

    
    # Element {http://www.iho.int/s100gml/5.0}datasetFileIdentifier uses Python identifier datasetFileIdentifier
    __datasetFileIdentifier = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'datasetFileIdentifier'), 'datasetFileIdentifier', '__httpwww_iho_ints100gml5_0_DataSetIdentificationType_httpwww_iho_ints100gml5_0datasetFileIdentifier', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 239, 12), )

    
    datasetFileIdentifier = property(__datasetFileIdentifier.value, __datasetFileIdentifier.set, None, 'The file identifier of the dataset')

    
    # Element {http://www.iho.int/s100gml/5.0}datasetTitle uses Python identifier datasetTitle
    __datasetTitle = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'datasetTitle'), 'datasetTitle', '__httpwww_iho_ints100gml5_0_DataSetIdentificationType_httpwww_iho_ints100gml5_0datasetTitle', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 244, 12), )

    
    datasetTitle = property(__datasetTitle.value, __datasetTitle.set, None, 'The title of the dataset')

    
    # Element {http://www.iho.int/s100gml/5.0}datasetReferenceDate uses Python identifier datasetReferenceDate
    __datasetReferenceDate = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'datasetReferenceDate'), 'datasetReferenceDate', '__httpwww_iho_ints100gml5_0_DataSetIdentificationType_httpwww_iho_ints100gml5_0datasetReferenceDate', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 249, 12), )

    
    datasetReferenceDate = property(__datasetReferenceDate.value, __datasetReferenceDate.set, None, 'The reference date of the dataset')

    
    # Element {http://www.iho.int/s100gml/5.0}datasetLanguage uses Python identifier datasetLanguage
    __datasetLanguage = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'datasetLanguage'), 'datasetLanguage', '__httpwww_iho_ints100gml5_0_DataSetIdentificationType_httpwww_iho_ints100gml5_0datasetLanguage', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 254, 12), )

    
    datasetLanguage = property(__datasetLanguage.value, __datasetLanguage.set, None, 'The (primary) language used in this dataset')

    
    # Element {http://www.iho.int/s100gml/5.0}datasetAbstract uses Python identifier datasetAbstract
    __datasetAbstract = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'datasetAbstract'), 'datasetAbstract', '__httpwww_iho_ints100gml5_0_DataSetIdentificationType_httpwww_iho_ints100gml5_0datasetAbstract', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 259, 12), )

    
    datasetAbstract = property(__datasetAbstract.value, __datasetAbstract.set, None, 'The abstract of the dataset')

    
    # Element {http://www.iho.int/s100gml/5.0}datasetTopicCategory uses Python identifier datasetTopicCategory
    __datasetTopicCategory = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'datasetTopicCategory'), 'datasetTopicCategory', '__httpwww_iho_ints100gml5_0_DataSetIdentificationType_httpwww_iho_ints100gml5_0datasetTopicCategory', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 264, 12), )

    
    datasetTopicCategory = property(__datasetTopicCategory.value, __datasetTopicCategory.set, None, 'A set of topic categories')

    
    # Element {http://www.iho.int/s100gml/5.0}datasetPurpose uses Python identifier datasetPurpose
    __datasetPurpose = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'datasetPurpose'), 'datasetPurpose', '__httpwww_iho_ints100gml5_0_DataSetIdentificationType_httpwww_iho_ints100gml5_0datasetPurpose', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 269, 12), )

    
    datasetPurpose = property(__datasetPurpose.value, __datasetPurpose.set, None, 'base or update')

    
    # Element {http://www.iho.int/s100gml/5.0}updateNumber uses Python identifier updateNumber
    __updateNumber = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'updateNumber'), 'updateNumber', '__httpwww_iho_ints100gml5_0_DataSetIdentificationType_httpwww_iho_ints100gml5_0updateNumber', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 274, 12), )

    
    updateNumber = property(__updateNumber.value, __updateNumber.set, None, 'Update Number, 0 for a Base dataset')

    _ElementMap.update({
        __encodingSpecification.name() : __encodingSpecification,
        __encodingSpecificationEdition.name() : __encodingSpecificationEdition,
        __productIdentifier.name() : __productIdentifier,
        __productEdition.name() : __productEdition,
        __applicationProfile.name() : __applicationProfile,
        __datasetFileIdentifier.name() : __datasetFileIdentifier,
        __datasetTitle.name() : __datasetTitle,
        __datasetReferenceDate.name() : __datasetReferenceDate,
        __datasetLanguage.name() : __datasetLanguage,
        __datasetAbstract.name() : __datasetAbstract,
        __datasetTopicCategory.name() : __datasetTopicCategory,
        __datasetPurpose.name() : __datasetPurpose,
        __updateNumber.name() : __updateNumber
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.DataSetIdentificationType = DataSetIdentificationType
Namespace.addCategoryObject('typeBinding', 'DataSetIdentificationType', DataSetIdentificationType)


# Complex type {http://www.iho.int/s100gml/5.0}S100_GM_KnotType with content type ELEMENT_ONLY
class S100_GM_KnotType (pyxb.binding.basis.complexTypeDefinition):
    """S-100 Knot is the GML 3.2.1 definition of Knot with the erroneous "weight" element removed."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'S100_GM_KnotType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 624, 4)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.iho.int/s100gml/5.0}value uses Python identifier value_
    __value = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'value'), 'value_', '__httpwww_iho_ints100gml5_0_S100_GM_KnotType_httpwww_iho_ints100gml5_0value', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 629, 12), )

    
    value_ = property(__value.value, __value.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}multiplicity uses Python identifier multiplicity
    __multiplicity = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'multiplicity'), 'multiplicity', '__httpwww_iho_ints100gml5_0_S100_GM_KnotType_httpwww_iho_ints100gml5_0multiplicity', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 630, 12), )

    
    multiplicity = property(__multiplicity.value, __multiplicity.set, None, None)

    _ElementMap.update({
        __value.name() : __value,
        __multiplicity.name() : __multiplicity
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.S100_GM_KnotType = S100_GM_KnotType
Namespace.addCategoryObject('typeBinding', 'S100_GM_KnotType', S100_GM_KnotType)


# Complex type {http://www.iho.int/s100gml/5.0}KnotPropertyType with content type ELEMENT_ONLY
class KnotPropertyType (pyxb.binding.basis.complexTypeDefinition):
    """gml:KnotPropertyType encapsulates a knot to use it in a geometric type. The S100 version is needed so as to use the updated definition of knots"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'KnotPropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 633, 4)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.iho.int/s100gml/5.0}Knot uses Python identifier Knot
    __Knot = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'Knot'), 'Knot', '__httpwww_iho_ints100gml5_0_KnotPropertyType_httpwww_iho_ints100gml5_0Knot', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 638, 12), )

    
    Knot = property(__Knot.value, __Knot.set, None, 'A knot is a breakpoint on a piecewise spline curve.\n                        value is the value of the parameter at the knot of the spline (see ISO 19107:2003, 6.4.24.2).\n                        multiplicity is the multiplicity of this knot used in the definition of the spline (with the same weight).\n                        weight is the value of the averaging weight used for this knot of the spline.')

    _ElementMap.update({
        __Knot.name() : __Knot
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.KnotPropertyType = KnotPropertyType
Namespace.addCategoryObject('typeBinding', 'KnotPropertyType', KnotPropertyType)


# Complex type {http://www.iho.int/s100gml/5.0}VectorType with content type ELEMENT_ONLY
class VectorType (pyxb.binding.basis.complexTypeDefinition):
    """Defintion of the Vector datatype used in splines"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'VectorType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 648, 4)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.iho.int/s100gml/5.0}origin uses Python identifier origin
    __origin = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'origin'), 'origin', '__httpwww_iho_ints100gml5_0_VectorType_httpwww_iho_ints100gml5_0origin', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 653, 12), )

    
    origin = property(__origin.value, __origin.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}dimension uses Python identifier dimension
    __dimension = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'dimension'), 'dimension', '__httpwww_iho_ints100gml5_0_VectorType_httpwww_iho_ints100gml5_0dimension', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 661, 12), )

    
    dimension = property(__dimension.value, __dimension.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}offset uses Python identifier offset
    __offset = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'offset'), 'offset', '__httpwww_iho_ints100gml5_0_VectorType_httpwww_iho_ints100gml5_0offset', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 662, 12), )

    
    offset = property(__offset.value, __offset.set, None, 'The number of values must be the same as "dimension" value')

    _ElementMap.update({
        __origin.name() : __origin,
        __dimension.name() : __dimension,
        __offset.name() : __offset
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.VectorType = VectorType
Namespace.addCategoryObject('typeBinding', 'VectorType', VectorType)


# Complex type [anonymous] with content type ELEMENT_ONLY
class CTD_ANON (pyxb.binding.basis.complexTypeDefinition):
    """Complex type [anonymous] with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = None
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 654, 16)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.opengis.net/gml/3.2}pos uses Python identifier pos
    __pos = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(_Namespace_gml, 'pos'), 'pos', '__httpwww_iho_ints100gml5_0_CTD_ANON_httpwww_opengis_netgml3_2pos', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1), )

    
    pos = property(__pos.value, __pos.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}pointProperty uses Python identifier pointProperty
    __pointProperty = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(_Namespace_gml, 'pointProperty'), 'pointProperty', '__httpwww_iho_ints100gml5_0_CTD_ANON_httpwww_opengis_netgml3_2pointProperty', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1), )

    
    pointProperty = property(__pointProperty.value, __pointProperty.set, None, 'This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.')

    _ElementMap.update({
        __pos.name() : __pos,
        __pointProperty.name() : __pointProperty
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.CTD_ANON = CTD_ANON


# Complex type {http://www.iho.int/s100gml/5.0}S100_TruncatedDate with content type ELEMENT_ONLY
class S100_TruncatedDate (pyxb.binding.basis.complexTypeDefinition):
    """built in date types from W3C XML schema, implementing S-100 truncated date"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'S100_TruncatedDate')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 755, 2)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.iho.int/s100gml/5.0}gDay uses Python identifier gDay
    __gDay = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'gDay'), 'gDay', '__httpwww_iho_ints100gml5_0_S100_TruncatedDate_httpwww_iho_ints100gml5_0gDay', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 760, 6), )

    
    gDay = property(__gDay.value, __gDay.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}gMonth uses Python identifier gMonth
    __gMonth = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'gMonth'), 'gMonth', '__httpwww_iho_ints100gml5_0_S100_TruncatedDate_httpwww_iho_ints100gml5_0gMonth', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 761, 6), )

    
    gMonth = property(__gMonth.value, __gMonth.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}gYear uses Python identifier gYear
    __gYear = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'gYear'), 'gYear', '__httpwww_iho_ints100gml5_0_S100_TruncatedDate_httpwww_iho_ints100gml5_0gYear', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 762, 6), )

    
    gYear = property(__gYear.value, __gYear.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}gMonthDay uses Python identifier gMonthDay
    __gMonthDay = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'gMonthDay'), 'gMonthDay', '__httpwww_iho_ints100gml5_0_S100_TruncatedDate_httpwww_iho_ints100gml5_0gMonthDay', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 763, 6), )

    
    gMonthDay = property(__gMonthDay.value, __gMonthDay.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}gYearMonth uses Python identifier gYearMonth
    __gYearMonth = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'gYearMonth'), 'gYearMonth', '__httpwww_iho_ints100gml5_0_S100_TruncatedDate_httpwww_iho_ints100gml5_0gYearMonth', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 764, 6), )

    
    gYearMonth = property(__gYearMonth.value, __gYearMonth.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}date uses Python identifier date
    __date = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'date'), 'date', '__httpwww_iho_ints100gml5_0_S100_TruncatedDate_httpwww_iho_ints100gml5_0date', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 765, 6), )

    
    date = property(__date.value, __date.set, None, None)

    _ElementMap.update({
        __gDay.name() : __gDay,
        __gMonth.name() : __gMonth,
        __gYear.name() : __gYear,
        __gMonthDay.name() : __gMonthDay,
        __gYearMonth.name() : __gYearMonth,
        __date.name() : __date
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.S100_TruncatedDate = S100_TruncatedDate
Namespace.addCategoryObject('typeBinding', 'S100_TruncatedDate', S100_TruncatedDate)


# Complex type {http://www.iho.int/s100gml/5.0}AbstractAttributeType with content type EMPTY
class AbstractAttributeType (_ImportedBinding__gml.AbstractGMLType):
    """Abstract type for attributes"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_EMPTY
    _Abstract = True
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractAttributeType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 282, 4)
    _ElementMap = _ImportedBinding__gml.AbstractGMLType._ElementMap.copy()
    _AttributeMap = _ImportedBinding__gml.AbstractGMLType._AttributeMap.copy()
    # Base type is _ImportedBinding__gml.AbstractGMLType
    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.AbstractAttributeType = AbstractAttributeType
Namespace.addCategoryObject('typeBinding', 'AbstractAttributeType', AbstractAttributeType)


# Complex type {http://www.iho.int/s100gml/5.0}AbstractInformationType with content type EMPTY
class AbstractInformationType (_ImportedBinding__gml.AbstractGMLType):
    """Abstract type for an S-100 information type. This is the base type from which domain application schemas derive definitions for their individual information types. """
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_EMPTY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractInformationType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 304, 4)
    _ElementMap = _ImportedBinding__gml.AbstractGMLType._ElementMap.copy()
    _AttributeMap = _ImportedBinding__gml.AbstractGMLType._AttributeMap.copy()
    # Base type is _ImportedBinding__gml.AbstractGMLType
    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.AbstractInformationType = AbstractInformationType
Namespace.addCategoryObject('typeBinding', 'AbstractInformationType', AbstractInformationType)


# Complex type {http://www.iho.int/s100gml/5.0}S100_ArcByCenterPointType with content type ELEMENT_ONLY
class S100_ArcByCenterPointType (_ImportedBinding__gml.AbstractCurveSegmentType):
    """Type for S-100 arc by center point geometry"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'S100_ArcByCenterPointType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 523, 4)
    _ElementMap = _ImportedBinding__gml.AbstractCurveSegmentType._ElementMap.copy()
    _AttributeMap = _ImportedBinding__gml.AbstractCurveSegmentType._AttributeMap.copy()
    # Base type is _ImportedBinding__gml.AbstractCurveSegmentType
    
    # Element {http://www.iho.int/s100gml/5.0}radius uses Python identifier radius
    __radius = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'radius'), 'radius', '__httpwww_iho_ints100gml5_0_S100_ArcByCenterPointType_httpwww_iho_ints100gml5_0radius', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 534, 20), )

    
    radius = property(__radius.value, __radius.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}startAngle uses Python identifier startAngle
    __startAngle = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'startAngle'), 'startAngle', '__httpwww_iho_ints100gml5_0_S100_ArcByCenterPointType_httpwww_iho_ints100gml5_0startAngle', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 535, 20), )

    
    startAngle = property(__startAngle.value, __startAngle.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}angularDistance uses Python identifier angularDistance
    __angularDistance = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'angularDistance'), 'angularDistance', '__httpwww_iho_ints100gml5_0_S100_ArcByCenterPointType_httpwww_iho_ints100gml5_0angularDistance', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 536, 20), )

    
    angularDistance = property(__angularDistance.value, __angularDistance.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}pos uses Python identifier pos
    __pos = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(_Namespace_gml, 'pos'), 'pos', '__httpwww_iho_ints100gml5_0_S100_ArcByCenterPointType_httpwww_opengis_netgml3_2pos', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1), )

    
    pos = property(__pos.value, __pos.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}pointProperty uses Python identifier pointProperty
    __pointProperty = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(_Namespace_gml, 'pointProperty'), 'pointProperty', '__httpwww_iho_ints100gml5_0_S100_ArcByCenterPointType_httpwww_opengis_netgml3_2pointProperty', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1), )

    
    pointProperty = property(__pointProperty.value, __pointProperty.set, None, 'This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.')

    
    # Attribute interpolation uses Python identifier interpolation
    __interpolation = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'interpolation'), 'interpolation', '__httpwww_iho_ints100gml5_0_S100_ArcByCenterPointType_interpolation', _ImportedBinding__gml.CurveInterpolationType, fixed=True, unicode_default='circularArcCenterPointWithRadius')
    __interpolation._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 538, 16)
    __interpolation._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 538, 16)
    
    interpolation = property(__interpolation.value, __interpolation.set, None, None)

    
    # Attribute numDerivativesAtStart inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute numDerivativesAtEnd inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute numDerivativeInterior inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    _ElementMap.update({
        __radius.name() : __radius,
        __startAngle.name() : __startAngle,
        __angularDistance.name() : __angularDistance,
        __pos.name() : __pos,
        __pointProperty.name() : __pointProperty
    })
    _AttributeMap.update({
        __interpolation.name() : __interpolation
    })
_module_typeBindings.S100_ArcByCenterPointType = S100_ArcByCenterPointType
Namespace.addCategoryObject('typeBinding', 'S100_ArcByCenterPointType', S100_ArcByCenterPointType)


# Complex type {http://www.iho.int/s100gml/5.0}S100_GM_SplineCurveType with content type ELEMENT_ONLY
class S100_GM_SplineCurveType (_ImportedBinding__gml.AbstractCurveSegmentType):
    """"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'S100_GM_SplineCurveType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 669, 4)
    _ElementMap = _ImportedBinding__gml.AbstractCurveSegmentType._ElementMap.copy()
    _AttributeMap = _ImportedBinding__gml.AbstractCurveSegmentType._AttributeMap.copy()
    # Base type is _ImportedBinding__gml.AbstractCurveSegmentType
    
    # Element {http://www.iho.int/s100gml/5.0}degree uses Python identifier degree
    __degree = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'degree'), 'degree', '__httpwww_iho_ints100gml5_0_S100_GM_SplineCurveType_httpwww_iho_ints100gml5_0degree', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 683, 20), )

    
    degree = property(__degree.value, __degree.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}knot uses Python identifier knot
    __knot = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'knot'), 'knot', '__httpwww_iho_ints100gml5_0_S100_GM_SplineCurveType_httpwww_iho_ints100gml5_0knot', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 684, 20), )

    
    knot = property(__knot.value, __knot.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}knotSpec uses Python identifier knotSpec
    __knotSpec = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'knotSpec'), 'knotSpec', '__httpwww_iho_ints100gml5_0_S100_GM_SplineCurveType_httpwww_iho_ints100gml5_0knotSpec', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 685, 20), )

    
    knotSpec = property(__knotSpec.value, __knotSpec.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}isRational uses Python identifier isRational
    __isRational = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'isRational'), 'isRational', '__httpwww_iho_ints100gml5_0_S100_GM_SplineCurveType_httpwww_iho_ints100gml5_0isRational', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 686, 20), )

    
    isRational = property(__isRational.value, __isRational.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}pos uses Python identifier pos
    __pos = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(_Namespace_gml, 'pos'), 'pos', '__httpwww_iho_ints100gml5_0_S100_GM_SplineCurveType_httpwww_opengis_netgml3_2pos', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1), )

    
    pos = property(__pos.value, __pos.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}posList uses Python identifier posList
    __posList = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(_Namespace_gml, 'posList'), 'posList', '__httpwww_iho_ints100gml5_0_S100_GM_SplineCurveType_httpwww_opengis_netgml3_2posList', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 490, 1), )

    
    posList = property(__posList.value, __posList.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}pointProperty uses Python identifier pointProperty
    __pointProperty = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(_Namespace_gml, 'pointProperty'), 'pointProperty', '__httpwww_iho_ints100gml5_0_S100_GM_SplineCurveType_httpwww_opengis_netgml3_2pointProperty', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1), )

    
    pointProperty = property(__pointProperty.value, __pointProperty.set, None, 'This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.')

    
    # Attribute interpolation uses Python identifier interpolation
    __interpolation = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'interpolation'), 'interpolation', '__httpwww_iho_ints100gml5_0_S100_GM_SplineCurveType_interpolation', _ImportedBinding__gml.CurveInterpolationType)
    __interpolation._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 688, 16)
    __interpolation._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 688, 16)
    
    interpolation = property(__interpolation.value, __interpolation.set, None, None)

    
    # Attribute numDerivativesAtStart inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute numDerivativesAtEnd inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute numDerivativeInterior inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    _ElementMap.update({
        __degree.name() : __degree,
        __knot.name() : __knot,
        __knotSpec.name() : __knotSpec,
        __isRational.name() : __isRational,
        __pos.name() : __pos,
        __posList.name() : __posList,
        __pointProperty.name() : __pointProperty
    })
    _AttributeMap.update({
        __interpolation.name() : __interpolation
    })
_module_typeBindings.S100_GM_SplineCurveType = S100_GM_SplineCurveType
Namespace.addCategoryObject('typeBinding', 'S100_GM_SplineCurveType', S100_GM_SplineCurveType)


# Complex type {http://www.iho.int/s100gml/5.0}S100_GM_CurveType with content type ELEMENT_ONLY
class S100_GM_CurveType (_ImportedBinding__gml.AbstractCurveSegmentType):
    """"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'S100_GM_CurveType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 716, 4)
    _ElementMap = _ImportedBinding__gml.AbstractCurveSegmentType._ElementMap.copy()
    _AttributeMap = _ImportedBinding__gml.AbstractCurveSegmentType._AttributeMap.copy()
    # Base type is _ImportedBinding__gml.AbstractCurveSegmentType
    
    # Element {http://www.opengis.net/gml/3.2}pos uses Python identifier pos
    __pos = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(_Namespace_gml, 'pos'), 'pos', '__httpwww_iho_ints100gml5_0_S100_GM_CurveType_httpwww_opengis_netgml3_2pos', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1), )

    
    pos = property(__pos.value, __pos.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}posList uses Python identifier posList
    __posList = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(_Namespace_gml, 'posList'), 'posList', '__httpwww_iho_ints100gml5_0_S100_GM_CurveType_httpwww_opengis_netgml3_2posList', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 490, 1), )

    
    posList = property(__posList.value, __posList.set, None, None)

    
    # Element {http://www.opengis.net/gml/3.2}pointProperty uses Python identifier pointProperty
    __pointProperty = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(_Namespace_gml, 'pointProperty'), 'pointProperty', '__httpwww_iho_ints100gml5_0_S100_GM_CurveType_httpwww_opengis_netgml3_2pointProperty', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1), )

    
    pointProperty = property(__pointProperty.value, __pointProperty.set, None, 'This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.')

    
    # Attribute interpolation uses Python identifier interpolation
    __interpolation = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'interpolation'), 'interpolation', '__httpwww_iho_ints100gml5_0_S100_GM_CurveType_interpolation', _ImportedBinding__gml.CurveInterpolationType)
    __interpolation._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 731, 16)
    __interpolation._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 731, 16)
    
    interpolation = property(__interpolation.value, __interpolation.set, None, None)

    
    # Attribute numDerivativesAtStart inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute numDerivativesAtEnd inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute numDerivativeInterior inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    _ElementMap.update({
        __pos.name() : __pos,
        __posList.name() : __posList,
        __pointProperty.name() : __pointProperty
    })
    _AttributeMap.update({
        __interpolation.name() : __interpolation
    })
_module_typeBindings.S100_GM_CurveType = S100_GM_CurveType
Namespace.addCategoryObject('typeBinding', 'S100_GM_CurveType', S100_GM_CurveType)


# Complex type {http://www.iho.int/s100gml/5.0}AbstractFeatureType with content type ELEMENT_ONLY
class AbstractFeatureType (_ImportedBinding__gml.AbstractFeatureType):
    """Abstract type for an S-100 feature. This is the base type from which domain application schemas derive definitions for their individual features. It derives from GML AbstractFeatureType. """
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'AbstractFeatureType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 318, 4)
    _ElementMap = _ImportedBinding__gml.AbstractFeatureType._ElementMap.copy()
    _AttributeMap = _ImportedBinding__gml.AbstractFeatureType._AttributeMap.copy()
    # Base type is _ImportedBinding__gml.AbstractFeatureType
    
    # Element boundedBy ({http://www.opengis.net/gml/3.2}boundedBy) inherited from {http://www.opengis.net/gml/3.2}AbstractFeatureType
    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.AbstractFeatureType = AbstractFeatureType
Namespace.addCategoryObject('typeBinding', 'AbstractFeatureType', AbstractFeatureType)


# Complex type {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType with content type ELEMENT_ONLY
class S100_SpatialAttributeType (pyxb.binding.basis.complexTypeDefinition):
    """S-100 Base type for the geometry of a feature."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'S100_SpatialAttributeType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 334, 4)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.iho.int/s100gml/5.0}maskReference uses Python identifier maskReference
    __maskReference = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'maskReference'), 'maskReference', '__httpwww_iho_ints100gml5_0_S100_SpatialAttributeType_httpwww_iho_ints100gml5_0maskReference', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 339, 12), )

    
    maskReference = property(__maskReference.value, __maskReference.set, None, None)

    
    # Attribute scaleMinimum uses Python identifier scaleMinimum
    __scaleMinimum = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'scaleMinimum'), 'scaleMinimum', '__httpwww_iho_ints100gml5_0_S100_SpatialAttributeType_scaleMinimum', pyxb.binding.datatypes.positiveInteger)
    __scaleMinimum._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 342, 8)
    __scaleMinimum._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 342, 8)
    
    scaleMinimum = property(__scaleMinimum.value, __scaleMinimum.set, None, None)

    
    # Attribute scaleMaximum uses Python identifier scaleMaximum
    __scaleMaximum = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'scaleMaximum'), 'scaleMaximum', '__httpwww_iho_ints100gml5_0_S100_SpatialAttributeType_scaleMaximum', pyxb.binding.datatypes.positiveInteger)
    __scaleMaximum._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 343, 8)
    __scaleMaximum._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 343, 8)
    
    scaleMaximum = property(__scaleMaximum.value, __scaleMaximum.set, None, None)

    
    # Attribute nilReason uses Python identifier nilReason
    __nilReason = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'nilReason'), 'nilReason', '__httpwww_iho_ints100gml5_0_S100_SpatialAttributeType_nilReason', _ImportedBinding__gml.NilReasonType)
    __nilReason._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    __nilReason._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    
    nilReason = property(__nilReason.value, __nilReason.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'type'), 'type', '__httpwww_iho_ints100gml5_0_S100_SpatialAttributeType_httpwww_w3_org1999xlinktype', _ImportedBinding__xlink.typeType, fixed=True, unicode_default='simple')
    __type._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 52, 1)
    __type._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 135, 2)
    
    type = property(__type.value, __type.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}href uses Python identifier href
    __href = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'href'), 'href', '__httpwww_iho_ints100gml5_0_S100_SpatialAttributeType_httpwww_w3_org1999xlinkhref', _ImportedBinding__xlink.hrefType)
    __href._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 65, 1)
    __href._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 136, 2)
    
    href = property(__href.value, __href.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}role uses Python identifier role
    __role = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'role'), 'role', '__httpwww_iho_ints100gml5_0_S100_SpatialAttributeType_httpwww_w3_org1999xlinkrole', _ImportedBinding__xlink.roleType)
    __role._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 71, 1)
    __role._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 137, 2)
    
    role = property(__role.value, __role.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}arcrole uses Python identifier arcrole
    __arcrole = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'arcrole'), 'arcrole', '__httpwww_iho_ints100gml5_0_S100_SpatialAttributeType_httpwww_w3_org1999xlinkarcrole', _ImportedBinding__xlink.arcroleType)
    __arcrole._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 79, 1)
    __arcrole._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 138, 2)
    
    arcrole = property(__arcrole.value, __arcrole.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'title'), 'title', '__httpwww_iho_ints100gml5_0_S100_SpatialAttributeType_httpwww_w3_org1999xlinktitle', _ImportedBinding__xlink.titleAttrType)
    __title._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 87, 1)
    __title._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 139, 2)
    
    title = property(__title.value, __title.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}show uses Python identifier show
    __show = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'show'), 'show', '__httpwww_iho_ints100gml5_0_S100_SpatialAttributeType_httpwww_w3_org1999xlinkshow', _ImportedBinding__xlink.showType)
    __show._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 93, 1)
    __show._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 140, 2)
    
    show = property(__show.value, __show.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}actuate uses Python identifier actuate
    __actuate = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'actuate'), 'actuate', '__httpwww_iho_ints100gml5_0_S100_SpatialAttributeType_httpwww_w3_org1999xlinkactuate', _ImportedBinding__xlink.actuateType)
    __actuate._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 105, 1)
    __actuate._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 141, 2)
    
    actuate = property(__actuate.value, __actuate.set, None, None)

    _ElementMap.update({
        __maskReference.name() : __maskReference
    })
    _AttributeMap.update({
        __scaleMinimum.name() : __scaleMinimum,
        __scaleMaximum.name() : __scaleMaximum,
        __nilReason.name() : __nilReason,
        __type.name() : __type,
        __href.name() : __href,
        __role.name() : __role,
        __arcrole.name() : __arcrole,
        __title.name() : __title,
        __show.name() : __show,
        __actuate.name() : __actuate
    })
_module_typeBindings.S100_SpatialAttributeType = S100_SpatialAttributeType
Namespace.addCategoryObject('typeBinding', 'S100_SpatialAttributeType', S100_SpatialAttributeType)


# Complex type {http://www.iho.int/s100gml/5.0}PolygonPropertyType with content type ELEMENT_ONLY
class PolygonPropertyType (pyxb.binding.basis.complexTypeDefinition):
    """Polygon property using the S-100 polygon type."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'PolygonPropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 512, 4)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.iho.int/s100gml/5.0}Polygon uses Python identifier Polygon
    __Polygon = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'Polygon'), 'Polygon', '__httpwww_iho_ints100gml5_0_PolygonPropertyType_httpwww_iho_ints100gml5_0Polygon', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 507, 4), )

    
    Polygon = property(__Polygon.value, __Polygon.set, None, 'S100 version of polygon type')

    
    # Attribute nilReason uses Python identifier nilReason
    __nilReason = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'nilReason'), 'nilReason', '__httpwww_iho_ints100gml5_0_PolygonPropertyType_nilReason', _ImportedBinding__gml.NilReasonType)
    __nilReason._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    __nilReason._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 194, 2)
    
    nilReason = property(__nilReason.value, __nilReason.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'type'), 'type', '__httpwww_iho_ints100gml5_0_PolygonPropertyType_httpwww_w3_org1999xlinktype', _ImportedBinding__xlink.typeType, fixed=True, unicode_default='simple')
    __type._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 52, 1)
    __type._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 135, 2)
    
    type = property(__type.value, __type.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}href uses Python identifier href
    __href = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'href'), 'href', '__httpwww_iho_ints100gml5_0_PolygonPropertyType_httpwww_w3_org1999xlinkhref', _ImportedBinding__xlink.hrefType)
    __href._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 65, 1)
    __href._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 136, 2)
    
    href = property(__href.value, __href.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}role uses Python identifier role
    __role = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'role'), 'role', '__httpwww_iho_ints100gml5_0_PolygonPropertyType_httpwww_w3_org1999xlinkrole', _ImportedBinding__xlink.roleType)
    __role._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 71, 1)
    __role._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 137, 2)
    
    role = property(__role.value, __role.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}arcrole uses Python identifier arcrole
    __arcrole = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'arcrole'), 'arcrole', '__httpwww_iho_ints100gml5_0_PolygonPropertyType_httpwww_w3_org1999xlinkarcrole', _ImportedBinding__xlink.arcroleType)
    __arcrole._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 79, 1)
    __arcrole._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 138, 2)
    
    arcrole = property(__arcrole.value, __arcrole.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'title'), 'title', '__httpwww_iho_ints100gml5_0_PolygonPropertyType_httpwww_w3_org1999xlinktitle', _ImportedBinding__xlink.titleAttrType)
    __title._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 87, 1)
    __title._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 139, 2)
    
    title = property(__title.value, __title.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}show uses Python identifier show
    __show = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'show'), 'show', '__httpwww_iho_ints100gml5_0_PolygonPropertyType_httpwww_w3_org1999xlinkshow', _ImportedBinding__xlink.showType)
    __show._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 93, 1)
    __show._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 140, 2)
    
    show = property(__show.value, __show.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}actuate uses Python identifier actuate
    __actuate = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(_Namespace_xlink, 'actuate'), 'actuate', '__httpwww_iho_ints100gml5_0_PolygonPropertyType_httpwww_w3_org1999xlinkactuate', _ImportedBinding__xlink.actuateType)
    __actuate._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 105, 1)
    __actuate._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 141, 2)
    
    actuate = property(__actuate.value, __actuate.set, None, None)

    _ElementMap.update({
        __Polygon.name() : __Polygon
    })
    _AttributeMap.update({
        __nilReason.name() : __nilReason,
        __type.name() : __type,
        __href.name() : __href,
        __role.name() : __role,
        __arcrole.name() : __arcrole,
        __title.name() : __title,
        __show.name() : __show,
        __actuate.name() : __actuate
    })
_module_typeBindings.PolygonPropertyType = PolygonPropertyType
Namespace.addCategoryObject('typeBinding', 'PolygonPropertyType', PolygonPropertyType)


# Complex type {http://www.iho.int/s100gml/5.0}S100_CircleByCenterPointType with content type ELEMENT_ONLY
class S100_CircleByCenterPointType (S100_ArcByCenterPointType):
    """Complex type {http://www.iho.int/s100gml/5.0}S100_CircleByCenterPointType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'S100_CircleByCenterPointType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 563, 4)
    _ElementMap = S100_ArcByCenterPointType._ElementMap.copy()
    _AttributeMap = S100_ArcByCenterPointType._AttributeMap.copy()
    # Base type is S100_ArcByCenterPointType
    
    # Element radius ({http://www.iho.int/s100gml/5.0}radius) inherited from {http://www.iho.int/s100gml/5.0}S100_ArcByCenterPointType
    
    # Element startAngle ({http://www.iho.int/s100gml/5.0}startAngle) inherited from {http://www.iho.int/s100gml/5.0}S100_ArcByCenterPointType
    
    # Element {http://www.iho.int/s100gml/5.0}angularDistance uses Python identifier angularDistance
    __angularDistance_ = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'angularDistance'), 'angularDistance', '__httpwww_iho_ints100gml5_0_S100_CircleByCenterPointType_httpwww_iho_ints100gml5_0angularDistance', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 573, 20), )

    
    angularDistance = property(__angularDistance_.value, __angularDistance_.set, None, None)

    
    # Element pos ({http://www.opengis.net/gml/3.2}pos) inherited from {http://www.iho.int/s100gml/5.0}S100_ArcByCenterPointType
    
    # Element pointProperty ({http://www.opengis.net/gml/3.2}pointProperty) inherited from {http://www.iho.int/s100gml/5.0}S100_ArcByCenterPointType
    
    # Attribute interpolation inherited from {http://www.iho.int/s100gml/5.0}S100_ArcByCenterPointType
    
    # Attribute numDerivativesAtStart inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute numDerivativesAtEnd inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute numDerivativeInterior inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    _ElementMap.update({
        __angularDistance_.name() : __angularDistance_
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.S100_CircleByCenterPointType = S100_CircleByCenterPointType
Namespace.addCategoryObject('typeBinding', 'S100_CircleByCenterPointType', S100_CircleByCenterPointType)


# Complex type {http://www.iho.int/s100gml/5.0}S100_GM_PolynomialSplineType with content type ELEMENT_ONLY
class S100_GM_PolynomialSplineType (S100_GM_SplineCurveType):
    """"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'S100_GM_PolynomialSplineType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 697, 4)
    _ElementMap = S100_GM_SplineCurveType._ElementMap.copy()
    _AttributeMap = S100_GM_SplineCurveType._AttributeMap.copy()
    # Base type is S100_GM_SplineCurveType
    
    # Element degree ({http://www.iho.int/s100gml/5.0}degree) inherited from {http://www.iho.int/s100gml/5.0}S100_GM_SplineCurveType
    
    # Element knot ({http://www.iho.int/s100gml/5.0}knot) inherited from {http://www.iho.int/s100gml/5.0}S100_GM_SplineCurveType
    
    # Element knotSpec ({http://www.iho.int/s100gml/5.0}knotSpec) inherited from {http://www.iho.int/s100gml/5.0}S100_GM_SplineCurveType
    
    # Element isRational ({http://www.iho.int/s100gml/5.0}isRational) inherited from {http://www.iho.int/s100gml/5.0}S100_GM_SplineCurveType
    
    # Element {http://www.iho.int/s100gml/5.0}derivativeAtStart uses Python identifier derivativeAtStart
    __derivativeAtStart = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'derivativeAtStart'), 'derivativeAtStart', '__httpwww_iho_ints100gml5_0_S100_GM_PolynomialSplineType_httpwww_iho_ints100gml5_0derivativeAtStart', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 704, 20), )

    
    derivativeAtStart = property(__derivativeAtStart.value, __derivativeAtStart.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}derivativeAtEnd uses Python identifier derivativeAtEnd
    __derivativeAtEnd = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'derivativeAtEnd'), 'derivativeAtEnd', '__httpwww_iho_ints100gml5_0_S100_GM_PolynomialSplineType_httpwww_iho_ints100gml5_0derivativeAtEnd', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 705, 20), )

    
    derivativeAtEnd = property(__derivativeAtEnd.value, __derivativeAtEnd.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}numDerivativeInterior uses Python identifier numDerivativeInterior_
    __numDerivativeInterior_ = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'numDerivativeInterior'), 'numDerivativeInterior_', '__httpwww_iho_ints100gml5_0_S100_GM_PolynomialSplineType_httpwww_iho_ints100gml5_0numDerivativeInterior', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 706, 20), )

    
    numDerivativeInterior_ = property(__numDerivativeInterior_.value, __numDerivativeInterior_.set, None, None)

    
    # Element pos ({http://www.opengis.net/gml/3.2}pos) inherited from {http://www.iho.int/s100gml/5.0}S100_GM_SplineCurveType
    
    # Element posList ({http://www.opengis.net/gml/3.2}posList) inherited from {http://www.iho.int/s100gml/5.0}S100_GM_SplineCurveType
    
    # Element pointProperty ({http://www.opengis.net/gml/3.2}pointProperty) inherited from {http://www.iho.int/s100gml/5.0}S100_GM_SplineCurveType
    
    # Attribute interpolation inherited from {http://www.iho.int/s100gml/5.0}S100_GM_SplineCurveType
    
    # Attribute numDerivativesAtStart inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute numDerivativesAtEnd inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    
    # Attribute numDerivativeInterior inherited from {http://www.opengis.net/gml/3.2}AbstractCurveSegmentType
    _ElementMap.update({
        __derivativeAtStart.name() : __derivativeAtStart,
        __derivativeAtEnd.name() : __derivativeAtEnd,
        __numDerivativeInterior_.name() : __numDerivativeInterior_
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.S100_GM_PolynomialSplineType = S100_GM_PolynomialSplineType
Namespace.addCategoryObject('typeBinding', 'S100_GM_PolynomialSplineType', S100_GM_PolynomialSplineType)


# Complex type {http://www.iho.int/s100gml/5.0}DatasetType with content type ELEMENT_ONLY
class DatasetType (_ImportedBinding__gml.AbstractFeatureType):
    """Dataset element for dataset as "GML document" """
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'DatasetType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 771, 2)
    _ElementMap = _ImportedBinding__gml.AbstractFeatureType._ElementMap.copy()
    _AttributeMap = _ImportedBinding__gml.AbstractFeatureType._AttributeMap.copy()
    # Base type is _ImportedBinding__gml.AbstractFeatureType
    
    # Element {http://www.iho.int/s100gml/5.0}Point uses Python identifier Point
    __Point = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'Point'), 'Point', '__httpwww_iho_ints100gml5_0_DatasetType_httpwww_iho_ints100gml5_0Point', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 359, 4), )

    
    Point = property(__Point.value, __Point.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}MultiPoint uses Python identifier MultiPoint
    __MultiPoint = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'MultiPoint'), 'MultiPoint', '__httpwww_iho_ints100gml5_0_DatasetType_httpwww_iho_ints100gml5_0MultiPoint', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 389, 4), )

    
    MultiPoint = property(__MultiPoint.value, __MultiPoint.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}Curve uses Python identifier Curve
    __Curve = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'Curve'), 'Curve', '__httpwww_iho_ints100gml5_0_DatasetType_httpwww_iho_ints100gml5_0Curve', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 418, 4), )

    
    Curve = property(__Curve.value, __Curve.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}CompositeCurve uses Python identifier CompositeCurve
    __CompositeCurve = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'CompositeCurve'), 'CompositeCurve', '__httpwww_iho_ints100gml5_0_DatasetType_httpwww_iho_ints100gml5_0CompositeCurve', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 448, 4), )

    
    CompositeCurve = property(__CompositeCurve.value, __CompositeCurve.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}OrientableCurve uses Python identifier OrientableCurve
    __OrientableCurve = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'OrientableCurve'), 'OrientableCurve', '__httpwww_iho_ints100gml5_0_DatasetType_httpwww_iho_ints100gml5_0OrientableCurve', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 450, 4), )

    
    OrientableCurve = property(__OrientableCurve.value, __OrientableCurve.set, None, 'S-100 orientable curve is the same as GML orientable curve. Added for consistency.')

    
    # Element {http://www.iho.int/s100gml/5.0}Surface uses Python identifier Surface
    __Surface = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'Surface'), 'Surface', '__httpwww_iho_ints100gml5_0_DatasetType_httpwww_iho_ints100gml5_0Surface', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 479, 4), )

    
    Surface = property(__Surface.value, __Surface.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}Polygon uses Python identifier Polygon
    __Polygon = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'Polygon'), 'Polygon', '__httpwww_iho_ints100gml5_0_DatasetType_httpwww_iho_ints100gml5_0Polygon', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 507, 4), )

    
    Polygon = property(__Polygon.value, __Polygon.set, None, 'S100 version of polygon type')

    
    # Element {http://www.iho.int/s100gml/5.0}DatasetIdentificationInformation uses Python identifier DatasetIdentificationInformation
    __DatasetIdentificationInformation = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'DatasetIdentificationInformation'), 'DatasetIdentificationInformation', '__httpwww_iho_ints100gml5_0_DatasetType_httpwww_iho_ints100gml5_0DatasetIdentificationInformation', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 778, 10), )

    
    DatasetIdentificationInformation = property(__DatasetIdentificationInformation.value, __DatasetIdentificationInformation.set, None, 'Dataset identification information')

    
    # Element boundedBy ({http://www.opengis.net/gml/3.2}boundedBy) inherited from {http://www.opengis.net/gml/3.2}AbstractFeatureType
    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    _ElementMap.update({
        __Point.name() : __Point,
        __MultiPoint.name() : __MultiPoint,
        __Curve.name() : __Curve,
        __CompositeCurve.name() : __CompositeCurve,
        __OrientableCurve.name() : __OrientableCurve,
        __Surface.name() : __Surface,
        __Polygon.name() : __Polygon,
        __DatasetIdentificationInformation.name() : __DatasetIdentificationInformation
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.DatasetType = DatasetType
Namespace.addCategoryObject('typeBinding', 'DatasetType', DatasetType)


# Complex type {http://www.iho.int/s100gml/5.0}PointPropertyType with content type ELEMENT_ONLY
class PointPropertyType (S100_SpatialAttributeType):
    """Point property using the S-100 point type."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'PointPropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 362, 4)
    _ElementMap = S100_SpatialAttributeType._ElementMap.copy()
    _AttributeMap = S100_SpatialAttributeType._AttributeMap.copy()
    # Base type is S100_SpatialAttributeType
    
    # Element maskReference ({http://www.iho.int/s100gml/5.0}maskReference) inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Element {http://www.iho.int/s100gml/5.0}Point uses Python identifier Point
    __Point = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'Point'), 'Point', '__httpwww_iho_ints100gml5_0_PointPropertyType_httpwww_iho_ints100gml5_0Point', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 359, 4), )

    
    Point = property(__Point.value, __Point.set, None, None)

    
    # Attribute scaleMinimum inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute scaleMaximum inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute nilReason inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute type inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute href inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute role inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute arcrole inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute title inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute show inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute actuate inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    _ElementMap.update({
        __Point.name() : __Point
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.PointPropertyType = PointPropertyType
Namespace.addCategoryObject('typeBinding', 'PointPropertyType', PointPropertyType)


# Complex type {http://www.iho.int/s100gml/5.0}MultiPointPropertyType with content type ELEMENT_ONLY
class MultiPointPropertyType (S100_SpatialAttributeType):
    """MultiPoint property using the S-100 multipoint type."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'MultiPointPropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 391, 4)
    _ElementMap = S100_SpatialAttributeType._ElementMap.copy()
    _AttributeMap = S100_SpatialAttributeType._AttributeMap.copy()
    # Base type is S100_SpatialAttributeType
    
    # Element maskReference ({http://www.iho.int/s100gml/5.0}maskReference) inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Element {http://www.iho.int/s100gml/5.0}MultiPoint uses Python identifier MultiPoint
    __MultiPoint = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'MultiPoint'), 'MultiPoint', '__httpwww_iho_ints100gml5_0_MultiPointPropertyType_httpwww_iho_ints100gml5_0MultiPoint', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 389, 4), )

    
    MultiPoint = property(__MultiPoint.value, __MultiPoint.set, None, None)

    
    # Attribute scaleMinimum inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute scaleMaximum inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute nilReason inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute type inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute href inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute role inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute arcrole inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute title inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute show inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute actuate inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    _ElementMap.update({
        __MultiPoint.name() : __MultiPoint
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.MultiPointPropertyType = MultiPointPropertyType
Namespace.addCategoryObject('typeBinding', 'MultiPointPropertyType', MultiPointPropertyType)


# Complex type {http://www.iho.int/s100gml/5.0}CurvePropertyType with content type ELEMENT_ONLY
class CurvePropertyType (S100_SpatialAttributeType):
    """Curve property using the S-100 curve type."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'CurvePropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 420, 4)
    _ElementMap = S100_SpatialAttributeType._ElementMap.copy()
    _AttributeMap = S100_SpatialAttributeType._AttributeMap.copy()
    # Base type is S100_SpatialAttributeType
    
    # Element maskReference ({http://www.iho.int/s100gml/5.0}maskReference) inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Element {http://www.iho.int/s100gml/5.0}Curve uses Python identifier Curve
    __Curve = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'Curve'), 'Curve', '__httpwww_iho_ints100gml5_0_CurvePropertyType_httpwww_iho_ints100gml5_0Curve', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 418, 4), )

    
    Curve = property(__Curve.value, __Curve.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}CompositeCurve uses Python identifier CompositeCurve
    __CompositeCurve = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'CompositeCurve'), 'CompositeCurve', '__httpwww_iho_ints100gml5_0_CurvePropertyType_httpwww_iho_ints100gml5_0CompositeCurve', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 448, 4), )

    
    CompositeCurve = property(__CompositeCurve.value, __CompositeCurve.set, None, None)

    
    # Element {http://www.iho.int/s100gml/5.0}OrientableCurve uses Python identifier OrientableCurve
    __OrientableCurve = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'OrientableCurve'), 'OrientableCurve', '__httpwww_iho_ints100gml5_0_CurvePropertyType_httpwww_iho_ints100gml5_0OrientableCurve', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 450, 4), )

    
    OrientableCurve = property(__OrientableCurve.value, __OrientableCurve.set, None, 'S-100 orientable curve is the same as GML orientable curve. Added for consistency.')

    
    # Attribute scaleMinimum inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute scaleMaximum inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute nilReason inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute type inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute href inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute role inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute arcrole inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute title inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute show inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute actuate inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    _ElementMap.update({
        __Curve.name() : __Curve,
        __CompositeCurve.name() : __CompositeCurve,
        __OrientableCurve.name() : __OrientableCurve
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.CurvePropertyType = CurvePropertyType
Namespace.addCategoryObject('typeBinding', 'CurvePropertyType', CurvePropertyType)


# Complex type {http://www.iho.int/s100gml/5.0}SurfacePropertyType with content type ELEMENT_ONLY
class SurfacePropertyType (S100_SpatialAttributeType):
    """Surface property using the S-100 surface type."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'SurfacePropertyType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 481, 4)
    _ElementMap = S100_SpatialAttributeType._ElementMap.copy()
    _AttributeMap = S100_SpatialAttributeType._AttributeMap.copy()
    # Base type is S100_SpatialAttributeType
    
    # Element maskReference ({http://www.iho.int/s100gml/5.0}maskReference) inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Element {http://www.iho.int/s100gml/5.0}Surface uses Python identifier Surface
    __Surface = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'Surface'), 'Surface', '__httpwww_iho_ints100gml5_0_SurfacePropertyType_httpwww_iho_ints100gml5_0Surface', False, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 479, 4), )

    
    Surface = property(__Surface.value, __Surface.set, None, None)

    
    # Attribute scaleMinimum inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute scaleMaximum inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute nilReason inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute type inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute href inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute role inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute arcrole inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute title inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute show inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    
    # Attribute actuate inherited from {http://www.iho.int/s100gml/5.0}S100_SpatialAttributeType
    _ElementMap.update({
        __Surface.name() : __Surface
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.SurfacePropertyType = SurfacePropertyType
Namespace.addCategoryObject('typeBinding', 'SurfacePropertyType', SurfacePropertyType)


# Complex type {http://www.iho.int/s100gml/5.0}PointType with content type ELEMENT_ONLY
class PointType (_ImportedBinding__gml.PointType):
    """S-100 point type adds an information association to the GML spatial type Point"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'PointType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 347, 4)
    _ElementMap = _ImportedBinding__gml.PointType._ElementMap.copy()
    _AttributeMap = _ImportedBinding__gml.PointType._AttributeMap.copy()
    # Base type is _ImportedBinding__gml.PointType
    
    # Element {http://www.iho.int/s100gml/5.0}informationAssociation uses Python identifier informationAssociation
    __informationAssociation = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation'), 'informationAssociation', '__httpwww_iho_ints100gml5_0_PointType_httpwww_iho_ints100gml5_0informationAssociation', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 302, 4), )

    
    informationAssociation = property(__informationAssociation.value, __informationAssociation.set, None, None)

    
    # Element pos ({http://www.opengis.net/gml/3.2}pos) inherited from {http://www.opengis.net/gml/3.2}PointType
    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        __informationAssociation.name() : __informationAssociation
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.PointType = PointType
Namespace.addCategoryObject('typeBinding', 'PointType', PointType)


# Complex type {http://www.iho.int/s100gml/5.0}MultiPointType with content type ELEMENT_ONLY
class MultiPointType (_ImportedBinding__gml.MultiPointType):
    """S-100 multipoint type adds an information association to the GML spatial type MultiPoint"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'MultiPointType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 377, 4)
    _ElementMap = _ImportedBinding__gml.MultiPointType._ElementMap.copy()
    _AttributeMap = _ImportedBinding__gml.MultiPointType._AttributeMap.copy()
    # Base type is _ImportedBinding__gml.MultiPointType
    
    # Element {http://www.iho.int/s100gml/5.0}informationAssociation uses Python identifier informationAssociation
    __informationAssociation = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation'), 'informationAssociation', '__httpwww_iho_ints100gml5_0_MultiPointType_httpwww_iho_ints100gml5_0informationAssociation', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 302, 4), )

    
    informationAssociation = property(__informationAssociation.value, __informationAssociation.set, None, None)

    
    # Element pointMember ({http://www.opengis.net/gml/3.2}pointMember) inherited from {http://www.opengis.net/gml/3.2}MultiPointType
    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute aggregationType inherited from {http://www.opengis.net/gml/3.2}AbstractGeometricAggregateType
    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        __informationAssociation.name() : __informationAssociation
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.MultiPointType = MultiPointType
Namespace.addCategoryObject('typeBinding', 'MultiPointType', MultiPointType)


# Complex type {http://www.iho.int/s100gml/5.0}CurveType with content type ELEMENT_ONLY
class CurveType (_ImportedBinding__gml.CurveType):
    """S-100 curve type adds an information association to the GML spatial type Curve"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'CurveType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 406, 4)
    _ElementMap = _ImportedBinding__gml.CurveType._ElementMap.copy()
    _AttributeMap = _ImportedBinding__gml.CurveType._AttributeMap.copy()
    # Base type is _ImportedBinding__gml.CurveType
    
    # Element {http://www.iho.int/s100gml/5.0}informationAssociation uses Python identifier informationAssociation
    __informationAssociation = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation'), 'informationAssociation', '__httpwww_iho_ints100gml5_0_CurveType_httpwww_iho_ints100gml5_0informationAssociation', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 302, 4), )

    
    informationAssociation = property(__informationAssociation.value, __informationAssociation.set, None, None)

    
    # Element segments ({http://www.opengis.net/gml/3.2}segments) inherited from {http://www.opengis.net/gml/3.2}CurveType
    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        __informationAssociation.name() : __informationAssociation
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.CurveType = CurveType
Namespace.addCategoryObject('typeBinding', 'CurveType', CurveType)


# Complex type {http://www.iho.int/s100gml/5.0}CompositeCurveType with content type ELEMENT_ONLY
class CompositeCurveType (_ImportedBinding__gml.CompositeCurveType):
    """S-100 composite curve type adds an information association to the GML spatial type CompositeCurve"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'CompositeCurveType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 436, 4)
    _ElementMap = _ImportedBinding__gml.CompositeCurveType._ElementMap.copy()
    _AttributeMap = _ImportedBinding__gml.CompositeCurveType._AttributeMap.copy()
    # Base type is _ImportedBinding__gml.CompositeCurveType
    
    # Element {http://www.iho.int/s100gml/5.0}informationAssociation uses Python identifier informationAssociation
    __informationAssociation = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation'), 'informationAssociation', '__httpwww_iho_ints100gml5_0_CompositeCurveType_httpwww_iho_ints100gml5_0informationAssociation', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 302, 4), )

    
    informationAssociation = property(__informationAssociation.value, __informationAssociation.set, None, None)

    
    # Element curveMember ({http://www.opengis.net/gml/3.2}curveMember) inherited from {http://www.opengis.net/gml/3.2}CompositeCurveType
    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute aggregationType inherited from {http://www.opengis.net/gml/3.2}CompositeCurveType
    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        __informationAssociation.name() : __informationAssociation
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.CompositeCurveType = CompositeCurveType
Namespace.addCategoryObject('typeBinding', 'CompositeCurveType', CompositeCurveType)


# Complex type {http://www.iho.int/s100gml/5.0}SurfaceType with content type ELEMENT_ONLY
class SurfaceType (_ImportedBinding__gml.SurfaceType):
    """S-100 surface type adds an information association to the GML spatial type Surface"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'SurfaceType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 467, 4)
    _ElementMap = _ImportedBinding__gml.SurfaceType._ElementMap.copy()
    _AttributeMap = _ImportedBinding__gml.SurfaceType._AttributeMap.copy()
    # Base type is _ImportedBinding__gml.SurfaceType
    
    # Element {http://www.iho.int/s100gml/5.0}informationAssociation uses Python identifier informationAssociation
    __informationAssociation = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation'), 'informationAssociation', '__httpwww_iho_ints100gml5_0_SurfaceType_httpwww_iho_ints100gml5_0informationAssociation', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 302, 4), )

    
    informationAssociation = property(__informationAssociation.value, __informationAssociation.set, None, None)

    
    # Element patches ({http://www.opengis.net/gml/3.2}patches) inherited from {http://www.opengis.net/gml/3.2}SurfaceType
    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        __informationAssociation.name() : __informationAssociation
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.SurfaceType = SurfaceType
Namespace.addCategoryObject('typeBinding', 'SurfaceType', SurfaceType)


# Complex type {http://www.iho.int/s100gml/5.0}PolygonType with content type ELEMENT_ONLY
class PolygonType (_ImportedBinding__gml.PolygonType):
    """S-100 polygon type adds an information association to the GML spatial type Polygon"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'PolygonType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 495, 4)
    _ElementMap = _ImportedBinding__gml.PolygonType._ElementMap.copy()
    _AttributeMap = _ImportedBinding__gml.PolygonType._AttributeMap.copy()
    # Base type is _ImportedBinding__gml.PolygonType
    
    # Element {http://www.iho.int/s100gml/5.0}informationAssociation uses Python identifier informationAssociation
    __informationAssociation = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation'), 'informationAssociation', '__httpwww_iho_ints100gml5_0_PolygonType_httpwww_iho_ints100gml5_0informationAssociation', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 302, 4), )

    
    informationAssociation = property(__informationAssociation.value, __informationAssociation.set, None, None)

    
    # Element exterior ({http://www.opengis.net/gml/3.2}exterior) inherited from {http://www.opengis.net/gml/3.2}PolygonType
    
    # Element interior ({http://www.opengis.net/gml/3.2}interior) inherited from {http://www.opengis.net/gml/3.2}PolygonType
    
    # Attribute id inherited from {http://www.opengis.net/gml/3.2}AbstractGMLType
    
    # Attribute srsName inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    
    # Attribute srsDimension inherited from {http://www.opengis.net/gml/3.2}AbstractGeometryType
    _ElementMap.update({
        __informationAssociation.name() : __informationAssociation
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.PolygonType = PolygonType
Namespace.addCategoryObject('typeBinding', 'PolygonType', PolygonType)


complianceLevel = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'complianceLevel'), STD_ANON, documentation='\n            Level 1 = \n            Level 2 = \n         ', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 793, 1))
Namespace.addCategoryObject('elementBinding', complianceLevel.name().localName(), complianceLevel)

S100_ArcByCenterPoint = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'S100_ArcByCenterPoint'), S100_ArcByCenterPointType, documentation='This variant of the arc requires that the points on the arc shall be\n                computed instead of storing the coordinates directly. The single control point is\n                the center point of the arc. The other parameters are the radius, the bearing at start,\n                and the angle from the start to the end relative to the center of the arc. This\n                representation can be used only in 2D. The element radius specifies the radius of\n                the arc. The element startAngle specifies the bearing of the arc at the start. The\n                element angularDistance specifies the difference in bearing from the start to the end.\n                The sign of angularDistance specifies the direction of the arc, positive values mean the\n                direction is clockwise from start to end looking down from a point vertically above the\n                center of the arc.\n                Drawing starts at a bearing of 0.0 from the ray pointing due north from the center. If the\n                center is at a pole the reference direction follows the prime meridian starting from the pole.\n                The interpolation is fixed as "circularArcCenterPointWithRadius". Since this type always\n                describes a single arc, the GML attribute "numArc" is not used.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 544, 4))
Namespace.addCategoryObject('elementBinding', S100_ArcByCenterPoint.name().localName(), S100_ArcByCenterPoint)

S100_GM_SplineCurve = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'S100_GM_SplineCurve'), S100_GM_SplineCurveType, documentation='', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 692, 4))
Namespace.addCategoryObject('elementBinding', S100_GM_SplineCurve.name().localName(), S100_GM_SplineCurve)

S100_GM_Curve = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'S100_GM_Curve'), S100_GM_CurveType, documentation='', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 735, 4))
Namespace.addCategoryObject('elementBinding', S100_GM_Curve.name().localName(), S100_GM_Curve)

informationAssociation = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation'), _ImportedBinding__gml.ReferenceType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 302, 4))
Namespace.addCategoryObject('elementBinding', informationAssociation.name().localName(), informationAssociation)

polygonProperty = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'polygonProperty'), PolygonPropertyType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 521, 4))
Namespace.addCategoryObject('elementBinding', polygonProperty.name().localName(), polygonProperty)

S100_CircleByCenterPoint = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'S100_CircleByCenterPoint'), S100_CircleByCenterPointType, documentation='An S100_CircleByCenterPoint is an S100_ArcByCenterPoint with angular\n                distance +/- 360.0 degrees to form a full circle.\n                Angular distance is assumed to be +360.0 degrees if it is missing.\n                The interpolation is fixed as "circularArcCenterPointWithRadius". This representation\n                can be used only in 2D.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 585, 4))
Namespace.addCategoryObject('elementBinding', S100_CircleByCenterPoint.name().localName(), S100_CircleByCenterPoint)

S100_GM_PolynomialSpline = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'S100_GM_PolynomialSpline'), S100_GM_PolynomialSplineType, documentation='', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 711, 4))
Namespace.addCategoryObject('elementBinding', S100_GM_PolynomialSpline.name().localName(), S100_GM_PolynomialSpline)

pointProperty = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'pointProperty'), PointPropertyType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 375, 4))
Namespace.addCategoryObject('elementBinding', pointProperty.name().localName(), pointProperty)

multiPointProperty = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'multiPointProperty'), MultiPointPropertyType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 404, 4))
Namespace.addCategoryObject('elementBinding', multiPointProperty.name().localName(), multiPointProperty)

curveProperty = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'curveProperty'), CurvePropertyType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 433, 4))
Namespace.addCategoryObject('elementBinding', curveProperty.name().localName(), curveProperty)

surfaceProperty = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'surfaceProperty'), SurfacePropertyType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 493, 4))
Namespace.addCategoryObject('elementBinding', surfaceProperty.name().localName(), surfaceProperty)

Point = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Point'), PointType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 359, 4))
Namespace.addCategoryObject('elementBinding', Point.name().localName(), Point)

MultiPoint = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'MultiPoint'), MultiPointType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 389, 4))
Namespace.addCategoryObject('elementBinding', MultiPoint.name().localName(), MultiPoint)

OrientableCurve = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'OrientableCurve'), _ImportedBinding__gml.OrientableCurveType, documentation='S-100 orientable curve is the same as GML orientable curve. Added for consistency.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 450, 4))
Namespace.addCategoryObject('elementBinding', OrientableCurve.name().localName(), OrientableCurve)

Curve = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Curve'), CurveType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 418, 4))
Namespace.addCategoryObject('elementBinding', Curve.name().localName(), Curve)

CompositeCurve = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'CompositeCurve'), CompositeCurveType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 448, 4))
Namespace.addCategoryObject('elementBinding', CompositeCurve.name().localName(), CompositeCurve)

Surface = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Surface'), SurfaceType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 479, 4))
Namespace.addCategoryObject('elementBinding', Surface.name().localName(), Surface)

Polygon = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Polygon'), PolygonType, documentation='S100 version of polygon type', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 507, 4))
Namespace.addCategoryObject('elementBinding', Polygon.name().localName(), Polygon)



DataSetIdentificationType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'encodingSpecification'), pyxb.binding.datatypes.string, scope=DataSetIdentificationType, documentation='Encoding specification that defines the encoding.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 214, 12), fixed=True, unicode_default='S-100 Part 10b'))

DataSetIdentificationType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'encodingSpecificationEdition'), pyxb.binding.datatypes.string, scope=DataSetIdentificationType, documentation='Edition of the encoding specification', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 219, 12), fixed=True, unicode_default='1.0'))

DataSetIdentificationType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'productIdentifier'), pyxb.binding.datatypes.string, scope=DataSetIdentificationType, documentation='Unique identifier of the data product as specified in the product specification', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 224, 12)))

DataSetIdentificationType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'productEdition'), pyxb.binding.datatypes.string, scope=DataSetIdentificationType, documentation='Edition of the product specification', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 229, 12)))

DataSetIdentificationType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'applicationProfile'), pyxb.binding.datatypes.string, scope=DataSetIdentificationType, documentation='Identifier that specifies a profile within the data product', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 234, 12)))

DataSetIdentificationType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'datasetFileIdentifier'), pyxb.binding.datatypes.string, scope=DataSetIdentificationType, documentation='The file identifier of the dataset', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 239, 12)))

DataSetIdentificationType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'datasetTitle'), pyxb.binding.datatypes.string, scope=DataSetIdentificationType, documentation='The title of the dataset', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 244, 12)))

DataSetIdentificationType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'datasetReferenceDate'), pyxb.binding.datatypes.date, scope=DataSetIdentificationType, documentation='The reference date of the dataset', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 249, 12)))

DataSetIdentificationType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'datasetLanguage'), ISO_639_2, scope=DataSetIdentificationType, documentation='The (primary) language used in this dataset', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 254, 12), unicode_default='eng'))

DataSetIdentificationType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'datasetAbstract'), pyxb.binding.datatypes.string, scope=DataSetIdentificationType, documentation='The abstract of the dataset', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 259, 12)))

DataSetIdentificationType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'datasetTopicCategory'), MD_TopicCategoryCode, scope=DataSetIdentificationType, documentation='A set of topic categories', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 264, 12)))

DataSetIdentificationType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'datasetPurpose'), datasetPurposeType, scope=DataSetIdentificationType, documentation='base or update', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 269, 12)))

DataSetIdentificationType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'updateNumber'), pyxb.binding.datatypes.nonNegativeInteger, scope=DataSetIdentificationType, documentation='Update Number, 0 for a Base dataset', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 274, 12)))

def _BuildAutomaton ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton
    del _BuildAutomaton
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 259, 12))
    counters.add(cc_0)
    states = []
    final_update = None
    symbol = pyxb.binding.content.ElementUse(DataSetIdentificationType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'encodingSpecification')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 214, 12))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(DataSetIdentificationType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'encodingSpecificationEdition')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 219, 12))
    st_1 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(DataSetIdentificationType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'productIdentifier')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 224, 12))
    st_2 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(DataSetIdentificationType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'productEdition')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 229, 12))
    st_3 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_3)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(DataSetIdentificationType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'applicationProfile')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 234, 12))
    st_4 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_4)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(DataSetIdentificationType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'datasetFileIdentifier')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 239, 12))
    st_5 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_5)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(DataSetIdentificationType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'datasetTitle')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 244, 12))
    st_6 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_6)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(DataSetIdentificationType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'datasetReferenceDate')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 249, 12))
    st_7 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_7)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(DataSetIdentificationType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'datasetLanguage')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 254, 12))
    st_8 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_8)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(DataSetIdentificationType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'datasetAbstract')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 259, 12))
    st_9 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_9)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(DataSetIdentificationType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'datasetTopicCategory')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 264, 12))
    st_10 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_10)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(DataSetIdentificationType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'datasetPurpose')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 269, 12))
    st_11 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_11)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(DataSetIdentificationType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'updateNumber')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 274, 12))
    st_12 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_12)
    transitions = []
    transitions.append(fac.Transition(st_1, [
         ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_2, [
         ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_3, [
         ]))
    st_2._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_4, [
         ]))
    st_3._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_5, [
         ]))
    st_4._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_6, [
         ]))
    st_5._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_7, [
         ]))
    st_6._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_8, [
         ]))
    st_7._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_9, [
         ]))
    transitions.append(fac.Transition(st_10, [
         ]))
    st_8._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_9, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_10, [
        fac.UpdateInstruction(cc_0, False) ]))
    st_9._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_10, [
         ]))
    transitions.append(fac.Transition(st_11, [
         ]))
    st_10._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_12, [
         ]))
    st_11._set_transitionSet(transitions)
    transitions = []
    st_12._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
DataSetIdentificationType._Automaton = _BuildAutomaton()




S100_GM_KnotType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'value'), pyxb.binding.datatypes.double, scope=S100_GM_KnotType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 629, 12)))

S100_GM_KnotType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'multiplicity'), pyxb.binding.datatypes.nonNegativeInteger, scope=S100_GM_KnotType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 630, 12)))

def _BuildAutomaton_ ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_
    del _BuildAutomaton_
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_GM_KnotType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'value')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 629, 12))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(S100_GM_KnotType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'multiplicity')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 630, 12))
    st_1 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    transitions = []
    transitions.append(fac.Transition(st_1, [
         ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    st_1._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
S100_GM_KnotType._Automaton = _BuildAutomaton_()




KnotPropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Knot'), S100_GM_KnotType, scope=KnotPropertyType, documentation='A knot is a breakpoint on a piecewise spline curve.\n                        value is the value of the parameter at the knot of the spline (see ISO 19107:2003, 6.4.24.2).\n                        multiplicity is the multiplicity of this knot used in the definition of the spline (with the same weight).\n                        weight is the value of the averaging weight used for this knot of the spline.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 638, 12)))

def _BuildAutomaton_2 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_2
    del _BuildAutomaton_2
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(KnotPropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'Knot')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 638, 12))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
KnotPropertyType._Automaton = _BuildAutomaton_2()




VectorType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'origin'), CTD_ANON, scope=VectorType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 653, 12)))

VectorType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'dimension'), pyxb.binding.datatypes.nonNegativeInteger, scope=VectorType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 661, 12)))

VectorType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'offset'), _ImportedBinding__gml.doubleList, scope=VectorType, documentation='The number of values must be the same as "dimension" value', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 662, 12)))

def _BuildAutomaton_3 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_3
    del _BuildAutomaton_3
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = None
    symbol = pyxb.binding.content.ElementUse(VectorType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'origin')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 653, 12))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(VectorType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'dimension')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 661, 12))
    st_1 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(VectorType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'offset')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 662, 12))
    st_2 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    transitions = []
    transitions.append(fac.Transition(st_1, [
         ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_2, [
         ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    st_2._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
VectorType._Automaton = _BuildAutomaton_3()




CTD_ANON._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(_Namespace_gml, 'pos'), _ImportedBinding__gml.DirectPositionType, scope=CTD_ANON, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1)))

CTD_ANON._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(_Namespace_gml, 'pointProperty'), _ImportedBinding__gml.PointPropertyType, scope=CTD_ANON, documentation='This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1)))

def _BuildAutomaton_4 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_4
    del _BuildAutomaton_4
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(CTD_ANON._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'pos')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 656, 24))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(CTD_ANON._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'pointProperty')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 657, 24))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    transitions = []
    st_0._set_transitionSet(transitions)
    transitions = []
    st_1._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
CTD_ANON._Automaton = _BuildAutomaton_4()




S100_TruncatedDate._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'gDay'), pyxb.binding.datatypes.gDay, scope=S100_TruncatedDate, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 760, 6)))

S100_TruncatedDate._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'gMonth'), pyxb.binding.datatypes.gMonth, scope=S100_TruncatedDate, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 761, 6)))

S100_TruncatedDate._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'gYear'), pyxb.binding.datatypes.gYear, scope=S100_TruncatedDate, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 762, 6)))

S100_TruncatedDate._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'gMonthDay'), pyxb.binding.datatypes.gMonthDay, scope=S100_TruncatedDate, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 763, 6)))

S100_TruncatedDate._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'gYearMonth'), pyxb.binding.datatypes.gYearMonth, scope=S100_TruncatedDate, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 764, 6)))

S100_TruncatedDate._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'date'), pyxb.binding.datatypes.date, scope=S100_TruncatedDate, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 765, 6)))

def _BuildAutomaton_5 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_5
    del _BuildAutomaton_5
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(S100_TruncatedDate._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'gDay')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 760, 6))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(S100_TruncatedDate._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'gMonth')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 761, 6))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(S100_TruncatedDate._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'gYear')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 762, 6))
    st_2 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(S100_TruncatedDate._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'gMonthDay')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 763, 6))
    st_3 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_3)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(S100_TruncatedDate._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'gYearMonth')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 764, 6))
    st_4 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_4)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(S100_TruncatedDate._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'date')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 765, 6))
    st_5 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_5)
    transitions = []
    st_0._set_transitionSet(transitions)
    transitions = []
    st_1._set_transitionSet(transitions)
    transitions = []
    st_2._set_transitionSet(transitions)
    transitions = []
    st_3._set_transitionSet(transitions)
    transitions = []
    st_4._set_transitionSet(transitions)
    transitions = []
    st_5._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
S100_TruncatedDate._Automaton = _BuildAutomaton_5()




S100_ArcByCenterPointType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'radius'), _ImportedBinding__gml.LengthType, scope=S100_ArcByCenterPointType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 534, 20)))

S100_ArcByCenterPointType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'startAngle'), BearingType, scope=S100_ArcByCenterPointType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 535, 20)))

S100_ArcByCenterPointType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'angularDistance'), PlusOrMinus360Degrees, scope=S100_ArcByCenterPointType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 536, 20)))

S100_ArcByCenterPointType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(_Namespace_gml, 'pos'), _ImportedBinding__gml.DirectPositionType, scope=S100_ArcByCenterPointType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1)))

S100_ArcByCenterPointType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(_Namespace_gml, 'pointProperty'), _ImportedBinding__gml.PointPropertyType, scope=S100_ArcByCenterPointType, documentation='This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1)))

def _BuildAutomaton_6 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_6
    del _BuildAutomaton_6
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 535, 20))
    counters.add(cc_0)
    cc_1 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 536, 20))
    counters.add(cc_1)
    states = []
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_ArcByCenterPointType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'pos')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 531, 24))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_ArcByCenterPointType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'pointProperty')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 532, 24))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(S100_ArcByCenterPointType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'radius')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 534, 20))
    st_2 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(S100_ArcByCenterPointType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'startAngle')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 535, 20))
    st_3 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_3)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(S100_ArcByCenterPointType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'angularDistance')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 536, 20))
    st_4 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_4)
    transitions = []
    transitions.append(fac.Transition(st_2, [
         ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_2, [
         ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_3, [
         ]))
    transitions.append(fac.Transition(st_4, [
         ]))
    st_2._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_4, [
        fac.UpdateInstruction(cc_0, False) ]))
    st_3._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_4, [
        fac.UpdateInstruction(cc_1, True) ]))
    st_4._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
S100_ArcByCenterPointType._Automaton = _BuildAutomaton_6()




S100_GM_SplineCurveType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'degree'), pyxb.binding.datatypes.nonNegativeInteger, scope=S100_GM_SplineCurveType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 683, 20)))

S100_GM_SplineCurveType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'knot'), KnotPropertyType, scope=S100_GM_SplineCurveType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 684, 20)))

S100_GM_SplineCurveType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'knotSpec'), S100_GM_KnotTypeType, scope=S100_GM_SplineCurveType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 685, 20)))

S100_GM_SplineCurveType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'isRational'), _ImportedBinding__gml.booleanOrNilReason, scope=S100_GM_SplineCurveType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 686, 20)))

S100_GM_SplineCurveType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(_Namespace_gml, 'pos'), _ImportedBinding__gml.DirectPositionType, scope=S100_GM_SplineCurveType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1)))

S100_GM_SplineCurveType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(_Namespace_gml, 'posList'), _ImportedBinding__gml.DirectPositionListType, scope=S100_GM_SplineCurveType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 490, 1)))

S100_GM_SplineCurveType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(_Namespace_gml, 'pointProperty'), _ImportedBinding__gml.PointPropertyType, scope=S100_GM_SplineCurveType, documentation='This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1)))

def _BuildAutomaton_7 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_7
    del _BuildAutomaton_7
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 677, 24))
    counters.add(cc_0)
    cc_1 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 684, 20))
    counters.add(cc_1)
    cc_2 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 685, 20))
    counters.add(cc_2)
    states = []
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_GM_SplineCurveType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'pos')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 678, 28))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_GM_SplineCurveType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'pointProperty')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 679, 28))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_GM_SplineCurveType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'posList')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 681, 24))
    st_2 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_GM_SplineCurveType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'degree')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 683, 20))
    st_3 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_3)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_GM_SplineCurveType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'knot')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 684, 20))
    st_4 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_4)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_GM_SplineCurveType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'knotSpec')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 685, 20))
    st_5 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_5)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(S100_GM_SplineCurveType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'isRational')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 686, 20))
    st_6 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_6)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_0, False) ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_0, False) ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_3, [
         ]))
    st_2._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_4, [
         ]))
    transitions.append(fac.Transition(st_5, [
         ]))
    transitions.append(fac.Transition(st_6, [
         ]))
    st_3._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_4, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_5, [
        fac.UpdateInstruction(cc_1, False) ]))
    transitions.append(fac.Transition(st_6, [
        fac.UpdateInstruction(cc_1, False) ]))
    st_4._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_5, [
        fac.UpdateInstruction(cc_2, True) ]))
    transitions.append(fac.Transition(st_6, [
        fac.UpdateInstruction(cc_2, False) ]))
    st_5._set_transitionSet(transitions)
    transitions = []
    st_6._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
S100_GM_SplineCurveType._Automaton = _BuildAutomaton_7()




S100_GM_CurveType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(_Namespace_gml, 'pos'), _ImportedBinding__gml.DirectPositionType, scope=S100_GM_CurveType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 471, 1)))

S100_GM_CurveType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(_Namespace_gml, 'posList'), _ImportedBinding__gml.DirectPositionListType, scope=S100_GM_CurveType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 490, 1)))

S100_GM_CurveType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(_Namespace_gml, 'pointProperty'), _ImportedBinding__gml.PointPropertyType, scope=S100_GM_CurveType, documentation='This property element either references a point via the XLink-attributes\n\t\t\t\tor contains the point element. pointProperty is the predefined property which may be\n\t\t\t\tused by GML Application Schemas whenever a GML feature has a property with a value\n\t\t\t\tthat is substitutable for Point.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 593, 1)))

def _BuildAutomaton_8 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_8
    del _BuildAutomaton_8
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 724, 24))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(S100_GM_CurveType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'pos')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 725, 28))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(S100_GM_CurveType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'pointProperty')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 726, 28))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(S100_GM_CurveType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'posList')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 728, 24))
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
    return fac.Automaton(states, counters, True, containing_state=None)
S100_GM_CurveType._Automaton = _BuildAutomaton_8()




def _BuildAutomaton_9 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_9
    del _BuildAutomaton_9
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 370, 5))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(AbstractFeatureType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'boundedBy')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 370, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
AbstractFeatureType._Automaton = _BuildAutomaton_9()




S100_SpatialAttributeType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'maskReference'), _ImportedBinding__gml.ReferenceType, scope=S100_SpatialAttributeType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 339, 12)))

def _BuildAutomaton_10 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_10
    del _BuildAutomaton_10
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 339, 12))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(S100_SpatialAttributeType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'maskReference')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 339, 12))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
S100_SpatialAttributeType._Automaton = _BuildAutomaton_10()




PolygonPropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Polygon'), PolygonType, scope=PolygonPropertyType, documentation='S100 version of polygon type', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 507, 4)))

def _BuildAutomaton_11 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_11
    del _BuildAutomaton_11
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 517, 12))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(PolygonPropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'Polygon')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 517, 12))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
PolygonPropertyType._Automaton = _BuildAutomaton_11()




S100_CircleByCenterPointType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'angularDistance'), STD_ANON_, scope=S100_CircleByCenterPointType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 573, 20), unicode_default='360.0'))

def _BuildAutomaton_12 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_12
    del _BuildAutomaton_12
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_CircleByCenterPointType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'pos')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 568, 24))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_CircleByCenterPointType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'pointProperty')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 569, 24))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_CircleByCenterPointType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'radius')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 571, 20))
    st_2 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_CircleByCenterPointType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'startAngle')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 572, 20))
    st_3 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_3)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(S100_CircleByCenterPointType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'angularDistance')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 573, 20))
    st_4 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_4)
    transitions = []
    transitions.append(fac.Transition(st_2, [
         ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_2, [
         ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_3, [
         ]))
    st_2._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_4, [
         ]))
    st_3._set_transitionSet(transitions)
    transitions = []
    st_4._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
S100_CircleByCenterPointType._Automaton = _BuildAutomaton_12()




S100_GM_PolynomialSplineType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'derivativeAtStart'), VectorType, scope=S100_GM_PolynomialSplineType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 704, 20)))

S100_GM_PolynomialSplineType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'derivativeAtEnd'), VectorType, scope=S100_GM_PolynomialSplineType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 705, 20)))

S100_GM_PolynomialSplineType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'numDerivativeInterior'), pyxb.binding.datatypes.nonNegativeInteger, scope=S100_GM_PolynomialSplineType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 706, 20)))

def _BuildAutomaton_13 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_13
    del _BuildAutomaton_13
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 677, 24))
    counters.add(cc_0)
    cc_1 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 684, 20))
    counters.add(cc_1)
    cc_2 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 685, 20))
    counters.add(cc_2)
    cc_3 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 704, 20))
    counters.add(cc_3)
    cc_4 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 705, 20))
    counters.add(cc_4)
    states = []
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_GM_PolynomialSplineType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'pos')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 678, 28))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_GM_PolynomialSplineType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'pointProperty')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 679, 28))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_GM_PolynomialSplineType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'posList')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 681, 24))
    st_2 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_GM_PolynomialSplineType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'degree')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 683, 20))
    st_3 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_3)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_GM_PolynomialSplineType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'knot')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 684, 20))
    st_4 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_4)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_GM_PolynomialSplineType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'knotSpec')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 685, 20))
    st_5 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_5)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_GM_PolynomialSplineType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'isRational')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 686, 20))
    st_6 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_6)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_GM_PolynomialSplineType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'derivativeAtStart')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 704, 20))
    st_7 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_7)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(S100_GM_PolynomialSplineType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'derivativeAtEnd')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 705, 20))
    st_8 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_8)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(S100_GM_PolynomialSplineType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'numDerivativeInterior')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 706, 20))
    st_9 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_9)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_0, False) ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_0, False) ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_3, [
         ]))
    st_2._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_4, [
         ]))
    transitions.append(fac.Transition(st_5, [
         ]))
    transitions.append(fac.Transition(st_6, [
         ]))
    st_3._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_4, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_5, [
        fac.UpdateInstruction(cc_1, False) ]))
    transitions.append(fac.Transition(st_6, [
        fac.UpdateInstruction(cc_1, False) ]))
    st_4._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_5, [
        fac.UpdateInstruction(cc_2, True) ]))
    transitions.append(fac.Transition(st_6, [
        fac.UpdateInstruction(cc_2, False) ]))
    st_5._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_7, [
         ]))
    transitions.append(fac.Transition(st_8, [
         ]))
    transitions.append(fac.Transition(st_9, [
         ]))
    st_6._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_7, [
        fac.UpdateInstruction(cc_3, True) ]))
    transitions.append(fac.Transition(st_8, [
        fac.UpdateInstruction(cc_3, False) ]))
    transitions.append(fac.Transition(st_9, [
        fac.UpdateInstruction(cc_3, False) ]))
    st_7._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_8, [
        fac.UpdateInstruction(cc_4, True) ]))
    transitions.append(fac.Transition(st_9, [
        fac.UpdateInstruction(cc_4, False) ]))
    st_8._set_transitionSet(transitions)
    transitions = []
    st_9._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
S100_GM_PolynomialSplineType._Automaton = _BuildAutomaton_13()




DatasetType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Point'), PointType, scope=DatasetType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 359, 4)))

DatasetType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'MultiPoint'), MultiPointType, scope=DatasetType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 389, 4)))

DatasetType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Curve'), CurveType, scope=DatasetType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 418, 4)))

DatasetType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'CompositeCurve'), CompositeCurveType, scope=DatasetType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 448, 4)))

DatasetType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'OrientableCurve'), _ImportedBinding__gml.OrientableCurveType, scope=DatasetType, documentation='S-100 orientable curve is the same as GML orientable curve. Added for consistency.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 450, 4)))

DatasetType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Surface'), SurfaceType, scope=DatasetType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 479, 4)))

DatasetType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Polygon'), PolygonType, scope=DatasetType, documentation='S100 version of polygon type', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 507, 4)))

DatasetType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'DatasetIdentificationInformation'), DataSetIdentificationType, scope=DatasetType, documentation='Dataset identification information', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 778, 10)))

def _BuildAutomaton_14 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_14
    del _BuildAutomaton_14
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 370, 5))
    counters.add(cc_0)
    cc_1 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 783, 10))
    counters.add(cc_1)
    states = []
    final_update = None
    symbol = pyxb.binding.content.ElementUse(DatasetType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'boundedBy')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 370, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(DatasetType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'DatasetIdentificationInformation')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 778, 10))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(DatasetType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'Point')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 747, 12))
    st_2 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(DatasetType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'MultiPoint')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 748, 12))
    st_3 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_3)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(DatasetType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'Curve')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 461, 12))
    st_4 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_4)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(DatasetType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'CompositeCurve')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 462, 12))
    st_5 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_5)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(DatasetType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'OrientableCurve')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 463, 12))
    st_6 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_6)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(DatasetType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'Surface')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 750, 12))
    st_7 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_7)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(DatasetType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'Polygon')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 751, 12))
    st_8 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_8)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, False) ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_2, [
         ]))
    transitions.append(fac.Transition(st_3, [
         ]))
    transitions.append(fac.Transition(st_4, [
         ]))
    transitions.append(fac.Transition(st_5, [
         ]))
    transitions.append(fac.Transition(st_6, [
         ]))
    transitions.append(fac.Transition(st_7, [
         ]))
    transitions.append(fac.Transition(st_8, [
         ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_4, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_5, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_6, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_7, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_8, [
        fac.UpdateInstruction(cc_1, True) ]))
    st_2._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_4, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_5, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_6, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_7, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_8, [
        fac.UpdateInstruction(cc_1, True) ]))
    st_3._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_4, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_5, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_6, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_7, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_8, [
        fac.UpdateInstruction(cc_1, True) ]))
    st_4._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_4, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_5, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_6, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_7, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_8, [
        fac.UpdateInstruction(cc_1, True) ]))
    st_5._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_4, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_5, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_6, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_7, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_8, [
        fac.UpdateInstruction(cc_1, True) ]))
    st_6._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_4, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_5, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_6, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_7, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_8, [
        fac.UpdateInstruction(cc_1, True) ]))
    st_7._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_4, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_5, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_6, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_7, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_8, [
        fac.UpdateInstruction(cc_1, True) ]))
    st_8._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
DatasetType._Automaton = _BuildAutomaton_14()




PointPropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Point'), PointType, scope=PointPropertyType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 359, 4)))

def _BuildAutomaton_15 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_15
    del _BuildAutomaton_15
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 339, 12))
    counters.add(cc_0)
    cc_1 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 369, 20))
    counters.add(cc_1)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(PointPropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'maskReference')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 339, 12))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(PointPropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'Point')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 369, 20))
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
PointPropertyType._Automaton = _BuildAutomaton_15()




MultiPointPropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'MultiPoint'), MultiPointType, scope=MultiPointPropertyType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 389, 4)))

def _BuildAutomaton_16 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_16
    del _BuildAutomaton_16
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 339, 12))
    counters.add(cc_0)
    cc_1 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 398, 20))
    counters.add(cc_1)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(MultiPointPropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'maskReference')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 339, 12))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(MultiPointPropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'MultiPoint')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 398, 20))
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
MultiPointPropertyType._Automaton = _BuildAutomaton_16()




CurvePropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Curve'), CurveType, scope=CurvePropertyType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 418, 4)))

CurvePropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'CompositeCurve'), CompositeCurveType, scope=CurvePropertyType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 448, 4)))

CurvePropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'OrientableCurve'), _ImportedBinding__gml.OrientableCurveType, scope=CurvePropertyType, documentation='S-100 orientable curve is the same as GML orientable curve. Added for consistency.', location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 450, 4)))

def _BuildAutomaton_17 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_17
    del _BuildAutomaton_17
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 339, 12))
    counters.add(cc_0)
    cc_1 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 427, 20))
    counters.add(cc_1)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(CurvePropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'maskReference')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 339, 12))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(CurvePropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'Curve')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 461, 12))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(CurvePropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'CompositeCurve')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 462, 12))
    st_2 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(CurvePropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'OrientableCurve')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 463, 12))
    st_3 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_3)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, False) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_0, False) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_0, False) ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_1, True) ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_1, True) ]))
    st_2._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_1, True) ]))
    st_3._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
CurvePropertyType._Automaton = _BuildAutomaton_17()




SurfacePropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'Surface'), SurfaceType, scope=SurfacePropertyType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 479, 4)))

def _BuildAutomaton_18 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_18
    del _BuildAutomaton_18
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 339, 12))
    counters.add(cc_0)
    cc_1 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 488, 20))
    counters.add(cc_1)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(SurfacePropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'maskReference')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 339, 12))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(SurfacePropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'Surface')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 488, 20))
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
SurfacePropertyType._Automaton = _BuildAutomaton_18()




PointType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation'), _ImportedBinding__gml.ReferenceType, scope=PointType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 302, 4)))

def _BuildAutomaton_19 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_19
    del _BuildAutomaton_19
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 354, 20))
    counters.add(cc_0)
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(PointType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'pos')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 573, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(PointType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 354, 20))
    st_1 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    transitions = []
    transitions.append(fac.Transition(st_1, [
         ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_1._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
PointType._Automaton = _BuildAutomaton_19()




MultiPointType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation'), _ImportedBinding__gml.ReferenceType, scope=MultiPointType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 302, 4)))

def _BuildAutomaton_20 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_20
    del _BuildAutomaton_20
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1245, 5))
    counters.add(cc_0)
    cc_1 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 384, 20))
    counters.add(cc_1)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(MultiPointType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'pointMember')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1245, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(MultiPointType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 384, 20))
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
MultiPointType._Automaton = _BuildAutomaton_20()




CurveType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation'), _ImportedBinding__gml.ReferenceType, scope=CurveType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 302, 4)))

def _BuildAutomaton_21 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_21
    del _BuildAutomaton_21
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 413, 20))
    counters.add(cc_0)
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(CurveType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'segments')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 803, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(CurveType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 413, 20))
    st_1 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    transitions = []
    transitions.append(fac.Transition(st_1, [
         ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_1._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
CurveType._Automaton = _BuildAutomaton_21()




CompositeCurveType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation'), _ImportedBinding__gml.ReferenceType, scope=CompositeCurveType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 302, 4)))

def _BuildAutomaton_22 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_22
    del _BuildAutomaton_22
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 443, 20))
    counters.add(cc_0)
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(CompositeCurveType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'curveMember')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1201, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(CompositeCurveType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 443, 20))
    st_1 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    transitions = []
    transitions.append(fac.Transition(st_0, [
         ]))
    transitions.append(fac.Transition(st_1, [
         ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_1._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
CompositeCurveType._Automaton = _BuildAutomaton_22()




SurfaceType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation'), _ImportedBinding__gml.ReferenceType, scope=SurfaceType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 302, 4)))

def _BuildAutomaton_23 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_23
    del _BuildAutomaton_23
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 474, 20))
    counters.add(cc_0)
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(SurfaceType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'patches')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 1101, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(SurfaceType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 474, 20))
    st_1 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    transitions = []
    transitions.append(fac.Transition(st_1, [
         ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_1._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
SurfaceType._Automaton = _BuildAutomaton_23()




PolygonType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation'), _ImportedBinding__gml.ReferenceType, scope=PolygonType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 302, 4)))

def _BuildAutomaton_24 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_24
    del _BuildAutomaton_24
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 701, 5))
    counters.add(cc_0)
    cc_1 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 702, 5))
    counters.add(cc_1)
    cc_2 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 502, 20))
    counters.add(cc_2)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(PolygonType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'exterior')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 701, 5))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(PolygonType._UseForTag(pyxb.namespace.ExpandedName(_Namespace_gml, 'interior')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/S100_gmlProfile.xsd', 702, 5))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_2, False))
    symbol = pyxb.binding.content.ElementUse(PolygonType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'informationAssociation')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/S100GML/20220620/s100gmlbase.xsd', 502, 20))
    st_2 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, False) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_0, False) ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_1, False) ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_2, True) ]))
    st_2._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
PolygonType._Automaton = _BuildAutomaton_24()


S100_ArcByCenterPoint._setSubstitutionGroup(_ImportedBinding__gml.AbstractCurveSegment)

S100_GM_SplineCurve._setSubstitutionGroup(_ImportedBinding__gml.AbstractCurveSegment)

S100_GM_Curve._setSubstitutionGroup(_ImportedBinding__gml.AbstractCurveSegment)

S100_CircleByCenterPoint._setSubstitutionGroup(S100_ArcByCenterPoint)

S100_GM_PolynomialSpline._setSubstitutionGroup(_ImportedBinding__gml.AbstractCurveSegment)

Point._setSubstitutionGroup(_ImportedBinding__gml.AbstractGeometricPrimitive)

MultiPoint._setSubstitutionGroup(_ImportedBinding__gml.AbstractGeometricAggregate)

OrientableCurve._setSubstitutionGroup(_ImportedBinding__gml.AbstractCurve)

Curve._setSubstitutionGroup(_ImportedBinding__gml.Curve)

CompositeCurve._setSubstitutionGroup(_ImportedBinding__gml.AbstractCurve)

Surface._setSubstitutionGroup(_ImportedBinding__gml.Surface)

Polygon._setSubstitutionGroup(_ImportedBinding__gml.Polygon)
