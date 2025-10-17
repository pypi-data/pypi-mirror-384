import pytest
import os
import re

from xsdata.models.datatype import XmlDate
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from datetime import date
from iso639 import Lang

from grad.s201 import *


@pytest.fixture
def s201_msg_xml():
    # Get absolute path of this test file
    test_dir = os.path.dirname(__file__)

    # Open the file
    s201_msg_file = open(test_dir + '/s201-msg.xml', mode="rb")

    # And return the contents
    yield s201_msg_file.read().decode("utf-8")


@pytest.fixture
def bounding_shape():
    boundingShape = BoundingShapeType()
    boundingShape.envelope = EnvelopeType()
    boundingShape.envelope.srs_name = 'EPSG:4326'
    boundingShape.envelope.srs_dimension = '1'
    boundingShape.envelope.lower_corner = [51.8916667, 1.4233333]
    boundingShape.envelope.upper_corner = [51.8916667, 1.4233333]

    yield boundingShape


@pytest.fixture
def virtual_ais_aton(bounding_shape):
    virtualAISAidToNavigation = VirtualAisaidToNavigation()
    virtualAISAidToNavigation.bounded_by = bounding_shape
    virtualAISAidToNavigation.id = 'ID001'
    virtualAISAidToNavigation.i_dcode = 'urn:mrn:grad:aton:test:corkhole'
    virtualAISAidToNavigation.seasonal_action_required = ['none']
    virtualAISAidToNavigation.m_msicode = '992359598'
    virtualAISAidToNavigation.source = 'CHT'
    virtualAISAidToNavigation.source_date = XmlDate(2000, 1, 1)
    virtualAISAidToNavigation.pictorial_representation = 'N/A'
    virtualAISAidToNavigation.installation_date = XmlDate(2000, 1, 1)
    virtualAISAidToNavigation.inspection_frequency = 'yearly'
    virtualAISAidToNavigation.inspection_requirements = 'IALA'
    virtualAISAidToNavigation.a_to_nmaintenance_record = 'urn:mrn:grad:aton:test:corkhole:maintenance:x001'
    virtualAISAidToNavigation.virtual_aisaid_to_navigation_type = VirtualAisaidToNavigationTypeType.SPECIAL_PURPOSE
    virtualAISAidToNavigation.status = [StatusType.CONFIRMED]
    virtualAISAidToNavigation.virtual_aisbroadcasts = []
    
    # Setup the feature name
    virtualAISAidToNavigation.feature_name = []
    featureName = FeatureNameType()
    featureName.display_name = 1
    featureName.language = Lang("English").pt3
    featureName.name = 'Test AtoN for Cork Hole'
    virtualAISAidToNavigation.feature_name.append(featureName)

    # Setup the date range
    fixedDateRange = FixedDateRangeType()
    fixedDateRange.date_start = S100TruncatedDate2()
    fixedDateRange.date_start.date = XmlDate(2001, 1, 1)
    fixedDateRange.date_end = S100TruncatedDate2()
    fixedDateRange.date_end.date = XmlDate(2099, 1, 1)
    virtualAISAidToNavigation.fixed_date_range = fixedDateRange

    # Setup the geometry
    geometry = VirtualAisaidToNavigationType.Geometry()
    geometry.point_property = PointProperty2()
    point = Point2()
    pos = Pos()
    pos.id = 'AtoNPoint'
    pos.srs_name = 'EPSG:4326'
    pos.srs_dimension = 1
    pos.value = [51.8916667, 1.4233333]
    point.pos = pos
    geometry.point_property.point = point
    virtualAISAidToNavigation.geometry = [geometry]

    yield virtualAISAidToNavigation


@pytest.fixture
def virtual_ais_aton_status():
    atonStatusInformation = AtonStatusInformation()
    atonStatusInformation.id = 'ID002'
    atonStatusInformation.change_details = ChangeDetailsType()
    atonStatusInformation.change_details.electronic_aton_change = ElectronicAtonChangeType.AIS_TRANSMITTER_OPERATING_PROPERLY
    atonStatusInformation.change_types =  ChangeTypesType.ADVANCED_NOTICE_OF_CHANGES 

    yield atonStatusInformation


@pytest.fixture
def s201_dataset(bounding_shape, virtual_ais_aton, virtual_ais_aton_status):
    # Create a new dataset
    s201Dataset = Dataset()

    # Initialise the dataset
    s201Dataset.id = "CorkHoleTestDataset"
    s201Dataset.bounded_by = bounding_shape    

    # Add the dataset identification information
    dataSetIdentificationType = DataSetIdentificationType()
    dataSetIdentificationType.encoding_specification = 'S-100 Part 10b'
    dataSetIdentificationType.encoding_specification_edition = '1.0'
    dataSetIdentificationType.product_identifier = 'S-201'
    dataSetIdentificationType.product_edition = '0.0.1'
    dataSetIdentificationType.application_profile = 'test'
    dataSetIdentificationType.dataset_file_identifier = 'junit'
    dataSetIdentificationType.dataset_title = 'S-201 Cork Hole Test Dataset'
    dataSetIdentificationType.dataset_reference_date = XmlDate(2001, 1, 1)
    dataSetIdentificationType.dataset_language = Lang("English").pt3
    dataSetIdentificationType.dataset_abstract = 'Test dataset for unit testing'
    dataSetIdentificationType.dataset_topic_category = [MdTopicCategoryCode.OCEANS]
    dataSetIdentificationType.dataset_purpose = DatasetPurposeType.BASE
    dataSetIdentificationType.update_number = 2
    s201Dataset.dataset_identification_information = dataSetIdentificationType

    # Link the aton and its status
    virtual_ais_aton.statuspart = ReferenceType()
    virtual_ais_aton.statuspart.href = virtual_ais_aton_status.id
    virtual_ais_aton.statuspart.role = "association"
    virtual_ais_aton.statuspart.arcrole = "urn:IALA:S201:roles:association"

    # Add the dataset members - A single Virtual AIS Aid to Navigation and its status
    s201Dataset.members = ThisDatasetType.Members()
    s201Dataset.members.virtual_aisaid_to_navigation = [
        virtual_ais_aton_status,
        virtual_ais_aton
    ]


    # And return the dataset
    yield s201Dataset


def test_marshall(s201_dataset, s201_msg_xml):
    """
    Test that we can successfully marshall an S-201 dataset from the generated
    python objects using the PYXB library.
    """    
    # 3. Create the XML serializer
    config = SerializerConfig(indent="    ")
    serializer = XmlSerializer(config=config)

    # And Marshall to XMl
    s201_dataset_xml = serializer.render(s201_dataset)
    
    # Remove the namespaces from the datasets
    s201_dataset_xml_without_ns = re.sub("<ns\\d:Dataset[^>]*>","<Dataset>", s201_dataset_xml).replace("\r\n", "").replace("\n", "")
    s201_msg_xml_without_ns = re.sub("<ns\\d:Dataset[^>]*>","<Dataset>", s201_msg_xml).replace("\r\n", "").replace("\n", "")

    # Make sure the XMl seems correct
    assert s201_dataset_xml_without_ns == s201_msg_xml_without_ns


def test_unmarshall(s201_msg_xml):
    """
    Test that we can successfully unmarshall a packaged S-201 dataset using the 
    generated python objects of the PYXB library.
    """
    # Parse the S201 test message XML
    #s201_msg = s201.CreateFromDocument(s201_msg_xml)
    parser = XmlParser()
    dataset = parser.from_string(s201_msg_xml, Dataset)

    # And make sure the contents seem correct
    assert dataset.members.virtual_aisaid_to_navigation[1].feature_name[0].name == 'Test AtoN for Cork Hole'

