# ./_xlink.py
# -*- coding: utf-8 -*-
# PyXB bindings for NM:b43cd366527ddb6a0e58594876e07421e0148f30
# Generated 2025-10-13 15:57:18.382353 by PyXB version 1.2.6 using Python 3.12.3.final.0
# Namespace http://www.w3.org/1999/xlink [xmlns:xlink]

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
import pyxb.binding.datatypes
import pyxb.binding.xml_

# NOTE: All namespace declarations are reserved within the binding
Namespace = pyxb.namespace.NamespaceForURI('http://www.w3.org/1999/xlink', create_if_missing=True)
Namespace.configureCategories(['typeBinding', 'elementBinding'])

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


# Atomic simple type: {http://www.w3.org/1999/xlink}typeType
class typeType (pyxb.binding.datatypes.token, pyxb.binding.basis.enumeration_mixin):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'typeType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 54, 1)
    _Documentation = None
typeType._CF_enumeration = pyxb.binding.facets.CF_enumeration(enum_prefix=None, value_datatype=typeType)
typeType.simple = typeType._CF_enumeration.addEnumeration(unicode_value='simple', tag='simple')
typeType.extended = typeType._CF_enumeration.addEnumeration(unicode_value='extended', tag='extended')
typeType.title = typeType._CF_enumeration.addEnumeration(unicode_value='title', tag='title')
typeType.resource = typeType._CF_enumeration.addEnumeration(unicode_value='resource', tag='resource')
typeType.locator = typeType._CF_enumeration.addEnumeration(unicode_value='locator', tag='locator')
typeType.arc = typeType._CF_enumeration.addEnumeration(unicode_value='arc', tag='arc')
typeType._InitializeFacetMap(typeType._CF_enumeration)
Namespace.addCategoryObject('typeBinding', 'typeType', typeType)
_module_typeBindings.typeType = typeType

# Atomic simple type: {http://www.w3.org/1999/xlink}hrefType
class hrefType (pyxb.binding.datatypes.anyURI):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'hrefType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 67, 1)
    _Documentation = None
hrefType._InitializeFacetMap()
Namespace.addCategoryObject('typeBinding', 'hrefType', hrefType)
_module_typeBindings.hrefType = hrefType

# Atomic simple type: {http://www.w3.org/1999/xlink}roleType
class roleType (pyxb.binding.datatypes.anyURI):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'roleType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 73, 1)
    _Documentation = None
roleType._CF_minLength = pyxb.binding.facets.CF_minLength(value=pyxb.binding.datatypes.nonNegativeInteger(1))
roleType._InitializeFacetMap(roleType._CF_minLength)
Namespace.addCategoryObject('typeBinding', 'roleType', roleType)
_module_typeBindings.roleType = roleType

# Atomic simple type: {http://www.w3.org/1999/xlink}arcroleType
class arcroleType (pyxb.binding.datatypes.anyURI):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'arcroleType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 81, 1)
    _Documentation = None
arcroleType._CF_minLength = pyxb.binding.facets.CF_minLength(value=pyxb.binding.datatypes.nonNegativeInteger(1))
arcroleType._InitializeFacetMap(arcroleType._CF_minLength)
Namespace.addCategoryObject('typeBinding', 'arcroleType', arcroleType)
_module_typeBindings.arcroleType = arcroleType

# Atomic simple type: {http://www.w3.org/1999/xlink}titleAttrType
class titleAttrType (pyxb.binding.datatypes.string):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'titleAttrType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 89, 1)
    _Documentation = None
titleAttrType._InitializeFacetMap()
Namespace.addCategoryObject('typeBinding', 'titleAttrType', titleAttrType)
_module_typeBindings.titleAttrType = titleAttrType

# Atomic simple type: {http://www.w3.org/1999/xlink}showType
class showType (pyxb.binding.datatypes.token, pyxb.binding.basis.enumeration_mixin):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'showType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 95, 1)
    _Documentation = None
showType._CF_enumeration = pyxb.binding.facets.CF_enumeration(enum_prefix=None, value_datatype=showType)
showType.new = showType._CF_enumeration.addEnumeration(unicode_value='new', tag='new')
showType.replace = showType._CF_enumeration.addEnumeration(unicode_value='replace', tag='replace')
showType.embed = showType._CF_enumeration.addEnumeration(unicode_value='embed', tag='embed')
showType.other = showType._CF_enumeration.addEnumeration(unicode_value='other', tag='other')
showType.none = showType._CF_enumeration.addEnumeration(unicode_value='none', tag='none')
showType._InitializeFacetMap(showType._CF_enumeration)
Namespace.addCategoryObject('typeBinding', 'showType', showType)
_module_typeBindings.showType = showType

# Atomic simple type: {http://www.w3.org/1999/xlink}actuateType
class actuateType (pyxb.binding.datatypes.token, pyxb.binding.basis.enumeration_mixin):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'actuateType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 107, 1)
    _Documentation = None
actuateType._CF_enumeration = pyxb.binding.facets.CF_enumeration(enum_prefix=None, value_datatype=actuateType)
actuateType.onLoad = actuateType._CF_enumeration.addEnumeration(unicode_value='onLoad', tag='onLoad')
actuateType.onRequest = actuateType._CF_enumeration.addEnumeration(unicode_value='onRequest', tag='onRequest')
actuateType.other = actuateType._CF_enumeration.addEnumeration(unicode_value='other', tag='other')
actuateType.none = actuateType._CF_enumeration.addEnumeration(unicode_value='none', tag='none')
actuateType._InitializeFacetMap(actuateType._CF_enumeration)
Namespace.addCategoryObject('typeBinding', 'actuateType', actuateType)
_module_typeBindings.actuateType = actuateType

# Atomic simple type: {http://www.w3.org/1999/xlink}labelType
class labelType (pyxb.binding.datatypes.NCName):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'labelType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 118, 1)
    _Documentation = None
labelType._InitializeFacetMap()
Namespace.addCategoryObject('typeBinding', 'labelType', labelType)
_module_typeBindings.labelType = labelType

# Atomic simple type: {http://www.w3.org/1999/xlink}fromType
class fromType (pyxb.binding.datatypes.NCName):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'fromType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 124, 1)
    _Documentation = None
fromType._InitializeFacetMap()
Namespace.addCategoryObject('typeBinding', 'fromType', fromType)
_module_typeBindings.fromType = fromType

# Atomic simple type: {http://www.w3.org/1999/xlink}toType
class toType (pyxb.binding.datatypes.NCName):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'toType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 130, 1)
    _Documentation = None
toType._InitializeFacetMap()
Namespace.addCategoryObject('typeBinding', 'toType', toType)
_module_typeBindings.toType = toType

# Complex type {http://www.w3.org/1999/xlink}simple with content type MIXED
class simple (pyxb.binding.basis.complexTypeDefinition):
    """
    Intended for use as the type of user-declared elements to make them
    simple links.
   """
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_MIXED
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'simple')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 150, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'type'), 'type', '__httpwww_w3_org1999xlink_simple_httpwww_w3_org1999xlinktype', _module_typeBindings.typeType, fixed=True, unicode_default='simple')
    __type._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 52, 1)
    __type._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 135, 2)
    
    type = property(__type.value, __type.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}href uses Python identifier href
    __href = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'href'), 'href', '__httpwww_w3_org1999xlink_simple_httpwww_w3_org1999xlinkhref', _module_typeBindings.hrefType)
    __href._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 65, 1)
    __href._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 136, 2)
    
    href = property(__href.value, __href.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}role uses Python identifier role
    __role = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'role'), 'role', '__httpwww_w3_org1999xlink_simple_httpwww_w3_org1999xlinkrole', _module_typeBindings.roleType)
    __role._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 71, 1)
    __role._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 137, 2)
    
    role = property(__role.value, __role.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}arcrole uses Python identifier arcrole
    __arcrole = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'arcrole'), 'arcrole', '__httpwww_w3_org1999xlink_simple_httpwww_w3_org1999xlinkarcrole', _module_typeBindings.arcroleType)
    __arcrole._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 79, 1)
    __arcrole._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 138, 2)
    
    arcrole = property(__arcrole.value, __arcrole.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'title'), 'title', '__httpwww_w3_org1999xlink_simple_httpwww_w3_org1999xlinktitle', _module_typeBindings.titleAttrType)
    __title._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 87, 1)
    __title._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 139, 2)
    
    title = property(__title.value, __title.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}show uses Python identifier show
    __show = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'show'), 'show', '__httpwww_w3_org1999xlink_simple_httpwww_w3_org1999xlinkshow', _module_typeBindings.showType)
    __show._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 93, 1)
    __show._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 140, 2)
    
    show = property(__show.value, __show.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}actuate uses Python identifier actuate
    __actuate = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'actuate'), 'actuate', '__httpwww_w3_org1999xlink_simple_httpwww_w3_org1999xlinkactuate', _module_typeBindings.actuateType)
    __actuate._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 105, 1)
    __actuate._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 141, 2)
    
    actuate = property(__actuate.value, __actuate.set, None, None)

    _HasWildcardElement = True
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __type.name() : __type,
        __href.name() : __href,
        __role.name() : __role,
        __arcrole.name() : __arcrole,
        __title.name() : __title,
        __show.name() : __show,
        __actuate.name() : __actuate
    })
_module_typeBindings.simple = simple
Namespace.addCategoryObject('typeBinding', 'simple', simple)


# Complex type {http://www.w3.org/1999/xlink}extended with content type ELEMENT_ONLY
class extended (pyxb.binding.basis.complexTypeDefinition):
    """
    Intended for use as the type of user-declared elements to make them
    extended links.
    Note that the elements referenced in the content model are all abstract.
    The intention is that by simply declaring elements with these as their
    substitutionGroup, all the right things will happen.
   """
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'extended')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 176, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'title'), 'title', '__httpwww_w3_org1999xlink_extended_httpwww_w3_org1999xlinktitle', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 190, 1), )

    
    title = property(__title.value, __title.set, None, None)

    
    # Element {http://www.w3.org/1999/xlink}resource uses Python identifier resource
    __resource = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'resource'), 'resource', '__httpwww_w3_org1999xlink_extended_httpwww_w3_org1999xlinkresource', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 216, 1), )

    
    resource = property(__resource.value, __resource.set, None, None)

    
    # Element {http://www.w3.org/1999/xlink}locator uses Python identifier locator
    __locator = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'locator'), 'locator', '__httpwww_w3_org1999xlink_extended_httpwww_w3_org1999xlinklocator', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 236, 1), )

    
    locator = property(__locator.value, __locator.set, None, None)

    
    # Element {http://www.w3.org/1999/xlink}arc uses Python identifier arc
    __arc = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'arc'), 'arc', '__httpwww_w3_org1999xlink_extended_httpwww_w3_org1999xlinkarc', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 264, 1), )

    
    arc = property(__arc.value, __arc.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'type'), 'type', '__httpwww_w3_org1999xlink_extended_httpwww_w3_org1999xlinktype', _module_typeBindings.typeType, fixed=True, unicode_default='extended', required=True)
    __type._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 52, 1)
    __type._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 162, 2)
    
    type = property(__type.value, __type.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}role uses Python identifier role
    __role = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'role'), 'role', '__httpwww_w3_org1999xlink_extended_httpwww_w3_org1999xlinkrole', _module_typeBindings.roleType)
    __role._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 71, 1)
    __role._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 163, 2)
    
    role = property(__role.value, __role.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title_
    __title_ = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'title'), 'title_', '__httpwww_w3_org1999xlink_extended_httpwww_w3_org1999xlinktitle_', _module_typeBindings.titleAttrType)
    __title_._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 87, 1)
    __title_._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 164, 2)
    
    title_ = property(__title_.value, __title_.set, None, None)

    _ElementMap.update({
        __title.name() : __title,
        __resource.name() : __resource,
        __locator.name() : __locator,
        __arc.name() : __arc
    })
    _AttributeMap.update({
        __type.name() : __type,
        __role.name() : __role,
        __title_.name() : __title_
    })
_module_typeBindings.extended = extended
Namespace.addCategoryObject('typeBinding', 'extended', extended)


# Complex type {http://www.w3.org/1999/xlink}titleEltType with content type MIXED
class titleEltType (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://www.w3.org/1999/xlink}titleEltType with content type MIXED"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_MIXED
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'titleEltType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 211, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Attribute {http://www.w3.org/XML/1998/namespace}lang uses Python identifier lang
    __lang = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(pyxb.namespace.XML, 'lang'), 'lang', '__httpwww_w3_org1999xlink_titleEltType_httpwww_w3_orgXML1998namespacelang', pyxb.binding.xml_.STD_ANON_lang)
    __lang._DeclarationLocation = None
    __lang._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 194, 2)
    
    lang = property(__lang.value, __lang.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'type'), 'type', '__httpwww_w3_org1999xlink_titleEltType_httpwww_w3_org1999xlinktype', _module_typeBindings.typeType, fixed=True, unicode_default='title', required=True)
    __type._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 52, 1)
    __type._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 193, 2)
    
    type = property(__type.value, __type.set, None, None)

    _HasWildcardElement = True
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __lang.name() : __lang,
        __type.name() : __type
    })
_module_typeBindings.titleEltType = titleEltType
Namespace.addCategoryObject('typeBinding', 'titleEltType', titleEltType)


# Complex type {http://www.w3.org/1999/xlink}resourceType with content type MIXED
class resourceType (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://www.w3.org/1999/xlink}resourceType with content type MIXED"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_MIXED
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'resourceType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 231, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'type'), 'type', '__httpwww_w3_org1999xlink_resourceType_httpwww_w3_org1999xlinktype', _module_typeBindings.typeType, fixed=True, unicode_default='resource', required=True)
    __type._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 52, 1)
    __type._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 219, 2)
    
    type = property(__type.value, __type.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}role uses Python identifier role
    __role = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'role'), 'role', '__httpwww_w3_org1999xlink_resourceType_httpwww_w3_org1999xlinkrole', _module_typeBindings.roleType)
    __role._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 71, 1)
    __role._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 220, 2)
    
    role = property(__role.value, __role.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'title'), 'title', '__httpwww_w3_org1999xlink_resourceType_httpwww_w3_org1999xlinktitle', _module_typeBindings.titleAttrType)
    __title._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 87, 1)
    __title._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 221, 2)
    
    title = property(__title.value, __title.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}label uses Python identifier label
    __label = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'label'), 'label', '__httpwww_w3_org1999xlink_resourceType_httpwww_w3_org1999xlinklabel', _module_typeBindings.labelType)
    __label._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 116, 1)
    __label._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 222, 2)
    
    label = property(__label.value, __label.set, None, None)

    _HasWildcardElement = True
    _ElementMap.update({
        
    })
    _AttributeMap.update({
        __type.name() : __type,
        __role.name() : __role,
        __title.name() : __title,
        __label.name() : __label
    })
_module_typeBindings.resourceType = resourceType
Namespace.addCategoryObject('typeBinding', 'resourceType', resourceType)


# Complex type {http://www.w3.org/1999/xlink}locatorType with content type ELEMENT_ONLY
class locatorType (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://www.w3.org/1999/xlink}locatorType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'locatorType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 259, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'title'), 'title', '__httpwww_w3_org1999xlink_locatorType_httpwww_w3_org1999xlinktitle', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 190, 1), )

    
    title = property(__title.value, __title.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'type'), 'type', '__httpwww_w3_org1999xlink_locatorType_httpwww_w3_org1999xlinktype', _module_typeBindings.typeType, fixed=True, unicode_default='locator', required=True)
    __type._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 52, 1)
    __type._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 239, 2)
    
    type = property(__type.value, __type.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}href uses Python identifier href
    __href = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'href'), 'href', '__httpwww_w3_org1999xlink_locatorType_httpwww_w3_org1999xlinkhref', _module_typeBindings.hrefType, required=True)
    __href._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 65, 1)
    __href._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 240, 2)
    
    href = property(__href.value, __href.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}role uses Python identifier role
    __role = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'role'), 'role', '__httpwww_w3_org1999xlink_locatorType_httpwww_w3_org1999xlinkrole', _module_typeBindings.roleType)
    __role._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 71, 1)
    __role._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 241, 2)
    
    role = property(__role.value, __role.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title_
    __title_ = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'title'), 'title_', '__httpwww_w3_org1999xlink_locatorType_httpwww_w3_org1999xlinktitle_', _module_typeBindings.titleAttrType)
    __title_._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 87, 1)
    __title_._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 242, 2)
    
    title_ = property(__title_.value, __title_.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}label uses Python identifier label
    __label = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'label'), 'label', '__httpwww_w3_org1999xlink_locatorType_httpwww_w3_org1999xlinklabel', _module_typeBindings.labelType)
    __label._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 116, 1)
    __label._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 243, 2)
    
    label = property(__label.value, __label.set, None, None)

    _ElementMap.update({
        __title.name() : __title
    })
    _AttributeMap.update({
        __type.name() : __type,
        __href.name() : __href,
        __role.name() : __role,
        __title_.name() : __title_,
        __label.name() : __label
    })
_module_typeBindings.locatorType = locatorType
Namespace.addCategoryObject('typeBinding', 'locatorType', locatorType)


# Complex type {http://www.w3.org/1999/xlink}arcType with content type ELEMENT_ONLY
class arcType (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://www.w3.org/1999/xlink}arcType with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'arcType')
    _XSDLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 288, 1)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(Namespace, 'title'), 'title', '__httpwww_w3_org1999xlink_arcType_httpwww_w3_org1999xlinktitle', True, pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 190, 1), )

    
    title = property(__title.value, __title.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'type'), 'type', '__httpwww_w3_org1999xlink_arcType_httpwww_w3_org1999xlinktype', _module_typeBindings.typeType, fixed=True, unicode_default='arc', required=True)
    __type._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 52, 1)
    __type._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 267, 2)
    
    type = property(__type.value, __type.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}arcrole uses Python identifier arcrole
    __arcrole = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'arcrole'), 'arcrole', '__httpwww_w3_org1999xlink_arcType_httpwww_w3_org1999xlinkarcrole', _module_typeBindings.arcroleType)
    __arcrole._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 79, 1)
    __arcrole._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 268, 2)
    
    arcrole = property(__arcrole.value, __arcrole.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title_
    __title_ = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'title'), 'title_', '__httpwww_w3_org1999xlink_arcType_httpwww_w3_org1999xlinktitle_', _module_typeBindings.titleAttrType)
    __title_._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 87, 1)
    __title_._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 269, 2)
    
    title_ = property(__title_.value, __title_.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}show uses Python identifier show
    __show = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'show'), 'show', '__httpwww_w3_org1999xlink_arcType_httpwww_w3_org1999xlinkshow', _module_typeBindings.showType)
    __show._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 93, 1)
    __show._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 270, 2)
    
    show = property(__show.value, __show.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}actuate uses Python identifier actuate
    __actuate = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'actuate'), 'actuate', '__httpwww_w3_org1999xlink_arcType_httpwww_w3_org1999xlinkactuate', _module_typeBindings.actuateType)
    __actuate._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 105, 1)
    __actuate._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 271, 2)
    
    actuate = property(__actuate.value, __actuate.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}from uses Python identifier from_
    __from = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'from'), 'from_', '__httpwww_w3_org1999xlink_arcType_httpwww_w3_org1999xlinkfrom', _module_typeBindings.fromType)
    __from._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 122, 1)
    __from._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 272, 2)
    
    from_ = property(__from.value, __from.set, None, None)

    
    # Attribute {http://www.w3.org/1999/xlink}to uses Python identifier to
    __to = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(Namespace, 'to'), 'to', '__httpwww_w3_org1999xlink_arcType_httpwww_w3_org1999xlinkto', _module_typeBindings.toType)
    __to._DeclarationLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 128, 1)
    __to._UseLocation = pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 273, 2)
    
    to = property(__to.value, __to.set, None, None)

    _ElementMap.update({
        __title.name() : __title
    })
    _AttributeMap.update({
        __type.name() : __type,
        __arcrole.name() : __arcrole,
        __title_.name() : __title_,
        __show.name() : __show,
        __actuate.name() : __actuate,
        __from.name() : __from,
        __to.name() : __to
    })
_module_typeBindings.arcType = arcType
Namespace.addCategoryObject('typeBinding', 'arcType', arcType)


title = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'title'), titleEltType, abstract=pyxb.binding.datatypes.boolean(1), location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 190, 1))
Namespace.addCategoryObject('elementBinding', title.name().localName(), title)

resource = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'resource'), resourceType, abstract=pyxb.binding.datatypes.boolean(1), location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 216, 1))
Namespace.addCategoryObject('elementBinding', resource.name().localName(), resource)

locator = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'locator'), locatorType, abstract=pyxb.binding.datatypes.boolean(1), location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 236, 1))
Namespace.addCategoryObject('elementBinding', locator.name().localName(), locator)

arc = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'arc'), arcType, abstract=pyxb.binding.datatypes.boolean(1), location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 264, 1))
Namespace.addCategoryObject('elementBinding', arc.name().localName(), arc)



def _BuildAutomaton ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton
    del _BuildAutomaton
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 146, 3))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.WildcardUse(pyxb.binding.content.Wildcard(process_contents=pyxb.binding.content.Wildcard.PC_lax, namespace_constraint=pyxb.binding.content.Wildcard.NC_any), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 146, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
simple._Automaton = _BuildAutomaton()




extended._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'title'), titleEltType, abstract=pyxb.binding.datatypes.boolean(1), scope=extended, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 190, 1)))

extended._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'resource'), resourceType, abstract=pyxb.binding.datatypes.boolean(1), scope=extended, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 216, 1)))

extended._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'locator'), locatorType, abstract=pyxb.binding.datatypes.boolean(1), scope=extended, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 236, 1)))

extended._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'arc'), arcType, abstract=pyxb.binding.datatypes.boolean(1), scope=extended, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 264, 1)))

def _BuildAutomaton_ ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_
    del _BuildAutomaton_
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 186, 2))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(extended._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'title')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 169, 4))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(extended._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'resource')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 170, 4))
    st_1 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(extended._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'locator')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 171, 4))
    st_2 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(extended._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'arc')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 172, 4))
    st_3 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_3)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_2._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_3, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_3._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
extended._Automaton = _BuildAutomaton_()




def _BuildAutomaton_2 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_2
    del _BuildAutomaton_2
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 207, 3))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.WildcardUse(pyxb.binding.content.Wildcard(process_contents=pyxb.binding.content.Wildcard.PC_lax, namespace_constraint=pyxb.binding.content.Wildcard.NC_any), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 207, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
titleEltType._Automaton = _BuildAutomaton_2()




def _BuildAutomaton_3 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_3
    del _BuildAutomaton_3
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 227, 3))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.WildcardUse(pyxb.binding.content.Wildcard(process_contents=pyxb.binding.content.Wildcard.PC_lax, namespace_constraint=pyxb.binding.content.Wildcard.NC_any), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 227, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
resourceType._Automaton = _BuildAutomaton_3()




locatorType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'title'), titleEltType, abstract=pyxb.binding.datatypes.boolean(1), scope=locatorType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 190, 1)))

def _BuildAutomaton_4 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_4
    del _BuildAutomaton_4
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 255, 3))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(locatorType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'title')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 255, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
locatorType._Automaton = _BuildAutomaton_4()




arcType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'title'), titleEltType, abstract=pyxb.binding.datatypes.boolean(1), scope=arcType, location=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 190, 1)))

def _BuildAutomaton_5 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_5
    del _BuildAutomaton_5
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 284, 3))
    counters.add(cc_0)
    states = []
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(arcType._UseForTag(pyxb.namespace.ExpandedName(Namespace, 'title')), pyxb.utils.utility.Location('https://schemas.s100dev.net/schemas/S100/5.0.0/w3c/XML/2008/06/xlink.xsd', 284, 3))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
arcType._Automaton = _BuildAutomaton_5()

