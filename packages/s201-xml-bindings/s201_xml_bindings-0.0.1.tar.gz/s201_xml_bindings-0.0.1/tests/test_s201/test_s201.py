import pytest
import os
import re

from datetime import date
from iso639 import Lang
from s201 import s201
from xml.dom.minidom import parseString


@pytest.fixture
def s201_msg_xml():
    # Get absolute path of this test file
    test_dir = os.path.dirname(__file__)

    # Open the file
    s201_msg_file = open(test_dir + '/s201-msg.xml', mode="rb")

    # And return the contents
    yield s201_msg_file.read().decode("utf-8").replace("\r\n","").replace("\n","").replace("\t","")


@pytest.fixture
def bounding_shape():
    boundingShape = s201._ImportedBinding__gml.BoundingShapeType()
    boundingShape.Envelope = s201._ImportedBinding__gml.EnvelopeType()
    boundingShape.Envelope.srsName = 'EPSG:4326'
    boundingShape.Envelope.srsDimension = '1'
    boundingShape.Envelope.lowerCorner = [51.8916667, 1.4233333]
    boundingShape.Envelope.upperCorner = [51.8916667, 1.4233333]

    yield boundingShape


@pytest.fixture
def virtual_ais_aton(bounding_shape):
    virtualAISAidToNavigation = s201.VirtualAISAidToNavigation()
    virtualAISAidToNavigation.boundedBy = bounding_shape
    virtualAISAidToNavigation.id = 'ID001'
    virtualAISAidToNavigation.iDCode = 'urn:mrn:grad:aton:test:corkhole'
    virtualAISAidToNavigation.SeasonalActionRequired = ['none']
    virtualAISAidToNavigation.mMSICode = '992359598'
    virtualAISAidToNavigation.source = 'CHT'
    virtualAISAidToNavigation.sourceDate = date(2000, 1, 1)
    virtualAISAidToNavigation.pictorialRepresentation = 'N/A'
    virtualAISAidToNavigation.installationDate = date(2000, 1, 1)
    virtualAISAidToNavigation.inspectionFrequency = 'yearly'
    virtualAISAidToNavigation.inspectionRequirements = 'IALA'
    virtualAISAidToNavigation.aToNMaintenanceRecord = 'urn:mrn:grad:aton:test:corkhole:maintenance:x001'
    virtualAISAidToNavigation.virtualAISAidToNavigationType = 'Special Purpose'
    virtualAISAidToNavigation.status = [s201.statusType.Confirmed]
    virtualAISAidToNavigation.virtualAISbroadcasts = []
    
    # Setup the feature name
    virtualAISAidToNavigation.featureName = []
    featureName = s201.featureNameType()
    featureName.displayName = 1
    featureName.language = Lang("English").pt3
    featureName.name = 'Test AtoN for Cork Hole'
    virtualAISAidToNavigation.append(featureName)

    # Setup the date range
    fixedDateRange = s201.fixedDateRangeType()
    fixedDateRange.dateStart = s201.S100_TruncatedDate()
    fixedDateRange.dateStart.date = date(2001, 1, 1)
    fixedDateRange.dateEnd = s201.S100_TruncatedDate()
    fixedDateRange.dateEnd.date = date(2099, 1, 1)
    virtualAISAidToNavigation.fixedDateRange = fixedDateRange

    # Setup the geometry
    virtualAISAidToNavigation.geometry = [s201.CTD_ANON_16()]
    virtualAISAidToNavigation.geometry[0].pointProperty = s201._ImportedBinding__S100.PointPropertyType()
    virtualAISAidToNavigation.geometry[0].pointProperty.Point =  s201._ImportedBinding__S100.PointType()
    virtualAISAidToNavigation.geometry[0].pointProperty.Point.id = 'AtoNPoint'
    virtualAISAidToNavigation.geometry[0].pointProperty.Point.srsName = 'EPSG:4326'
    virtualAISAidToNavigation.geometry[0].pointProperty.Point.srsDimension = '1'
    virtualAISAidToNavigation.geometry[0].pointProperty.Point.pos = [51.8916667, 1.4233333]

    yield virtualAISAidToNavigation


@pytest.fixture
def virtual_ais_aton_status():
    atonStatusInformation = s201.AtonStatusInformation()
    atonStatusInformation.id = 'ID002'
    atonStatusInformation.ChangeDetails = s201.ChangeDetailsType()
    atonStatusInformation.ChangeDetails.electronicAtonChange = s201.electronicAtonChangeType.AIS_transmitter_operating_properly
    atonStatusInformation.ChangeTypes =  s201.ChangeTypesType.Advanced_notice_of_changes 

    yield atonStatusInformation


@pytest.fixture
def s201_dataset(bounding_shape, virtual_ais_aton, virtual_ais_aton_status):
    # Create a new dataset
    s201Dataset = s201.Dataset()

    # Initialise the dataset
    s201Dataset.id = "CorkHoleTestDataset"
    s201Dataset.boundedBy = bounding_shape    

    # Add the dataset identification information
    dataSetIdentificationType = s201._ImportedBinding__S100.DataSetIdentificationType()
    dataSetIdentificationType.encodingSpecification = 'S-100 Part 10b'
    dataSetIdentificationType.encodingSpecificationEdition = '1.0'
    dataSetIdentificationType.productIdentifier = 'S-201'
    dataSetIdentificationType.productEdition = '0.0.1'
    dataSetIdentificationType.applicationProfile = 'test'
    dataSetIdentificationType.datasetFileIdentifier = 'junit'
    dataSetIdentificationType.datasetTitle = 'S-201 Cork Hole Test Dataset'
    dataSetIdentificationType.datasetReferenceDate = date(2001, 1, 1)
    dataSetIdentificationType.datasetLanguage = Lang("English").pt3
    dataSetIdentificationType.datasetAbstract = 'Test dataset for unit testing'
    dataSetIdentificationType.datasetTopicCategory = [s201._ImportedBinding__S100.MD_TopicCategoryCode.oceans]
    dataSetIdentificationType.datasetPurpose = s201._ImportedBinding__S100.datasetPurposeType.base
    dataSetIdentificationType.updateNumber = 2
    s201Dataset.DatasetIdentificationInformation = dataSetIdentificationType

    # Link the aton and its status
    virtual_ais_aton.Statuspart = s201._ImportedBinding__gml.ReferenceType()
    virtual_ais_aton.Statuspart.href = virtual_ais_aton_status.id
    virtual_ais_aton.Statuspart.role = "association"
    virtual_ais_aton.Statuspart.arcrole = "urn:IALA:S201:roles:association"

    # Add the dataset members - A single Virtual AIS Aid to Navigation and its status
    s201Dataset.members = s201.CTD_ANON_52()
    s201Dataset.members.VirtualAISAidToNavigation = [
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
    # And Marshall to XMl
    s201_dataset_xml = s201_dataset.toxml("utf-8").decode('utf-8')
    
    # Remove the namespaces from the datasets
    s201_dataset_xml_without_ns = re.sub("<ns\\d:Dataset[^>]*>","<Dataset>", s201_dataset_xml)
    s201_msg_xml_without_ns = re.sub("<ns\\d:Dataset[^>]*>","<Dataset>", s201_msg_xml)

    # Make sure the XMl seems correct
    assert s201_dataset_xml_without_ns == s201_msg_xml_without_ns


def test_unmarshall(s201_msg_xml):
    """
    Test that we can successfully unmarshall a packaged S-201 dataset using the 
    generated python objects of the PYXB library.
    """
    # Parse the S201 test message XML
    s201_msg = s201.CreateFromDocument(s201_msg_xml)

    # And make sure the contents seem correct
    assert s201_msg.members.VirtualAISAidToNavigation[1].featureName[0].name == 'Test AtoN for Cork Hole'

