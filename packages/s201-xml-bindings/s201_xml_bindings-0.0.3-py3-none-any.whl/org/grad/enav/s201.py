from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional, Union

from xsdata.models.datatype import XmlDate, XmlPeriod


class CategoryOfAggregationType(Enum):
    """
    :cvar LEADING_LINE: -
    :cvar MEASURED_DISTANCE: -
    :cvar RANGE_SYSTEM: -
    """

    LEADING_LINE = "leading line"
    MEASURED_DISTANCE = "measured distance"
    RANGE_SYSTEM = "range system"


class CategoryOfAssociationType(Enum):
    """
    :cvar CHANNEL_MARKINGS: -
    :cvar DANGER_MARKINGS: -
    """

    CHANNEL_MARKINGS = "channel markings"
    DANGER_MARKINGS = "danger markings"


class CategoryOfPhysicalAisaidToNavigationType(Enum):
    """
    :cvar PHYSICAL_AIS_TYPE_1: Simple transmission of static, pre-
        programmed information.
    :cvar PHYSICAL_AIS_TYPE_2: Transmission of dynamic, real-time
        updated information via connected sensors.
    :cvar PHYSICAL_AIS_TYPE_3: Full two-way communication: transmission
        + remote control / configuration.
    """

    PHYSICAL_AIS_TYPE_1 = "Physical AIS Type 1"
    PHYSICAL_AIS_TYPE_2 = "Physical AIS Type 2"
    PHYSICAL_AIS_TYPE_3 = "Physical AIS Type 3"


class CategoryOfPowerSourceType(Enum):
    """
    :cvar BATTERY: -
    :cvar GENERATOR: -
    :cvar SOLAR_PANEL: -
    :cvar ELECTRICAL_SERVICE: -
    """

    BATTERY = "battery"
    GENERATOR = "generator"
    SOLAR_PANEL = "solar panel"
    ELECTRICAL_SERVICE = "electrical service"


class CategoryOfSyntheticAisaidtoNavigationType(Enum):
    """
    :cvar PREDICTED: -
    :cvar MONITORED: -
    """

    PREDICTED = "predicted"
    MONITORED = "monitored"


class ChangeTypesType(Enum):
    """
    :cvar ADVANCED_NOTICE_OF_CHANGES: -
    :cvar DISCREPANCY: -
    :cvar PROPOSED_CHANGES: -
    :cvar TEMPORARY_CHANGES: -
    """

    ADVANCED_NOTICE_OF_CHANGES = "Advanced notice of changes"
    DISCREPANCY = "Discrepancy"
    PROPOSED_CHANGES = "Proposed changes"
    TEMPORARY_CHANGES = "Temporary changes"


@dataclass
class S100TruncatedDate2:
    """
    Built in date types from W3C XML schema, implementing S-100 truncated date.
    """

    class Meta:
        name = "S100_TruncatedDate"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    g_day: Optional[XmlPeriod] = field(
        default=None,
        metadata={
            "name": "gDay",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    g_month: Optional[XmlPeriod] = field(
        default=None,
        metadata={
            "name": "gMonth",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    g_year: Optional[XmlPeriod] = field(
        default=None,
        metadata={
            "name": "gYear",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    g_month_day: Optional[XmlPeriod] = field(
        default=None,
        metadata={
            "name": "gMonthDay",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    g_year_month: Optional[XmlPeriod] = field(
        default=None,
        metadata={
            "name": "gYearMonth",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    date: Optional[XmlDate] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


class ShackleTypeType(Enum):
    """
    :cvar FORELOCK_SHACKLES: -
    :cvar CLENCHING_SHACKLES: -
    :cvar BOLT_SHACKLES: -
    :cvar SCREW_PIN_SHACKLES: -
    :cvar KENTER_SHACKLE: -
    :cvar QUICK_RELEASE_LINK: -
    """

    FORELOCK_SHACKLES = "forelock shackles"
    CLENCHING_SHACKLES = "clenching shackles"
    BOLT_SHACKLES = "bolt shackles"
    SCREW_PIN_SHACKLES = "screw pin shackles"
    KENTER_SHACKLE = "kenter shackle"
    QUICK_RELEASE_LINK = "quick release link"


class AidAvailabilityCategoryType(Enum):
    """
    :cvar CATEGORY_1: An AtoN or system of AtoN that is considered by
        the Competent Authority to be of vital navigational
        significance.
    :cvar CATEGORY_2: An AtoN or system of AtoN that is considered by
        the Competent Authority to be of important navigational
        significance.
    :cvar CATEGORY_3: An AtoN or system of AtoN that is considered by
        the Competent Authority to be of necessary navigational
        significance.
    """

    CATEGORY_1 = "Category 1"
    CATEGORY_2 = "Category 2"
    CATEGORY_3 = "Category 3"


class AtonCommissioningType(Enum):
    """
    :cvar BUOY_ESTABLISHMENT: .
    :cvar LIGHT_ESTABLISHMENT: .
    :cvar BEACON_ESTABLISHMENT: .
    :cvar AUDIBLE_SIGNAL_ESTABLISHMENT: .
    :cvar FOG_SIGNAL_ESTABLISHMENT: .
    :cvar AIS_TRANSMITTER_ESTABLISHMENT: .
    :cvar V_AIS_ESTABLISHMENT: .
    :cvar RACON_ESTABLISHMENT: .
    :cvar DGPS_STATION_ESTABLISHMENT: .
    :cvar E_LORAN_STATION_ESTABLISHMENT: .
    :cvar DGLONASS_STATION_ESTABLISHMENT: .
    :cvar E_CHAYKA_STATION_ESTABLISHMENT: .
    :cvar EGNOS_ESTABLISHMENT: .
    """

    BUOY_ESTABLISHMENT = "Buoy establishment"
    LIGHT_ESTABLISHMENT = "Light establishment"
    BEACON_ESTABLISHMENT = "Beacon establishment"
    AUDIBLE_SIGNAL_ESTABLISHMENT = "Audible signal establishment"
    FOG_SIGNAL_ESTABLISHMENT = "Fog signal establishment"
    AIS_TRANSMITTER_ESTABLISHMENT = "AIS transmitter establishment"
    V_AIS_ESTABLISHMENT = "V-AIS establishment"
    RACON_ESTABLISHMENT = "RACON establishment"
    DGPS_STATION_ESTABLISHMENT = "DGPS station establishment"
    E_LORAN_STATION_ESTABLISHMENT = "eLORAN station establishment"
    DGLONASS_STATION_ESTABLISHMENT = "DGLONASS station establishment"
    E_CHAYKA_STATION_ESTABLISHMENT = "e-Chayka station establishment"
    EGNOS_ESTABLISHMENT = "EGNOS establishment"


class AtonRemovalType(Enum):
    """
    :cvar BUOY_REMOVAL: .
    :cvar BUOY_TEMPORARY_REMOVAL: .
    :cvar LIGHT_REMOVAL: .
    :cvar LIGHT_TEMPORARY_REMOVAL: .
    :cvar BEACON_REMOVAL: .
    :cvar BEACON_TEMPORARY_REMOVAL: .
    :cvar FOG_SIGNAL_REMOVAL: .
    :cvar FOG_SIGNAL_TEMPORARY_REMOVAL: .
    :cvar AUDIBLE_SIGNAL_REMOVAL: .
    :cvar AUDIBLE_SIGNAL_TEMPORARY_REMOVAL: .
    :cvar V_AIS_REMOVAL: .
    :cvar V_AIS_TEMPORARY_REMOVAL: .
    :cvar RACON_SIGNAL_REMOVAL: .
    :cvar RACON_TEMPORARY_REMOVAL: .
    :cvar DGPS_REMOVAL: .
    :cvar DGPS_TEMPORARY_REMOVAL: .
    :cvar EGNOS_REMOVAL: .
    :cvar EGNOS_TEMPORARY_REMOVAL: .
    :cvar LORAN_C_STATION_REMOVAL: .
    :cvar LORAN_C_STATION_TEMPORARY_REMOVAL: .
    :cvar E_LORAN_REMOVAL: .
    :cvar E_LORAN_TEMPORARY_REMOVAL: .
    :cvar CHAYKA_STATION_REMOVAL: .
    :cvar CHAYKA_STATION_TEMPORARY_REMOVAL: .
    :cvar E_CHAYKA_STATION_REMOVAL: .
    :cvar E_CHAYKA_STATION_TEMPORARY_REMOVAL: .
    """

    BUOY_REMOVAL = "Buoy removal"
    BUOY_TEMPORARY_REMOVAL = "Buoy temporary removal"
    LIGHT_REMOVAL = "Light removal"
    LIGHT_TEMPORARY_REMOVAL = "Light temporary removal"
    BEACON_REMOVAL = "Beacon removal"
    BEACON_TEMPORARY_REMOVAL = "Beacon temporary removal"
    FOG_SIGNAL_REMOVAL = "Fog signal removal"
    FOG_SIGNAL_TEMPORARY_REMOVAL = "Fog signal temporary removal"
    AUDIBLE_SIGNAL_REMOVAL = "Audible signal removal"
    AUDIBLE_SIGNAL_TEMPORARY_REMOVAL = "Audible signal temporary removal"
    V_AIS_REMOVAL = "V-AIS removal"
    V_AIS_TEMPORARY_REMOVAL = "V-AIS temporary removal"
    RACON_SIGNAL_REMOVAL = "RACON signal removal"
    RACON_TEMPORARY_REMOVAL = "RACON temporary removal"
    DGPS_REMOVAL = "DGPS removal"
    DGPS_TEMPORARY_REMOVAL = "DGPS temporary removal"
    EGNOS_REMOVAL = "EGNOS removal"
    EGNOS_TEMPORARY_REMOVAL = "EGNOS temporary removal"
    LORAN_C_STATION_REMOVAL = "LORAN C station removal"
    LORAN_C_STATION_TEMPORARY_REMOVAL = "LORAN C station temporary removal"
    E_LORAN_REMOVAL = "eLORAN removal"
    E_LORAN_TEMPORARY_REMOVAL = "eLORAN temporary removal"
    CHAYKA_STATION_REMOVAL = "Chayka station removal"
    CHAYKA_STATION_TEMPORARY_REMOVAL = "Chayka station temporary removal"
    E_CHAYKA_STATION_REMOVAL = "e-Chayka station removal"
    E_CHAYKA_STATION_TEMPORARY_REMOVAL = "e-Chayka station temporary removal"


class AtonReplacementType(Enum):
    """
    :cvar BUOY_CHANGE: .
    :cvar BUOY_TEMPORARY_CHANGE: .
    :cvar LIGHT_CHANGE: .
    :cvar LIGHT_TEMPORARY_CHANGE: .
    :cvar SECTOR_LIGHT_CHANGE: .
    :cvar SECTOR_LIGHT_TEMPORARY_CHANGE: .
    :cvar BEACON_CHANGE: .
    :cvar BEACON_TEMPORARY_CHANGE: .
    :cvar FOG_SIGNAL_CHANGE: .
    :cvar FOG_SIGNAL_TEMPORARY_CHANGE: .
    :cvar AUDIBLE_SIGNAL_CHANGE: .
    :cvar AUDIBLE_SIGNAL_TEMPORARY_CHANGE: .
    :cvar V_AIS_CHANGE: .
    :cvar V_AIS_TEMPORARY_CHANGE: .
    :cvar RACON_SIGNAL_CHANGE: .
    :cvar RACON_TEMPORARY_CHANGE: .
    """

    BUOY_CHANGE = "Buoy change"
    BUOY_TEMPORARY_CHANGE = "Buoy temporary change"
    LIGHT_CHANGE = "Light change"
    LIGHT_TEMPORARY_CHANGE = "Light temporary change"
    SECTOR_LIGHT_CHANGE = "Sector light change"
    SECTOR_LIGHT_TEMPORARY_CHANGE = "Sector light temporary change"
    BEACON_CHANGE = "Beacon change"
    BEACON_TEMPORARY_CHANGE = "Beacon temporary change"
    FOG_SIGNAL_CHANGE = "Fog signal change"
    FOG_SIGNAL_TEMPORARY_CHANGE = "Fog signal temporary change"
    AUDIBLE_SIGNAL_CHANGE = "Audible signal change"
    AUDIBLE_SIGNAL_TEMPORARY_CHANGE = "Audible signal temporary change"
    V_AIS_CHANGE = "V-AIS change"
    V_AIS_TEMPORARY_CHANGE = "V-AIS temporary change"
    RACON_SIGNAL_CHANGE = "RACON signal change"
    RACON_TEMPORARY_CHANGE = "RACON temporary change"


class AudibleSignalAtonChangeType(Enum):
    """
    :cvar AUDIBLE_SIGNAL_OUT_OF_SERVICE: .
    :cvar FOG_SIGNAL_OUT_OF_SERVICE: .
    :cvar AUDIBLE_SIGNAL_OPERATING_PROPERLY: .
    :cvar FOG_SIGNAL_OPERATING_PROPERLY: .
    """

    AUDIBLE_SIGNAL_OUT_OF_SERVICE = "Audible signal out of service"
    FOG_SIGNAL_OUT_OF_SERVICE = "Fog signal out of service"
    AUDIBLE_SIGNAL_OPERATING_PROPERLY = "Audible signal operating properly"
    FOG_SIGNAL_OPERATING_PROPERLY = "Fog signal operating properly"


class BeaconShapeType(Enum):
    """
    :cvar STAKE_POLE_PERCH_POST: An elongated wood or metal pole, driven
        into the ground or seabed, which serves as a navigational aid or
        a support for a navigational aid.
    :cvar WITHY: A tree without roots stuck or spoiled into the bottom
        of the sea to serve as a navigational aid.
    :cvar BEACON_TOWER: A solid structure of the order of 10 metres in
        height used as a navigational aid.
    :cvar LATTICE_BEACON: A structure consisting of strips of metal or
        wood crossed or interlaced to form a structure to serve as an
        aid to navigation or as a support for an aid to navigation.
    :cvar PILE_BEACON: A long heavy timber(s) or section(s) of steel,
        wood, concrete, etc., forced into the seabed to serve as an aid
        to navigation or as a support for an aid to navigation.
    :cvar CAIRN: A mound of stones, usually conical or pyramidal, raised
        as a landmark or to designate a point of importance in
        surveying.
    :cvar BUOYANT_BEACON: A tall spar-like beacon fitted with a
        permanently submerged buoyancy chamber, the lower end of the
        body is secured to seabed sinker either by a flexible joint or
        by a cable under tension.
    """

    STAKE_POLE_PERCH_POST = "Stake, Pole, Perch, Post"
    WITHY = "Withy"
    BEACON_TOWER = "Beacon Tower"
    LATTICE_BEACON = "Lattice Beacon"
    PILE_BEACON = "Pile Beacon"
    CAIRN = "Cairn"
    BUOYANT_BEACON = "Buoyant Beacon"


class BuildingShapeType(Enum):
    """
    :cvar HIGH_RISE_BUILDING: A building having many storeys.
    :cvar PYRAMID: A polyhedron of which one face is a polygon of any
        number of sides, and the other faces are triangles with a common
        vertex.
    :cvar CYLINDRICAL: Shaped like a cylinder, which is a solid
        geometrical figure generated by straight lines fixed in
        direction and describing with one of its points a closed curve,
        especially a circle.
    :cvar SPHERICAL: Shaped like a sphere, which is a body the surface
        of which is at all points equidistant from the centre.
    :cvar CUBIC: A shape the sides of which are six equal squares; a
        regular hexahedron.
    """

    HIGH_RISE_BUILDING = "High-Rise Building"
    PYRAMID = "Pyramid"
    CYLINDRICAL = "Cylindrical"
    SPHERICAL = "Spherical"
    CUBIC = "Cubic"


class BuoyShapeType(Enum):
    """
    :cvar CONICAL: The upper part of the body above the water-line, or
        the greater part of the superstructure, has approximately the
        shape or the appearance of a pointed cone with the point
        upwards.
    :cvar CAN: The upper part of the body above the water-line, or the
        greater part of the superstructure, has the shape of a cylinder,
        or a truncated cone that approximates to a cylinder, with a flat
        end uppermost.
    :cvar SPHERICAL: Shaped like a sphere, which is a body the surface
        of which is at all points equidistant from the centre.
    :cvar PILLAR: The upper part of the body above the water-line, or
        the greater part of the superstructure is a narrow vertical
        structure, pillar or lattice tower.
    :cvar SPAR: The upper part of the body above the water-line, or the
        greater part of the superstructure, has the form of a pole, or
        of a very long cylinder, floating upright.
    :cvar BARREL: The upper part of the body above the water-line, or
        the greater part of the superstructure, has the form of a barrel
        or cylinder floating horizontally.
    :cvar SUPERBUOY: A very large buoy designed to carry a signal light
        of high luminous intensity at a high elevation.
    :cvar ICE_BUOY: A specially constructed shuttle shaped buoy which is
        used in ice conditions.
    """

    CONICAL = "Conical"
    CAN = "Can"
    SPHERICAL = "Spherical"
    PILLAR = "Pillar"
    SPAR = "Spar"
    BARREL = "Barrel"
    SUPERBUOY = "Superbuoy"
    ICE_BUOY = "Ice Buoy"


class CategoryOfCableType(Enum):
    """
    :cvar POWER_LINE: A cable that transmits or distributes electrical
        power.
    :cvar TRANSMISSION_LINE: Multiple un-insulated cables usually
        supported by steel lattice towers. Such features are generally
        more prominent than normal power lines.
    :cvar TELEPHONE: A cable that transmits telephone signals.
    :cvar TELEGRAPH: An apparatus, system or process for communication
        at a distance by electric transmission over wire.
    :cvar MOORING_CABLE: A chain or very strong fibre or wire rope used
        to anchor or moor vessels or buoys.
    :cvar FERRY: A vessel for transporting passengers, vehicles, and/or
        goods across a stretch of water, especially as a regular
        service.
    :cvar FIBRE_OPTIC_CABLE: A cable made of glass or plastic fiber
        designed to guide light along its length, fibre optic cables are
        widely used in fiber-optic communication, which permits
        transmission over longer distances and at higher data rates than
        other forms of communication.
    """

    POWER_LINE = "Power Line"
    TRANSMISSION_LINE = "Transmission Line"
    TELEPHONE = "Telephone"
    TELEGRAPH = "Telegraph"
    MOORING_CABLE = "Mooring Cable"
    FERRY = "Ferry"
    FIBRE_OPTIC_CABLE = "Fibre Optic Cable"


class CategoryOfCardinalMarkType(Enum):
    """
    :cvar NORTH_CARDINAL_MARK: Quadrant bounded by the true bearing NW-
        NE taken from the point of interest; it should be passed to the
        north side of the mark.
    :cvar EAST_CARDINAL_MARK: Quadrant bounded by the true bearing NE-SE
        taken from the point of interest. It should be passed to the
        east side of the mark.
    :cvar SOUTH_CARDINAL_MARK: Quadrant bounded by the true bearing SE-
        SW taken from the point of interest; it should be passed to the
        south side of the mark.
    :cvar WEST_CARDINAL_MARK: Quadrant bounded by the true bearing SW-NW
        taken from the point of interest; it should be passed to the
        west side of the mark.
    """

    NORTH_CARDINAL_MARK = "North Cardinal Mark"
    EAST_CARDINAL_MARK = "East Cardinal Mark"
    SOUTH_CARDINAL_MARK = "South Cardinal Mark"
    WEST_CARDINAL_MARK = "West Cardinal Mark"


class CategoryOfFogSignalType(Enum):
    """
    :cvar EXPLOSIVE: A signal produced by the firing of explosive
        charges.
    :cvar DIAPHONE: A diaphone uses compressed air and generally emits a
        powerful low-pitched sound, which often concludes with a brief
        sound of suddenly lowered pitch, termed the 'grunt'.
    :cvar SIREN: A type of fog signal apparatus which produces sound by
        virtue of the passage of air through slots or holes in a
        revolving disk.
    :cvar NAUTOPHONE: A horn having a diaphragm oscillated by
        electricity.
    :cvar REED: [1]  A reed uses compressed air and emits a weak, high
        pitched sound.  [2]  Any of various water or marsh plants with a
        firm stem. (Concise Oxford English Dictionary)
    :cvar TYFON: A diaphragm horn which operates under the influence of
        compressed air or steam.
    :cvar BELL: A ringing sound with a short range.
    :cvar WHISTLE: A distinctive sound made by a jet of air passing
        through an orifice. The apparatus may be operated automatically,
        by hand or by air being forced up a tube by waves acting on a
        buoy.
    :cvar GONG: A sound produced by vibration of a disc when struck.
    :cvar HORN: A horn uses compressed air or electricity to vibrate a
        diaphragm and exists in a variety of types which differ greatly
        in their sound and power.
    """

    EXPLOSIVE = "Explosive"
    DIAPHONE = "Diaphone"
    SIREN = "Siren"
    NAUTOPHONE = "Nautophone"
    REED = "Reed"
    TYFON = "Tyfon"
    BELL = "Bell"
    WHISTLE = "Whistle"
    GONG = "Gong"
    HORN = "Horn"


class CategoryOfInstallationBuoyType(Enum):
    """
    :cvar CATENARY_ANCHOR_LEG_MOORING: incorporates a large buoy which
        remains on the surface at all times and is moored by 4 or more
        anchors. Mooring hawsers and cargo hoses lead from a turntable
        on top of the buoy, so that the buoy does not turn as the ship
        swings to wind and stream.
    :cvar SINGLE_BUOY_MOORING: a mooring structure used by tankers to
        load and unload in port approaches or in offshore oil and gas
        fields. The size of the structure can vary between a large
        mooring buoy and a manned floating structure. Also known as
        single point mooring (SPM)
    """

    CATENARY_ANCHOR_LEG_MOORING = "Catenary Anchor Leg Mooring"
    SINGLE_BUOY_MOORING = "Single Buoy Mooring"


class CategoryOfLandmarkType(Enum):
    """
    :cvar CAIRN: A mound of stones, usually conical or pyramidal, raised
        as a landmark or to designate a point of importance in
        surveying.
    :cvar CEMETERY: A site and associated structures devoted to the
        burial of the dead.
    :cvar CHIMNEY: A vertical structure containing a passage or flue for
        discharging smoke and gases of combustion.
    :cvar DISH_AERIAL: A parabolic aerial for the receipt and
        transmission of high frequency radio signals.
    :cvar FLAGSTAFF: A staff or pole on which flags are raised.
    :cvar FLARE_STACK: A tall structure used for burning-off waste oil
        or gas.
    :cvar MAST: A relatively tall structure usually held vertical by guy
        lines.
    :cvar WINDSOCK: A tapered fabric sleeve mounted so as to catch and
        swing with the wind, thus indicating the wind direction.
    :cvar MONUMENT: A structure erected and/or maintained as a memorial
        to a person and/or event.
    :cvar COLUMN_PILLAR: A cylindrical or slightly tapering body of
        considerably greater length than diameter erected vertically.
    :cvar MEMORIAL_PLAQUE: A slab of metal, usually ornamented, erected
        as a memorial to a person or event.
    :cvar OBELISK: A tapering shaft usually of stone or concrete, square
        or rectangular in section, with a pyramidal apex.
    :cvar STATUE: A representation of a living being, sculptured,
        moulded, or cast in a variety of materials (for example: marble,
        metal, or plaster).
    :cvar CROSS: A monument, or other structure in form of a cross.
    :cvar DOME: A landmark comprising a hemispherical or spheroidal
        shaped structure.
    :cvar RADAR_SCANNER: A device used for directing a radar beam
        through a search pattern.
    :cvar TOWER: A relatively tall, narrow structure that may either
        stand alone or may form part of another structure.
    :cvar WINDMILL: A system of vanes attached to a tower and driven by
        wind (excluding wind turbines).
    :cvar WINDMOTOR: A modern structure for the use of wind power.
    :cvar SPIRE_MINARET: A tall conical or pyramid-shaped structure
        often built on the roof or tower of a building, especially a
        church or mosque.
    :cvar LARGE_ROCK_OR_BOULDER_ON_LAND: An isolated rocky formation or
        a single large stone.
    :cvar TRIANGULATION_MARK: A recoverable point on the earth, whose
        geographic position has been determined by angular methods with
        geodetic instruments. A triangulation point is a selected point,
        which has been marked with a station mark, or it is a
        conspicuous natural or artificial feature.
    :cvar BOUNDARY_MARK: A marker identifying the location of a surveyed
        boundary line.
    :cvar OBSERVATION_WHEEL: Wheels with passenger cars mounted external
        to the rim and independently rotated by electric motors.
    :cvar TORII: A form of decorative gateway or portal, consisting of
        two upright wooden posts connected at the top by two horizontal
        crosspieces, commonly found at the entrance to Shinto temples.
    :cvar BRIDGE: (1) An elevated structure extending across or over the
        weather deck of a vessel, or part of such a structure. The term
        is sometimes modified to indicate the intended use, such as
        navigating bridge or signal bridge.  (2) A structure erected
        over a depression or an obstacle such as a body of water,
        railroad, etc., to provide a roadway for vehicles or
        pedestrians.
    :cvar DAM: A barrier to check or confine anything in motion;
        particularly one constructed to hold back water and raise its
        level to form a reservoir, or to prevent flooding.
    """

    CAIRN = "Cairn"
    CEMETERY = "Cemetery"
    CHIMNEY = "Chimney"
    DISH_AERIAL = "Dish Aerial"
    FLAGSTAFF = "Flagstaff"
    FLARE_STACK = "Flare Stack"
    MAST = "Mast"
    WINDSOCK = "Windsock"
    MONUMENT = "Monument"
    COLUMN_PILLAR = "Column/Pillar"
    MEMORIAL_PLAQUE = "Memorial Plaque"
    OBELISK = "Obelisk"
    STATUE = "Statue"
    CROSS = "Cross"
    DOME = "Dome"
    RADAR_SCANNER = "Radar Scanner"
    TOWER = "Tower"
    WINDMILL = "Windmill"
    WINDMOTOR = "Windmotor"
    SPIRE_MINARET = "Spire/Minaret"
    LARGE_ROCK_OR_BOULDER_ON_LAND = "Large Rock or Boulder on Land"
    TRIANGULATION_MARK = "Triangulation Mark"
    BOUNDARY_MARK = "Boundary Mark"
    OBSERVATION_WHEEL = "Observation Wheel"
    TORII = "Torii"
    BRIDGE = "Bridge"
    DAM = "Dam"


class CategoryOfLateralMarkType(Enum):
    """
    :cvar PORT_HAND_LATERAL_MARK: Indicates the port boundary of a
        navigational channel or suggested route when proceeding in the
        "conventional direction of buoyage".
    :cvar STARBOARD_HAND_LATERAL_MARK: Indicates the starboard boundary
        of a navigational channel or suggested route when proceeding in
        the "conventional direction of buoyage".
    :cvar PREFERRED_CHANNEL_TO_STARBOARD_LATERAL_MARK: At a point where
        a channel divides, when proceeding in the "conventional
        direction of buoyage", the preferred channel (or primary route)
        is indicated by a modified port-hand lateral mark.
    :cvar PREFERRED_CHANNEL_TO_PORT_LATERAL_MARK: At a point where a
        channel divides, when proceeding in the "conventional direction
        of buoyage", the preferred channel (or primary route) is
        indicated by a modified starboard-hand lateral mark.
    """

    PORT_HAND_LATERAL_MARK = "Port-Hand Lateral Mark"
    STARBOARD_HAND_LATERAL_MARK = "Starboard-Hand Lateral Mark"
    PREFERRED_CHANNEL_TO_STARBOARD_LATERAL_MARK = (
        "Preferred Channel to Starboard Lateral Mark"
    )
    PREFERRED_CHANNEL_TO_PORT_LATERAL_MARK = (
        "Preferred Channel to Port Lateral Mark"
    )


class CategoryOfLightType(Enum):
    """
    :cvar DIRECTIONAL_FUNCTION: A light illuminating a sector of very
        narrow angle and intended to mark a direction to follow.
    :cvar LEADING_LIGHT: A light associated with other lights so as to
        form a leading line to be followed.
    :cvar AERO_LIGHT: An aero light is established for aeronautical
        navigation and may be of higher power than marine lights and
        visible from well offshore.
    :cvar AIR_OBSTRUCTION_LIGHT: A light marking an obstacle which
        constitutes a danger to air navigation.
    :cvar FLOOD_LIGHT: A broad beam light used to illuminate a structure
        or area.
    :cvar STRIP_LIGHT: A light whose source has a linear form generally
        horizontal, which can reach a length of several metres.
    :cvar SUBSIDIARY_LIGHT: A light placed on or near the support of a
        main light and having a special use in navigation.
    :cvar SPOTLIGHT: A powerful light focused so as to illuminate a
        small area.
    :cvar FRONT: Term used with leading lights to describe the position
        of the light on the lead as viewed from seaward.
    :cvar REAR: Term used with leading lights to describe the position
        of the light on the lead as viewed from seaward.
    :cvar LOWER: Term used with leading lights to describe the position
        of the light on the lead as viewed from seaward.
    :cvar UPPER: Term used with leading lights to describe the position
        of the light on the lead as viewed from seaward.
    :cvar EMERGENCY: A light available as a backup to a main light which
        will be illuminated should the main light fail.
    :cvar BEARING_LIGHT: A light which enables its approximate bearing
        to be obtained without the use of a compass.
    :cvar HORIZONTALLY_DISPOSED: A group of lights of identical
        character and almost identical position, that are disposed
        horizontally.
    :cvar VERTICALLY_DISPOSED: A group of lights of identical character
        and almost identical position, that are disposed vertically.
    """

    DIRECTIONAL_FUNCTION = "Directional Function"
    LEADING_LIGHT = "Leading Light"
    AERO_LIGHT = "Aero Light"
    AIR_OBSTRUCTION_LIGHT = "Air Obstruction Light"
    FLOOD_LIGHT = "Flood Light"
    STRIP_LIGHT = "Strip Light"
    SUBSIDIARY_LIGHT = "Subsidiary Light"
    SPOTLIGHT = "Spotlight"
    FRONT = "Front"
    REAR = "Rear"
    LOWER = "Lower"
    UPPER = "Upper"
    EMERGENCY = "Emergency"
    BEARING_LIGHT = "Bearing Light"
    HORIZONTALLY_DISPOSED = "Horizontally Disposed"
    VERTICALLY_DISPOSED = "Vertically Disposed"


class CategoryOfNavigationLineType(Enum):
    """
    :cvar CLEARING_LINE: A straight line that marks the boundary between
        a safe and a dangerous area or that passes clear of a
        navigational danger.
    :cvar TRANSIT_LINE: A line passing through one or more fixed marks.
    :cvar LEADING_LINE_BEARING_A_RECOMMENDED_TRACK: A line passing
        through one or more clearly defined objects, along the path of
        which a vessel can approach safely up to a certain distance off.
    """

    CLEARING_LINE = "Clearing Line"
    TRANSIT_LINE = "Transit Line"
    LEADING_LINE_BEARING_A_RECOMMENDED_TRACK = (
        "Leading Line Bearing a Recommended Track"
    )


class CategoryOfOffshorePlatformType(Enum):
    """
    :cvar OIL_RIG: A temporary mobile structure, either fixed or
        floating, used in the exploration stages of oil and gas fields.
    :cvar PRODUCTION_PLATFORM: A term used to indicate a permanent
        offshore structure equipped to control the flow of oil or gas.
        It does not include entirely submarine structures.
    :cvar OBSERVATION_RESEARCH_PLATFORM: A platform from which one's
        surroundings or events can be observed, noted or recorded such
        as for scientific study.
    :cvar ARTICULATED_LOADING_PLATFORM: A metal lattice tower, buoyant
        at one end and attached at the other by a universal joint to a
        concrete filled base on the sea bed. The platform may be fitted
        with a helicopter platform, emergency accommodation and
        hawser/hose retrieval.
    :cvar SINGLE_ANCHOR_LEG_MOORING: A rigid frame or tube with a
        buoyancy device at its upper end , secured at its lower end to a
        universal joint on a large steel or concrete base resting on the
        sea bed, and at its upper end to a mooring buoy by a chain or
        wire.
    :cvar MOORING_TOWER: A platform secured to the sea bed and
        surmounted by a turntable to which ships moor.
    :cvar ARTIFICIAL_ISLAND: A man-made structure usually built for the
        exploration or exploitation of marine resources, marine
        scientific research, tidal observations, etc.
    :cvar FLOATING_PRODUCTION_STORAGE_AND_OFF_LOADING_VESSEL: An
        offshore oil/gas facility consisting of a moored tanker/barge by
        which the product is extracted, stored and exported.
    :cvar ACCOMMODATION_PLATFORM: A platform used primarily for eating,
        sleeping and recreation purposes.
    :cvar NAVIGATION_COMMUNICATION_AND_CONTROL_BUOY: A floating
        structure with control room, power and storage facilities,
        attached to the sea bed by a flexible pipeline and cables.
    :cvar FLOATING_OIL_TANK: A floating structure, anchored to the
        seabed, for storing oil.
    """

    OIL_RIG = "Oil Rig"
    PRODUCTION_PLATFORM = "Production Platform"
    OBSERVATION_RESEARCH_PLATFORM = "Observation/Research Platform"
    ARTICULATED_LOADING_PLATFORM = "Articulated Loading Platform"
    SINGLE_ANCHOR_LEG_MOORING = "Single Anchor Leg Mooring"
    MOORING_TOWER = "Mooring Tower"
    ARTIFICIAL_ISLAND = "Artificial Island"
    FLOATING_PRODUCTION_STORAGE_AND_OFF_LOADING_VESSEL = (
        "Floating Production, Storage and Off-Loading Vessel"
    )
    ACCOMMODATION_PLATFORM = "Accommodation Platform"
    NAVIGATION_COMMUNICATION_AND_CONTROL_BUOY = (
        "Navigation, Communication and Control Buoy"
    )
    FLOATING_OIL_TANK = "Floating Oil Tank"


class CategoryOfPileType(Enum):
    """
    :cvar STAKE: An elongated wood or metal pole embedded in the seabed
        to serve as a marker or support.
    :cvar POST: A vertical piece of timber, metal or concrete forced
        into the earth or sea bed.
    :cvar TRIPODAL: A single structure comprising 3 or more piles held
        together (sections of heavy timber, steel or concrete), and
        forced into the earth or sea bed.
    :cvar PILING: A number of piles, usually in a straight line, and
        usually connected or bolted together.
    :cvar AREA_OF_PILES: A number of piles, usually in a straight line,
        but not connected by structural members.
    :cvar PIPE: A vertical hollow cylinder of metal, wood, or other
        material forced into the earth or seabed.
    """

    STAKE = "Stake"
    POST = "Post"
    TRIPODAL = "Tripodal"
    PILING = "Piling"
    AREA_OF_PILES = "Area of Piles"
    PIPE = "Pipe"


class CategoryOfRadarTransponderBeaconType(Enum):
    """
    :cvar RAMARK_RADAR_BEACON_TRANSMITTING_CONTINUOUSLY: A radar marker
        beacon which continuously transmits a signal appearing as a
        radial line on a radar screen, the line indicating the direction
        of the beacon. Ramarks are intended primarily for marine use.
        The name 'ramark' is derived from the words radar marker.
    :cvar RACON_RADAR_TRANSPONDER_BEACON: A radar beacon which returns a
        coded signal which provides identification of the beacon, as
        well as range and bearing. The range and bearing are indicated
        by the location of the first character received on the radar
        screen. The name 'racon' is derived from the words radar beacon.
    :cvar LEADING_RACON_RADAR_TRANSPONDER_BEACON: A radar beacon that
        may be used (in conjunction with at least one other radar
        beacon) to indicate a leading line.
    """

    RAMARK_RADAR_BEACON_TRANSMITTING_CONTINUOUSLY = (
        "Ramark, Radar Beacon Transmitting Continuously"
    )
    RACON_RADAR_TRANSPONDER_BEACON = "Racon, Radar Transponder Beacon"
    LEADING_RACON_RADAR_TRANSPONDER_BEACON = (
        "Leading Racon/Radar Transponder Beacon"
    )


class CategoryOfRadioStationType(Enum):
    """
    :cvar CIRCULAR_NON_DIRECTIONAL_MARINE_OR_AERO_MARINE_RADIOBEACON: A
        radio station which need not necessarily be manned, the
        emissions of which, radiated around the horizon, enable its
        bearing to be determined by means of the radio direction finder
        of a ship.
    :cvar DIRECTIONAL_RADIOBEACON: A special type of radiobeacon station
        the emissions of which are intended to provide a definite track
        for guidance.
    :cvar ROTATING_PATTERN_RADIOBEACON: A special type of radiobeacon
        station emitting a beam of waves to which a uniform turning
        movement is given, the bearing of the station being determined
        by means of an ordinary listening receiver and a stop watch.
        Also referred to as a rotating loop radiobeacon.
    :cvar CONSOL_BEACON: A type of long range position fixing beacon.
    :cvar RADIO_DIRECTION_FINDING_STATION: A radio station intended to
        determine only the direction of other stations by means of
        transmission from the latter.
    :cvar COAST_RADIO_STATION_PROVIDING_QTG_SERVICE: A radio station
        which is prepared to provide QTG service; that is to say, to
        transmit upon request from a ship a radio signal, the bearing of
        which can be taken by that ship.
    :cvar AERONAUTICAL_RADIOBEACON: A radio beacon designed for
        aeronautical use.
    :cvar DECCA: The Decca Navigator System is a high accuracy, short to
        medium range radio navigational aid intended for coastal and
        landfall navigation.
    :cvar LORAN_C: A low frequency electronic position fixing system
        using pulsed transmissions at 100 Khz.
    :cvar DIFFERENTIAL_GNSS: A radiobeacon transmitting DGPS correction
        signals.
    :cvar TORAN: An electronic position fixing system used mainly by
        aircraft.
    :cvar OMEGA: A long-range radio navigational aid which operates
        within the VLF frequency band. The system comprises eight land
        based stations.
    :cvar SYLEDIS: A ranging position fixing system operating at 420-450
        MHz over a range of up to 400 Km.
    :cvar CHAIKA: Chaika is a low frequency electronic position fixing
        system using pulsed transmissions at 100 Khz.
    :cvar RADIO_TELEPHONE_STATION: The equipment needed at one station
        to carry on two way voice communication by radio waves only.
    :cvar AIS_BASE_STATION: An onshore AIS unit that monitors traffic in
        the waterways.
    """

    CIRCULAR_NON_DIRECTIONAL_MARINE_OR_AERO_MARINE_RADIOBEACON = (
        "Circular (Non-Directional) Marine or Aero-Marine Radiobeacon"
    )
    DIRECTIONAL_RADIOBEACON = "Directional Radiobeacon"
    ROTATING_PATTERN_RADIOBEACON = "Rotating Pattern Radiobeacon"
    CONSOL_BEACON = "Consol Beacon"
    RADIO_DIRECTION_FINDING_STATION = "Radio Direction-Finding Station"
    COAST_RADIO_STATION_PROVIDING_QTG_SERVICE = (
        "Coast Radio Station Providing QTG Service"
    )
    AERONAUTICAL_RADIOBEACON = "Aeronautical Radiobeacon"
    DECCA = "Decca"
    LORAN_C = "Loran C"
    DIFFERENTIAL_GNSS = "Differential GNSS"
    TORAN = "Toran"
    OMEGA = "Omega"
    SYLEDIS = "Syledis"
    CHAIKA = "Chaika"
    RADIO_TELEPHONE_STATION = "Radio Telephone Station"
    AIS_BASE_STATION = "AIS Base Station"


class CategoryOfSiloTankType(Enum):
    """
    :cvar SILO_IN_GENERAL: A large storage structure used for storing
        loose materials.
    :cvar TANK_IN_GENERAL: A fixed structure for storing liquids.
    :cvar GRAIN_ELEVATOR: A storage building for grain. Usually a tall
        frame, metal or concrete structure with an especially
        compartmented interior.
    :cvar WATER_TOWER: A tower supporting an elevated storage tank of
        water.
    """

    SILO_IN_GENERAL = "Silo in General"
    TANK_IN_GENERAL = "Tank in General"
    GRAIN_ELEVATOR = "Grain Elevator"
    WATER_TOWER = "Water Tower"


class CategoryOfSpecialPurposeMarkType(Enum):
    """
    :cvar FIRING_DANGER_MARK: A mark used to indicate a firing danger
        area, usually at sea.
    :cvar TARGET_MARK: Any object toward which something is directed.
        The distinctive marking or instrumentation of a ground point to
        aid its identification on a photograph.
    :cvar MARKER_SHIP_MARK: A mark marking the position of a ship which
        is used as a target during some military exercise.
    :cvar DEGAUSSING_RANGE_MARK: A mark used to indicate a degaussing
        range.
    :cvar BARGE_MARK: A mark of relevance to barges.
    :cvar CABLE_MARK: A mark used to indicate the position of submarine
        cables or the point at which they run on to the land.
    :cvar SPOIL_GROUND_MARK: A mark used to indicate the limit of a
        spoil ground.
    :cvar OUTFALL_MARK: A mark used to indicate the position of an
        outfall or the point at which it leaves the land.
    :cvar ODAS: Ocean Data Acquisition System.
    :cvar RECORDING_MARK: A mark used to record data for scientific
        purposes.
    :cvar SEAPLANE_ANCHORAGE_MARK: A mark used to indicate a seaplane
        anchorage.
    :cvar RECREATION_ZONE_MARK: A mark used to indicate a recreation
        zone.
    :cvar PRIVATE_MARK: A privately maintained mark.
    :cvar MOORING_MARK: A mark indicating a mooring or moorings.
    :cvar LANBY: A large buoy designed to take the place of a lightship
        where construction of an offshore light station is not feasible.
    :cvar LEADING_MARK: Aids to navigation or other indicators so
        located as to indicate the path to be followed. Leading marks
        identify a leading line when they are in transit.
    :cvar MEASURED_DISTANCE_MARK: A mark forming part of a transit
        indicating one end of a measured distance.
    :cvar NOTICE_MARK: A notice board or sign indicating information to
        the mariner.
    :cvar TSS_MARK: A mark indicating a Traffic Separation Scheme.
    :cvar ANCHORING_PROHIBITED_MARK: A mark indicating an anchoring
        prohibited area.
    :cvar BERTHING_PROHIBITED_MARK: A mark indicating that berthing is
        prohibited.
    :cvar OVERTAKING_PROHIBITED_MARK: A mark indicating that overtaking
        is prohibited.
    :cvar TWO_WAY_TRAFFIC_PROHIBITED_MARK: A mark indicating a one-way
        route.
    :cvar REDUCED_WAKE_MARK: A mark indicating that vessels must not
        generate excessive wake.
    :cvar SPEED_LIMIT_MARK: A mark indicating that a speed limit
        applies.
    :cvar STOP_MARK: A mark indicating the place where the bow of a ship
        must stop when traffic lights show red.
    :cvar GENERAL_WARNING_MARK: A mark indicating that special caution
        must be exercised in the vicinity of the mark.
    :cvar SOUND_SHIP_S_SIREN_MARK: A mark indicating that a ship should
        sound its siren or horn.
    :cvar RESTRICTED_VERTICAL_CLEARANCE_MARK: A mark indicating the
        minimum vertical space available for passage.
    :cvar MAXIMUM_VESSEL_S_DRAUGHT_MARK: A mark indicating the maximum
        draught of vessel permitted.
    :cvar RESTRICTED_HORIZONTAL_CLEARANCE_MARK: A mark indicating the
        minimum horizontal space available for passage.
    :cvar STRONG_CURRENT_WARNING_MARK: A mark warning of strong
        currents.
    :cvar BERTHING_PERMITTED_MARK: A mark indicating that berthing is
        allowed.
    :cvar OVERHEAD_POWER_CABLE_MARK: A mark indicating an overhead power
        cable.
    :cvar CHANNEL_EDGE_GRADIENT_MARK: A mark indicating the gradient of
        the slope of a dredge channel edge.
    :cvar TELEPHONE_MARK: A mark indicating the presence of a telephone.
    :cvar FERRY_CROSSING_MARK: A mark indicating that a ferry route
        crosses the ship route; often used with a 'sound ship's siren'
        mark.
    :cvar PIPELINE_MARK: A mark used to indicate the position of
        submarine pipelines or the point at which they run on to the
        land.
    :cvar ANCHORAGE_MARK: A mark indicating an anchorage area.
    :cvar CLEARING_MARK: A mark used to indicate a clearing line.
    :cvar CONTROL_MARK: A mark indicating the location at which a
        restriction or requirement exists.
    :cvar DIVING_MARK: A mark indicating that diving may take place in
        the vicinity.
    :cvar REFUGE_BEACON: A mark providing or indicating a place of
        safety.
    :cvar FOUL_GROUND_MARK: A mark indicating a foul ground.
    :cvar YACHTING_MARK: A mark installed for use by yachtsmen.
    :cvar HELIPORT_MARK: A mark indicating an area where helicopters may
        land.
    :cvar GNSS_MARK: A mark indicating a location at which a GNSS
        position has been accurately determined.
    :cvar SEAPLANE_LANDING_MARK: A mark indicating an area where sea-
        planes land.
    :cvar ENTRY_PROHIBITED_MARK: A mark indicating that entry is
        prohibited.
    :cvar WORK_IN_PROGRESS_MARK: A mark indicating that work (generally
        construction) is in progress.
    :cvar MARK_WITH_UNKNOWN_PURPOSE: A mark whose detailed
        characteristics are unknown.
    :cvar WELLHEAD_MARK: A mark indicating a borehole that produces or
        is capable of producing oil or natural gas.
    :cvar CHANNEL_SEPARATION_MARK: A mark indicating the point at which
        a channel divides separately into two channels.
    :cvar MARINE_FARM_MARK: A mark indicating the existence of a fish,
        mussel, oyster or pearl farm/culture.
    :cvar ARTIFICIAL_REEF_MARK: A mark indicating the existence or the
        extent of an artificial reef.
    :cvar ICE_MARK: A mark, used year round, that may be submerged when
        ice passes through the area.
    :cvar NATURE_RESERVE_MARK: A mark used to define the boundary of a
        nature reserve.
    :cvar FISH_AGGREGATING_DEVICE: A fish aggregating (or aggregation)
        device (FAD) is a man-made object used to attract ocean going
        pelagic fish such as marlin, tuna and mahi-mahi (dolphin fish).
        They usually consist of buoys or floats tethered to the ocean
        floor with concrete blocks.
    :cvar WRECK_MARK: A mark used to indicate the existence of a wreck.
    :cvar CUSTOMS_MARK: A mark used to indicate the existence of a
        customs checkpoint.
    :cvar CAUSEWAY_MARK: A mark used to indicate the existence of a
        causeway.
    :cvar WAVE_RECORDER: A surface following buoy used to measure wave
        activity.
    :cvar JETSKI_PROHIBITED: A mark indicating a jetski prohibited area.
    :cvar FACILITY_PROTECTION_MARK: -
    :cvar OIL_PIPELINE_PROTECTION_MARK: -
    :cvar MARINE_CABLE_PROTECTION_MARK: -
    """

    FIRING_DANGER_MARK = "Firing Danger Mark"
    TARGET_MARK = "Target Mark"
    MARKER_SHIP_MARK = "Marker Ship Mark"
    DEGAUSSING_RANGE_MARK = "Degaussing Range Mark"
    BARGE_MARK = "Barge Mark"
    CABLE_MARK = "Cable Mark"
    SPOIL_GROUND_MARK = "Spoil Ground Mark"
    OUTFALL_MARK = "Outfall Mark"
    ODAS = "ODAS"
    RECORDING_MARK = "Recording Mark"
    SEAPLANE_ANCHORAGE_MARK = "Seaplane Anchorage Mark"
    RECREATION_ZONE_MARK = "Recreation Zone Mark"
    PRIVATE_MARK = "Private Mark"
    MOORING_MARK = "Mooring Mark"
    LANBY = "LANBY"
    LEADING_MARK = "Leading Mark"
    MEASURED_DISTANCE_MARK = "Measured Distance Mark"
    NOTICE_MARK = "Notice Mark"
    TSS_MARK = "TSS Mark"
    ANCHORING_PROHIBITED_MARK = "Anchoring Prohibited Mark"
    BERTHING_PROHIBITED_MARK = "Berthing Prohibited Mark"
    OVERTAKING_PROHIBITED_MARK = "Overtaking Prohibited Mark"
    TWO_WAY_TRAFFIC_PROHIBITED_MARK = "Two-Way Traffic Prohibited Mark"
    REDUCED_WAKE_MARK = "Reduced Wake Mark"
    SPEED_LIMIT_MARK = "Speed Limit Mark"
    STOP_MARK = "Stop Mark"
    GENERAL_WARNING_MARK = "General Warning Mark"
    SOUND_SHIP_S_SIREN_MARK = "Sound Ship's Siren Mark"
    RESTRICTED_VERTICAL_CLEARANCE_MARK = "Restricted Vertical Clearance Mark"
    MAXIMUM_VESSEL_S_DRAUGHT_MARK = "Maximum Vessel's Draught Mark"
    RESTRICTED_HORIZONTAL_CLEARANCE_MARK = (
        "Restricted Horizontal Clearance Mark"
    )
    STRONG_CURRENT_WARNING_MARK = "Strong Current Warning Mark"
    BERTHING_PERMITTED_MARK = "Berthing Permitted Mark"
    OVERHEAD_POWER_CABLE_MARK = "Overhead Power Cable Mark"
    CHANNEL_EDGE_GRADIENT_MARK = "Channel Edge Gradient Mark"
    TELEPHONE_MARK = "Telephone Mark"
    FERRY_CROSSING_MARK = "Ferry Crossing Mark"
    PIPELINE_MARK = "Pipeline Mark"
    ANCHORAGE_MARK = "Anchorage Mark"
    CLEARING_MARK = "Clearing Mark"
    CONTROL_MARK = "Control Mark"
    DIVING_MARK = "Diving Mark"
    REFUGE_BEACON = "Refuge Beacon"
    FOUL_GROUND_MARK = "Foul Ground Mark"
    YACHTING_MARK = "Yachting Mark"
    HELIPORT_MARK = "Heliport Mark"
    GNSS_MARK = "GNSS Mark"
    SEAPLANE_LANDING_MARK = "Seaplane Landing Mark"
    ENTRY_PROHIBITED_MARK = "Entry Prohibited Mark"
    WORK_IN_PROGRESS_MARK = "Work in Progress Mark"
    MARK_WITH_UNKNOWN_PURPOSE = "Mark With Unknown Purpose"
    WELLHEAD_MARK = "Wellhead Mark"
    CHANNEL_SEPARATION_MARK = "Channel Separation Mark"
    MARINE_FARM_MARK = "Marine Farm Mark"
    ARTIFICIAL_REEF_MARK = "Artificial Reef Mark"
    ICE_MARK = "Ice Mark"
    NATURE_RESERVE_MARK = "Nature Reserve Mark"
    FISH_AGGREGATING_DEVICE = "Fish Aggregating Device"
    WRECK_MARK = "Wreck Mark"
    CUSTOMS_MARK = "Customs Mark"
    CAUSEWAY_MARK = "Causeway Mark"
    WAVE_RECORDER = "Wave Recorder"
    JETSKI_PROHIBITED = "Jetski Prohibited"
    FACILITY_PROTECTION_MARK = "Facility Protection Mark"
    OIL_PIPELINE_PROTECTION_MARK = "Oil Pipeline Protection Mark"
    MARINE_CABLE_PROTECTION_MARK = "Marine Cable Protection Mark"


class CategoryOfTemporalVariationType(Enum):
    """
    :cvar EXTREME_EVENT: Indication of the possible impact of a
        significant event (for example hurricane, earthquake, volcanic
        eruption, landslide, etc), which is considered likely to have
        changed the seafloor or landscape significantly.
    :cvar LIKELY_TO_CHANGE_AND_SIGNIFICANT_SHOALING_EXPECTED: Continuous
        or frequent change (for example river siltation, sand waves,
        seasonal storms, icebergs, etc) that is likely to result in new
        significant shoaling.
    :cvar LIKELY_TO_CHANGE_BUT_SIGNIFICANT_SHOALING_NOT_EXPECTED:
        Continuous or frequent change (for example sand wave shift,
        seasonal storms, icebergs, etc) that is not likely to result in
        new significant shoaling.
    :cvar LIKELY_TO_CHANGE: Continuous or frequent change to non-
        bathymetric features (for example river siltation, glacier
        creep/recession, sand dunes, buoys, marine farms, etc).
    :cvar UNLIKELY_TO_CHANGE: Significant change to the seafloor is not
        expected.
    :cvar UNASSESSED: Not having been assessed.
    """

    EXTREME_EVENT = "Extreme Event"
    LIKELY_TO_CHANGE_AND_SIGNIFICANT_SHOALING_EXPECTED = (
        "Likely to Change and Significant Shoaling Expected"
    )
    LIKELY_TO_CHANGE_BUT_SIGNIFICANT_SHOALING_NOT_EXPECTED = (
        "Likely to Change But Significant Shoaling Not Expected"
    )
    LIKELY_TO_CHANGE = "Likely to Change"
    UNLIKELY_TO_CHANGE = "Unlikely to Change"
    UNASSESSED = "Unassessed"


class ColourPatternType(Enum):
    """
    :cvar HORIZONTAL_STRIPES: Straight bands or stripes of differing
        colours oriented horizontally.
    :cvar VERTICAL_STRIPES: Straight bands or stripes of differing
        colours oriented vertically.
    :cvar DIAGONAL_STRIPES: Straight bands or stripes of differing
        colours oriented diagonally (that is, not horizontally or
        vertically).
    :cvar SQUARED: Often referred to as checker plate, where alternate
        colours are used to create squares similar to a chess or draught
        board. The pattern may be straight or diagonal.
    :cvar STRIPES_DIRECTION_UNKNOWN: Straight bands or stripes of
        differing colours oriented in an unknown direction.
    :cvar BORDER_STRIPE: A band or stripe of colour which is displayed
        around the outer edge of the object, which may also form a
        border to an inner pattern or plain colour.
    :cvar SINGLE_COLOUR: One solid colour of uniform coverage.
    :cvar RECTANGLE: A four-sided shape that is made up of two pairs of
        parallel lines and that has four right angles, on a different
        coloured background.
    :cvar TRIANGLE: A shape that is made up of three lines and three
        angles, on a different coloured background.
    """

    HORIZONTAL_STRIPES = "Horizontal Stripes"
    VERTICAL_STRIPES = "Vertical Stripes"
    DIAGONAL_STRIPES = "Diagonal Stripes"
    SQUARED = "Squared"
    STRIPES_DIRECTION_UNKNOWN = "Stripes (Direction Unknown)"
    BORDER_STRIPE = "Border Stripe"
    SINGLE_COLOUR = "Single Colour"
    RECTANGLE = "Rectangle"
    TRIANGLE = "Triangle"


class ColourType(Enum):
    """
    :cvar WHITE: The achromatic object colour of greatest lightness
        characteristically perceived to belong to objects that reflect
        diffusely nearly all incident energy throughout the visible
        spectrum.
    :cvar BLACK: The achromatic color of least lightness
        characteristically perceived to belong to objects that neither
        reflect nor transmit light.
    :cvar RED: A color whose hue resembles that of blood or of the ruby
        or is that of the long-wave extreme of the visible spectrum.
    :cvar GREEN: Of the color green.
    :cvar BLUE: A color whose hue is that of the clear sky or that of
        the portion of the color spectrum lying between green and
        violet.
    :cvar YELLOW: A color whose hue resembles that of ripe lemons or
        sunflowers or is that of the portion of the spectrum lying
        between green and orange.
    :cvar GREY: Of the color grey.
    :cvar BROWN: Any of a group of colors between red and yellow in hue,
        of medium to low lightness, and of moderate to low saturation.
    :cvar AMBER: A variable color averaging a dark orange yellow.
    :cvar VIOLET: Any of a group of colors of reddish-blue hue, low
        lightness, and medium saturation.
    :cvar ORANGE: Any of a group of colors that are between red and
        yellow in hue.
    :cvar MAGENTA: A deep purplish red.
    :cvar PINK: Any of a group of colors bluish red to red in hue, of
        medium to high lightness, and of low to moderate saturation.
    :cvar GREEN_A: -
    :cvar GREEN_B: -
    :cvar WHITE_TEMPORARY: -
    :cvar RED_TEMPORARY: -
    :cvar YELLOW_TEMPORARY: -
    :cvar GREEN_PREFERRED: -
    :cvar GREEN_TEMPORARY: -
    """

    WHITE = "White"
    BLACK = "Black"
    RED = "Red"
    GREEN = "Green"
    BLUE = "Blue"
    YELLOW = "Yellow"
    GREY = "Grey"
    BROWN = "Brown"
    AMBER = "Amber"
    VIOLET = "Violet"
    ORANGE = "Orange"
    MAGENTA = "Magenta"
    PINK = "Pink"
    GREEN_A = "Green A"
    GREEN_B = "Green B"
    WHITE_TEMPORARY = "White Temporary"
    RED_TEMPORARY = "Red Temporary"
    YELLOW_TEMPORARY = "Yellow Temporary"
    GREEN_PREFERRED = "Green Preferred"
    GREEN_TEMPORARY = "Green Temporary"


class ConditionType(Enum):
    """
    :cvar UNDER_CONSTRUCTION: Being built but not yet capable of
        function.
    :cvar RUINED: A structure in a decayed or deteriorated condition
        resulting from neglect or disuse, or a damaged structure in need
        of repair.
    :cvar UNDER_RECLAMATION: An area of the sea, a lake or the navigable
        part of a river that is being reclaimed as land, usually by the
        dumping of earth and other material.
    :cvar WINGLESS: A windmill or wind turbine from which the vanes or
        turbine blades are missing.
    :cvar PLANNED_CONSTRUCTION: Detailed planning has been completed but
        construction has not been initiated.
    """

    UNDER_CONSTRUCTION = "Under Construction"
    RUINED = "Ruined"
    UNDER_RECLAMATION = "Under Reclamation"
    WINGLESS = "Wingless"
    PLANNED_CONSTRUCTION = "Planned Construction"


@dataclass
class ContactAddressType:
    """
    Direction or superscription of a letter, package, etc., specifying the name of
    the place to which it is directed, and optionally a contact person or
    organisation who should receive it.

    :ivar delivery_point: Details of where post can be delivered such as
        the apartment, name and/or number of a street, building or PO
        Box.
    :ivar city_name: The name of a town or city.
    :ivar administrative_division: A generic term for an administrative
        region within a country at a level below that of the sovereign
        state.
    :ivar country_name: The name of a nation.
    :ivar postal_code: Known in various countries as a postcode, or ZIP
        code, the postal code is a series of letters and/or digits that
        identifies each postal delivery area.
    """

    class Meta:
        name = "contactAddressType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    delivery_point: Optional[str] = field(
        default=None,
        metadata={
            "name": "deliveryPoint",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    city_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "cityName",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    administrative_division: Optional[str] = field(
        default=None,
        metadata={
            "name": "administrativeDivision",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    country_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "countryName",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    postal_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "postalCode",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


class ElectronicAtonChangeType(Enum):
    """
    :cvar AIS_TRANSMITTER_OUT_OF_SERVICE: .
    :cvar AIS_TRANSMITTER_UNRELIABLE: .
    :cvar AIS_TRANSMITTER_OPERATING_PROPERLY: .
    :cvar V_AIS_OUT_OF_SERVICE: .
    :cvar V_AIS_UNRELIABLE: .
    :cvar V_AIS_OPERATING_PROPERLY: .
    :cvar RACON_OUT_OF_SERVICE: .
    :cvar RACON_UNRELIABLE: .
    :cvar RACON_OPERATING_PROPERLY: .
    :cvar DGPS_OUT_OF_SERVICE: .
    :cvar DGPS_OPERATING_PROPERLY: .
    :cvar DGPS_UNRELIABLE: .
    :cvar LORAN_C_OPERATING_PROPERLY: .
    :cvar LORAN_C_UNRELIABLE: .
    :cvar LORAN_C_OUT_OF_SERVICE: .
    :cvar E_LORAN_OPERATING_PROPERLY: .
    :cvar E_LORAN_UNRELIABLE: .
    :cvar E_LORAN_OUT_OF_SERVICE: .
    :cvar DGLOANSS_OPERATING_PROPERLY: .
    :cvar DGLOANSS_UNRELIABLE: .
    :cvar DGLOANSS_OUT_OF_SERVICE: .
    :cvar CHAYKA_OPERATING_PROPERLY: .
    :cvar CHAYKA_UNRELIABLE: .
    :cvar CHAYKA_OUT_OF_SERVICE: .
    :cvar E_CHAYKA_OPERATING_PROPERLY: .
    :cvar E_CHAYKA_UNRELIABLE: .
    :cvar E_CHAYKA_OUT_OF_SERVICE: .
    :cvar EGNOS_OPERATING_PROPERLY: .
    :cvar EGNOS_UNRELIABLE: .
    :cvar EGNOS_OUT_OF_SERVICE: .
    """

    AIS_TRANSMITTER_OUT_OF_SERVICE = "AIS transmitter out of service"
    AIS_TRANSMITTER_UNRELIABLE = "AIS transmitter unreliable"
    AIS_TRANSMITTER_OPERATING_PROPERLY = "AIS transmitter operating properly"
    V_AIS_OUT_OF_SERVICE = "V-AIS out of service"
    V_AIS_UNRELIABLE = "V-AIS unreliable"
    V_AIS_OPERATING_PROPERLY = "V-AIS operating properly"
    RACON_OUT_OF_SERVICE = "RACON out of service"
    RACON_UNRELIABLE = "RACON unreliable"
    RACON_OPERATING_PROPERLY = "RACON operating properly"
    DGPS_OUT_OF_SERVICE = "DGPS out of service"
    DGPS_OPERATING_PROPERLY = "DGPS operating properly"
    DGPS_UNRELIABLE = "DGPS unreliable"
    LORAN_C_OPERATING_PROPERLY = "LORAN C operating properly"
    LORAN_C_UNRELIABLE = "LORAN C unreliable"
    LORAN_C_OUT_OF_SERVICE = "LORAN C out of service"
    E_LORAN_OPERATING_PROPERLY = "eLORAN operating properly"
    E_LORAN_UNRELIABLE = "eLORAN unreliable"
    E_LORAN_OUT_OF_SERVICE = "eLORAN out of service"
    DGLOANSS_OPERATING_PROPERLY = "DGLOANSS operating properly"
    DGLOANSS_UNRELIABLE = "DGLOANSS unreliable"
    DGLOANSS_OUT_OF_SERVICE = "DGLOANSS out of service"
    CHAYKA_OPERATING_PROPERLY = "Chayka operating properly"
    CHAYKA_UNRELIABLE = "Chayka unreliable"
    CHAYKA_OUT_OF_SERVICE = "Chayka out of service"
    E_CHAYKA_OPERATING_PROPERLY = "e-Chayka operating properly"
    E_CHAYKA_UNRELIABLE = "e-Chayka unreliable"
    E_CHAYKA_OUT_OF_SERVICE = "e-Chayka out of service"
    EGNOS_OPERATING_PROPERLY = "EGNOS operating properly"
    EGNOS_UNRELIABLE = "EGNOS unreliable"
    EGNOS_OUT_OF_SERVICE = "EGNOS out of service"


class ExhibitionConditionOfLightType(Enum):
    """
    :cvar LIGHT_SHOWN_WITHOUT_CHANGE_OF_CHARACTER: A light shown
        throughout the 24 hours without change of character.
    :cvar DAYTIME_LIGHT: A light which is only exhibited by day.
    :cvar FOG_LIGHT: A light which is exhibited in fog or conditions of
        reduced visibility.
    :cvar NIGHT_LIGHT: A light which is only exhibited at night.
    """

    LIGHT_SHOWN_WITHOUT_CHANGE_OF_CHARACTER = (
        "Light Shown Without Change of Character"
    )
    DAYTIME_LIGHT = "Daytime Light"
    FOG_LIGHT = "Fog Light"
    NIGHT_LIGHT = "Night Light"


@dataclass
class FeatureNameType:
    """
    Provides the name of an entity, defines the national language of the name, and
    provides the option to display the name at various system display settings.

    :ivar display_name: A statement expressing if a feature name is to
        be displayed in certain system display settings or not.
    :ivar language: The method of human communication, either spoken or
        written, consisting of the use of words in a structured and
        conventional way.
    :ivar name: The individual name of a feature.
    """

    class Meta:
        name = "featureNameType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    display_name: Optional[bool] = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    language: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )


class FixedAtonChangeType(Enum):
    """
    :cvar BEACON_MISSING: .
    :cvar BEACON_DAMAGED: .
    :cvar LIGHT_BEACON_UNLIT: .
    :cvar LIGHT_BEACON_UNRELIABLE: .
    :cvar LIGHT_BEACON_NOT_SYNCHRONIZED: .
    :cvar LIGHT_BEACON_DAMAGED: .
    :cvar BEACON_TOPMARK_MISSING: .
    :cvar BEACON_TOPMARK_DAMAGED: .
    :cvar BEACON_DAYMARK_UNRELIABLE: .
    :cvar FLOODLIT_BEACON_UNLIT: .
    :cvar BEACON_RESTORED_TO_NORMAL: .
    """

    BEACON_MISSING = "Beacon missing"
    BEACON_DAMAGED = "Beacon damaged"
    LIGHT_BEACON_UNLIT = "Light beacon Unlit"
    LIGHT_BEACON_UNRELIABLE = "Light beacon Unreliable"
    LIGHT_BEACON_NOT_SYNCHRONIZED = "Light beacon Not synchronized"
    LIGHT_BEACON_DAMAGED = "Light beacon damaged"
    BEACON_TOPMARK_MISSING = "Beacon topmark missing"
    BEACON_TOPMARK_DAMAGED = "Beacon topmark damaged"
    BEACON_DAYMARK_UNRELIABLE = "Beacon daymark unreliable"
    FLOODLIT_BEACON_UNLIT = "Floodlit beacon Unlit"
    BEACON_RESTORED_TO_NORMAL = "Beacon restored to normal"


class FloatingAtonChangeType(Enum):
    """
    :cvar BUOY_ADRIFT: .
    :cvar BUOY_DAMAGED: .
    :cvar BUOY_DAYMARK_UNRELIABLE: .
    :cvar BUOY_DESTROYED: .
    :cvar BUOY_MISSING: .
    :cvar BUOY_MOVE: .
    :cvar BUOY_OFF_POSITION: .
    :cvar BUOY_RE_ESTABLISHMENT: .
    :cvar BUOY_RESTORED_TO_NORMAL: .
    :cvar BUOY_TOPMARK_DAMAGED: .
    :cvar BUOY_TOPMARK_MISSING: .
    :cvar BUOY_WILL_BE_WITHDRAWN: .
    :cvar BUOY_WITHDRAWN: .
    :cvar DECOMMISSIONED_FOR_WINTER: .
    :cvar LIFTED_FOR_WINTER: .
    :cvar LIGHT_BUOY_LIGHT_DAMAGED: .
    :cvar LIGHT_BUOY_LIGHT_NOT_SYNCHRONIZED: .
    :cvar LIGHT_BUOY_LIGHT_UNLIT: .
    :cvar LIGHT_BUOY_LIGHT_UNRELIABLE: .
    :cvar MARINE_AIDS_TO_NAVIGATION_UNRELIABLE: .
    :cvar RECOMMISSIONED_FOR_NAVIGATION_SEASON: .
    :cvar REPLACED_BY_WINTER_SPAR: .
    :cvar SEASONAL_DECOMMISSIONING_COMPLETE: .
    :cvar SEASONAL_DECOMMISSIONING_IN_PROGRESS: .
    :cvar SEASONAL_RECOMMISSIONING_COMPLETE: .
    :cvar SEASONAL_RECOMMISSIONING_IN_PROGRESS: .
    """

    BUOY_ADRIFT = "Buoy adrift"
    BUOY_DAMAGED = "Buoy damaged"
    BUOY_DAYMARK_UNRELIABLE = "Buoy daymark unreliable"
    BUOY_DESTROYED = "Buoy destroyed"
    BUOY_MISSING = "Buoy missing"
    BUOY_MOVE = "Buoy move"
    BUOY_OFF_POSITION = "Buoy off position"
    BUOY_RE_ESTABLISHMENT = "Buoy re-establishment"
    BUOY_RESTORED_TO_NORMAL = "Buoy restored to normal"
    BUOY_TOPMARK_DAMAGED = "Buoy topmark damaged"
    BUOY_TOPMARK_MISSING = "Buoy topmark missing"
    BUOY_WILL_BE_WITHDRAWN = "Buoy will be withdrawn"
    BUOY_WITHDRAWN = "Buoy withdrawn"
    DECOMMISSIONED_FOR_WINTER = "Decommissioned for winter"
    LIFTED_FOR_WINTER = "Lifted for Winter"
    LIGHT_BUOY_LIGHT_DAMAGED = "Light buoy Light damaged"
    LIGHT_BUOY_LIGHT_NOT_SYNCHRONIZED = "Light buoy Light not synchronized"
    LIGHT_BUOY_LIGHT_UNLIT = "Light buoy Light unlit"
    LIGHT_BUOY_LIGHT_UNRELIABLE = "Light buoy Light unreliable"
    MARINE_AIDS_TO_NAVIGATION_UNRELIABLE = (
        "Marine Aids to Navigation unreliable"
    )
    RECOMMISSIONED_FOR_NAVIGATION_SEASON = (
        "Recommissioned for navigation season"
    )
    REPLACED_BY_WINTER_SPAR = "Replaced by Winter Spar"
    SEASONAL_DECOMMISSIONING_COMPLETE = "Seasonal decommissioning complete"
    SEASONAL_DECOMMISSIONING_IN_PROGRESS = (
        "Seasonal decommissioning in progress"
    )
    SEASONAL_RECOMMISSIONING_COMPLETE = "Seasonal recommissioning complete"
    SEASONAL_RECOMMISSIONING_IN_PROGRESS = (
        "Seasonal recommissioning in progress"
    )


class FunctionType(Enum):
    """
    :cvar HARBOUR_MASTERS_OFFICE: A local official who has charge of
        mooring and berthing of vessels, collecting harbour fees, etc.
    :cvar CUSTOMS_OFFICE: Serves as a government office where customs
        duties are collected, the flow of goods are regulated and
        restrictions enforced, and shipments or vehicles are cleared for
        entering or leaving a country.
    :cvar HEALTH_OFFICE: The office which is charged with the
        administration of health laws and sanitary inspections.
    :cvar HOSPITAL: An institution or establishment providing medical or
        surgical treatment for the ill or wounded.
    :cvar POST_OFFICE: The public department, agency or organisation
        responsible primarily for the collection, transmission and
        distribution of mail.
    :cvar HOTEL: An establishment, especially of a comfortable or
        luxurious kind, where paying visitors are provided with
        accommodation, meals and other services.
    :cvar RAILWAY_STATION: A building with platforms where trains
        arrive, load, discharge and depart.
    :cvar POLICE_STATION: The headquarters of a local police force and
        that is where those under arrest are first charged.
    :cvar WATER_POLICE_STATION: The headquarters of a local water-police
        force.
    :cvar PILOT_OFFICE: The office or headquarters of pilots; the place
        where the services of a pilot may be obtained.
    :cvar PILOT_LOOKOUT: A distinctive structure or place on shore from
        which personnel keep watch upon events at sea or along the
        coast.
    :cvar BANK_OFFICE: An office for custody, deposit, loan, exchange or
        issue of money.
    :cvar HEADQUARTERS_FOR_DISTRICT_CONTROL: The quarters of an
        executive officer (director, manager, etc.) with responsibility
        for an administrative area.
    :cvar TRANSIT_SHED_WAREHOUSE: A building or part of a building for
        storage of wares or goods.
    :cvar FACTORY: A building or buildings with equipment for
        manufacturing; a workshop.
    :cvar POWER_STATION: A stationary plant containing apparatus for
        large scale conversion of some form of energy (such as
        hydraulic, steam, chemical or nuclear energy) into electrical
        energy.
    :cvar ADMINISTRATIVE: A building for the management of affairs.
    :cvar EDUCATIONAL_FACILITY: A building concerned with education (for
        example school, college, university, etc).
    :cvar CHURCH: A building for public Christian worship.
    :cvar CHAPEL: A place for Christian worship other than a parish,
        cathedral or church, especially one attached to a private house
        or institution.
    :cvar TEMPLE: A building for public Jewish worship.
    :cvar PAGODA: A Hindu or Buddhist temple or sacred building.
    :cvar SHINTO_SHRINE: A building for public Shinto worship.
    :cvar BUDDHIST_TEMPLE: A building for public Buddhist worship.
    :cvar MOSQUE: A Muslim place of worship.
    :cvar MARABOUT: A shrine marking the burial place of a Muslim holy
        man.
    :cvar LOOKOUT: Keeping a watch upon events at sea or along the
        coast.
    :cvar COMMUNICATION: Transmitting and/or receiving electronic
        communication signals.
    :cvar TELEVISION: A system for reproducing on a screen visual images
        transmitted (usually with sound) by radio signals.
    :cvar RADIO: Transmitting and/or receiving radio-frequency
        electromagnetic waves as a means of communication.
    :cvar RADAR: A method, system or technique of using beamed,
        reflected, and timed radio waves for detecting, locating, or
        tracking objects, and for measuring altitudes.
    :cvar LIGHT_SUPPORT: A structure serving as a support for one or
        more lights.
    :cvar MICROWAVE: Broadcasting and receiving signals using
        microwaves.
    :cvar COOLING: Generation of chilled liquid and/or gas for cooling
        purposes.
    :cvar OBSERVATION: A place from which the surroundings can be
        observed but at which a watch is not habitually maintained.
    :cvar TIMEBALL: A visual time signal in the form of a ball.
    :cvar CLOCK: Instrument for measuring time and recording hours.
    :cvar CONTROL: Used to control the flow of traffic within a
        specified range of an installation.
    :cvar AIRSHIP_MOORING: Equipment or structure to secure an airship.
    :cvar STADIUM: An arena for holding and viewing events.
    :cvar BUS_STATION: A building where buses and coaches regularly stop
        to take on and/or let off passengers, especially for long-
        distance travel.
    :cvar PASSENGER_TERMINAL_BUILDING: A building within a terminal for
        the loading and unloading of passengers.
    :cvar SEA_RESCUE_CONTROL: A unit responsible for promoting efficient
        organization of search and rescue services and for coordinating
        the conduct of search and rescue operations within a search and
        rescue region.
    :cvar OBSERVATORY: A building designed and equipped for making
        observations of astronomical, meteorological, or other natural
        phenomena.
    :cvar ORE_CRUSHER: A building or structure used to crush ore.
    :cvar BOATHOUSE: A building or shed, usually built partly over
        water, for sheltering a boat or boats.
    :cvar PUMPING_STATION: A facility to move solids, liquids or gases
        by means of pressure or suction.
    """

    HARBOUR_MASTERS_OFFICE = "Harbour-Masters Office"
    CUSTOMS_OFFICE = "Customs Office"
    HEALTH_OFFICE = "Health Office"
    HOSPITAL = "Hospital"
    POST_OFFICE = "Post Office"
    HOTEL = "Hotel"
    RAILWAY_STATION = "Railway Station"
    POLICE_STATION = "Police Station"
    WATER_POLICE_STATION = "Water-Police Station"
    PILOT_OFFICE = "Pilot Office"
    PILOT_LOOKOUT = "Pilot Lookout"
    BANK_OFFICE = "Bank Office"
    HEADQUARTERS_FOR_DISTRICT_CONTROL = "Headquarters for District Control"
    TRANSIT_SHED_WAREHOUSE = "Transit Shed/Warehouse"
    FACTORY = "Factory"
    POWER_STATION = "Power Station"
    ADMINISTRATIVE = "Administrative"
    EDUCATIONAL_FACILITY = "Educational Facility"
    CHURCH = "Church"
    CHAPEL = "Chapel"
    TEMPLE = "Temple"
    PAGODA = "Pagoda"
    SHINTO_SHRINE = "Shinto Shrine"
    BUDDHIST_TEMPLE = "Buddhist Temple"
    MOSQUE = "Mosque"
    MARABOUT = "Marabout"
    LOOKOUT = "Lookout"
    COMMUNICATION = "Communication"
    TELEVISION = "Television"
    RADIO = "Radio"
    RADAR = "Radar"
    LIGHT_SUPPORT = "Light Support"
    MICROWAVE = "Microwave"
    COOLING = "Cooling"
    OBSERVATION = "Observation"
    TIMEBALL = "Timeball"
    CLOCK = "Clock"
    CONTROL = "Control"
    AIRSHIP_MOORING = "Airship Mooring"
    STADIUM = "Stadium"
    BUS_STATION = "Bus Station"
    PASSENGER_TERMINAL_BUILDING = "Passenger Terminal Building"
    SEA_RESCUE_CONTROL = "Sea Rescue Control"
    OBSERVATORY = "Observatory"
    ORE_CRUSHER = "Ore Crusher"
    BOATHOUSE = "Boathouse"
    PUMPING_STATION = "Pumping Station"


class HeightLengthUnitsType(Enum):
    """
    :cvar METRES: -
    :cvar FEET: -
    :cvar KILOMETRES: -
    :cvar HECTOMETRES: -
    :cvar STATUTE_MILES: -
    :cvar NAUTICAL_MILES: -
    """

    METRES = "Metres"
    FEET = "Feet"
    KILOMETRES = "Kilometres"
    HECTOMETRES = "Hectometres"
    STATUTE_MILES = "Statute Miles"
    NAUTICAL_MILES = "Nautical Miles"


class HorizontalDatumType(Enum):
    """
    :cvar WGS_72: A standard for use in cartography, geodesy, and
        satellite navigation including GPS. This standard includes the
        definition of the coordinate system's fundamental and derived
        constants, the ellipsoidal (normal) Earth Gravitational Model
        (EGM), a description of the associated World Magnetic Model
        (WMM), and a current list of local datum transformations. The
        WGS 72 is based on selected satellite, surface gravity and
        astrogeodetic data available through 1972.
    :cvar WGS_84: A standard for use in cartography, geodesy, and
        satellite navigation including GPS. This standard includes the
        definition of the coordinate system's fundamental and derived
        constants, the ellipsoidal (normal) Earth Gravitational Model
        (EGM), a description of the associated World Magnetic Model
        (WMM), and a current list of local datum transformations. WGS 84
        is the reference coordinate system used by the Global
        Positioning System.
    :cvar EUROPEAN_1950: A geodetic datum first defined in 1950 suitable
        for use in Europe - west: Andorra; Cyprus; Denmark - onshore and
        offshore; Faroe Islands - onshore; France - offshore; Germany -
        offshore North Sea; Gibraltar; Greece - offshore; Israel -
        offshore; Italy including San Marino and Vatican City State;
        Ireland offshore; Malta; Netherlands - offshore; North Sea;
        Norway including Svalbard - onshore and offshore; Portugal -
        mainland - offshore; Spain - onshore; Turkey - onshore and
        offshore; United Kingdom UKCS offshore east of 6W including
        Channel Islands (Guernsey and Jersey). Egypt - Western Desert;
        Iraq - onshore; Jordan. European Datum 1950 references the
        International 1924 ellipsoid and the Greenwich prime meridian.
        European Datum 1950 origin is Fundamental point: Potsdam
        (Helmert Tower). Latitude: 5222'51.4456"N, longitude:
        1303'58.9283"E (of Greenwich). European Datum 1950 is a geodetic
        datum for Topographic mapping, geodetic survey.
    :cvar POTSDAM_DATUM: A geodetic datum first defined in 1990 suitable
        for use in Germany - Thuringen. Potsdam Datum/83 references the
        Bessel 1841 ellipsoid and the Greenwich prime meridian. Potsdam
        Datum/83 origin is Fundamental point: Rauenberg. Latitude:
        5227'12.021"N, longitude: 1322'04.928"E (of Greenwich). This
        station was destroyed in 1910 and the station at Potsdam
        substituted as the fundamental point. Potsdam Datum/83 is a
        geodetic datum for Geodetic survey, cadastre, topographic
        mapping, engineering survey. It was defined by information from
        BKG via EuroGeographics. http://crs.bkg.bund.de PD/83 is the
        realisation of DHDN in Thuringen. It is the resultant of
        applying a transformation derived at 13 points on the border
        between East and West Germany to Pulkovo 1942/83 points in
        Thuringen.
    :cvar ADINDAN: A geodetic datum first defined in 1958 suitable for
        use in Eritrea; Ethiopia; South Sudan; Sudan. Adindan references
        the Clarke 1880 (RGS) ellipsoid and the Greenwich prime
        meridian. Adindan origin is Fundamental point: Station 15;
        Adindan. Latitude: 2210'07.110"N, longitude: 3129'21.608"E (of
        Greenwich). Adindan is a geodetic datum for Topographic mapping.
        It was defined by information from US Coast and Geodetic Survey
        via Geophysical Reasearch vol 67 #11, October 1962. The 12th
        parallel traverse of 1966-70 (Point 58 datum, code 6620) is
        connected to the Blue Nile 1958 network in western Sudan. This
        has given rise to misconceptions that the Blue Nile network is
        used in west Africa.
    :cvar AFGOOYE: A geodetic datum first defined in and suitable for
        use in Somalia - onshore. Afgooye references the Krassowsky 1940
        ellipsoid and the Greenwich prime meridian. Afgooye is a
        geodetic datum for Topographic mapping.
    :cvar AIN_EL_ABD_1970: A geodetic datum first defined in 1970 and
        suitable for use in Bahrain, Kuwait and Saudi Arabia - onshore.
        Ain el Abd 1970 references the International 1924 ellipsoid and
        the Greenwich prime meridian. Ain el Abd 1970 origin is
        Fundamental point: Ain El Abd. Latitude: 2814'06.171"N,
        longitude: 4816'20.906"E (of Greenwich). Ain el Abd 1970 is a
        geodetic datum for Topographic mapping.
    :cvar ANNA_1_ASTRO_1965: A geodetic datum first defined in 1965
        suitable for use in Cocos (Keeling) Islands - onshore. Cocos
        Islands 1965 references the Australian National Spheroid
        ellipsoid and the Greenwich prime meridian. Cocos Islands 1965
        origin is Fundamental point: Anna 1. Cocos Islands 1965 is a
        geodetic datum for Military and topographic mapping It was
        defined by information from DMA / NIMA / NGA TR8350.2 (3rd
        edition, Amendment 1, 3 January 2000).
    :cvar ANTIGUA_ISLAND_ASTRO_1943: A geodetic datum first defined in
        1943 suitable for use in Antigua island - onshore. Antigua 1943
        references the Clarke 1880 (RGS) ellipsoid and the Greenwich
        prime meridian. Antigua 1943 origin is Fundamental point:
        station A14. Antigua 1943 is a geodetic datum for Topographic
        mapping. It was defined by information from Ordnance Survey of
        Great Britain.
    :cvar ARC_1950: A geodetic datum first defined in 1950 suitable for
        use in Botswana; Malawi; Zambia; Zimbabwe. Arc 1950 references
        the Clarke 1880 (Arc) ellipsoid and the Greenwich prime
        meridian. Arc 1950 origin is Fundamental point: Buffelsfontein.
        Latitude: 3359'32.000"S, longitude: 2530'44.622"E (of
        Greenwich). Arc 1950 is a geodetic datum for Topographic
        mapping, geodetic survey.
    :cvar ARC_1960: A geodetic datum first defined in 1960 suitable for
        use in Kenya; Tanzania; Uganda. Arc 1960 references the Clarke
        1880 (RGS) ellipsoid and the Greenwich prime meridian. Arc 1960
        origin is Fundamental point: Buffelsfontein. Latitude:
        3359'32.000"S, longitude: 2530'44.622"E (of Greenwich). Arc 1960
        is a geodetic datum for Topographic mapping, geodetic survey.
    :cvar ASCENSION_ISLAND_1958: A geodetic datum first defined in 1958
        suitable for use in St Helena, Ascension and Tristan da Cunha -
        Ascension Island - onshore. Ascension Island 1958 references the
        International 1924 ellipsoid and the Greenwich prime meridian.
        Ascension Island 1958 is a geodetic datum for Military and
        topographic mapping. It was defined by information from DMA /
        NIMA / NGA TR8350.2 (3rd edition, Amendment 1, 3 January 2000).
    :cvar ASTRO_BEACON_E_1945: Astro beacon 'E' 1945
    :cvar ASTRO_DOS_71_4: A geodetic datum first defined in 1971
        suitable for use in St Helena, Ascension and Tristan da Cunha -
        St Helena Island - onshore. Astro DOS 71 references the
        International 1924 ellipsoid and the Greenwich prime meridian.
        Astro DOS 71 origin is Fundamental point: DOS 71/4, Ladder Hill
        Fort, latitude: 1555'30"S, longitude: 543'25"W (of Greenwich).
        Astro DOS 71 is a geodetic datum for Geodetic control, military
        and topographic mapping. It was defined by information from DMA
        / NIMA / NGA TR8350.2 (3rd edition, Amendment 1, 3 January 2000)
        and St. Helena Government, Environment and Natural Resources
        Directorate (ENRD).
    :cvar ASTRO_TERN_ISLAND_FRIG_1961: A geodetic datum first defined in
        1961 suitable for use in United States (USA) - Hawaii - Tern
        Island and Sorel Atoll. Tern Island 1961 references the
        International 1924 ellipsoid and the Greenwich prime meridian.
        Tern Island 1961 origin is Fundamental point: station FRIG on
        tern island, station B4 on Sorol Atoll. Tern Island 1961 is a
        geodetic datum for Military and topographic mapping It was
        defined by information from DMA / NIMA / NGA TR8350.2 (original
        1987 first edition and 3rd edition, Amendment 1, 3 January
        2000). Two independent astronomic determinations considered to
        be consistent through adoption of common transformation to WGS
        84 (see tfm code 15795).
    :cvar ASTRONOMICAL_STATION_1952: Astronomical station 1952.
    :cvar AUSTRALIAN_GEODETIC_1966: A geodetic datum first defined in
        1966 suitable for use in Australia - onshore and offshore. Papua
        New Guinea - onshore. Australian Geodetic Datum 1966 references
        the Australian National Spheroid ellipsoid and the Greenwich
        prime meridian. Australian Geodetic Datum 1966 origin is
        Fundamental point: Johnson Memorial Cairn. Latitude:
        2556'54.5515"S, longitude: 13312'30.0771"E (of Greenwich).
        Australian Geodetic Datum 1966 is a geodetic datum for
        Topographic mapping. It was defined by information from
        Australian Map Grid Technical Manual. National Mapping Council
        of Australia Technical Publication 7; 1972.
    :cvar AUSTRALIAN_GEODETIC_1984: A geodetic datum first defined in
        1984 suitable for use in Australia - Queensland, South
        Australia, Western Australia, federal areas offshore west of
        129E. Australian Geodetic Datum 1984 references the Australian
        National Spheroid ellipsoid and the Greenwich prime meridian.
        Australian Geodetic Datum 1984 origin is Fundamental point:
        Johnson Memorial Cairn. Latitude: 2556'54.5515"S, longitude:
        13312'30.0771"E (of Greenwich). Australian Geodetic Datum 1984
        is a geodetic datum for Topographic mapping. It was defined by
        information from "GDA technical manual v2_2", Intergovernmental
        Committee on Surveying and Mapping. www.anzlic.org.au/icsm/gdtm/
        Uses all data from 1966 adjustment with additional observations,
        improved software and a geoid model.
    :cvar AYABELLE_LIGHTHOUSE: A geodetic datum suitable for use in
        Djibouti - onshore and offshore. Ayabelle Lighthouse references
        the Clarke 1880 (RGS) ellipsoid and the Greenwich prime
        meridian. Ayabelle Lighthouse origin is Fundamental point:
        Ayabelle Lighthouse. Ayabelle Lighthouse is a geodetic datum for
        Military and topographic mapping. It was defined by information
        from DMA / NIMA / NGA TR8350.2 (3rd edition, Amendment 1, 3
        January 2000).
    :cvar BELLEVUE_IGN: A geodetic datum first defined in 1960 suitable
        for use in Vanuatu - southern islands - Aneityum, Efate,
        Erromango and Tanna. Bellevue references the International 1924
        ellipsoid and the Greenwich prime meridian. Bellevue is a
        geodetic datum for Military and topographic mapping. It was
        defined by information from DMA / NIMA / NGA TR8350.2 (3rd
        edition, Amendment 1, 3 January 2000). Datum covers all the
        major islands of Vanuatu in two different adjustment blocks, but
        practical usage is as given in the area of use.
    :cvar BERMUDA_1957: A geodetic datum first defined in 1957 suitable
        for use in Bermuda - onshore. Bermuda 1957 references the Clarke
        1866 ellipsoid and the Greenwich prime meridian. Bermuda 1957
        origin is Fundamental point: Fort George base. Latitude
        3222'44.36"N, longitude 6440'58.11"W (of Greenwich). Bermuda
        1957 is a geodetic datum for Topographic mapping. It was defined
        by information from Various oil industry sources.
    :cvar BISSAU: A geodetic datum first defined in and is suitable for
        use in Guinea-Bissau - onshore. Bissau references the
        International 1924 ellipsoid and the Greenwich prime meridian.
        Bissau origin is Bissau is a geodetic datum for Topographic
        mapping. It was defined by information from NIMA TR8350.2
        ftp://164.214.2.65/pub/gig/tr8350.2/changes.pdf.
    :cvar BOGOTA_OBSERVATORY: A geodetic datum first defined in 1975
        suitable for use in Colombia - mainland and offshore Caribbean.
        Bogota 1975 references the International 1924 ellipsoid and the
        Greenwich prime meridian. Bogota 1975 origin is Fundamental
        point: Bogota observatory. Latitude: 435'56.570"N, longitude:
        7404'51.300"W (of Greenwich). Bogota 1975 is a geodetic datum
        for Topographic mapping. It was defined by information from
        Instituto Geografico Agustin Codazzi (IGAC) special publication
        no. 1, 4th edition (1975) "Geodesia: Resultados Definitvos de
        Parte de las Redes Geodesicas Establecidas en el Pais". Replaces
        1951 adjustment. Replaced by MAGNA-SIRGAS (datum code 6685).
    :cvar BUKIT_RIMPAH: A geodetic datum suitable for use in Indonesia -
        Banga and Belitung Islands. Bukit Rimpah references the Bessel
        1841 ellipsoid and the Greenwich prime meridian. Bukit Rimpah
        origin is 200'40.16"S, 10551'39.76"E (of Greenwich). Bukit
        Rimpah is a geodetic datum for Topographic mapping.
    :cvar CAMP_AREA_ASTRO: A geodetic datum suitable for use in
        Antarctica - McMurdo Sound, Camp McMurdo area. Camp Area Astro
        references the International 1924 ellipsoid and the Greenwich
        prime meridian. Camp Area Astro is a geodetic datum for Geodetic
        and topographic survey. It was defined by information from DMA /
        NIMA / NGA TR8350.2 (3rd edition, Amendment 1, 3 January 2000).
    :cvar CAMPO_INCHAUSPE_1969: A geodetic datum suitable for use in
        Argentina - mainland onshore and Atlantic offshore Tierra del
        Fuego. Campo Inchauspe references the International 1924
        ellipsoid and the Greenwich prime meridian. Campo Inchauspe
        origin is Fundamental point: Campo Inchauspe. Latitude:
        3558'16.56"S, longitude: 6210'12.03"W (of Greenwich). Campo
        Inchauspe is a geodetic datum for Topographic mapping. It was
        defined by information from NIMA http://earth-info.nima.mil/
    :cvar CANTON_ASTRO_1966: A geodetic datum first defined in 1966
        suitable for use in Kiribati - Phoenix Islands: Kanton, Orona,
        McKean Atoll, Birnie Atoll, Phoenix Seamounts. Phoenix Islands
        1966 references the International 1924 ellipsoid and the
        Greenwich prime meridian. Phoenix Islands 1966 is a geodetic
        datum for Military and topographic mapping It was defined by
        information from DMA / NIMA / NGA TR8350.2 (3rd edition,
        Amendment 1, 3 January 2000).
    :cvar CAPE_DATUM: A geodetic datum suitable for use in Botswana;
        Lesotho; South Africa - mainland; Swaziland. Cape references the
        Clarke 1880 (Arc) ellipsoid and the Greenwich prime meridian.
        Cape origin is Fundamental point: Buffelsfontein. Latitude:
        3359'32.000"S, longitude: 2530'44.622"E (of Greenwich). Cape is
        a geodetic datum for Geodetic survey, cadastre, topographic
        mapping, engineering survey. It was defined by information from
        Private Communication, Directorate of Surveys and Land
        Information, Cape Town.
    :cvar CAPE_CANAVERAL: A geodetic datum first defined in 1963
        suitable for use in North America - onshore - Bahamas and USA -
        Florida (east). Cape Canaveral references the Clarke 1866
        ellipsoid and the Greenwich prime meridian. Cape Canaveral
        origin is Fundamental point: Central 1950. Latitude: 28
        29'32.36555"N, longitude 80 34'38.77362"W (of Greenwich). Cape
        Canaveral is a geodetic datum for US space and military
        operations. It was defined by information from US NGS and DMA /
        NIMA / NGA TR8350.2 (3rd edition, Amendment 1, 3 January 2000).
    :cvar CARTHAGE: A geodetic datum first defined in 1925 suitable for
        use in Tunisia - onshore and offshore. Carthage references the
        Clarke 1880 (IGN) ellipsoid and the Greenwich prime meridian.
        Carthage origin is Fundamental point: Carthage. Latitude:
        40.9464506g = 3651'06.50"N, longitude: 8.8724368g E of Paris =
        1019'20.72"E (of Greenwich). Carthage is a geodetic datum for
        Topographic mapping. Fundamental point astronomic coordinates
        determined in 1878.
    :cvar CHATAM_ISLAND_ASTRO_1971: A geodetic datum first defined in
        1971 suitable for use in New Zealand - Chatham Islands group -
        onshore. Chatham Islands Datum 1971 references the International
        1924 ellipsoid and the Greenwich prime meridian. Chatham Islands
        Datum 1971 is a geodetic datum for Geodetic survey, topographic
        mapping, engineering survey. It was defined by information from
        Office of Surveyor General (OSG) Technical Report 14, June 2001.
        Replaced by Chatham Islands Datum 1979 (code 6673).
    :cvar CHUA_ASTRO: A geodetic datum suitable for use in Brazil -
        south of 18S and west of 54W, plus Distrito Federal. Paraguay -
        north. Chua references the International 1924 ellipsoid and the
        Greenwich prime meridian. Chua origin is Fundamental point:
        Chua. Latitude: 1945'41.160"S, longitude: 4806'07.560"W (of
        Greenwich). Chua is a geodetic datum for Geodetic survey. It was
        defined by information from NIMA http://earth-info.nima.mil/.
        The Chua origin and associated network is in Brazil with a
        connecting traverse through northern Paraguay. It was used in
        Brazil only as input into the Corrego Allegre adjustment and for
        government work in Distrito Federal.
    :cvar CORREGO_ALEGRE: A geodetic datum first defined in 1972
        suitable for use in Brazil - onshore - west of 54W and south of
        18S; also south of 15S between 54W and 42W; also east of 42W.
        Corrego Alegre 1970-72 references the International 1924
        ellipsoid and the Greenwich prime meridian. Corrego Alegre
        1970-72 origin is Fundamental point: Corrego Alegre. Latitude:
        1950'14.91"S, longitude: 4857'41.98"W (of Greenwich). Corrego
        Alegre 1970-72 is a geodetic datum for Topographic mapping,
        geodetic survey. Superseded by SAD69. It was defined by
        information from IBGE. Replaces 1961 adjustment (datum code
        1074). NIMA gives coordinates of origin as latitude:
        1950'15.14"S, longitude: 4857'42.75"W; these may refer to 1961
        adjustment.
    :cvar DABOLA: A geodetic datum first defined in 1981 suitable for
        use in Guinea - onshore. Dabola 1981 references the Clarke 1880
        (IGN) ellipsoid and the Greenwich prime meridian. Dabola 1981 is
        a geodetic datum for Topographic mapping. It was defined by
        information from IGN Paris.
    :cvar DJAKARTA_BATAVIA: A geodetic datum suitable for use in
        Indonesia - onshore Java and Bali. Batavia (Jakarta) references
        the Bessel 1841 ellipsoid and the Jakarta prime meridian.
        Batavia (Jakarta) origin is Fundamental point: Longitude at
        Batavia astronomical station. Latitude: 607'39.522"S, longitude:
        000'00.0"E (of Jakarta). Latitude and azimuth at Genuk. Batavia
        (Jakarta) is a geodetic datum for Topographic mapping.
    :cvar DOS_1968: DOS 1968.
    :cvar EASTER_ISLAND_1967: A geodetic datum first defined in 1967
        suitable for use in Chile - Easter Island onshore. Easter Island
        1967 references the International 1924 ellipsoid and the
        Greenwich prime meridian. Easter Island 1967 is a geodetic datum
        for Military and topographic mapping, +/- 25 meters in each
        component. It was defined by information from DMA / NIMA / NGA
        TR8350.2 (3rd edition, Amendment 1, 3 January 2000).
    :cvar EUROPEAN_1979: A geodetic datum first defined in 1979 suitable
        for use in Europe - west. European Datum 1979 references the
        International 1924 ellipsoid and the Greenwich prime meridian.
        European Datum 1979 origin is Fundamental point: Potsdam
        (Helmert Tower). Latitude: 5222'51.4456"N, longitude:
        1303'58.9283"E (of Greenwich). European Datum 1979 is a geodetic
        datum for Scientific network. Replaced by 1987 adjustment.
    :cvar FORT_THOMAS_1955: Fort Thomas 1955 datum.
    :cvar GAN_1970: A geodetic datum first defined in 1970 suitable for
        use in Maldives - onshore. Gan 1970 references the International
        1924 ellipsoid and the Greenwich prime meridian. Gan 1970 is a
        geodetic datum for Topographic mapping. It was defined by
        information from Various industry sources. In some references
        incorrectly named "Gandajika 1970".
    :cvar GEODETIC_DATUM_1949: A geodetic datum first defined in 1949
        suitable for use in New Zealand - North Island, South Island,
        Stewart Island - onshore and nearshore. New Zealand Geodetic
        Datum 1949 references the International 1924 ellipsoid and the
        Greenwich prime meridian. New Zealand Geodetic Datum 1949 origin
        is Fundamental point: Papatahi. Latitude: 4119' 8.900"S,
        longitude: 17502'51.000"E (of Greenwich). New Zealand Geodetic
        Datum 1949 is a geodetic datum for Geodetic survey, cadastre,
        topographic mapping, engineering survey. It was defined by
        information from Land Information New Zealand.
        http://www.linz.govt.nz/rcs/linz/pub/web/root/core/SurveySystem/GeodeticInfo/GeodeticDatums/nzgd2000factsheet/index.jsp.
        Replaced by New Zealand Geodetic Datum 2000 (code 6167) from
        March 2000.
    :cvar GRACIOSA_BASE_SW_1948: Graciosa Base SW 1948 datum.
    :cvar GUAM_1963: A geodetic datum first defined in 1963 suitable for
        use in Guam - onshore. Guam 1963 references the Clarke 1866
        ellipsoid and the Greenwich prime meridian. Guam 1963 origin is
        Fundamental point: Tagcha. Latitude: 1322'38.49"N, longitude:
        14445'51.56"E (of Greenwich). Guam 1963 is a geodetic datum for
        Topographic mapping. It was defined by information from US
        National Geospatial Intelligence Agency (NGA). http://earth-
        info.nga.mil/ Replaced by NAD83(HARN)
    :cvar GUNUNG_SEGARA: A geodetic datum suitable for use in Indonesia
        - Kalimantan - onshore east coastal area including Mahakam delta
        coastal and offshore shelf areas. Gunung Segara references the
        Bessel 1841 ellipsoid and the Greenwich prime meridian. Gunung
        Segara origin is Station P5 (Gunung Segara). Latitude
        032'12.83"S, longitude 11708'48.47"E (of Greenwich). Gunung
        Segara is a geodetic datum for Topographic mapping. It was
        defined by information from TotalFinaElf.
    :cvar GUX_1_ASTRO: GUX 1 Astro datum.
    :cvar HERAT_NORTH: A geodetic datum suitable for use in Afghanistan.
        Herat North references the International 1924 ellipsoid and the
        Greenwich prime meridian. Herat North origin is Fundamental
        point: Herat North. Latitude: 3423'09.08"N, longitude:
        6410'58.94"E (of Greenwich). Herat North is a geodetic datum for
        Topographic mapping. It was defined by information from NIMA
        http://earth-info.nima.mil/.
    :cvar HJORSEY_1955: A geodetic datum first defined in 1955 suitable
        for use in Iceland - onshore. Hjorsey 1955 references the
        International 1924 ellipsoid and the Greenwich prime meridian.
        Hjorsey 1955 origin is Fundamental point: Latitude:
        6431'29.26"N, longitude: 2222'05.84"W (of Greenwich). Hjorsey
        1955 is a geodetic datum for 1/50,000 scale topographic mapping.
        It was defined by information from Landmaelingar Islands
        (National Survey of Iceland).
    :cvar HONG_KONG_1963: A geodetic datum first defined in 1963
        suitable for use in China - Hong Kong - onshore and offshore.
        Hong Kong 1963 references the Clarke 1858 ellipsoid and the
        Greenwich prime meridian. Hong Kong 1963 origin is Fundamental
        point: Trig "Zero", 38.4 feet south along the transit circle of
        the Kowloon Observatory. Latitude 2218'12.82"N, longitude
        11410'18.75"E (of Greenwich). Hong Kong 1963 is a geodetic datum
        for Topographic mapping and hydrographic charting. It was
        defined by information from Survey and Mapping Office, Lands
        Department. http://www.info.gov.hk/landsd/. Replaced by Hong
        Kong 1963(67) for military purposes only in 1967. Replaced by
        Hong Kong 1980.
    :cvar HU_TZU_SHAN: A geodetic datum first defined in 1950 suitable
        for use in Taiwan, Republic of China - onshore - Taiwan Island,
        Penghu (Pescadores) Islands. Hu Tzu Shan 1950 references the
        International 1924 ellipsoid and the Greenwich prime meridian.
        Hu Tzu Shan 1950 origin is Fundamental point: Hu Tzu Shan.
        Latitude: 2358'32.34"N, longitude: 12058'25.975"E (of
        Greenwich). Hu Tzu Shan 1950 is a geodetic datum for Topographic
        mapping. It was defined by information from NIMA US NGA,
        http://earth-info.nga.mil/GandG/index.html
    :cvar INDIAN: Indian datum.
    :cvar INDIAN_1954: A geodetic datum first defined in 1954 suitable
        for use in Myanmar (Burma) - onshore; Thailand - onshore. Indian
        1954 references the Everest 1830 (1937 Adjustment) ellipsoid and
        the Greenwich prime meridian. Indian 1954 origin is Extension of
        Kalianpur 1937 over Myanmar and Thailand. Indian 1954 is a
        geodetic datum for Topographic mapping.
    :cvar INDIAN_1975: A geodetic datum first defined in 1975 suitable
        for use in Thailand - onshore plus offshore Gulf of Thailand.
        Indian 1975 references the Everest 1830 (1937 Adjustment)
        ellipsoid and the Greenwich prime meridian. Indian 1975 origin
        is Fundamental point: Khau Sakaerang. Indian 1975 is a geodetic
        datum for Topographic mapping.
    :cvar IRELAND_1965: A geodetic datum first defined in 1975 suitable
        for use in Ireland - onshore. United Kingdom (UK) - Northern
        Ireland (Ulster) - onshore. Ireland 1965 references the Airy
        Modified 1849 ellipsoid and the Greenwich prime meridian.
        Ireland 1965 origin is Adjusted to best mean fit 9 stations of
        the OSNI 1952 primary adjustment in Northern Ireland plus the
        1965 values of 3 stations in the Republic of Ireland. Ireland
        1965 is a geodetic datum for Geodetic survey, topographic
        mapping and engineering survey. It was defined by information
        from "The Irish Grid - A Description of the Co-ordinate
        Reference System" published by Ordnance Survey of Ireland,
        Dublin and Ordnance Survey of Northern Ireland, Belfast.
        Differences from the 1965 adjustment (datum code 6299) are:
        average difference in Eastings 0.092m; average difference in
        Northings 0.108m; maximum vector difference 0.548m.
    :cvar ISTS_061_ASTRO_1968: A geodetic datum first defined in 1968
        suitable for use in South Georgia and the South Sandwich Islands
        - South Georgia onshore. ISTS 061 Astro 1968 references the
        International 1924 ellipsoid and the Greenwich prime meridian.
        ISTS 061 Astro 1968 origin is Fundamental point: ISTS 061. ISTS
        061 Astro 1968 is a geodetic datum for Military and topographic
        mapping It was defined by information from DMA / NIMA / NGA
        TR8350.2 (3rd edition, Amendment 1, 3 January 2000).
    :cvar ISTS_073_ASTRO_1969: A geodetic datum first defined in 1969
        suitable for use in British Indian Ocean Territory - Chagos
        Archipelago - Diego Garcia. ISTS 073 Astro 1969 references the
        International 1924 ellipsoid and the Greenwich prime meridian.
        ISTS 073 Astro 1969 origin is Fundamental point: ISTS 073. ISTS
        073 Astro 1969 is a geodetic datum for Military and topographic
        mapping. It was defined by information from DMA / NIMA / NGA
        TR8350.2 (3rd edition, Amendment 1, 3 January 2000).
    :cvar JOHNSTON_ISLAND_1961: A geodetic datum first defined in 1961
        suitable for use in United States Minor Outlying Islands -
        Johnston Island. Johnston Island 1961 references the
        International 1924 ellipsoid and the Greenwich prime meridian.
        Johnston Island 1961 is a geodetic datum for Military and
        topographic mapping. It was defined by information from DMA /
        NIMA / NGA TR8350.2 (3rd edition, Amendment 1, 3 January 2000).
    :cvar KANDAWALA: A geodetic datum first defined in 1930 suitable for
        use in Sri Lanka - onshore. Kandawala references the Everest
        1830 (1937 Adjustment) ellipsoid and the Greenwich prime
        meridian. Kandawala origin is Fundamental point: Kandawala.
        Latitude: 714'06.838"N, longitude: 7952'36.670"E. Kandawala is a
        geodetic datum for Topographic mapping. It was defined by
        information from Abeyratne, Featherstone and Tantrigoda in
        Survey Review vol. 42 no. 317 (July 2010).
    :cvar KERGUELEN_ISLAND_1949: A geodetic datum first defined in 1949
        suitable for use in French Southern Territories - Kerguelen
        onshore. References the International 1924 ellipsoid and the
        Greenwich prime meridian. Origin is K0 1949. Is a geodetic datum
        for Geodetic survey, cadastre, topographic mapping, engineering
        survey. It was defined by information from IGN Paris.
    :cvar KERTAU_1968: A geodetic datum first defined in 1968 suitable
        for use in Malaysia - West Malaysia onshore and offshore east
        coast; Singapore - onshore and offshore. Kertau 1968 references
        the Everest 1830 Modified ellipsoid and the Greenwich prime
        meridian. Kertau 1968 origin is Fundamental point: Kertau.
        Latitude: 327'50.710"N, longitude: 10237'24.550"E (of
        Greenwich). Kertau 1968 is a geodetic datum for Geodetic survey,
        cadastre. It was defined by information from Defence Geographic
        Centre. Replaces MRT48 and earlier adjustments. Adopts metric
        conversion of 39.370113 inches per metre. Not used for 1969
        metrication of RSO grid - see Kertau (RSO) (code 6751).
    :cvar KUSAIE_ASTRO_1951: A geodetic datum first defined in 1951
        suitable for use in Federated States of Micronesia - Kosrae
        (Kusaie). Kusaie 1951 references the International 1924
        ellipsoid and the Greenwich prime meridian. Kusaie 1951 is a
        geodetic datum for Military and topographic mapping. It was
        defined by information from DMA / NIMA / NGA TR8350.2 (3rd
        edition, Amendment 1, 3 January 2000).
    :cvar L_C_5_ASTRO_1961: L. C. 5 Astro 1961 datum.
    :cvar LEIGON: A geodetic datum suitable for use in Ghana - onshore
        and offshore. Leigon references the Clarke 1880 (RGS) ellipsoid
        and the Greenwich prime meridian. Leigon origin is Fundamental
        point: GCS Station 121, Leigon. Latitude: 538'52.27"N,
        longitude: 011'46.08"W (of Greenwich). Leigon is a geodetic
        datum for Topographic mapping. It was defined by information
        from Ordnance Survey International. Replaced Accra datum (code
        6168) from 1978. Coordinates at Leigon fundamental point defined
        as Accra datum values for that point.
    :cvar LIBERIA_1964: A geodetic datum first defined in 1964 suitable
        for use in Liberia - onshore. Liberia 1964 references the Clarke
        1880 (RGS) ellipsoid and the Greenwich prime meridian. Liberia
        1964 origin is Fundamental point: Robertsfield. Latitude:
        613'53.02"N, longitude: 1021'35.44"W (of Greenwich). Liberia
        1964 is a geodetic datum for Topographic mapping. It was defined
        by information from NIMA http://earth-info.nima.mil/.
    :cvar LUZON: A geodetic datum first defined in 1911 suitable for use
        in Philippines - onshore. Luzon references the Clarke 1866
        ellipsoid and the Greenwich prime meridian. Luzon origin is
        Fundamental point: Balacan. Latitude: 1333'41.000"N, longitude:
        12152'03.000"E (of Greenwich). Luzon is a geodetic datum for
        Topographic mapping. It was defined by information from Coast
        and Geodetic Survey Replaced by Philippine Reference system of
        1992 (datum code 6683).
    :cvar MAHE_1971: A geodetic datum first defined in 1971 suitable for
        use in Seychelles - Mahe Island. Mahe 1971 references the Clarke
        1880 (RGS) ellipsoid and the Greenwich prime meridian. Mahe 1971
        origin is Fundamental point: Station SITE. Latitude:
        440'14.644"S, longitude: 5528'44.488"E (of Greenwich). Mahe 1971
        is a geodetic datum for US military survey. It was defined by
        information from Clifford Mugnier's September 2007 PE&amp;RS
        "Grids and Datums" article on Seychelles
        (www.asprs.org/resources/grids/). South East Island 1943 (datum
        code 1138) used for topographic mapping, cadastral and
        hydrographic survey.
    :cvar MASSAWA: A geodetic datum suitable for use in Eritrea -
        onshore and offshore. Massawa references the Bessel 1841
        ellipsoid and the Greenwich prime meridian. Massawa is a
        geodetic datum for Topographic mapping.
    :cvar MERCHICH: A geodetic datum first defined in 1922 suitable for
        use in Morocco - onshore. Merchich references the Clarke 1880
        (IGN) ellipsoid and the Greenwich prime meridian. Merchich
        origin is Fundamental point: Merchich. Latitude: 3326'59.672"N,
        longitude: 733'27.295"W (of Greenwich). Merchich is a geodetic
        datum for Topographic mapping.
    :cvar MIDWAY_ASTRO_1961: A geodetic datum first defined in 1961
        suitable for use in United States Minor Outlying Islands -
        Midway Islands - Sand Island and Eastern Island. Midway 1961
        references the International 1924 ellipsoid and the Greenwich
        prime meridian. Midway 1961 is a geodetic datum for Military and
        topographic mapping. It was defined by information from DMA /
        NIMA / NGA TR8350.2 (3rd edition, Amendment 1, 3 January 2000).
    :cvar MINNA: A geodetic datum suitable for use in Nigeria - onshore
        and offshore. Minna references the Clarke 1880 (RGS) ellipsoid
        and the Greenwich prime meridian. Minna origin is Fundamental
        point: Minna base station L40. Latitude: 938'08.87"N, longitude:
        630'58.76"E (of Greenwich). Minna is a geodetic datum for
        Topographic mapping. It was defined by information from NIMA
        http://earth-info.nima.mil/.
    :cvar MONTSERRAT_ISLAND_ASTRO_1958: A geodetic datum first defined
        in 1958 suitable for use in Montserrat - onshore. Montserrat
        1958 references the Clarke 1880 (RGS) ellipsoid and the
        Greenwich prime meridian. Montserrat 1958 origin is Fundamental
        point: station M36. Montserrat 1958 is a geodetic datum for
        Topographic mapping. It was defined by information from Ordnance
        Survey of Great Britain.
    :cvar M_PORALOKO: A geodetic datum suitable for use in Gabon -
        onshore and offshore. M'poraloko references the Clarke 1880
        (IGN) ellipsoid and the Greenwich prime meridian. M'poraloko is
        a geodetic datum for Topographic mapping.
    :cvar NAHRWAN: A geodetic datum first defined in 1934 suitable for
        use in Iraq - onshore; Iran - onshore northern Gulf coast and
        west bordering southeast Iraq. Nahrwan 1934 references the
        Clarke 1880 (RGS) ellipsoid and the Greenwich prime meridian.
        Nahrwan 1934 origin is Fundamental point: Nahrwan south base.
        Latitude: 3319'10.87"N, longitude: 4443'25.54"E (of Greenwich).
        Nahrwan 1934 is a geodetic datum for Oil exploration and
        production. It was defined by information from Various industry
        sources. This adjustment later discovered to have a significant
        orientation error. In Iran replaced by FD58. In Iraq, replaced
        by Karbala 1979.
    :cvar NAPARIMA_BWI: A geodetic datum first defined in 1972 suitable
        for use in Trinidad and Tobago - Tobago - onshore. Naparima 1972
        references the International 1924 ellipsoid and the Greenwich
        prime meridian. Naparima 1972 origin is Fundamental point:
        Naparima. Latitude: 1016'44.860"N, longitude: 6127'34.620"W (of
        Greenwich). Naparima 1972 is a geodetic datum for Topographic
        mapping. It was defined by information from Ordnance Survey
        International. Naparima 1972 is an extension of the Naparima
        1955 network of Trinidad to include Tobago.
    :cvar NORTH_AMERICAN_1927: A geodetic datum first defined in 1927
        suitable for use in North and central America; Antigua and
        Barbuda; Bahamas; Belize; British Virgin Islandss. Usage shall
        be onshore only except that onshore and offshore shall apply to
        Canada east coast (New Brunswick; Newfoundland and Labrador;
        Prince Edward Island; Quebec). Cuba. Mexico (Gulf of Mexico and
        Caribbean coasts only). USA Alaska. USA Gulf of Mexico (Alabama;
        Florida; Louisiana; Mississippi; Texas). USA East Coast. Bahamas
        onshore plus offshore over internal continental shelf only.
        North American Datum 1927 references the Clarke 1866 ellipsoid
        and the Greenwich prime meridian. North American Datum 1927
        origin is Fundamental point: Meade's Ranch. Latitude:
        3913'26.686"N, longitude: 9832'30.506"W (of Greenwich). North
        American Datum 1927 is a geodetic datum for Topographic mapping.
        In United States (USA) and Canada, replaced by North American
        Datum 1983 (NAD83) (code 6269) ; in Mexico, replaced by Mexican
        Datum of 1993 (code 1042).
    :cvar NORTH_AMERICAN_1983: A geodetic datum first defined in 1986
        suitable for use in North America - onshore and offshore:
        Canada; Puerto Rico; United States (USA); US Virgin Islands;
        British Virgin Islands. North American Datum 1983 references the
        GRS 1980 ellipsoid and the Greenwich prime meridian. North
        American Datum 1983 origin is Origin at geocentre. North
        American Datum 1983 is a geodetic datum for Topographic mapping.
        Although the 1986 adjustment included connections to Greenland
        and Mexico, it has not been adopted there. In Canada and US,
        replaced NAD27.
    :cvar OBSERVATORIO_METEOROLOGICO_1939: A geodetic datum first
        defined in 1939 suitable for use in Portugal - western Azores
        onshore - Flores, Corvo. Azores Occidental Islands 1939
        references the International 1924 ellipsoid and the Greenwich
        prime meridian. Azores Occidental Islands 1939 origin is
        Fundamental point: Observatario Meteorologico Flores. Azores
        Occidental Islands 1939 is a geodetic datum for Topographic
        mapping. It was defined by information from Instituto Geografico
        e Cadastral Lisbon via EuroGeographics;
        http://crs.bkg.bund.de/crs-eu/.
    :cvar OLD_EGYPTIAN_1907: A geodetic datum first defined in 1907
        suitable for use in Egypt - onshore and offshore. Egypt 1907
        references the Helmert 1906 ellipsoid and the Greenwich prime
        meridian. Egypt 1907 origin is Fundamental point: Station F1
        (Venus). Latitude: 3001'42.86"N, longitude: 3116'33.60"E (of
        Greenwich). Egypt 1907 is a geodetic datum for Geodetic survey,
        cadastre, topographic mapping, engineering survey.
    :cvar OLD_HAWAIIAN: A geodetic datum suitable for use in United
        States (USA) - Hawaii - main islands onshore. Old Hawaiian
        references the Clarke 1866 ellipsoid and the Greenwich prime
        meridian. Old Hawaiian origin is Fundamental point: Oahu West
        Base Astro. Latitude: 2118'13.89"N, longitude 15750'55.79"W (of
        Greenwich). Old Hawaiian is a geodetic datum for Topographic
        mapping. It was defined by information from
        http://www.ngs.noaa.gov/ (NADCON readme file). Hawaiian Islands
        were never on NAD27 but rather on Old Hawaiian Datum. NADCON
        conversion program provides transformation from Old Hawaiian
        Datum to NAD83 (original 1986 realization) but making the
        transformation appear to user as if from NAD27.
    :cvar OMAN: A geodetic datum first defined in 2013 suitable for use
        in Oman - onshore and offshore. Oman National Geodetic Datum
        2014 references the GRS 1980 ellipsoid and the Greenwich prime
        meridian. Oman National Geodetic Datum 2014 origin is 20
        stations of the Oman primary network tied to ITRF2008 at epoch
        2013.15. Oman National Geodetic Datum 2014 is a geodetic datum
        for Geodetic Survey. It was defined by information from National
        Survey Authority, Sultanate of Oman. Replaces WGS 84 (G874).
    :cvar ORDNANCE_SURVEY_OF_GREAT_BRITAIN_1936: A geodetic datum first
        defined in 1936 suitable for use in United Kingdom (UK) -
        offshore to boundary of UKCS within 4946'N to 6101'N and 733'W
        to 333'E; onshore Great Britain (England, Wales and Scotland).
        Isle of Man onshore. OSGB 1936 references the Airy 1830
        ellipsoid and the Greenwich prime meridian. OSGB 1936 origin is
        Prior to 2002, fundamental point: Herstmonceux, Latitude:
        5051'55.271"N, longitude: 020'45.882"E (of Greenwich). From
        April 2002 the datum is defined through the application of the
        OSTN transformation from ETRS89. OSGB 1936 is a geodetic datum
        for Topographic mapping. It was defined by information from
        Ordnance Survey of Great Britain. The average accuracy of OSTN
        compared to the old triangulation network (down to 3rd order) is
        0.1m. With the introduction of OSTN15, the area for OSGB 1936
        has effectively been extended from Britain to cover the adjacent
        UK Continental Shelf.
    :cvar PICO_DE_LAS_NIEVES: A geodetic datum suitable for use in Spain
        - Canary Islands onshore. Pico de las Nieves 1984 references the
        International 1924 ellipsoid and the Greenwich prime meridian.
        Pico de las Nieves 1984 is a geodetic datum for Military and
        topographic mapping. It was defined by information from DMA /
        NIMA / NGA TR8350.2 (3rd edition, Amendment 1, 3 January 2000).
        Replaces Pico de las Nieves 1968 (PN68). Replaced by REGCAN95.
    :cvar PITCAIRN_ASTRO_1967: A geodetic datum first defined in 1967
        suitable for use in Pitcairn - Pitcairn Island. Pitcairn 1967
        references the International 1924 ellipsoid and the Greenwich
        prime meridian. Pitcairn 1967 origin is Fundamental point:
        Pitcairn Astro. Latitude: 2504'06.87"S, longitude: 13006'47.83"W
        (of Greenwich). Pitcairn 1967 is a geodetic datum for Military
        and topographic mapping. It was defined by information from DMA
        / NIMA / NGA TR8350.2 (3rd edition, Amendment 1, 3 January
        2000). Replaced by Pitcairn 2006.
    :cvar POINT_58: A geodetic datum first defined in 1969 suitable for
        use in Senegal - central, Mali - southwest, Burkina Faso -
        central, Niger - southwest, Nigeria - north, Chad - central. All
        in proximity to the parallel of latitude of 12N. Point 58
        references the Clarke 1880 (RGS) ellipsoid and the Greenwich
        prime meridian. Point 58 origin is Fundamental point: Point 58.
        Latitude: 1252'44.045"N, longitude: 358'37.040"E (of Greenwich).
        Point 58 is a geodetic datum for Geodetic survey. It was defined
        by information from IGN Paris. Used as the basis for computation
        of the 12th Parallel traverse conducted 1966-70 from Senegal to
        Chad and connecting to the Blue Nile 1958 (Adindan)
        triangulation in Sudan.
    :cvar POINTE_NOIRE_1948: Pointe Noire 1948 datum.
    :cvar PORTO_SANTO_1936: A geodetic datum first defined in 1936
        suitable for use in Portugal - Madeira, Porto Santo and Desertas
        islands - onshore. Porto Santo 1936 references the International
        1924 ellipsoid and the Greenwich prime meridian. Porto Santo
        1936 origin is SE Base on Porto Santo island. Porto Santo 1936
        is a geodetic datum for Topographic mapping. It was defined by
        information from Instituto Geografico e Cadastral Lisbon
        http://www.igeo.pt Replaced by 1995 adjustment (datum code
        6663). For Selvagens see Selvagem Grande (code 6616).
    :cvar PROVISIONAL_SOUTH_AMERICAN_1956: A geodetic datum first
        defined in 1956 suitable for use in Aruba - onshore; Bolivia;
        Bonaire - onshore; Brazil - offshore - Amazon Cone shelf; Chile
        - onshore north of 4330'S; Curacao - onshore; Ecuador - mainland
        onshore; Guyana - onshore; Peru - onshore; Venezuela - onshore.
        Provisional South American Datum 1956 references the
        International 1924 ellipsoid and the Greenwich prime meridian.
        Provisional South American Datum 1956 origin is Fundamental
        point: La Canoa. Latitude: 834'17.170"N, longitude:
        6351'34.880"W (of Greenwich). Provisional South American Datum
        1956 is a geodetic datum for Topographic mapping. Same origin as
        La Canoa datum.
    :cvar PROVISIONAL_SOUTH_CHILEAN_1963: A geodetic datum first defined
        in 1963 suitable for use in Argentina and Chile - Tierra del
        Fuego, onshore. Hito XVIII 1963 references the International
        1924 ellipsoid and the Greenwich prime meridian. Hito XVIII 1963
        origin is Chile-Argentina boundary survey. Hito XVIII 1963 is a
        geodetic datum for Geodetic survey. It was defined by
        information from Various oil company records. Used in Tierra del
        Fuego.
    :cvar PUERTO_RICO: A geodetic datum first defined in 1901 suitable
        for use in Puerto Rico, US Virgin Islands and British Virgin
        Islands - onshore. Puerto Rico references the Clarke 1866
        ellipsoid and the Greenwich prime meridian. Puerto Rico origin
        is Fundamental point: Cardona Island Lighthouse.
        Latitude:1757'31.40"N, longitude: 6638'07.53"W (of Greenwich).
        Puerto Rico is a geodetic datum for Topographic mapping. It was
        defined by information from Ordnance Survey of Great Britain and
        http://www.ngs.noaa.gov/ (NADCON readme file). NADCON conversion
        program provides transformation from Puerto Rico Datum to NAD83
        (original 1986 realization) but making the transformation appear
        to user as if from NAD27.
    :cvar QATAR_NATIONAL: A geodetic datum first defined in 1995
        suitable for use in Qatar - onshore. Qatar National Datum 1995
        references the International 1924 ellipsoid and the Greenwich
        prime meridian. Qatar National Datum 1995 origin is defined by
        transformation from WGS 84 - see coordinate operation code 1840.
        Qatar National Datum 1995 is a geodetic datum for Topographic
        mapping. It was defined by information from Qatar Centre for
        Geographic Information.
    :cvar QORNOQ: A geodetic datum first defined in 1927 suitable for
        use in Greenland - west coast onshore. Qornoq 1927 references
        the International 1924 ellipsoid and the Greenwich prime
        meridian. Qornoq 1927 origin is Fundamental point: Station 7008.
        Latitude: 6431'06.27"N, longitude: 5112'24.86"W (of Greenwich).
        Qornoq 1927 is a geodetic datum for Topographic mapping. It was
        defined by information from Kort &amp; Matrikelstyrelsen,
        Copenhagen. Origin coordinates from NIMA http://earth-
        info.nima.mil/.
    :cvar REUNION: A geodetic datum first defined in 1947 suitable for
        use in Reunion - onshore. Reunion 1947 references the
        International 1924 ellipsoid and the Greenwich prime meridian.
        Reunion 1947 origin is Fundamental point: Piton des Neiges
        (Borne). Latitude: 2105'13.119"S, longitude: 5529'09.193"E (of
        Greenwich). Reunion 1947 is a geodetic datum for Geodetic
        survey, cadastre, topographic mapping, engineering survey. It
        was defined by information from IGN Paris. Replaced by RGR92
        (datum code 6627).
    :cvar ROME_1940: A geodetic datum first defined in and is suitable
        for use in Italy - onshore and offshore; San Marino, Vatican
        City State. Monte Mario (Rome) references the International 1924
        ellipsoid and the Rome prime meridian. Monte Mario (Rome) origin
        is Fundamental point: Monte Mario. Latitude: 4155'25.51"N,
        longitude: 000' 00.00"E (of Rome). Monte Mario (Rome) is a
        geodetic datum for Topographic mapping. Replaced Genova datum,
        Bessel 1841 ellipsoid, from 1940.
    :cvar SANTO_DOS_1965: A geodetic datum first defined in 1965
        suitable for use in Vanuatu - northern islands - Aese, Ambrym,
        Aoba, Epi, Espiritu Santo, Maewo, Malo, Malkula, Paama,
        Pentecost, Shepherd and Tutuba. Santo 1965 references the
        International 1924 ellipsoid and the Greenwich prime meridian.
        Santo 1965 is a geodetic datum for Military and topographic
        mapping. It was defined by information from DMA / NIMA / NGA
        TR8350.2 (3rd edition, Amendment 1, 3 January 2000). Datum
        covers all the major islands of Vanuatu in two different
        adjustment blocks, but practical usage is as given in the area
        of use.
    :cvar SAO_BRAZ: A geodetic datum first defined in 1995 suitable for
        use in Portugal - eastern Azores onshore - Sao Miguel, Santa
        Maria, Formigas. Azores Oriental Islands 1995 references the
        International 1924 ellipsoid and the Greenwich prime meridian.
        Azores Oriental Islands 1995 origin is Fundamental point: Forte
        de So Bras. Origin and orientation constrained to those of the
        1940 adjustment. Azores Oriental Islands 1995 is a geodetic
        datum for Topographic mapping. It was defined by information
        from Instituto Geografico e Cadastral Lisbon;
        http://www.igeo.pt/ Classical and GPS observations. Replaces
        1940 adjustment (datum code 6184).
    :cvar SAPPER_HILL_1943: A geodetic datum first defined in 1943
        suitable for use in Falkland Islands (Malvinas) - onshore.
        Sapper Hill 1943 references the International 1924 ellipsoid and
        the Greenwich prime meridian. Sapper Hill 1943 is a geodetic
        datum for Topographic mapping.
    :cvar SCHWARZECK: A geodetic datum suitable for use in Namibia -
        onshore and offshore. Schwarzeck references the Bessel Namibia
        (GLM) ellipsoid and the Greenwich prime meridian. Schwarzeck
        origin is Fundamental point: Schwarzeck. Latitude:
        2245'35.820"S, longitude: 1840'34.549"E (of Greenwich). Fixed
        during German South West Africa-British Bechuanaland boundary
        survey of 1898-1903. Schwarzeck is a geodetic datum for
        Topographic mapping. It was defined by information from Private
        Communication, Directorate of Surveys and Land Information, Cape
        Town.
    :cvar SELVAGEM_GRANDE_1938: A geodetic datum suitable for use in
        Portugal - Selvagens islands (Madeira province) - onshore.
        Selvagem Grande references the International 1924 ellipsoid and
        the Greenwich prime meridian. Selvagem Grande is a geodetic
        datum for Topographic mapping. It was defined by information
        from Instituto Geografico e Cadastral Lisbon http://www.igeo.pt.
    :cvar SOUTH_AMERICAN_1969: A geodetic datum first defined in 1969
        suitable for use in Brazil - onshore and offshore. In rest of
        South America - onshore north of approximately 45S and Tierra
        del Fuego. South American Datum 1969 references the GRS 1967
        Modified ellipsoid and the Greenwich prime meridian. South
        American Datum 1969 origin is Fundamental point: Chua. Geodetic
        latitude: 1945'41.6527"S; geodetic longitude: 4806'04.0639"W (of
        Greenwich). (Astronomic coordinates: Latitude 1945'41.34"S +/-
        0.05", longitude 4806'07.80"W +/- 0.08"). South American Datum
        1969 is a geodetic datum for Topographic mapping. It was defined
        by information from DMA 1974. SAD69 uses GRS 1967 ellipsoid but
        with 1/f to exactly 2 decimal places. In Brazil only, replaced
        by SAD69(96) (datum code 1075).
    :cvar SOUTH_ASIA: South Asia datum.
    :cvar TANANARIVE_OBSERVATORY_1925: A geodetic datum first defined in
        1925 suitable for use in Madagascar - onshore and nearshore.
        Tananarive 1925 references the International 1924 ellipsoid and
        the Greenwich prime meridian. Tananarive 1925 origin is
        Fundamental point: Tananarive observatory. Latitude:
        1855'02.10"S, longitude: 4733'06.75"E (of Greenwich). Tananarive
        1925 is a geodetic datum for Topographic mapping. It was defined
        by information from IGN Paris.
    :cvar TIMBALAI_1948: A geodetic datum first defined in 1948 suitable
        for use in Brunei - onshore and offshore; Malaysia - East
        Malaysia (Sabah; Sarawak) - onshore and offshore. Timbalai 1948
        references the Everest 1830 (1967 Definition) ellipsoid and the
        Greenwich prime meridian. Timbalai 1948 origin is Fundamental
        point: Station P85 at Timbalai. Latitude: 517' 3.548"N,
        longitude: 11510'56.409"E (of Greenwich). Timbalai 1948 is a
        geodetic datum for Topographic mapping. It was defined by
        information from Defence Geographic Centre. In 1968, the
        original adjustment was densified in Sarawak and extended to
        Sabah.
    :cvar TOKYO: A geodetic datum first defined in 1918 suitable for use
        in Japan - onshore; North Korea - onshore; South Korea -
        onshore. Tokyo references the Bessel 1841 ellipsoid and the
        Greenwich prime meridian. Tokyo origin is Fundamental point:
        Nikon-Keido-Genten. Latitude: 3539'17.5148"N, longitude:
        13944'40.5020"E (of Greenwich). Longitude derived in 1918. Tokyo
        is a geodetic datum for Geodetic survey, cadastre, topographic
        mapping, engineering survey. It was defined by information from
        Geographic Survey Institute; Japan; Bulletin 40 (March 1994).
        Also http://vldb.gsi.go.jp/sokuchi/datum/tokyodatum.html. In
        Japan, replaces Tokyo 1892 (code 1048) and replaced by Japanese
        Geodetic Datum 2000 (code 6611). In Korea used only for geodetic
        applications before being replaced by Korean 1985 (code 6162).
    :cvar TRISTAN_ASTRO_1968: A geodetic datum first defined in 1968
        suitable for use in St Helena, Ascension and Tristan da Cunha -
        Tristan da Cunha island group including Tristan, Inaccessible,
        Nightingale, Middle and Stoltenhoff Islands. Tristan 1968
        references the International 1924 ellipsoid and the Greenwich
        prime meridian. Tristan 1968 is a geodetic datum for Military
        and topographic mapping. It was defined by information from DMA
        / NIMA / NGA TR8350.2 (3rd edition, Amendment 1, 3 January
        2000).
    :cvar VITI_LEVU_1916: A geodetic datum first defined in 1912
        suitable for use in Fiji - Viti Levu island. Viti Levu 1912
        references the Clarke 1880 (international foot) ellipsoid and
        the Greenwich prime meridian. Viti Levu 1912 Latitude origin was
        obtained astronomically at station Monavatu = 1753'28.285"S,
        longitude origin was obtained astronomically at station Suva =
        17825'35.835"E. Viti Levu 1912 is a geodetic datum for Geodetic
        survey, cadastre, topographic mapping, engineering survey. It
        was defined by information from Clifford J. Mugnier in
        Photogrammetric Engineering and Remote Sensing, October 2000,
        www.asprs.org. For topographic mapping, replaced by Fiji 1956.
        For other purposes, replaced by Fiji 1986.
    :cvar WAKE_ENIWETOK_1960: A geodetic datum first defined in 1960
        suitable for use in Marshall Islands - onshore. Wake atoll
        onshore. Marshall Islands 1960 references the Hough 1960
        ellipsoid and the Greenwich prime meridian. Marshall Islands
        1960 is a geodetic datum for Military and topographic mapping.
        It was defined by information from DMA / NIMA / NGA TR8350.2
        (3rd edition, Amendment 1, 3 January 2000).
    :cvar WAKE_ISLAND_ASTRO_1952: A geodetic datum first defined in 1952
        suitable for use in Wake atoll - onshore. Wake Island 1952
        references the International 1924 ellipsoid and the Greenwich
        prime meridian. Wake Island 1952 is a geodetic datum for
        Military and topographic mapping. It was defined by information
        from DMA / NIMA / NGA TR8350.2 (3rd edition, Amendment 1, 3
        January 2000).
    :cvar YACARE: A geodetic datum suitable for use in Uruguay -
        onshore. Yacare references the International 1924 ellipsoid and
        the Greenwich prime meridian. Yacare origin is Fundamental
        point: Yacare. Latitude: 3035'53.68"S, longitude: 5725'01.30"W
        (of Greenwich). Yacare is a geodetic datum for Topographic
        mapping. It was defined by information from NIMA http://earth-
        info.nima.mil/
    :cvar ZANDERIJ: A geodetic datum suitable for use in Suriname -
        onshore and offshore. Zanderij references the International 1924
        ellipsoid and the Greenwich prime meridian. Zanderij is a
        geodetic datum for Topographic mapping.
    :cvar AMERICAN_SAMOA_1962: A geodetic datum first defined in 1962
        suitable for use in American Samoa - Tutuila, Aunu'u, Ofu,
        Olesega and Ta'u islands. American Samoa 1962 references the
        Clarke 1866 ellipsoid and the Greenwich prime meridian. American
        Samoa 1962 origin is Fundamental point: Betty 13 eccentric.
        Latitude: 1420'08.34"S, longitude: 17042'52.25"W (of Greenwich).
        American Samoa 1962 is a geodetic datum for Topographic mapping.
        It was defined by information from NIMA TR8350.2 revision of
        January 2000. Oil industry sources for origin description
        details.
    :cvar DECEPTION_ISLAND: A geodetic datum suitable for use in
        Antarctica - South Shetland Islands - Deception Island.
        Deception Island references the Clarke 1880 (RGS) ellipsoid and
        the Greenwich prime meridian. Deception Island is a geodetic
        datum for Military and scientific mapping. It was defined by
        information from DMA / NIMA / NGA TR8350.2 (3rd edition,
        Amendment 1, 3 January 2000).
    :cvar INDIAN_1960: A geodetic datum suitable for use in Cambodia -
        onshore; Vietnam - onshore and offshore Cuu Long basin. Indian
        1960 references the Everest 1830 (1937 Adjustment) ellipsoid and
        the Greenwich prime meridian. Indian 1960 origin is DMA
        extension over IndoChina of the Indian 1954 network adjusted to
        better fit local geoid. Indian 1960 is a geodetic datum for
        Topographic mapping. Also known as Indian (DMA Reduced).
    :cvar INDONESIAN_1974: A geodetic datum first defined in 1974
        suitable for use in Indonesia - onshore. Indonesian Datum 1974
        references the Indonesian National Spheroid ellipsoid and the
        Greenwich prime meridian. Indonesian Datum 1974 origin is
        Fundamental point: Padang. Latitude: 056'38.414"S, longitude:
        10022' 8.804"E (of Greenwich). Ellipsoidal height 3.190m,
        gravity-related height 14.0m above mean sea level. Indonesian
        Datum 1974 is a geodetic datum for Topographic mapping. It was
        defined by information from Bakosurtanal 1979 paper by Jacob
        Rais. Replaced by DGN95.
    :cvar NORTH_SAHARA_1959: A geodetic datum first defined in 1959
        suitable for use in Algeria - onshore and offshore. Nord Sahara
        1959 references the Clarke 1880 (RGS) ellipsoid and the
        Greenwich prime meridian. Nord Sahara 1959 origin is Coordinates
        of primary network readjusted on ED50 datum and then transformed
        conformally to Clarke 1880 (RGS) ellipsoid. Nord Sahara 1959 is
        a geodetic datum for Topographic mapping. It was defined by
        information from "Le System Geodesique Nord-Sahara"; IGN Paris
        Adjustment includes Morocco and Tunisia but use only in Algeria.
        Within Algeria the adjustment is north of 32N but use has been
        extended southwards in many disconnected projects, some based on
        independent astro stations rather than the geodetic network.
    :cvar PULKOVO_1942: A geodetic datum first defined in 1942 suitable
        for use in Armenia; Azerbaijan; Belarus; Estonia - onshore;
        Georgia - onshore; Kazakhstan; Kyrgyzstan; Latvia - onshore;
        Lithuania - onshore; Moldova; Russian Federation - onshore;
        Tajikistan; Turkmenistan; Ukraine - onshore; Uzbekistan. Pulkovo
        1942 references the Krassowsky 1940 ellipsoid and the Greenwich
        prime meridian. Pulkovo 1942 origin is Fundamental point:
        Pulkovo observatory. Latitude: 5946'18.550"N, longitude:
        3019'42.090"E (of Greenwich). Pulkovo 1942 is a geodetic datum
        for Topographic mapping.
    :cvar S_JTSK: A geodetic datum suitable for use in Czech Republic;
        Slovakia. System Jednotne Trigonometricke Site Katastralni
        references the Bessel 1841 ellipsoid and the Greenwich prime
        meridian. System Jednotne Trigonometricke Site Katastralni
        origin is Modification of Austrian MGI datum, code 6312. System
        Jednotne Trigonometricke Site Katastralni is a geodetic datum
        for Geodetic survey, cadastre, topographic mapping, engineering
        survey. It was defined by information from Research Institute
        for Geodesy Topography and Cartography (VUGTK); Prague. S-JTSK =
        System of the Unified Trigonometrical Cadastral Network.
    :cvar VOIROL_1950: Voirol 1950 datum.
    :cvar AVERAGE_TERRESTRIAL_SYSTEM_1977: A geodetic datum first
        defined in 1977 suitable for use in Canada - New Brunswick; Nova
        Scotia; Prince Edward Island. Average Terrestrial System 1977
        references the Average Terrestrial System 1977 ellipsoid and the
        Greenwich prime meridian. Average Terrestrial System 1977 is a
        geodetic datum for Topographic mapping. It was defined by
        information from New Brunswick Geographic Information
        Corporation land and water information standards manual. In use
        from 1979.
    :cvar COMPENSATION_GEODESIQUE_DU_QUEBEC_1977: Compensation
        Geodesique du Quebec 1977.
    :cvar FINNISH_KKJ: A geodetic datum first defined in 1966 suitable
        for use in Finland - onshore. Kartastokoordinaattijarjestelma
        (1966) references the International 1924 ellipsoid and the
        Greenwich prime meridian. Kartastokoordinaattijarjestelma (1966)
        origin is Adjustment with fundamental point SF31 based on ED50
        transformed to best fit the older VVJ adjustment.
        Kartastokoordinaattijarjestelma (1966) is a geodetic datum for
        Geodetic survey, cadastre, topographic mapping, engineering
        survey. It was defined by information from National Land Survey
        of Finland; http://www.maanmittauslaitos.fi. Adopted in 1970.
    :cvar ORDNANCE_SURVEY_OF_IRELAND: A geodetic datum first defined in
        1952 suitable for use in United Kingdom (UK) - Northern Ireland
        (Ulster) - onshore. OSNI 1952 references the Airy 1830 ellipsoid
        and the Greenwich prime meridian. OSNI 1952 origin is Position
        fixed to the coordinates from the 19th century Principle
        Triangulation of station Divis. Scale and orientation controlled
        by position of Principle Triangulation stations Knocklayd and
        Trostan. OSNI 1952 is a geodetic datum for Geodetic survey and
        topographic mapping. It was defined by information from Ordnance
        Survey of Northern Ireland. Replaced by Geodetic Datum of 1965
        alias 1975 Mapping Adjustment or TM75 (datum code 6300).
    :cvar REVISED_KERTAU: A geodetic datum first defined in 1969
        suitable for use in Malaysia - West Malaysia; Singapore. Kertau
        (RSO) references the Everest 1830 (RSO 1969) ellipsoid and the
        Greenwich prime meridian. Kertau (RSO) is a geodetic datum for
        Metrication of RSO grid. It was defined by information from
        Defence Geographic Centre. Adopts metric conversion of 0.914398
        metres per yard exactly. This is a truncation of the Sears 1922
        ratio.
    :cvar REVISED_NAHRWAN: A geodetic datum first defined in 1967
        suitable for use in Arabian Gulf; Qatar - offshore; United Arab
        Emirates (UAE) - Abu Dhabi; Dubai; Sharjah; Ajman; Fujairah; Ras
        Al Kaimah; Umm Al Qaiwain - onshore and offshore. Nahrwan 1967
        references the Clarke 1880 (RGS) ellipsoid and the Greenwich
        prime meridian. Nahrwan 1967 origin is Fundamental point:
        Nahrwan south base. Latitude: 3319'10.87"N, longitude:
        4443'25.54"E (of Greenwich). Nahrwan 1967 is a geodetic datum
        for Topographic mapping. In Iraq, replaces Nahrwan 1934.
    :cvar GGRS_76_GREECE: A geodetic datum first defined in 1987
        suitable for use in Greece - onshore. Greek Geodetic Reference
        System 1987 references the GRS 1980 ellipsoid and the Greenwich
        prime meridian. Greek Geodetic Reference System 1987 origin is
        Fundamental point: Dionysos. Latitude 3804'33.8"N, longitude
        2355'51.0"E of Greenwich; geoid height 7.0 m. Greek Geodetic
        Reference System 1987 is a geodetic datum for Topographic
        mapping. It was defined by information from L. Portokalakis;
        Public Petroleum Corporation of Greece. Replaced (old) Greek
        datum. Oil industry work based on ED50.
    :cvar NOUVELLE_TRIANGULATION_DE_FRANCE: A geodetic datum first
        defined in 1895 suitable for use in France - onshore - mainland
        and Corsica. Nouvelle Triangulation Francaise references the
        Clarke 1880 (IGN) ellipsoid and the Greenwich prime meridian.
        Nouvelle Triangulation Francaise origin is Fundamental point:
        Pantheon. Latitude: 4850'46.522"N, longitude: 220'48.667"E (of
        Greenwich). Nouvelle Triangulation Francaise is a geodetic datum
        for Topographic mapping.
    :cvar RT_90_SWEDEN: A geodetic datum first defined in 1982 suitable
        for use in Sweden - onshore and offshore. Rikets koordinatsystem
        1990 references the Bessel 1841 ellipsoid and the Greenwich
        prime meridian. Rikets koordinatsystem 1990 is a geodetic datum
        for Geodetic survey, cadastre, topographic mapping, engineering
        survey. It was defined by information from National Land Survey
        of Sweden Replaces RT38 adjustment (datum code 6308).
    :cvar GEOCENTRIC_DATUM_OF_AUSTRALIA: A geodetic datum first defined
        in 1994 suitable for use in Australia including Lord Howe
        Island, Macquarie Islands, Ashmore and Cartier Islands,
        Christmas Island, Cocos (Keeling) Islands, Norfolk Island. All
        onshore and offshore. Geocentric Datum of Australia 1994
        references the GRS 1980 ellipsoid and the Greenwich prime
        meridian. Geocentric Datum of Australia 1994 origin is ITRF92 at
        epoch 1994.0. Geocentric Datum of Australia 1994 is a geodetic
        datum for Topographic mapping, geodetic survey. It was defined
        by information from Australian Surveying and Land Information
        Group Internet WWW page.
        http://www.auslig.gov.au/geodesy/datums/gda.htm#specs Coincident
        with WGS84 to within 1 metre.
    :cvar BJZ54_A954_BEIJING_COORDINATES: A geodetic datum first defined
        in 1954 suitable for use in China - onshore. Beijing 1954
        references the Krassowsky 1940 ellipsoid and the Greenwich prime
        meridian. Beijing 1954 origin is Pulkovo, transferred through
        Russian triangulation. Beijing 1954 is a geodetic datum for
        Topographic mapping. It was defined by information from Chinese
        Science Bulletin, 2009, 54:2714-2721 Scale determined through
        three baselines in northeast China. Discontinuities at
        boundaries of adjustment blocks. From 1982 replaced by Xian 1980
        and New Beijing.
    :cvar MODIFIED_BJZ54: Modified BJZ54 datum.
    :cvar GDZ80: GDZ80 datum.
    :cvar LOCAL_DATUM: An arbitrary datum defined by a local harbour
        authority, from which levels and tidal heights are measured by
        this authority.
    """

    WGS_72 = "WGS 72"
    WGS_84 = "WGS 84"
    EUROPEAN_1950 = "European 1950"
    POTSDAM_DATUM = "Potsdam Datum"
    ADINDAN = "Adindan"
    AFGOOYE = "Afgooye"
    AIN_EL_ABD_1970 = "Ain el Abd 1970"
    ANNA_1_ASTRO_1965 = "Anna 1 Astro 1965"
    ANTIGUA_ISLAND_ASTRO_1943 = "Antigua Island Astro 1943"
    ARC_1950 = "Arc 1950"
    ARC_1960 = "Arc 1960"
    ASCENSION_ISLAND_1958 = "Ascension Island 1958"
    ASTRO_BEACON_E_1945 = "Astro Beacon 'E' 1945"
    ASTRO_DOS_71_4 = "Astro DOS 71/4"
    ASTRO_TERN_ISLAND_FRIG_1961 = "Astro Tern Island (FRIG) 1961"
    ASTRONOMICAL_STATION_1952 = "Astronomical Station 1952"
    AUSTRALIAN_GEODETIC_1966 = "Australian Geodetic 1966"
    AUSTRALIAN_GEODETIC_1984 = "Australian Geodetic 1984"
    AYABELLE_LIGHTHOUSE = "Ayabelle Lighthouse"
    BELLEVUE_IGN = "Bellevue (IGN)"
    BERMUDA_1957 = "Bermuda 1957"
    BISSAU = "Bissau"
    BOGOTA_OBSERVATORY = "Bogota Observatory"
    BUKIT_RIMPAH = "Bukit Rimpah"
    CAMP_AREA_ASTRO = "Camp Area Astro"
    CAMPO_INCHAUSPE_1969 = "Campo Inchauspe 1969"
    CANTON_ASTRO_1966 = "Canton Astro 1966"
    CAPE_DATUM = "Cape Datum"
    CAPE_CANAVERAL = "Cape Canaveral"
    CARTHAGE = "Carthage"
    CHATAM_ISLAND_ASTRO_1971 = "Chatam Island Astro 1971"
    CHUA_ASTRO = "Chua Astro"
    CORREGO_ALEGRE = "Corrego Alegre"
    DABOLA = "Dabola"
    DJAKARTA_BATAVIA = "Djakarta (Batavia)"
    DOS_1968 = "DOS 1968"
    EASTER_ISLAND_1967 = "Easter Island 1967"
    EUROPEAN_1979 = "European 1979"
    FORT_THOMAS_1955 = "Fort Thomas 1955"
    GAN_1970 = "Gan 1970"
    GEODETIC_DATUM_1949 = "Geodetic Datum 1949"
    GRACIOSA_BASE_SW_1948 = "Graciosa Base SW 1948"
    GUAM_1963 = "Guam 1963"
    GUNUNG_SEGARA = "Gunung Segara"
    GUX_1_ASTRO = "GUX 1 Astro"
    HERAT_NORTH = "Herat North"
    HJORSEY_1955 = "Hjorsey 1955"
    HONG_KONG_1963 = "Hong Kong 1963"
    HU_TZU_SHAN = "Hu-Tzu-Shan"
    INDIAN = "Indian"
    INDIAN_1954 = "Indian 1954"
    INDIAN_1975 = "Indian 1975"
    IRELAND_1965 = "Ireland 1965"
    ISTS_061_ASTRO_1968 = "ISTS 061 Astro 1968"
    ISTS_073_ASTRO_1969 = "ISTS 073 Astro 1969"
    JOHNSTON_ISLAND_1961 = "Johnston Island 1961"
    KANDAWALA = "Kandawala"
    KERGUELEN_ISLAND_1949 = "Kerguelen Island 1949"
    KERTAU_1968 = "Kertau 1968"
    KUSAIE_ASTRO_1951 = "Kusaie Astro 1951"
    L_C_5_ASTRO_1961 = "L. C. 5 Astro 1961"
    LEIGON = "Leigon"
    LIBERIA_1964 = "Liberia 1964"
    LUZON = "Luzon"
    MAHE_1971 = "Mahe 1971"
    MASSAWA = "Massawa"
    MERCHICH = "Merchich"
    MIDWAY_ASTRO_1961 = "Midway Astro 1961"
    MINNA = "Minna"
    MONTSERRAT_ISLAND_ASTRO_1958 = "Montserrat Island Astro 1958"
    M_PORALOKO = "M'poraloko"
    NAHRWAN = "Nahrwan"
    NAPARIMA_BWI = "Naparima, BWI"
    NORTH_AMERICAN_1927 = "North American 1927"
    NORTH_AMERICAN_1983 = "North American 1983"
    OBSERVATORIO_METEOROLOGICO_1939 = "Observatorio Meteorologico 1939"
    OLD_EGYPTIAN_1907 = "Old Egyptian 1907"
    OLD_HAWAIIAN = "Old Hawaiian"
    OMAN = "Oman"
    ORDNANCE_SURVEY_OF_GREAT_BRITAIN_1936 = (
        "Ordnance Survey of Great Britain 1936"
    )
    PICO_DE_LAS_NIEVES = "Pico de las Nieves"
    PITCAIRN_ASTRO_1967 = "Pitcairn Astro 1967"
    POINT_58 = "Point 58"
    POINTE_NOIRE_1948 = "Pointe Noire 1948"
    PORTO_SANTO_1936 = "Porto Santo 1936"
    PROVISIONAL_SOUTH_AMERICAN_1956 = "Provisional South American 1956"
    PROVISIONAL_SOUTH_CHILEAN_1963 = "Provisional South Chilean 1963"
    PUERTO_RICO = "Puerto Rico"
    QATAR_NATIONAL = "Qatar National"
    QORNOQ = "Qornoq"
    REUNION = "Reunion"
    ROME_1940 = "Rome 1940"
    SANTO_DOS_1965 = "Santo (DOS) 1965"
    SAO_BRAZ = "Sao Braz"
    SAPPER_HILL_1943 = "Sapper Hill 1943"
    SCHWARZECK = "Schwarzeck"
    SELVAGEM_GRANDE_1938 = "Selvagem Grande 1938"
    SOUTH_AMERICAN_1969 = "South American 1969"
    SOUTH_ASIA = "South Asia"
    TANANARIVE_OBSERVATORY_1925 = "Tananarive Observatory 1925"
    TIMBALAI_1948 = "Timbalai 1948"
    TOKYO = "Tokyo"
    TRISTAN_ASTRO_1968 = "Tristan Astro 1968"
    VITI_LEVU_1916 = "Viti Levu 1916"
    WAKE_ENIWETOK_1960 = "Wake-Eniwetok 1960"
    WAKE_ISLAND_ASTRO_1952 = "Wake Island Astro 1952"
    YACARE = "Yacare"
    ZANDERIJ = "Zanderij"
    AMERICAN_SAMOA_1962 = "American Samoa 1962"
    DECEPTION_ISLAND = "Deception Island"
    INDIAN_1960 = "Indian 1960"
    INDONESIAN_1974 = "Indonesian 1974"
    NORTH_SAHARA_1959 = "North Sahara 1959"
    PULKOVO_1942 = "Pulkovo 1942"
    S_JTSK = "S-JTSK"
    VOIROL_1950 = "Voirol 1950"
    AVERAGE_TERRESTRIAL_SYSTEM_1977 = "Average Terrestrial System 1977"
    COMPENSATION_GEODESIQUE_DU_QUEBEC_1977 = (
        "Compensation Geodesique du Quebec 1977"
    )
    FINNISH_KKJ = "Finnish (KKJ)"
    ORDNANCE_SURVEY_OF_IRELAND = "Ordnance Survey of Ireland"
    REVISED_KERTAU = "Revised Kertau"
    REVISED_NAHRWAN = "Revised Nahrwan"
    GGRS_76_GREECE = "GGRS 76 (Greece)"
    NOUVELLE_TRIANGULATION_DE_FRANCE = "Nouvelle Triangulation de France"
    RT_90_SWEDEN = "RT 90 (Sweden)"
    GEOCENTRIC_DATUM_OF_AUSTRALIA = "Geocentric Datum of Australia"
    BJZ54_A954_BEIJING_COORDINATES = "BJZ54 (A954 Beijing Coordinates)"
    MODIFIED_BJZ54 = "Modified BJZ54"
    GDZ80 = "GDZ80"
    LOCAL_DATUM = "Local Datum"


@dataclass
class HorizontalPositionUncertaintyType:
    """
    The best estimate of the accuracy of a position.

    :ivar uncertainty_fixed: The best estimate of the fixed horizontal
        or vertical accuracy component for positions, depths, heights,
        vertical distances and vertical clearances.
    :ivar uncertainty_variable_factor: The factor to be applied to the
        variable component of an uncertainty equation so as to provide
        the best estimate of the variable horizontal or vertical
        accuracy component for positions, depths, heights, vertical
        distances and vertical clearances.
    """

    class Meta:
        name = "horizontalPositionUncertaintyType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    uncertainty_fixed: Optional[float] = field(
        default=None,
        metadata={
            "name": "uncertaintyFixed",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    uncertainty_variable_factor: Optional[float] = field(
        default=None,
        metadata={
            "name": "uncertaintyVariableFactor",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class InformationType:
    """Textual information about the feature.

    The information may be provided as a string of text or as a file
    name of a single external text file that contains the text.

    :ivar file_locator: The location of a fragment of text or other
        information in a support file.
    :ivar file_reference: The file name of an externally referenced text
        file.
    :ivar headline: Words set at the head of a passage or page to
        introduce or categorize.
    :ivar language: The method of human communication, either spoken or
        written, consisting of the use of words in a structured and
        conventional way.
    :ivar text: A non-formatted digital text string.
    """

    class Meta:
        name = "informationType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    file_locator: Optional[str] = field(
        default=None,
        metadata={
            "name": "fileLocator",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    file_reference: Optional[str] = field(
        default=None,
        metadata={
            "name": "fileReference",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    headline: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    language: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    text: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


class LightCharacteristicType(Enum):
    """
    :cvar FIXED: A signal light that shows continuously, in any given
        direction, with constant luminous intensity and colour.
    :cvar FLASHING: A rhythmic light in which the total duration of
        light in a period is clearly shorter than the total duration of
        darkness and all the appearances of light are of equal duration.
    :cvar LONG_FLASHING: A single-flashing light in which a single flash
        of not less than two seconds duration is regularly repeated.
    :cvar QUICK_FLASHING: A rhythmic light in which flashes are repeated
        at a rate of not less than 50 flashes per minutes but less than
        80 flashes per minutes. It may be: - Continuous quick-flashing:
        A quick-flashing light in which a flash is regularly repeated. -
        Group quick-flashing: A quick-flashing light in which a group of
        two or more flashes, which are specified in number, is regularly
        repeated.
    :cvar VERY_QUICK_FLASHING: A rhythmic light in which flashes are
        repeated at a rate of not less than 80 flashes per minute but
        less than 160 flashes per minute. It may be:- Continuous very
        quick-flashing: A very quick-flashing light in which a flash is
        regularly repeated.- Group very quick-flashing: A very quick-
        flashing light in which a group of two or more flashes, which
        are specified in number, is regularly repeated.
    :cvar CONTINUOUS_ULTRA_QUICK_FLASHING: A rhythmic light in which
        flashes are regularly repeated at a rate of not less than 160
        flashes per minute.
    :cvar ISOPHASED: A light with all durations of light and darkness
        equal.
    :cvar OCCULTING: A rhythmic light in which the total duration of
        light in a period is clearly longer than the total duration of
        darkness and all the eclipses are of equal duration. It may be:
        - Single-occulting: An occulting light in which an eclipse is
        regularly repeated.  - Group-occulting: An occulting light in
        which a group of two or more eclipses, which are specified in
        number, is regularly repeated.  - Composite group-occulting: An
        occulting light in which a sequence of groups of one or more
        eclipses, which are specified in number, is regularly repeated,
        and the groups comprise different numbers of eclipses.
    :cvar MORSE: A rhythmic light in which appearances of light of two
        clearly different durations are grouped to represent a character
        or characters in the Morse code.
    :cvar FIXED_AND_FLASH: A rhythmic light in which a fixed light is
        combined with a flashing light of higher luminous intensity.
    :cvar FLASH_AND_LONG_FLASH: A rhythmic light in which a flashing
        light is combined with a long-flashing light of higher luminous
        intensity.
    :cvar OCCULTING_AND_FLASH: A rhythmic light in which an occulting
        light is combined with a flashing light of higher luminous
        intensity.
    :cvar FIXED_AND_LONG_FLASH: A rhythmic light in which a fixed light
        is combined with a long-flashing light of higher luminous
        intensity.
    :cvar OCCULTING_ALTERNATING: An alternating light in which the total
        duration of light in each period is clearly longer than the
        total duration of darkness and in which the intervals of
        darkness (occultations) are all of equal duration.
    :cvar LONG_FLASH_ALTERNATING: An alternating single-flashing light
        in which an appearance of light of not less than two seconds
        duration is regularly repeated.
    :cvar FLASH_ALTERNATING: An alternating rhythmic light in which the
        total duration of light in a period is clearly shorter than the
        total duration of darkness and all the appearances of light are
        of equal duration.
    :cvar GROUP_ALTERNATING: Occulting light in which the occultations
        are combined in groups, each group including the same number of
        occultations, and in which the groups are repeated at regular
        intervals.
    :cvar QUICK_FLASH_PLUS_LONG_FLASH: A rhythmic light in which a group
        of quick flashes is followed by one or more long flashes in a
        regularly repeated sequence with a regular periodicity.
    :cvar VERY_QUICK_FLASH_PLUS_LONG_FLASH: A rhythmic light in which a
        group of very quick flashes is followed by one or more long
        flashes in a regularly repeated sequence with a regular
        periodicity.
    :cvar ULTRA_QUICK_FLASH_PLUS_LONG_FLASH: A rhythmic light in which a
        group of ultra quick flashes is followed by one or more long
        flashes in a regularly repeated sequence with a regular
        periodicity.
    :cvar ALTERNATING: A signal light that shows, in any given
        direction, two or more colours in a regularly repeated sequence
        with a regular periodicity.
    :cvar FIXED_AND_ALTERNATING_FLASHING:
    :cvar GROUP_OCCULTING_LIGHT: An occulting light in which a group of
        two or more eclipses, which are specified in number, is
        regularly repeated.
    :cvar COMPOSITE_GROUP_OCCULTING_LIGHT: An occulting light in which a
        sequence of groups of one or more eclipses, which are specified
        in number, is regularly repeated, and the groups comprise
        different numbers of eclipses.
    :cvar GROUP_FLASHING_LIGHT: A flashing light in which a group of
        flashes, specified in number, is regularly repeated.
    :cvar COMPOSITE_GROUP_FLASHING_LIGHT: A light similar to a group-
        flashing light except that successive groups in a period have
        different numbers of flashes.
    :cvar GROUP_QUICK_LIGHT: A quick-flashing light in which a group of
        two or more flashes, which are specified in number, is regularly
        repeated.
    :cvar GROUP_VERY_QUICK_LIGHT: A very quick-flashing light in which a
        group of two or more flashes, which are specified in number, is
        regularly repeated.
    """

    FIXED = "Fixed"
    FLASHING = "Flashing"
    LONG_FLASHING = "Long-Flashing"
    QUICK_FLASHING = "Quick-Flashing"
    VERY_QUICK_FLASHING = "Very Quick-Flashing"
    CONTINUOUS_ULTRA_QUICK_FLASHING = "Continuous Ultra Quick-Flashing"
    ISOPHASED = "Isophased"
    OCCULTING = "Occulting"
    MORSE = "Morse"
    FIXED_AND_FLASH = "Fixed and Flash"
    FLASH_AND_LONG_FLASH = "Flash and Long-Flash"
    OCCULTING_AND_FLASH = "Occulting and Flash"
    FIXED_AND_LONG_FLASH = "Fixed and Long-Flash"
    OCCULTING_ALTERNATING = "Occulting Alternating"
    LONG_FLASH_ALTERNATING = "Long-Flash Alternating"
    FLASH_ALTERNATING = "Flash Alternating"
    GROUP_ALTERNATING = "Group Alternating"
    QUICK_FLASH_PLUS_LONG_FLASH = "Quick-Flash Plus Long-Flash"
    VERY_QUICK_FLASH_PLUS_LONG_FLASH = "Very Quick-Flash Plus Long-Flash"
    ULTRA_QUICK_FLASH_PLUS_LONG_FLASH = "Ultra Quick-Flash Plus Long-Flash"
    ALTERNATING = "Alternating"
    FIXED_AND_ALTERNATING_FLASHING = "Fixed and Alternating Flashing"
    GROUP_OCCULTING_LIGHT = "Group-occulting light"
    COMPOSITE_GROUP_OCCULTING_LIGHT = "Composite group-occulting light"
    GROUP_FLASHING_LIGHT = "Group flashing light"
    COMPOSITE_GROUP_FLASHING_LIGHT = "Composite group-flashing light"
    GROUP_QUICK_LIGHT = "Group quick light"
    GROUP_VERY_QUICK_LIGHT = "Group very quick light"


class LightVisibilityType(Enum):
    """
    :cvar HIGH_INTENSITY: Non-marine lights with a higher power than
        marine lights and visible from well off shore (often 'Aero'
        lights).
    :cvar LOW_INTENSITY: Non-marine lights with lower power than marine
        lights.
    :cvar FAINT: A decrease in the apparent intensity of a light which
        may occur in the case of partial obstructions.
    :cvar INTENSIFIED: A light in a sector is intensified (that is, has
        longer range than other sectors).
    :cvar UNINTENSIFIED: A light in a sector is unintensified (that is,
        has shorter range than other sectors).
    :cvar VISIBILITY_DELIBERATELY_RESTRICTED: A light sector is
        deliberately reduced in intensity, for example to reduce its
        effect on a built-up area.
    :cvar OBSCURED: Said of the arc of a light sector designated by its
        limiting bearings in which the light is not visible from
        seaward.
    :cvar PARTIALLY_OBSCURED: This value specifies that parts of the
        sector are obscured.
    :cvar VISIBLE_IN_LINE_OF_RANGE: Lights that must in line to be
        visible.
    """

    HIGH_INTENSITY = "High Intensity"
    LOW_INTENSITY = "Low Intensity"
    FAINT = "Faint"
    INTENSIFIED = "Intensified"
    UNINTENSIFIED = "Unintensified"
    VISIBILITY_DELIBERATELY_RESTRICTED = "Visibility Deliberately Restricted"
    OBSCURED = "Obscured"
    PARTIALLY_OBSCURED = "Partially Obscured"
    VISIBLE_IN_LINE_OF_RANGE = "Visible in Line of Range"


class LightedAtonChangeType(Enum):
    """
    :cvar LIGHT_UNLIT: .
    :cvar LIGHT_UNRELIABLE: .
    :cvar LIGHT_RE_ESTABLISHMENT: .
    :cvar LIGHT_RANGE_REDUCED: .
    :cvar LIGHT_WITHOUT_RHYTHM: .
    :cvar LIGHT_OUT_OF_SYNCHRONIZATION: .
    :cvar LIGHT_DAYMARK_UNRELIABLE: .
    :cvar LIGHT_OPERATING_PROPERLY: .
    :cvar SECTOR_LIGHT_SECTOR_OBSCURED: .
    :cvar FRONT_LEADING_RANGE_LIGHT_UNLIT: .
    :cvar REAR_LEADING_RANGE_LIGHT_UNLIT: .
    :cvar FRONT_LEADING_RANGE_LIGHT_UNRELIABLE: .
    :cvar REAR_LEADING_RANGE_LIGHT_UNRELIABLE: .
    :cvar FRONT_LEADING_RANGE_LIGHT_LIGHT_RANGE_REDUCED: .
    :cvar REAR_LEADING_RANGE_LIGHT_LIGHT_RANGE_REDUCED: .
    :cvar FRONT_LEADING_RANGE_LIGHT_WITHOUT_RHYTHM: .
    :cvar REAR_LEADING_RANGE_LIGHT_WITHOUT_RHYTHM: .
    :cvar LEADING_RANGE_LIGHTS_OUT_OF_SYNCHRONIZATION: .
    :cvar FRONT_LEADING_RANGE_BEACON_UNRELIABLE: .
    :cvar REAR_LEADING_RANGE_BEACON_UNRELIABLE: .
    :cvar FRONT_LEADING_RANGE_LIGHT_IS_OPERATING_PROPERLY: .
    :cvar REAR_LEADING_RANGE_LIGHT_IS_OPERATING_PROPERLY: .
    :cvar FRONT_LEADING_RANGE_BEACON_RESTORED_TO_NORMAL: .
    :cvar REAR_LEADING_RANGE_BEACON_RESTORED_TO_NORMAL: .
    """

    LIGHT_UNLIT = "Light unlit"
    LIGHT_UNRELIABLE = "Light unreliable"
    LIGHT_RE_ESTABLISHMENT = "Light re-establishment"
    LIGHT_RANGE_REDUCED = "Light range reduced"
    LIGHT_WITHOUT_RHYTHM = "Light without rhythm"
    LIGHT_OUT_OF_SYNCHRONIZATION = "Light out of synchronization"
    LIGHT_DAYMARK_UNRELIABLE = "Light daymark unreliable"
    LIGHT_OPERATING_PROPERLY = "Light operating properly"
    SECTOR_LIGHT_SECTOR_OBSCURED = "Sector light Sector obscured"
    FRONT_LEADING_RANGE_LIGHT_UNLIT = "Front leading/range light Unlit"
    REAR_LEADING_RANGE_LIGHT_UNLIT = "Rear leading/range light Unlit"
    FRONT_LEADING_RANGE_LIGHT_UNRELIABLE = (
        "Front leading/range light Unreliable"
    )
    REAR_LEADING_RANGE_LIGHT_UNRELIABLE = "Rear leading/range light Unreliable"
    FRONT_LEADING_RANGE_LIGHT_LIGHT_RANGE_REDUCED = (
        "Front leading/range light Light range reduced"
    )
    REAR_LEADING_RANGE_LIGHT_LIGHT_RANGE_REDUCED = (
        "Rear leading/range light Light range reduced"
    )
    FRONT_LEADING_RANGE_LIGHT_WITHOUT_RHYTHM = (
        "Front leading/range light without rhythm"
    )
    REAR_LEADING_RANGE_LIGHT_WITHOUT_RHYTHM = (
        "Rear leading/range light without rhythm"
    )
    LEADING_RANGE_LIGHTS_OUT_OF_SYNCHRONIZATION = (
        "Leading/range lights out of synchronization"
    )
    FRONT_LEADING_RANGE_BEACON_UNRELIABLE = (
        "Front leading/range beacon Unreliable"
    )
    REAR_LEADING_RANGE_BEACON_UNRELIABLE = (
        "Rear leading/range beacon Unreliable"
    )
    FRONT_LEADING_RANGE_LIGHT_IS_OPERATING_PROPERLY = (
        "Front leading/range light is operating properly"
    )
    REAR_LEADING_RANGE_LIGHT_IS_OPERATING_PROPERLY = (
        "Rear leading/range light is operating properly"
    )
    FRONT_LEADING_RANGE_BEACON_RESTORED_TO_NORMAL = (
        "Front leading/range beacon restored to normal"
    )
    REAR_LEADING_RANGE_BEACON_RESTORED_TO_NORMAL = (
        "Rear leading/range beacon restored to normal"
    )


class MarksNavigationalSystemOfType(Enum):
    """
    :cvar IALA_A: Navigational aids conform to the International
        Association of Marine Aids to Navigation and Lighthouse
        Authorities - IALA A system.
    :cvar IALA_B: Navigational aids conform to the International
        Association of Marine Aids to Navigation and Lighthouse
        Authorities - IALA B system.
    :cvar NO_SYSTEM: Navigational aids do not conform to any defined
        system.
    :cvar OTHER_SYSTEM: Navigational aids conform to a defined system
        other than International Association of Marine Aids to
        Navigation and Lighthouse Authorities - IALA.
    :cvar CEVNI: CEVNI (European Code for Navigation on Inland
        Waterways) is the European code for rivers, canals land lakes in
        most of Europe.
    :cvar RUSSIAN_INLAND_WATERWAY_REGULATIONS: Navigational aids conform
        to the Russian inland waterway regulations.
    :cvar BRAZILIAN_NATIONAL_INLAND_WATERWAY_REGULATIONS_TWO_SIDES:
        Navigational aids conform to the Brazilian national inland
        waterway regulations for two sides.
    :cvar
        BRAZILIAN_NATIONAL_INLAND_WATERWAY_REGULATIONS_SIDE_INDEPENDENT:
        Navigational aids conform to the Brazilian national inland
        waterway regulations - side independent.
    :cvar PARAGUAY_PARANA_WATERWAY_BRAZILIAN_COMPLEMENTARY_AIDS:
        Navigational aids conform to the Brazilian complementary aids on
        the Paraguay-Parana waterway.
    """

    IALA_A = "IALA A"
    IALA_B = "IALA B"
    NO_SYSTEM = "No System"
    OTHER_SYSTEM = "Other System"
    CEVNI = "CEVNI"
    RUSSIAN_INLAND_WATERWAY_REGULATIONS = "Russian Inland Waterway Regulations"
    BRAZILIAN_NATIONAL_INLAND_WATERWAY_REGULATIONS_TWO_SIDES = (
        "Brazilian National Inland Waterway Regulations - Two Sides"
    )
    BRAZILIAN_NATIONAL_INLAND_WATERWAY_REGULATIONS_SIDE_INDEPENDENT = (
        "Brazilian National Inland Waterway Regulations - Side Independent"
    )
    PARAGUAY_PARANA_WATERWAY_BRAZILIAN_COMPLEMENTARY_AIDS = (
        "Paraguay-Parana Waterway - Brazilian Complementary Aids"
    )


@dataclass
class MultiplicityOfFeaturesType:
    """
    The number of features of identical character that exist as a colocated group.

    :ivar multiplicity_known: The number of features of identical
        character that exist as a co-located group is or is not known.
    :ivar number_of_features: The number of features of identical
        character that exist as a co-located group.
    """

    class Meta:
        name = "multiplicityOfFeaturesType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    multiplicity_known: Optional[bool] = field(
        default=None,
        metadata={
            "name": "multiplicityKnown",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    number_of_features: Optional[int] = field(
        default=None,
        metadata={
            "name": "numberOfFeatures",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


class NatureOfConstructionType(Enum):
    """
    :cvar MASONRY: Constructed of stones or bricks, usually quarried,
        shaped, and mortared.
    :cvar CONCRETED: Constructed of concrete, a material made of sand
        and gravel that is united by cement into a hardened mass used
        for roads, foundations, etc.
    :cvar LOOSE_BOULDERS: Constructed from large stones or blocks of
        concrete, often placed loosely for protection against waves or
        water turbulence.
    :cvar HARD_SURFACED: Constructed with a surface of hard material,
        usually a term applied to roads surfaced with asphalt or
        concrete.
    :cvar UNSURFACED: Constructed with no extra protection, usually a
        term applied to roads not surfaced with a hard material.
    :cvar WOODEN: Constructed from wood.
    :cvar METAL: Constructed from metal.
    :cvar GLASS_REINFORCED_PLASTIC: Constructed from a plastic material
        strengthened with fibres of glass.
    :cvar PAINTED: The application of paint to some other construction
        or natural feature.
    :cvar FRAMEWORK: Constructed from a lattice framework of, often
        diagonal, intersecting struts.
    :cvar LATTICED: A structure of crossed wooden or metal strips
        usually arranged to form a diagonal pattern of open spaces
        between the strips.
    :cvar GLASS: [1] Any artificial or natural substance having similar
        properties and composition, as fused borax, obsidian, or the
        like.   [2] Something made of such a substance, as a windowpane.
    :cvar FIBERGLASS: Constructed from fiberglass.
    :cvar PLASTIC: Constructed from plastic.
    """

    MASONRY = "Masonry"
    CONCRETED = "Concreted"
    LOOSE_BOULDERS = "Loose Boulders"
    HARD_SURFACED = "Hard Surfaced"
    UNSURFACED = "Unsurfaced"
    WOODEN = "Wooden"
    METAL = "Metal"
    GLASS_REINFORCED_PLASTIC = "Glass Reinforced Plastic"
    PAINTED = "Painted"
    FRAMEWORK = "Framework"
    LATTICED = "Latticed"
    GLASS = "Glass"
    FIBERGLASS = "Fiberglass"
    PLASTIC = "Plastic"


@dataclass
class OrientationType:
    """(1) The angular distance measured from true north to the major axis of the
    feature.

    (2) In ECDIS, the mode in which information on the ECDIS is being presented. Typical modes include: north-up - as shown on a nautical chart, north is at the top of the display; Ships head-up - based on the actual heading of the ship, (e.g. Ships gyrocompass); course-up display - based on the course or route being taken.

    :ivar orientation_uncertainty: The best estimate of the accuracy of
        a bearing.
    :ivar orientation_value: The angular distance measured from true
        north to the major axis of the feature.
    """

    class Meta:
        name = "orientationType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    orientation_uncertainty: Optional[float] = field(
        default=None,
        metadata={
            "name": "orientationUncertainty",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    orientation_value: Optional[float] = field(
        default=None,
        metadata={
            "name": "orientationValue",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )


class PositioningEquipmentType(Enum):
    """
    :cvar DGPS_RECEIVER: .
    :cvar GLONASS_RECEIVER: .
    :cvar GPS_RECEIVER: .
    :cvar GPS_WAAS_RECEIVER: .
    """

    DGPS_RECEIVER = "DGPS Receiver"
    GLONASS_RECEIVER = "GLONASS Receiver"
    GPS_RECEIVER = "GPS Receiver"
    GPS_WAAS_RECEIVER = "GPS/WAAS Receiver"


class ProductType(Enum):
    """
    :cvar OIL: A thick, slippery liquid that will not dissolve in water,
        usually petroleum based in the context of storage tanks.
    :cvar GAS: A substance with particles that can move freely, usually
        a fuel substance in the context of storage tanks.
    :cvar WATER: A colourless, odourless, tasteless liquid that is a
        compound of hydrogen and oxygen.
    :cvar STONE: A general term for rock and rock fragments ranging in
        size from pebbles and gravel to boulders or large rock masses.
    :cvar COAL: A hard black mineral that is burned as fuel.
    :cvar ORE: A solid rock or mineral from which metal is obtained.
    :cvar CHEMICALS: Any substance obtained by or used in a chemical
        process.
    :cvar DRINKING_WATER: Water that is suitable for human consumption.
    :cvar MILK: A white fluid secreted by female mammals as food for
        their young.
    :cvar BAUXITE: A mineral from which aluminum is obtained.
    :cvar COKE: A solid substance obtained after gas and tar have been
        extracted from coal, used as a fuel.
    :cvar IRON_INGOTS: An oblong lump of cast iron metal.
    :cvar SALT: Sodium chloride obtained from mines or by the
        evaporation of sea water.
    :cvar SAND: Loose material consisting of small but easily
        distinguishable, separate grains, between 0.0625 and 2.000
        millimetres in diameter.
    :cvar TIMBER: Wood prepared for use in building or carpentry.
    :cvar SAWDUST_WOOD_CHIPS: Powdery fragments of wood made in sawing
        timber or coarse chips produced for use in manufacturing pressed
        board.
    :cvar SCRAP_METAL: Discarded metal suitable for being reprocessed.
    :cvar LIQUEFIED_NATURAL_GAS: Natural gas that has been liquefied for
        ease of transport by cooling the gas to -162 Celsius.
    :cvar LIQUEFIED_PETROLEUM_GAS: A compressed gas consisting of
        flammable light hydrocarbons and derived from petroleum.
    :cvar WINE: The fermented juice of grapes.
    :cvar CEMENT: A substance made of powdered lime and clay, mixed with
        water.
    :cvar GRAIN: A small hard seed, especially that of any cereal plant
        such as wheat, rice, corn, rye etc.
    :cvar ELECTRICITY: Electric charge or current.
    :cvar ICE: The solid form of water.
    :cvar CLAY: (Particles of less than 0.002mm); stiff, sticky earth
        that becomes hard when baked.
    """

    OIL = "Oil"
    GAS = "Gas"
    WATER = "Water"
    STONE = "Stone"
    COAL = "Coal"
    ORE = "Ore"
    CHEMICALS = "Chemicals"
    DRINKING_WATER = "Drinking Water"
    MILK = "Milk"
    BAUXITE = "Bauxite"
    COKE = "Coke"
    IRON_INGOTS = "Iron Ingots"
    SALT = "Salt"
    SAND = "Sand"
    TIMBER = "Timber"
    SAWDUST_WOOD_CHIPS = "Sawdust/Wood Chips"
    SCRAP_METAL = "Scrap Metal"
    LIQUEFIED_NATURAL_GAS = "Liquefied Natural Gas"
    LIQUEFIED_PETROLEUM_GAS = "Liquefied Petroleum Gas"
    WINE = "Wine"
    CEMENT = "Cement"
    GRAIN = "Grain"
    ELECTRICITY = "Electricity"
    ICE = "Ice"
    CLAY = "Clay"


class QualityOfHorizontalMeasurementType(Enum):
    """
    :cvar SURVEYED: The position(s) was(were) determined by the
        operation of making measurements for determining the relative
        position of points on, above or beneath the earth's surface.
        Survey implies a regular, controlled survey of any date.
    :cvar UNSURVEYED: Survey data is does not exist or is very poor.
    :cvar INADEQUATELY_SURVEYED: Not surveyed to modern standards; or
        due to its age, scale, or positional or vertical uncertainties
        is not suitable to the type of navigation expected in the area.
    :cvar APPROXIMATE: A position that is considered to be less than
        third-order accuracy, but is generally considered to be within
        30.5 metres of its correct geographic location. Also may apply
        to an object whose position does not remain fixed.
    :cvar POSITION_DOUBTFUL: Of uncertain position. The expression is
        used principally on charts to indicate that a wreck, shoal,
        etc., has been reported in various positions and not definitely
        determined in any.
    :cvar UNRELIABLE: A feature's position has been obtained from
        questionable or unreliable data.
    :cvar REPORTED_NOT_SURVEYED: An object whose position has been
        reported and its position confirmed by some means other than a
        formal survey such as an independent report of the same object.
    :cvar REPORTED_NOT_CONFIRMED: An object whose position has been
        reported and its position has not been confirmed.
    :cvar ESTIMATED: The most probable position of an object determined
        from incomplete data or data of questionable accuracy.
    :cvar PRECISELY_KNOWN: A position that is of a known value, such as
        the position of an anchor berth or other defined object.
    :cvar CALCULATED: A position that is computed from data.
    """

    SURVEYED = "Surveyed"
    UNSURVEYED = "Unsurveyed"
    INADEQUATELY_SURVEYED = "Inadequately Surveyed"
    APPROXIMATE = "Approximate"
    POSITION_DOUBTFUL = "Position Doubtful"
    UNRELIABLE = "Unreliable"
    REPORTED_NOT_SURVEYED = "Reported (Not Surveyed)"
    REPORTED_NOT_CONFIRMED = "Reported (Not Confirmed)"
    ESTIMATED = "Estimated"
    PRECISELY_KNOWN = "Precisely Known"
    CALCULATED = "Calculated"


class QualityOfVerticalMeasurementType(Enum):
    """
    :cvar DEPTH_KNOWN: The depth from the chart datum to the seabed (or
        to the top of a drying feature) is known.
    :cvar DEPTH_OR_LEAST_DEPTH_UNKNOWN: The depth from chart datum to
        the seabed, or the shoalest depth of the feature is unknown.
    :cvar DOUBTFUL_SOUNDING: A depth that may be less than indicated.
    :cvar UNRELIABLE_SOUNDING: A depth that is considered to be an
        unreliable value.
    :cvar NO_BOTTOM_FOUND_AT_VALUE_SHOWN: Upon investigation the bottom
        was not found at this depth.
    :cvar LEAST_DEPTH_KNOWN: The shoalest depth over a feature is of
        known value.
    :cvar LEAST_DEPTH_UNKNOWN_SAFE_CLEARANCE_AT_VALUE_SHOWN: The least
        depth over a feature is unknown, but there is considered to be
        safe clearance at this depth.
    :cvar VALUE_REPORTED_NOT_SURVEYED: Depth value obtained from a
        report, but not fully surveyed.
    :cvar VALUE_REPORTED_NOT_CONFIRMED: Depth value obtained from a
        report, which it has not been possible to confirm.
    :cvar MAINTAINED_DEPTH: The depth at which a channel is kept by
        human influence, usually by dredging.
    :cvar NOT_REGULARLY_MAINTAINED: Depths may be altered by human
        influence, but will not be routinely maintained.
    """

    DEPTH_KNOWN = "Depth Known"
    DEPTH_OR_LEAST_DEPTH_UNKNOWN = "Depth or Least Depth Unknown"
    DOUBTFUL_SOUNDING = "Doubtful Sounding"
    UNRELIABLE_SOUNDING = "Unreliable Sounding"
    NO_BOTTOM_FOUND_AT_VALUE_SHOWN = "No Bottom Found at Value Shown"
    LEAST_DEPTH_KNOWN = "Least Depth Known"
    LEAST_DEPTH_UNKNOWN_SAFE_CLEARANCE_AT_VALUE_SHOWN = (
        "Least Depth Unknown, Safe Clearance at Value Shown"
    )
    VALUE_REPORTED_NOT_SURVEYED = "Value Reported (Not Surveyed)"
    VALUE_REPORTED_NOT_CONFIRMED = "Value Reported (Not Confirmed)"
    MAINTAINED_DEPTH = "Maintained Depth"
    NOT_REGULARLY_MAINTAINED = "Not Regularly Maintained"


@dataclass
class RadarWaveLengthType:
    """
    The distance between two successive peaks (or other points of identical phase)
    on an electromagnetic wave in the radar band of the electromagnetic spectrum.

    :ivar radar_band: The band code character of the electromagnetic
        spectrum within which radar wave lengths lie.
    :ivar wave_length_value: The distance between two successive peaks
        (or other points of identical phase) on an electromagnetic wave.
    """

    class Meta:
        name = "radarWaveLengthType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    radar_band: Optional[str] = field(
        default=None,
        metadata={
            "name": "radarBand",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    wave_length_value: Optional[float] = field(
        default=None,
        metadata={
            "name": "waveLengthValue",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )


@dataclass
class SectorInformationType:
    """
    Additional textual information about a light sector.

    :ivar language: The method of human communication, either spoken or
        written, consisting of the use of words in a structured and
        conventional way.
    :ivar text: A non-formatted digital text string.
    """

    class Meta:
        name = "sectorInformationType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    language: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    text: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )


@dataclass
class SectorLimitOneType:
    """A sector is the part of a circle between two straight lines drawn from the
    centre to the circumference.

    Sector limit one specifies the first limit of the sector. The order
    of sector limit one and sector limit two is clockwise around the
    central feature (for example a light).

    :ivar sector_bearing: A sector is the part of a circle between two
        straight lines drawn from the centre to the circumference.
        Sector bearing specifies the limit of the sector.
    :ivar sector_line_length: A sector is the part of a circle between
        two straight lines drawn from the centre to the circumference.
        Sector line length specifies the displayed length of the line,
        in ground units, defining the limit of the sector.
    """

    class Meta:
        name = "sectorLimitOneType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    sector_bearing: Optional[float] = field(
        default=None,
        metadata={
            "name": "sectorBearing",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    sector_line_length: Optional[int] = field(
        default=None,
        metadata={
            "name": "sectorLineLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class SectorLimitTwoType:
    """A sector is the part of a circle between two straight lines drawn from the
    centre to the circumference.

    Sector limit two specifies the second limit of the sector. The order
    of sector limit one and sector limit two is clockwise around the
    central feature (for example a light).

    :ivar sector_bearing: A sector is the part of a circle between two
        straight lines drawn from the centre to the circumference.
        Sector bearing specifies the limit of the sector.
    :ivar sector_line_length: A sector is the part of a circle between
        two straight lines drawn from the centre to the circumference.
        Sector line length specifies the displayed length of the line,
        in ground units, defining the limit of the sector.
    """

    class Meta:
        name = "sectorLimitTwoType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    sector_bearing: Optional[float] = field(
        default=None,
        metadata={
            "name": "sectorBearing",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    sector_line_length: Optional[int] = field(
        default=None,
        metadata={
            "name": "sectorLineLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class ShapeInformationType:
    """
    Textual information about the shape of a non-standard topmark.

    :ivar language: The method of human communication, either spoken or
        written, consisting of the use of words in a structured and
        conventional way.
    :ivar text: A non-formatted digital text string.
    """

    class Meta:
        name = "shapeInformationType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    language: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    text: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )


class SignalGenerationType(Enum):
    """
    :cvar AUTOMATICALLY: Signal generation is initiated by a self
        regulating mechanism such as a timer or light sensor.
    :cvar BY_WAVE_ACTION: The signal is generated by the motion of the
        sea surface such as a bell in a buoy.
    :cvar BY_HAND: The signal is generated by a manually operated
        mechanism such as a hand cranked siren.
    :cvar BY_WIND: The signal is generated by the motion of air such as
        a wind driven whistle.
    :cvar RADIO_ACTIVATED: Activated by radio signal.
    :cvar CALL_ACTIVATED: Activated by making a call to a manned
        station.
    """

    AUTOMATICALLY = "Automatically"
    BY_WAVE_ACTION = "By Wave Action"
    BY_HAND = "By Hand"
    BY_WIND = "By Wind"
    RADIO_ACTIVATED = "Radio Activated"
    CALL_ACTIVATED = "Call Activated"


class SignalStatusType(Enum):
    """
    :cvar LIT_SOUND: The indication of an element of a signal sequence
        being a period of light or sound.
    :cvar ECLIPSED_SILENT: The indication of an element of a signal
        sequence being a period of eclipse or silence.
    """

    LIT_SOUND = "Lit/Sound"
    ECLIPSED_SILENT = "Eclipsed/Silent"


class StatusType(Enum):
    """
    :cvar PERMANENT: Intended to last or function indefinitely.
    :cvar OCCASIONAL: Acting on special occasions; happening
        irregularly.
    :cvar RECOMMENDED: Presented as worthy of confidence, acceptance,
        use, etc.
    :cvar NOT_IN_USE: Use has ceased, but the facility still exists
        intact; disused.
    :cvar PERIODIC_INTERMITTENT: Recurring at intervals.
    :cvar RESERVED: Set apart for some specific use.
    :cvar TEMPORARY: Meant to last only for a time.
    :cvar PRIVATE: Administered by an individual or corporation, rather
        than a State or a public body.
    :cvar MANDATORY: Compulsory; enforced.
    :cvar EXTINGUISHED: No longer lit.
    :cvar ILLUMINATED: Lit by floodlights, strip lights, etc.
    :cvar HISTORIC: Famous in history; of historical interest.
    :cvar PUBLIC: Belonging to, available to, used or shared by, the
        community as a whole and not restricted to private use.
    :cvar SYNCHRONIZED: Occur at a time, coincide in point of time, be
        contemporary or simultaneous.
    :cvar WATCHED: Looked at or observed over a period of time
        especially so as to be aware of any movement or change.
    :cvar UNWATCHED: Usually automatic in operation, without any
        permanently-stationed personnel to superintend it.
    :cvar EXISTENCE_DOUBTFUL: A feature that has been reported but has
        not been definitely determined to exist.
    :cvar ON_REQUEST: When you ask for it.
    :cvar DROP_AWAY: To become lower in level.
    :cvar RISING: To become higher in level.
    :cvar INCREASING: Becoming larger in magnitude.
    :cvar DECREASING: Becoming smaller in magnitude.
    :cvar STRONG: Not easily broken or destroyed.
    :cvar GOOD: In a satisfactory condition to use.
    :cvar MODERATELY: Fairly but not very.
    :cvar POOR: Not as good as it could be or should.
    :cvar BUOYED: Marked by buoys.
    :cvar FULLY_OPERATIONAL: Entire observation platform is operating in
        accordance with, or exceeding, manufacturer specifications.
    :cvar PARTIALLY_OPERATIONAL: At least one instrument that is part of
        an observation platform is not operating to manufacturer
        specification.
    :cvar DRIFTING: Floating platform at the mercy of environmental
        elements, whether intentional or not.
    :cvar BROKEN: Fractured or in pieces.
    :cvar OFFLINE: Observation platform is intentionally not reporting
        an environmental observation.
    :cvar DISCONTINUED: Observation station, suite of instruments, or an
        individual instrument, for a particular location, has been
        removed and is no longer at the particular location.
    :cvar MANUAL_OBSERVATION: Observations made by a human observer.
    :cvar UNKNOWN_STATUS: Status of an observation platform, suite of
        instruments, or individual instrument is not known or
        unspecified.
    :cvar CONFIRMED: Made certain as to truth, accuracy, validity,
        availability, etc.
    :cvar CANDIDATE: Item selected for an action.
    :cvar UNDER_MODIFICATION: Item that is in the process of being
        modified.
    :cvar EXPERIMENTAL:
    :cvar UNDER_REMOVAL_DELETION: Item in the process of being removed
        or deleted.
    :cvar REMOVED_DELETED: Item that has been removed or deleted.
    :cvar CANDIDATE_FOR_MODIFICATION: Item selected for modification.
    """

    PERMANENT = "Permanent"
    OCCASIONAL = "Occasional"
    RECOMMENDED = "Recommended"
    NOT_IN_USE = "Not in Use"
    PERIODIC_INTERMITTENT = "Periodic/Intermittent"
    RESERVED = "Reserved"
    TEMPORARY = "Temporary"
    PRIVATE = "Private"
    MANDATORY = "Mandatory"
    EXTINGUISHED = "Extinguished"
    ILLUMINATED = "Illuminated"
    HISTORIC = "Historic"
    PUBLIC = "Public"
    SYNCHRONIZED = "Synchronized"
    WATCHED = "Watched"
    UNWATCHED = "Unwatched"
    EXISTENCE_DOUBTFUL = "Existence Doubtful"
    ON_REQUEST = "On Request"
    DROP_AWAY = "Drop Away"
    RISING = "Rising"
    INCREASING = "Increasing"
    DECREASING = "Decreasing"
    STRONG = "Strong"
    GOOD = "Good"
    MODERATELY = "Moderately"
    POOR = "Poor"
    BUOYED = "Buoyed"
    FULLY_OPERATIONAL = "Fully Operational"
    PARTIALLY_OPERATIONAL = "Partially Operational"
    DRIFTING = "Drifting"
    BROKEN = "Broken"
    OFFLINE = "Offline"
    DISCONTINUED = "Discontinued"
    MANUAL_OBSERVATION = "Manual Observation"
    UNKNOWN_STATUS = "Unknown Status"
    CONFIRMED = "Confirmed"
    CANDIDATE = "Candidate"
    UNDER_MODIFICATION = "Under Modification"
    EXPERIMENTAL = "Experimental"
    UNDER_REMOVAL_DELETION = "Under Removal / Deletion"
    REMOVED_DELETED = "Removed / Deleted"
    CANDIDATE_FOR_MODIFICATION = "Candidate for Modification"


class TechniqueOfVerticalMeasurementType(Enum):
    """
    :cvar FOUND_BY_ECHO_SOUNDER: The depth was determined by using an
        instrument that determines depth of water by measuring the time
        interval between emission of a sonic or ultrasonic signal and
        return of its echo from the bottom.
    :cvar FOUND_BY_SIDE_SCAN_SONAR: The depth was computed from a record
        produced by active sonar in which fixed acoustic beams are
        directed into the water perpendicularly to the direction of
        travel to scan the seabed and generate a record of the seabed
        configuration.
    :cvar FOUND_BY_MULTI_BEAM: The depth was determined by using a wide
        swath echo sounder that uses multiple beams to measure depths
        directly below and transverse to the ship's track.
    :cvar FOUND_BY_DIVER: The depth was determined by a person skilled
        in the practice of diving.
    :cvar FOUND_BY_LEAD_LINE: The depth was determined by using a line,
        graduated with attached marks and fastened to a sounding lead.
    :cvar SWEPT_BY_WIRE_DRAG: The given area was determined to be free
        from navigational dangers to a certain depth by towing a buoyed
        wire at the desired depth by two launches, or a least depth was
        identified using the same technique.
    :cvar FOUND_BY_LASER: The depth was determined by using an
        instrument that measures distance by emitting timed pulses of
        laser light and measuring the time between emission and
        reception of the reflected pulses.
    :cvar SWEPT_BY_VERTICAL_ACOUSTIC_SYSTEM: The given area has been
        swept using a system comprised of multiple echo sounder
        transducers attached to booms deployed from the survey vessel.
    :cvar FOUND_BY_ELECTROMAGNETIC_SENSOR: The depth was determined by
        using an instrument that compares electromagnetic signals.
    :cvar PHOTOGRAMMETRY: The science or art of obtaining reliable
        measurements from photographs.
    :cvar SATELLITE_IMAGERY: The depth was determined by using
        instruments placed aboard an artificial satellite.
    :cvar FOUND_BY_LEVELLING: The depth was determined by using
        levelling techniques to find the elevation of the point relative
        to a datum.
    :cvar SWEPT_BY_SIDE_SCAN_SONAR: The given area was determined to be
        free from navigational dangers to a certain depth by towing a
        side scan sonar.
    :cvar COMPUTER_GENERATED: The sounding was determined from a bottom
        model constructed using a computer.
    :cvar FOUND_BY_LIDAR: The depth was measured by using an instrument
        that measures distance by emitting timed pulses of laser light
        and measuring the time between emission and reception of the
        reflected pulses.
    :cvar SYNTHETIC_APERTURE_RADAR: A radar with a synthetic aperture
        antenna which is composed of a large number of elementary
        transducing elements. The signals are electronically combined
        into a resulting signal equivalent to that of a single antenna
        of a given aperture in a given direction.
    :cvar HYPERSPECTRAL_IMAGERY: Term used to describe the imagery
        derived from subdividing the electromagnetic spectrum into very
        narrow bandwidths. These narrow bandwidths may be combined with
        or subtracted from each other in various ways to form images
        useful in precise terrain or target analysis.
    """

    FOUND_BY_ECHO_SOUNDER = "Found by Echo Sounder"
    FOUND_BY_SIDE_SCAN_SONAR = "Found by Side Scan Sonar"
    FOUND_BY_MULTI_BEAM = "Found by Multi Beam"
    FOUND_BY_DIVER = "Found by Diver"
    FOUND_BY_LEAD_LINE = "Found by Lead Line"
    SWEPT_BY_WIRE_DRAG = "Swept by Wire-Drag"
    FOUND_BY_LASER = "Found by Laser"
    SWEPT_BY_VERTICAL_ACOUSTIC_SYSTEM = "Swept by Vertical Acoustic System"
    FOUND_BY_ELECTROMAGNETIC_SENSOR = "Found by Electromagnetic Sensor"
    PHOTOGRAMMETRY = "Photogrammetry"
    SATELLITE_IMAGERY = "Satellite Imagery"
    FOUND_BY_LEVELLING = "Found by Levelling"
    SWEPT_BY_SIDE_SCAN_SONAR = "Swept by Side Scan Sonar"
    COMPUTER_GENERATED = "Computer Generated"
    FOUND_BY_LIDAR = "Found by LIDAR"
    SYNTHETIC_APERTURE_RADAR = "Synthetic Aperture Radar"
    HYPERSPECTRAL_IMAGERY = "Hyperspectral Imagery"


@dataclass
class TextualDescriptionType:
    """
    Encodes the file name of a single external text file that contains the text in
    a defined language, which provides additional textual information that cannot
    be provided using other allowable attributes for the feature.

    :ivar file_reference: The file name of an externally referenced text
        file.
    :ivar language: The method of human communication, either spoken or
        written, consisting of the use of words in a structured and
        conventional way.
    """

    class Meta:
        name = "textualDescriptionType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    file_reference: Optional[str] = field(
        default=None,
        metadata={
            "name": "fileReference",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    language: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


class TopmarkDaymarkShapeType(Enum):
    """
    :cvar CONE_POINT_UP: Is where the vertex points up. A cone is a
        solid figure generated by straight lines drawn from a fixed
        point (the vertex) to a circle in a plane not containing the
        vertex. Cones are commonly used as International Association of
        Marine Aids to Navigation and Lighthouse Authorities - IALA
        topmarks, lateral.
    :cvar CONE_POINT_DOWN: Is where the vertex points down. A cone is a
        solid figure generated by straight lines drawn from a fixed
        point (the vertex) to a circle in a plane not containing the
        vertex. Cones are commonly used as International Association of
        Marine Aids to Navigation and Lighthouse Authorities - IALA
        topmarks, lateral.
    :cvar SPHERE: A curved surface all points of which are equidistant
        from a fixed point within, called the centre.
    :cvar VALUE_2_SPHERES: Two spheres, one above the other. Two black
        spheres are commonly used as an International Association of
        Marine Aids to Navigation and Lighthouse Authorities - IALA
        topmark (isolated danger).
    :cvar CYLINDER: A solid geometrical figure generated by straight
        lines fixed in direction and describing with one of point a
        closed curve, especially a circle (in which case the figure is
        circular cylinder, it's ends being parallel circles). Cylinders
        are commonly used as International Association of Marine Aids to
        Navigation and Lighthouse Authorities - IALA topmarks lateral.
    :cvar BOARD: Usually of rectangular shape, made from timber or metal
        and used to provide a contrast with the natural background of a
        daymark. The actual daymark is often painted on to this board.
    :cvar X_SHAPED: Having a shape or a cross-section like the capital
        letter X. An x-shape as an International Association of Marine
        Aids to Navigation and Lighthouse Authorities - IALA topmark
        should be 3 dimensional in shape. It is made of at least three
        crossed bars.
    :cvar UPRIGHT_CROSS: A cross with one vertical member and one
        horizontal member; that is, similar in shape to the character
        '+'.
    :cvar CUBE_POINT_UP: A cube standing on one of its vertexes. A cube
        is a solid contained by six equal squares, a regular hexahedron.
    :cvar VALUE_2_CONES_POINT_TO_POINT: 2 cones, one above the other,
        with their vertices together in the centre.
    :cvar VALUE_2_CONES_BASE_TO_BASE: 2 cones, one above the other, with
        their bases together in the centre and their vertices pointing
        up and down.
    :cvar RHOMBUS: A plane figure having four equal sides and equal
        opposite angles (two acute and two obtuse); an oblique
        equilateral parallelogram.
    :cvar VALUE_2_CONES_POINTS_UPWARD: 2 cones, one above the other,
        with their vertices pointing up.
    :cvar VALUE_2_CONES_POINTS_DOWNWARD: 2 cones, one above the other,
        with their vertices pointing down.
    :cvar BESOM_POINT_UP: Besom: A bundle of rods or twigs. Perch: A
        staff placed on top of a buoy, rock or shoal as a mark for
        navigation. A besom, point up is where the thicker (untied) end
        of the besom is at the bottom.
    :cvar BESOM_POINT_DOWN: Besom: A bundle of rods or twigs. Perch: A
        staff placed on top of a buoy, rock or shoal as a mark for
        navigation. A besom, point down is where the thinner (tied) end
        of the besom is at the bottom.
    :cvar FLAG: A flag mounted on a short pole.
    :cvar SPHERE_OVER_A_RHOMBUS: A sphere located above a rhombus.
    :cvar SQUARE: A plane figure with four right angles and four equal
        straight sides.
    :cvar RECTANGLE_HORIZONTAL: Where the two longer opposite sides are
        standing horizontally. A rectangle is a plane figure with four
        right angles and four straight sides, opposite sides being
        parallel and equal in length.
    :cvar RECTANGLE_VERTICAL: Where the two longer opposite sides are
        standing vertically. A rectangle is a plane figure with four
        right angles and four straight sides, opposite sides being
        parallel and equal in length.
    :cvar TRAPEZIUM_UP: A quadrilateral having one pair of opposite
        sides parallel, and which stands on its longer parallel side.
    :cvar TRAPEZIUM_DOWN: A quadrilateral having one pair of opposite
        sides parallel, and which stands on its shorter parallel side.
    :cvar TRIANGLE_POINT_UP: A figure having three angles and three
        sides, and which has a vertex at the top.
    :cvar TRIANGLE_POINT_DOWN: A figure having three angles and three
        sides, and which has a side at the top.
    :cvar CIRCLE: A perfectly round plane figure whose circumference is
        everywhere equidistant from its centre.
    :cvar TWO_UPRIGHT_CROSSES_ONE_OVER_THE_OTHER: Two upright crosses,
        generally vertically disposed one above the other.
    :cvar T_SHAPE: Having a shape like the capital letter T.
    :cvar TRIANGLE_POINTING_UP_OVER_A_CIRCLE: A triangle, vertex
        uppermost, located above a circle.
    :cvar UPRIGHT_CROSS_OVER_A_CIRCLE: An upright cross located above a
        circle.
    :cvar RHOMBUS_OVER_A_CIRCLE: A rhombus located above a circle.
    :cvar CIRCLE_OVER_A_TRIANGLE_POINTING_UP: A circle located over a
        triangle, vertex uppermost.
    :cvar OTHER_SHAPE_SEE_SHAPE_INFORMATION: An uncommon and/or non-
        standardized shape as textually described using an associated
        attribute.
    :cvar TUBULAR: Having the form of or consisting of a tube.
    """

    CONE_POINT_UP = "Cone (Point Up)"
    CONE_POINT_DOWN = "Cone (Point Down)"
    SPHERE = "Sphere"
    VALUE_2_SPHERES = "2 Spheres"
    CYLINDER = "Cylinder"
    BOARD = "Board"
    X_SHAPED = "X-Shaped"
    UPRIGHT_CROSS = "Upright Cross"
    CUBE_POINT_UP = "Cube (Point Up)"
    VALUE_2_CONES_POINT_TO_POINT = "2 Cones (Point to Point)"
    VALUE_2_CONES_BASE_TO_BASE = "2 Cones (Base to Base)"
    RHOMBUS = "Rhombus"
    VALUE_2_CONES_POINTS_UPWARD = "2 Cones (Points Upward)"
    VALUE_2_CONES_POINTS_DOWNWARD = "2 Cones (Points Downward)"
    BESOM_POINT_UP = "Besom (Point Up)"
    BESOM_POINT_DOWN = "Besom (Point Down)"
    FLAG = "Flag"
    SPHERE_OVER_A_RHOMBUS = "Sphere Over a Rhombus"
    SQUARE = "Square"
    RECTANGLE_HORIZONTAL = "Rectangle (Horizontal)"
    RECTANGLE_VERTICAL = "Rectangle (Vertical)"
    TRAPEZIUM_UP = "Trapezium (Up)"
    TRAPEZIUM_DOWN = "Trapezium (Down)"
    TRIANGLE_POINT_UP = "Triangle (Point Up)"
    TRIANGLE_POINT_DOWN = "Triangle (Point Down)"
    CIRCLE = "Circle"
    TWO_UPRIGHT_CROSSES_ONE_OVER_THE_OTHER = (
        "Two Upright Crosses (One Over the Other)"
    )
    T_SHAPE = "T-Shape"
    TRIANGLE_POINTING_UP_OVER_A_CIRCLE = "Triangle Pointing Up Over a Circle"
    UPRIGHT_CROSS_OVER_A_CIRCLE = "Upright Cross Over a Circle"
    RHOMBUS_OVER_A_CIRCLE = "Rhombus Over a Circle"
    CIRCLE_OVER_A_TRIANGLE_POINTING_UP = "Circle Over a Triangle Pointing Up"
    OTHER_SHAPE_SEE_SHAPE_INFORMATION = "Other Shape (See Shape Information)"
    TUBULAR = "Tubular"


class TrafficFlowType(Enum):
    """
    :cvar INBOUND: Traffic flow in a general direction toward a port or
        similar destination.
    :cvar OUTBOUND: Traffic flow in a general direction away from a port
        or similar point of origin.
    :cvar ONE_WAY: Traffic flow in one general direction only.
    :cvar TWO_WAY: Traffic flow in two generally opposite directions.
    """

    INBOUND = "Inbound"
    OUTBOUND = "Outbound"
    ONE_WAY = "One-Way"
    TWO_WAY = "Two-Way"


class VerticalDatumType(Enum):
    """
    :cvar MEAN_LOW_WATER_SPRINGS: The average height of the low waters
        of spring tides. This level is used as a tidal datum in some
        areas. Also called spring low water.
    :cvar MEAN_LOWER_LOW_WATER_SPRINGS: The average height of lower low
        water springs at a place.
    :cvar MEAN_SEA_LEVEL: The average height of the surface of the sea
        at a tide station for all stages of the tide over a 19-year
        period, usually determined from hourly height readings measured
        from a fixed predetermined reference level.
    :cvar LOWEST_LOW_WATER: An arbitrary level conforming to the lowest
        tide observed at a place, or some what lower.
    :cvar MEAN_LOW_WATER: The average height of all low waters at a
        place over a 19-year period.
    :cvar LOWEST_LOW_WATER_SPRINGS: An arbitrary level conforming to the
        lowest water level observed at a place at spring tides during a
        period of time shorter than 19 years.
    :cvar APPROXIMATE_MEAN_LOW_WATER_SPRINGS: An arbitrary level,
        usually within 0.3m from that of Mean Low Water Springs (MLWS).
    :cvar INDIAN_SPRING_LOW_WATER: An arbitrary tidal datum
        approximating the level of the mean of the lower low water at
        spring tides. It was first used in waters surrounding India.
    :cvar LOW_WATER_SPRINGS: An arbitrary level, approximating that of
        mean low water springs (MLWS).
    :cvar APPROXIMATE_LOWEST_ASTRONOMICAL_TIDE: An arbitrary level,
        usually within 0.3m from that of Lowest Astronomical Tide (LAT).
    :cvar NEARLY_LOWEST_LOW_WATER: An arbitrary level approximating the
        lowest water level observed at a place, usually equivalent to
        the Indian Spring Low Water (ISLW).
    :cvar MEAN_LOWER_LOW_WATER: The average height of the lower low
        waters at a place over a 19-year period.
    :cvar LOW_WATER: The lowest level reached at a place by the water
        surface in one oscillation. Also called low tide.
    :cvar APPROXIMATE_MEAN_LOW_WATER: An arbitrary level, usually within
        0.3m from that of Mean Low Water (MLW).
    :cvar APPROXIMATE_MEAN_LOWER_LOW_WATER: An arbitrary level, usually
        within 0.3m from that of Mean Lower Low Water (MLLW).
    :cvar MEAN_HIGH_WATER: The average height of all high waters at a
        place over a 19-year period.
    :cvar MEAN_HIGH_WATER_SPRINGS: The average height of the high waters
        of spring tides. Also called spring high water.
    :cvar HIGH_WATER: The highest level reached at a place by the water
        surface in one oscillation.
    :cvar APPROXIMATE_MEAN_SEA_LEVEL: An arbitrary level, usually within
        0.3m from that of Mean Sea Level (MSL).
    :cvar HIGH_WATER_SPRINGS: An arbitrary level, approximating that of
        mean high water springs (MHWS).
    :cvar MEAN_HIGHER_HIGH_WATER: The average height of higher high
        waters at a place over a 19-year period.
    :cvar EQUINOCTIAL_SPRING_LOW_WATER: The level of low water springs
        near the time of an equinox.
    :cvar LOWEST_ASTRONOMICAL_TIDE: The lowest tide level which can be
        predicted to occur under average meteorological conditions and
        under any combination of astronomical conditions.
    :cvar LOCAL_DATUM: An arbitrary datum defined by a local harbour
        authority, from which levels and tidal heights are measured by
        this authority.
    :cvar INTERNATIONAL_GREAT_LAKES_DATUM_1985: A vertical reference
        system with its zero based on the mean water level at
        Rimouski/Pointe-au-Pere, Quebec, over the period 1970 to 1988.
    :cvar MEAN_WATER_LEVEL: The average of all hourly water levels over
        the available period of record.
    :cvar LOWER_LOW_WATER_LARGE_TIDE: The average of the lowest low
        waters, one from each of 19 years of observations.
    :cvar HIGHER_HIGH_WATER_LARGE_TIDE: The average of the highest high
        waters, one from each of 19 years of observations.
    :cvar NEARLY_HIGHEST_HIGH_WATER: An arbitrary level approximating
        the highest water level observed at a place, usually equivalent
        to the high water springs.
    :cvar HIGHEST_ASTRONOMICAL_TIDE: The highest tidal level which can
        be predicted to occur under average meteorological conditions
        and under any combination of astronomical conditions.
    :cvar LOCAL_LOW_WATER_REFERENCE_LEVEL: Low water reference level of
        the local area.
    :cvar LOCAL_HIGH_WATER_REFERENCE_LEVEL: High water reference level
        of the local area.
    :cvar LOCAL_MEAN_WATER_REFERENCE_LEVEL: Mean water reference level
        of the local area.
    :cvar EQUIVALENT_HEIGHT_OF_WATER_GERMAN_GL_W: A low water level
        which is the result of a defined low water discharge - called
        "equivalent discharge".
    :cvar HIGHEST_SHIPPING_HEIGHT_OF_WATER_GERMAN_HSW: Upper limit of
        water levels where navigation is allowed.
    :cvar REFERENCE_LOW_WATER_LEVEL_ACCORDING_TO_DANUBE_COMMISSION: The
        water level at a discharge, which is exceeded 94 % of the year
        within a period of 30 years.
    :cvar
        HIGHEST_SHIPPING_HEIGHT_OF_WATER_ACCORDING_TO_DANUBE_COMMISSION:
        The water level at a discharge, which is exceeded 1% of the year
        within a period of 30 years.
    :cvar DUTCH_RIVER_LOW_WATER_REFERENCE_LEVEL_OLR: The water level at
        a discharge, which is exceeded 95% of the year within a period
        of 20 years.
    :cvar RUSSIAN_PROJECT_WATER_LEVEL: Conditional low water level with
        established probability.
    :cvar RUSSIAN_NORMAL_BACKWATER_LEVEL: Highest water level derived
        from the upper backwater stream in watercourse or reservoir
        under the normal operational conditions.
    :cvar OHIO_RIVER_DATUM: The Ohio River datum.
    :cvar DUTCH_HIGH_WATER_REFERENCE_LEVEL: Dutch High Water Reference
        Level.
    :cvar BALTIC_SEA_CHART_DATUM_2000: The datum refers to each Baltic
        country's realization of the European Vertical Reference System
        (EVRS) with land-uplift epoch 2000, which is connected to the
        Normaal Amsterdams Peil (NAP).
    :cvar DUTCH_ESTUARY_LOW_WATER_REFERENCE_LEVEL_OLW: Dutch Estuary Low
        Water Reference Level (OLW)
    :cvar INTERNATIONAL_GREAT_LAKES_DATUM_2020: -
    :cvar SEA_FLOOR: -
    :cvar SEA_SURFACE: -
    :cvar HYDROGRAPHIC_ZERO: -
    """

    MEAN_LOW_WATER_SPRINGS = "Mean Low Water Springs"
    MEAN_LOWER_LOW_WATER_SPRINGS = "Mean Lower Low Water Springs"
    MEAN_SEA_LEVEL = "Mean Sea Level"
    LOWEST_LOW_WATER = "Lowest Low Water"
    MEAN_LOW_WATER = "Mean Low Water"
    LOWEST_LOW_WATER_SPRINGS = "Lowest Low Water Springs"
    APPROXIMATE_MEAN_LOW_WATER_SPRINGS = "Approximate Mean Low Water Springs"
    INDIAN_SPRING_LOW_WATER = "Indian Spring Low Water"
    LOW_WATER_SPRINGS = "Low Water Springs"
    APPROXIMATE_LOWEST_ASTRONOMICAL_TIDE = (
        "Approximate Lowest Astronomical Tide"
    )
    NEARLY_LOWEST_LOW_WATER = "Nearly Lowest Low Water"
    MEAN_LOWER_LOW_WATER = "Mean Lower Low Water"
    LOW_WATER = "Low Water"
    APPROXIMATE_MEAN_LOW_WATER = "Approximate Mean Low Water"
    APPROXIMATE_MEAN_LOWER_LOW_WATER = "Approximate Mean Lower Low Water"
    MEAN_HIGH_WATER = "Mean High Water"
    MEAN_HIGH_WATER_SPRINGS = "Mean High Water Springs"
    HIGH_WATER = "High Water"
    APPROXIMATE_MEAN_SEA_LEVEL = "Approximate Mean Sea Level"
    HIGH_WATER_SPRINGS = "High Water Springs"
    MEAN_HIGHER_HIGH_WATER = "Mean Higher High Water"
    EQUINOCTIAL_SPRING_LOW_WATER = "Equinoctial Spring Low Water"
    LOWEST_ASTRONOMICAL_TIDE = "Lowest Astronomical Tide"
    LOCAL_DATUM = "Local Datum"
    INTERNATIONAL_GREAT_LAKES_DATUM_1985 = (
        "International Great Lakes Datum 1985"
    )
    MEAN_WATER_LEVEL = "Mean Water Level"
    LOWER_LOW_WATER_LARGE_TIDE = "Lower Low Water Large Tide"
    HIGHER_HIGH_WATER_LARGE_TIDE = "Higher High Water Large Tide"
    NEARLY_HIGHEST_HIGH_WATER = "Nearly Highest High Water"
    HIGHEST_ASTRONOMICAL_TIDE = "Highest Astronomical Tide"
    LOCAL_LOW_WATER_REFERENCE_LEVEL = "Local Low Water Reference Level"
    LOCAL_HIGH_WATER_REFERENCE_LEVEL = "Local High Water Reference Level"
    LOCAL_MEAN_WATER_REFERENCE_LEVEL = "Local Mean Water Reference Level"
    EQUIVALENT_HEIGHT_OF_WATER_GERMAN_GL_W = (
        "Equivalent Height of Water (German GlW)"
    )
    HIGHEST_SHIPPING_HEIGHT_OF_WATER_GERMAN_HSW = (
        "Highest Shipping Height of Water (German HSW)"
    )
    REFERENCE_LOW_WATER_LEVEL_ACCORDING_TO_DANUBE_COMMISSION = (
        "Reference Low Water Level According to Danube Commission"
    )
    HIGHEST_SHIPPING_HEIGHT_OF_WATER_ACCORDING_TO_DANUBE_COMMISSION = (
        "Highest Shipping Height of Water According to Danube Commission"
    )
    DUTCH_RIVER_LOW_WATER_REFERENCE_LEVEL_OLR = (
        "Dutch River Low Water Reference Level (OLR)"
    )
    RUSSIAN_PROJECT_WATER_LEVEL = "Russian Project Water Level"
    RUSSIAN_NORMAL_BACKWATER_LEVEL = "Russian Normal Backwater Level"
    OHIO_RIVER_DATUM = "Ohio River Datum"
    DUTCH_HIGH_WATER_REFERENCE_LEVEL = "Dutch High Water Reference Level"
    BALTIC_SEA_CHART_DATUM_2000 = "Baltic Sea Chart Datum 2000"
    DUTCH_ESTUARY_LOW_WATER_REFERENCE_LEVEL_OLW = (
        "Dutch Estuary Low Water Reference Level (OLW)"
    )
    INTERNATIONAL_GREAT_LAKES_DATUM_2020 = (
        "International Great Lakes Datum 2020"
    )
    SEA_FLOOR = "Sea Floor"
    SEA_SURFACE = "Sea Surface"
    HYDROGRAPHIC_ZERO = "Hydrographic Zero"


@dataclass
class VerticalUncertaintyType:
    """
    The best estimate of the vertical accuracy of depths, heights, vertical
    distances and vertical clearances.

    :ivar uncertainty_fixed: The best estimate of the fixed horizontal
        or vertical accuracy component for positions, depths, heights,
        vertical distances and vertical clearances.
    :ivar uncertainty_variable_factor: The factor to be applied to the
        variable component of an uncertainty equation so as to provide
        the best estimate of the variable horizontal or vertical
        accuracy component for positions, depths, heights, vertical
        distances and vertical clearances.
    """

    class Meta:
        name = "verticalUncertaintyType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    uncertainty_fixed: Optional[float] = field(
        default=None,
        metadata={
            "name": "uncertaintyFixed",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    uncertainty_variable_factor: Optional[float] = field(
        default=None,
        metadata={
            "name": "uncertaintyVariableFactor",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


class VirtualAisaidToNavigationTypeType(Enum):
    """
    :cvar NORTH_CARDINAL: Indicates that it should be passed to the
        north side of the aid.
    :cvar EAST_CARDINAL: Indicates that it should be passed to the east
        side of the aid.
    :cvar SOUTH_CARDINAL: Indicates that it should be passed to the
        south side of the aid.
    :cvar WEST_CARDINAL: Indicates that it should be passed to the west
        side of the aid.
    :cvar PORT_LATERAL: Indicates the port boundary of a navigational
        channel or suggested route when proceeding in the conventional
        direction of buoyage.
    :cvar STARBOARD_LATERAL: Indicates the starboard boundary of a
        navigational channel or suggested route when proceeding in the
        conventional direction of buoyage.
    :cvar PREFERRED_CHANNEL_TO_PORT: At a point where a channel divides,
        when proceeding in the conventional direction of buoyage, the
        preferred channel (or primary route) is indicated by a modified
        port-hand lateral mark.
    :cvar PREFERRED_CHANNEL_TO_STARBOARD: At a point where a channel
        divides, when proceeding in the conventional direction of
        buoyage, the preferred channel (or primary route) is indicated
        by a modified starboard-hand lateral mark.
    :cvar ISOLATED_DANGER: A mark used alone to indicate a dangerous
        reef or shoal. The mark may be passed on either hand.
    :cvar SAFE_WATER: Indicates that there is navigable water around the
        mark.
    :cvar SPECIAL_PURPOSE: A special purpose aid is primarily used to
        indicate an area or feature, the nature of which is apparent
        from reference to a chart, Sailing Directions or Notice to
        Mariners
    :cvar NEW_DANGER_MARKING: A mark used to indicate the existence of a
        recently identified new danger, such as a wreck.
    """

    NORTH_CARDINAL = "North Cardinal"
    EAST_CARDINAL = "East Cardinal"
    SOUTH_CARDINAL = "South Cardinal"
    WEST_CARDINAL = "West Cardinal"
    PORT_LATERAL = "Port Lateral"
    STARBOARD_LATERAL = "Starboard Lateral"
    PREFERRED_CHANNEL_TO_PORT = "Preferred Channel to Port"
    PREFERRED_CHANNEL_TO_STARBOARD = "Preferred Channel to Starboard"
    ISOLATED_DANGER = "Isolated Danger"
    SAFE_WATER = "Safe Water"
    SPECIAL_PURPOSE = "Special Purpose"
    NEW_DANGER_MARKING = "New Danger Marking"


class VisualProminenceType(Enum):
    """
    :cvar VISUALLY_CONSPICUOUS: Term applied to a feature either natural
        or artificial which is distinctly and notably visible from
        seaward.
    :cvar NOT_VISUALLY_CONSPICUOUS: An object that may be visible from
        seaward, but cannot be used as a fixing mark and is not
        conspicuous.
    :cvar PROMINENT: Objects which are easily identifiable, but do not
        justify being classed as conspicuous.
    """

    VISUALLY_CONSPICUOUS = "Visually Conspicuous"
    NOT_VISUALLY_CONSPICUOUS = "Not Visually Conspicuous"
    PROMINENT = "Prominent"


class MdTopicCategoryCode(Enum):
    """Topic categories in S-100 Edition 1.0.0 and gmxCodelists.xml from OGC ISO 19139 XML schemas - see MD_TopicCategoryCode.
    Alternatives to this enumeration: (1) Add the ISO 19139 schemas to this profile and use the codelist MD_TopicCategoryCode instead.
    (2) Ise numeric codes for literals instead of labels, e.g., "1" instead of "farming".

    :cvar FARMING: rearing of animals and/or cultivation of plants.
        Examples: agriculture, irrigation, aquaculture, plantations,
        herding, pests and diseases affecting crops and livestock
    :cvar BIOTA: flora and/or fauna in natural environment. Examples:
        wildlife, vegetation, biological sciences, ecology, wilderness,
        sealife, wetlands, habitat
    :cvar BOUNDARIES: legal land descriptions. Examples: political and
        administrative boundaries
    :cvar CLIMATOLOGY_METEOROLOGY_ATMOSPHERE: processes and phenomena of
        the atmosphere. Examples: cloud cover, weather, climate,
        atmospheric conditions, climate change, precipitation
    :cvar ECONOMY: economic activities, conditions and employment.
        Examples: production, labour, revenue, commerce, industry,
        tourism and ecotourism, forestry, fisheries, commercial or
        subsistence hunting, exploration and exploitation of resources
        such as minerals, oil and gas
    :cvar ELEVATION: height above or below sea level. Examples:
        altitude, bathymetry, digital elevation models, slope, derived
        products
    :cvar ENVIRONMENT: environmental resources, protection and
        conservation. Examples: environmental pollution, waste storage
        and treatment, environmental impact assessment, monitoring
        environmental risk, nature reserves, landscape
    :cvar GEOSCIENTIFIC_INFORMATION: information pertaining to earth
        sciences. Examples: geophysical features and processes, geology,
        minerals, sciences dealing with the composition, structure and
        origin of the earth s rocks, risks of earthquakes, volcanic
        activity, landslides, gravity information, soils, permafrost,
        hydrogeology, erosion
    :cvar HEALTH: health, health services, human ecology, and safety.
        Examples: disease and illness, factors affecting health,
        hygiene, substance abuse, mental and physical health, health
        services
    :cvar IMAGERY_BASE_MAPS_EARTH_COVER: base maps. Examples: land
        cover, topographic maps, imagery, unclassified images,
        annotations
    :cvar INTELLIGENCE_MILITARY: military bases, structures, activities.
        Examples: barracks, training grounds, military transportation,
        information collection
    :cvar INLAND_WATERS: inland water features, drainage systems and
        their characteristics. Examples: rivers and glaciers, salt
        lakes, water utilization plans, dams, currents, floods, water
        quality, hydrographic charts
    :cvar LOCATION: positional information and services. Examples:
        addresses, geodetic networks, control points, postal zones and
        services, place names
    :cvar OCEANS: features and characteristics of salt water bodies
        (excluding inland waters). Examples: tides, tidal waves, coastal
        information, reefs
    :cvar PLANNING_CADASTRE: information used for appropriate actions
        for future use of the land. Examples: land use maps, zoning
        maps, cadastral surveys, land ownership
    :cvar SOCIETY: characteristics of society and cultures. Examples:
        settlements, anthropology, archaeology, education, traditional
        beliefs, manners and customs, demographic data, recreational
        areas and activities, social impact assessments, crime and
        justice, census information
    :cvar STRUCTURE: man-made construction. Examples: buildings,
        museums, churches, factories, housing, monuments, shops, towers
    :cvar TRANSPORTATION: means and aids for conveying persons and/or
        goods. Examples: roads, airports/airstrips, shipping routes,
        tunnels, nautical charts, vehicle or vessel location,
        aeronautical charts, railways
    :cvar UTILITIES_COMMUNICATION: energy, water and waste systems and
        communications infrastructure and services. Examples:
        hydroelectricity, geothermal, solar and nuclear sources of
        energy, water purification and distribution, sewage collection
        and disposal, electricity and gas distribution, data
        communication, telecommunication, radio, communication networks
    """

    FARMING = "farming"
    BIOTA = "biota"
    BOUNDARIES = "boundaries"
    CLIMATOLOGY_METEOROLOGY_ATMOSPHERE = "climatologyMeteorologyAtmosphere"
    ECONOMY = "economy"
    ELEVATION = "elevation"
    ENVIRONMENT = "environment"
    GEOSCIENTIFIC_INFORMATION = "geoscientificInformation"
    HEALTH = "health"
    IMAGERY_BASE_MAPS_EARTH_COVER = "imageryBaseMapsEarthCover"
    INTELLIGENCE_MILITARY = "intelligenceMilitary"
    INLAND_WATERS = "inlandWaters"
    LOCATION = "location"
    OCEANS = "oceans"
    PLANNING_CADASTRE = "planningCadastre"
    SOCIETY = "society"
    STRUCTURE = "structure"
    TRANSPORTATION = "transportation"
    UTILITIES_COMMUNICATION = "utilitiesCommunication"


class S100CircleByCenterPointTypeAngularDistance(Enum):
    VALUE_360_0 = Decimal("360.0")
    VALUE_360_0_1 = Decimal("-360.0")


@dataclass
class S100GmKnotType:
    """
    S-100 Knot is the GML 3.2.1 definition of Knot with the erroneous "weight"
    element removed.
    """

    class Meta:
        name = "S100_GM_KnotType"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    value: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )
    multiplicity: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )


class S100GmKnotTypeType(Enum):
    """This enumeration type specifies values for the knots' type (see ISO
    19107:2003, 6.4.25).

    The S-100 3.1 type extends it with "nonUniform" in keeping with the
    2017 draft of 19107

    :cvar UNIFORM: knots are equally spaced, all multiplicity 1
    :cvar QUASI_UNIFORM: the interior knots are uniform, but the first
        and last have multiplicity one larger than the degree of the
        spline
    :cvar PIECEWISE_BEZIER: the underlying spline is formally a Bézier
        spline, but knot multiplicity is always the degree of the spline
        except at the ends where the knot degree is (p+1). Such a spline
        is a pure Bézier spline between its distinct knots
    :cvar NON_UNIFORM: knots have varying spacing and multiplicity
    """

    UNIFORM = "uniform"
    QUASI_UNIFORM = "quasiUniform"
    PIECEWISE_BEZIER = "piecewiseBezier"
    NON_UNIFORM = "nonUniform"


@dataclass
class S100TruncatedDate1:
    """
    Built in date types from W3C XML schema, implementing S-100 truncated date.
    """

    class Meta:
        name = "S100_TruncatedDate"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    g_day: Optional[XmlPeriod] = field(
        default=None,
        metadata={
            "name": "gDay",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    g_month: Optional[XmlPeriod] = field(
        default=None,
        metadata={
            "name": "gMonth",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    g_year: Optional[XmlPeriod] = field(
        default=None,
        metadata={
            "name": "gYear",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    g_month_day: Optional[XmlPeriod] = field(
        default=None,
        metadata={
            "name": "gMonthDay",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    g_year_month: Optional[XmlPeriod] = field(
        default=None,
        metadata={
            "name": "gYearMonth",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    date: Optional[XmlDate] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )


class ComplianceLevelValue(Enum):
    VALUE_1 = 1
    VALUE_2 = 2


class DatasetPurposeType(Enum):
    """
    New type introduced in S-100 Ed 5 to distinguish between a Base dataset and an
    Update.

    :cvar BASE: rearing of animals and/or cultivation of plants.
        Examples: agriculture, irrigation, aquaculture, plantations,
        herding, pests and diseases affecting crops and livestock
    :cvar UPDATE: flora and/or fauna in natural environment. Examples:
        wildlife, vegetation, biological sciences, ecology, wilderness,
        sealife, wetlands, habitat
    """

    BASE = "base"
    UPDATE = "update"


@dataclass
class AbstractCurveSegmentType:
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    num_derivatives_at_start: int = field(
        default=0,
        metadata={
            "name": "numDerivativesAtStart",
            "type": "Attribute",
        },
    )
    num_derivatives_at_end: int = field(
        default=0,
        metadata={
            "name": "numDerivativesAtEnd",
            "type": "Attribute",
        },
    )
    num_derivative_interior_attribute: int = field(
        default=0,
        metadata={
            "name": "numDerivativeInterior",
            "type": "Attribute",
        },
    )


@dataclass
class AbstractFeatureMemberType:
    """To create a collection of GML features, a property type shall be derived by
    extension from gml:AbstractFeatureMemberType.

    By default, this abstract property type does not imply any ownership
    of the features in the collection. The owns attribute of
    gml:OwnershipAttributeGroup may be used on a property element
    instance to assert ownership of a feature in the collection. A
    collection shall not own a feature already owned by another object.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    owns: bool = field(
        default=False,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class AbstractGmltype:
    class Meta:
        name = "AbstractGMLType"
        target_namespace = "http://www.opengis.net/gml/3.2"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.opengis.net/gml/3.2",
            "required": True,
        },
    )


@dataclass
class AbstractMemberType:
    """To create a collection of GML Objects that are not all features, a property
    type shall be derived by extension from gml:AbstractMemberType.

    This abstract property type is intended to be used only in object
    types where software shall be able to identify that an instance of
    such an object type is to be interpreted as a collection of objects.
    By default, this abstract property type does not imply any ownership
    of the objects in the collection. The owns attribute of
    gml:OwnershipAttributeGroup may be used on a property element
    instance to assert ownership of an object in the collection. A
    collection shall not own an object already owned by another object.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    owns: bool = field(
        default=False,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class AbstractMetadataPropertyType:
    """To associate metadata described by any XML Schema with a GML object, a
    property element shall be defined whose content model is derived by extension
    from gml:AbstractMetadataPropertyType.

    The value of such a property shall be metadata. The content model of
    such a property type, i.e. the metadata application schema shall be
    specified by the GML Application Schema. By default, this abstract
    property type does not imply any ownership of the metadata. The owns
    attribute of gml:OwnershipAttributeGroup may be used on a metadata
    property element instance to assert ownership of the metadata. If
    metadata following the conceptual model of ISO 19115 is to be
    encoded in a GML document, the corresponding Implementation
    Specification specified in ISO/TS 19139 shall be used to encode the
    metadata information.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    owns: bool = field(
        default=False,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class AbstractObject:
    """This element has no type defined, and is therefore implicitly (according to
    the rules of W3C XML Schema) an XML Schema anyType.

    It is used as the head of an XML Schema substitution group which
    unifies complex content and certain simple content elements used for
    datatypes in GML, including the gml:AbstractGML substitution group.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AbstractRingType:
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AbstractScalarValue:
    """
    Gml:AbstractScalarValue is an abstract element which acts as the head of a
    substitution group which contains gml:Boolean, gml:Category, gml:Count and
    gml:Quantity, and (transitively) the elements in their substitution groups.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"

    any_element: Optional[object] = field(
        default=None,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
        },
    )


@dataclass
class AbstractSurfacePatchType:
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AbstractValue:
    """Gml:AbstractValue is an abstract element which acts as the head of a
    substitution group which contains gml:AbstractScalarValue,
    gml:AbstractScalarValueList, gml:CompositeValue and gml:ValueExtent, and
    (transitively) the elements in their substitution groups.

    These elements may be used in an application schema as variables, so
    that in an XML instance document any member of its substitution
    group may occur.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"

    any_element: Optional[object] = field(
        default=None,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
        },
    )


class AggregationType(Enum):
    SET = "set"
    BAG = "bag"
    SEQUENCE = "sequence"
    ARRAY = "array"
    RECORD = "record"
    TABLE = "table"


@dataclass
class CodeType:
    """Gml:CodeType is a generalized type to be used for a term, keyword or name.

    It adds a XML attribute codeSpace to a term, where the value of the
    codeSpace attribute (if present) shall indicate a dictionary,
    thesaurus, classification scheme, authority, or pattern for the
    term.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    code_space: Optional[str] = field(
        default=None,
        metadata={
            "name": "codeSpace",
            "type": "Attribute",
        },
    )


class CurveInterpolationType(Enum):
    """Gml:CurveInterpolationType is a list of codes that may be used to identify
    the interpolation mechanisms specified by an applicationschema.

    S-100 3.1 note: The list has been extended by adding the S-100 3.1
    interpolations, given that the new draft of ISO 19107 explicitly
    says "As a codelist, there is no intention of limiting the potential
    values ofCurveInterpolation."

    :cvar NONE:
    :cvar LINEAR:
    :cvar GEODESIC:
    :cvar CIRCULAR_ARC3_POINTS:
    :cvar LOXODROMIC: Note that the new draft of 19107 now includes
        "rhumb".
    :cvar ELLIPTICAL:
    :cvar CONIC:
    :cvar CIRCULAR_ARC_CENTER_POINT_WITH_RADIUS:
    :cvar POLYNOMIAL_SPLINE:
    :cvar BEZIER_SPLINE:
    :cvar B_SPLINE:
    :cvar CUBIC_SPLINE:
    :cvar RATIONAL_SPLINE:
    :cvar BLENDED_PARABOLIC:
    """

    NONE = "none"
    LINEAR = "linear"
    GEODESIC = "geodesic"
    CIRCULAR_ARC3_POINTS = "circularArc3Points"
    LOXODROMIC = "loxodromic"
    ELLIPTICAL = "elliptical"
    CONIC = "conic"
    CIRCULAR_ARC_CENTER_POINT_WITH_RADIUS = "circularArcCenterPointWithRadius"
    POLYNOMIAL_SPLINE = "polynomialSpline"
    BEZIER_SPLINE = "bezierSpline"
    B_SPLINE = "bSpline"
    CUBIC_SPLINE = "cubicSpline"
    RATIONAL_SPLINE = "rationalSpline"
    BLENDED_PARABOLIC = "blendedParabolic"


@dataclass
class DirectPositionListType:
    """PosList instances (and other instances with the content model specified by
    DirectPositionListType) hold the coordinates for a sequence of direct positions
    within the same coordinate reference system (CRS).

    if no srsName attribute is given, the CRS shall be specified as part
    of the larger context this geometry element is part of, typically a
    geometric object like a point, curve, etc. The optional attribute
    count specifies the number of direct positions in the list. If the
    attribute count is present then the attribute srsDimension shall be
    present, too. The number of entries in the list is equal to the
    product of the dimensionality of the coordinate reference system
    (i.e. it is a derived value of the coordinate reference system
    definition) and the number of direct positions.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    value: list[float] = field(
        default_factory=list,
        metadata={
            "tokens": True,
        },
    )
    srs_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "srsName",
            "type": "Attribute",
        },
    )
    srs_dimension: Optional[int] = field(
        default=None,
        metadata={
            "name": "srsDimension",
            "type": "Attribute",
        },
    )
    count: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class DirectPositionType:
    """Direct position instances hold the coordinates for a position within some
    coordinate reference system (CRS).

    Since direct positions, as data types, will often be included in
    larger objects (such as geometry elements) that have references to
    CRS, the srsName attribute will in general be missing, if this
    particular direct position is included in a larger element with such
    a reference to a CRS. In this case, the CRS is implicitly assumed to
    take on the value of the containing object's CRS. if no srsName
    attribute is given, the CRS shall be specified as part of the larger
    context this geometry element is part of, typically a geometric
    object like a point, curve, etc.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    value: list[float] = field(
        default_factory=list,
        metadata={
            "tokens": True,
        },
    )
    srs_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "srsName",
            "type": "Attribute",
        },
    )
    srs_dimension: Optional[int] = field(
        default=None,
        metadata={
            "name": "srsDimension",
            "type": "Attribute",
        },
    )


@dataclass
class InlinePropertyType:
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    any_element: Optional[object] = field(
        default=None,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
        },
    )
    owns: bool = field(
        default=False,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class MeasureType:
    """Gml:MeasureType supports recording an amount encoded as a value of XML
    Schema double, together with a units of measure indicated by an attribute uom,
    short for "units Of measure".

    The value of the uom attribute identifies a reference system for the
    amount, usually a ratio or interval scale.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    value: Optional[float] = field(
        default=None,
        metadata={
            "required": True,
        },
    )
    uom: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r"[^: /n/r/t]+",
        },
    )


class NilReasonEnumerationValue(Enum):
    INAPPLICABLE = "inapplicable"
    MISSING = "missing"
    TEMPLATE = "template"
    UNKNOWN = "unknown"
    WITHHELD = "withheld"


class SignType(Enum):
    """
    Gml:SignType is a convenience type with values "+" (plus) and "-" (minus).
    """

    HYPHEN_MINUS = "-"
    PLUS_SIGN = "+"


class SurfaceInterpolationType(Enum):
    """
    Gml:SurfaceInterpolationType is a list of codes that may be used to identify
    the interpolation mechanisms specified by an application schema.
    """

    NONE = "none"
    PLANAR = "planar"
    SPHERICAL = "spherical"
    ELLIPTICAL = "elliptical"
    CONIC = "conic"
    TIN = "tin"
    PARAMETRIC_CURVE = "parametricCurve"
    POLYNOMIAL_SPLINE = "polynomialSpline"
    RATIONAL_SPLINE = "rationalSpline"
    TRIANGULATED_SPLINE = "triangulatedSpline"


@dataclass
class AssociationName:
    class Meta:
        name = "associationName"
        namespace = "http://www.opengis.net/gml/3.2"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )


@dataclass
class DefaultCodeSpace:
    class Meta:
        name = "defaultCodeSpace"
        namespace = "http://www.opengis.net/gml/3.2"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )


@dataclass
class GmlProfileSchema:
    class Meta:
        name = "gmlProfileSchema"
        namespace = "http://www.opengis.net/gml/3.2"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )


@dataclass
class ReversePropertyName:
    """If the value of an object property is another object and that object
    contains also a property for the association between the two objects, then this
    name of the reverse property may be encoded in a gml:reversePropertyName
    element in an appinfo annotation of the property element to document the
    constraint between the two properties.

    The value of the element shall contain the qualified name of the
    property element.
    """

    class Meta:
        name = "reversePropertyName"
        namespace = "http://www.opengis.net/gml/3.2"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )


@dataclass
class TargetElement:
    class Meta:
        name = "targetElement"
        namespace = "http://www.opengis.net/gml/3.2"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )


class ActuateType(Enum):
    ON_LOAD = "onLoad"
    ON_REQUEST = "onRequest"
    OTHER = "other"
    NONE = "none"


class ShowType(Enum):
    NEW = "new"
    REPLACE = "replace"
    EMBED = "embed"
    OTHER = "other"
    NONE = "none"


class TypeType(Enum):
    SIMPLE = "simple"
    EXTENDED = "extended"
    TITLE = "title"
    RESOURCE = "resource"
    LOCATOR = "locator"
    ARC = "arc"


class LangValue(Enum):
    VALUE = ""


@dataclass
class CableDimensionsType:
    """
    The dimensions of a cable to give its length and diameter.

    :ivar cable_length: Total length of a cable.
    :ivar height_length_units: Units of measure of waterway distances.
        (IHO Registry)
    :ivar diameter: -
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    cable_length: Optional[float] = field(
        default=None,
        metadata={
            "name": "cableLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    height_length_units: Optional[HeightLengthUnitsType] = field(
        default=None,
        metadata={
            "name": "heightLengthUnits",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    diameter: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )


@dataclass
class ChangeDetailsType:
    """-

    :ivar aton_commissioning: .
    :ivar aton_removal: .
    :ivar aton_replacement: .
    :ivar fixed_aton_change: .
    :ivar floating_aton_change: .
    :ivar audible_signal_aton_change: .
    :ivar lighted_aton_change: .
    :ivar electronic_aton_change: .
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    aton_commissioning: Optional[AtonCommissioningType] = field(
        default=None,
        metadata={
            "name": "atonCommissioning",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    aton_removal: Optional[AtonRemovalType] = field(
        default=None,
        metadata={
            "name": "atonRemoval",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    aton_replacement: Optional[AtonReplacementType] = field(
        default=None,
        metadata={
            "name": "atonReplacement",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    fixed_aton_change: Optional[FixedAtonChangeType] = field(
        default=None,
        metadata={
            "name": "fixedAtonChange",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    floating_aton_change: Optional[FloatingAtonChangeType] = field(
        default=None,
        metadata={
            "name": "floatingAtonChange",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    audible_signal_aton_change: Optional[AudibleSignalAtonChangeType] = field(
        default=None,
        metadata={
            "name": "audibleSignalAtonChange",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    lighted_aton_change: Optional[LightedAtonChangeType] = field(
        default=None,
        metadata={
            "name": "lightedAtonChange",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    electronic_aton_change: Optional[ElectronicAtonChangeType] = field(
        default=None,
        metadata={
            "name": "electronicAtonChange",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class DirectionalCharacterType:
    """
    A directional light is a light illuminating a sector of very narrow angle and
    intended to mark a direction to follow.

    :ivar moire_effect: A short range (up to 2km) type of directional
        light. Sodium lighting gives a yellow background to a screen on
        which a vertical black line will be seen by an observer on the
        centre line.
    :ivar orientation: (1) The angular distance measured from true north
        to the major axis of the feature. (2) In ECDIS, the mode in
        which information on the ECDIS is being presented. Typical modes
        include: north-up - as shown on a nautical chart, north is at
        the top of the display; Ships head-up - based on the actual
        heading of the ship, (e.g. Ships gyrocompass); course-up display
        - based on the course or route being taken.
    """

    class Meta:
        name = "directionalCharacterType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    moire_effect: Optional[bool] = field(
        default=None,
        metadata={
            "name": "moireEffect",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    orientation: Optional[OrientationType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )


@dataclass
class FixedDateRangeType:
    """
    An active period of a single fixed event or occurrence, as the date range
    between discrete start and end dates.

    :ivar date_end: The latest date on which an object (for example a
        buoy) will be present.
    :ivar date_start: The earliest date on which an object (for example
        a buoy) will be present.
    """

    class Meta:
        name = "fixedDateRangeType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    date_end: Optional[S100TruncatedDate2] = field(
        default=None,
        metadata={
            "name": "dateEnd",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    date_start: Optional[S100TruncatedDate2] = field(
        default=None,
        metadata={
            "name": "dateStart",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class PeriodicDateRangeType:
    """
    The active period of a recurring event or occurrence.

    :ivar date_end: The latest date on which an object (for example a
        buoy) will be present.
    :ivar date_start: The earliest date on which an object (for example
        a buoy) will be present.
    """

    class Meta:
        name = "periodicDateRangeType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    date_end: Optional[S100TruncatedDate2] = field(
        default=None,
        metadata={
            "name": "dateEnd",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    date_start: Optional[S100TruncatedDate2] = field(
        default=None,
        metadata={
            "name": "dateStart",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )


@dataclass
class PositioningMethodType:
    """
    A description of the method used to obtain a position.(proposed by CCG)

    :ivar positioning_equipment: .
    :ivar nmeastring: NMEA string captured from the positioning
        device.(proposed by CCG)
    """

    class Meta:
        name = "positioningMethodType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    positioning_equipment: Optional[PositioningEquipmentType] = field(
        default=None,
        metadata={
            "name": "positioningEquipment",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    nmeastring: Optional[str] = field(
        default=None,
        metadata={
            "name": "NMEAString",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )


@dataclass
class SectorLimitType:
    """A sector is the part of a circle between two straight lines drawn from the
    centre to the circumference.

    The sector limit specifies the limits of the sector In a clockwise
    direction around the central feature (for example a light).

    :ivar sector_limit_one: A sector is the part of a circle between two
        straight lines drawn from the centre to the circumference.
        Sector limit one specifies the first limit of the sector. The
        order of sector limit one and sector limit two is clockwise
        around the central feature (for example a light).
    :ivar sector_limit_two: A sector is the part of a circle between two
        straight lines drawn from the centre to the circumference.
        Sector limit two specifies the second limit of the sector. The
        order of sector limit one and sector limit two is clockwise
        around the central feature (for example a light).
    """

    class Meta:
        name = "sectorLimitType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    sector_limit_one: Optional[SectorLimitOneType] = field(
        default=None,
        metadata={
            "name": "sectorLimitOne",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    sector_limit_two: Optional[SectorLimitTwoType] = field(
        default=None,
        metadata={
            "name": "sectorLimitTwo",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )


@dataclass
class SignalSequenceType:
    """
    The sequence of times occupied by intervals of light and eclipse for all light
    characteristics.

    :ivar signal_duration: The time occupied by a single instance of
        light/sound or eclipse/silence in a signal sequence.
    :ivar signal_status: The indication of an element of a signal
        sequence being a period of light/sound or eclipse/silence.
    """

    class Meta:
        name = "signalSequenceType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    signal_duration: Optional[float] = field(
        default=None,
        metadata={
            "name": "signalDuration",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    signal_status: Optional[SignalStatusType] = field(
        default=None,
        metadata={
            "name": "signalStatus",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )


@dataclass
class SinkerDimensionsType:
    """
    The dimensions of a sinker/anchor to give its three dimensional shape
    measurements.

    :ivar height_length_units: Units of measure of waterway distances.
        (IHO Registry)
    :ivar horizontal_length: A measurement of the longer of two linear
        axis.
    :ivar horizontal_width: A measurement of the shorter of two linear
        axis.
    :ivar vertical_length: The total vertical length of a feature.
    """

    class Meta:
        name = "sinkerDimensionsType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    height_length_units: Optional[HeightLengthUnitsType] = field(
        default=None,
        metadata={
            "name": "heightLengthUnits",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    horizontal_length: Optional[float] = field(
        default=None,
        metadata={
            "name": "horizontalLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    horizontal_width: Optional[float] = field(
        default=None,
        metadata={
            "name": "horizontalWidth",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_length: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class AbstractAttributeType(AbstractGmltype):
    """
    Abstract type for attributes.
    """

    class Meta:
        target_namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class AbstractInformationType(AbstractGmltype):
    """Abstract type for an S-100 information type.

    This is the base type from which domain application schemas derive
    definitions for their individual information types.
    """

    class Meta:
        target_namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class DataSetIdentificationType:
    """S-100 Data Set Identification.

    The fields correspond to S-100 10a-5.1.2.1 fields. Attributes
    encodingSpecification and encodingSpecificationEdition are actually
    redundant here because in an XML schema the encoding specification
    and encoding specification edition are usually implicit in the
    namespace URI.

    :ivar encoding_specification: Encoding specification that defines
        the encoding.
    :ivar encoding_specification_edition: Edition of the encoding
        specification
    :ivar product_identifier: Unique identifier of the data product as
        specified in the product specification
    :ivar product_edition: Edition of the product specification
    :ivar application_profile: Identifier that specifies a profile
        within the data product
    :ivar dataset_file_identifier: The file identifier of the dataset
    :ivar dataset_title: The title of the dataset
    :ivar dataset_reference_date: The reference date of the dataset
    :ivar dataset_language: The (primary) language used in this dataset
    :ivar dataset_abstract: The abstract of the dataset
    :ivar dataset_topic_category: A set of topic categories
    :ivar dataset_purpose: base or update
    :ivar update_number: Update Number, 0 for a Base dataset
    """

    class Meta:
        target_namespace = "http://www.iho.int/s100gml/5.0"

    encoding_specification: str = field(
        init=False,
        default="S-100 Part 10b",
        metadata={
            "name": "encodingSpecification",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )
    encoding_specification_edition: str = field(
        init=False,
        default="1.0",
        metadata={
            "name": "encodingSpecificationEdition",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )
    product_identifier: Optional[str] = field(
        default=None,
        metadata={
            "name": "productIdentifier",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )
    product_edition: Optional[str] = field(
        default=None,
        metadata={
            "name": "productEdition",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )
    application_profile: Optional[str] = field(
        default=None,
        metadata={
            "name": "applicationProfile",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )
    dataset_file_identifier: Optional[str] = field(
        default=None,
        metadata={
            "name": "datasetFileIdentifier",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )
    dataset_title: Optional[str] = field(
        default=None,
        metadata={
            "name": "datasetTitle",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )
    dataset_reference_date: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "datasetReferenceDate",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )
    dataset_language: str = field(
        default="eng",
        metadata={
            "name": "datasetLanguage",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
            "pattern": r"\w{3}",
        },
    )
    dataset_abstract: Optional[str] = field(
        default=None,
        metadata={
            "name": "datasetAbstract",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    dataset_topic_category: list[MdTopicCategoryCode] = field(
        default_factory=list,
        metadata={
            "name": "datasetTopicCategory",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "min_occurs": 1,
        },
    )
    dataset_purpose: Optional[DatasetPurposeType] = field(
        default=None,
        metadata={
            "name": "datasetPurpose",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )
    update_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "updateNumber",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )


@dataclass
class KnotPropertyType:
    """Gml:KnotPropertyType encapsulates a knot to use it in a geometric type.

    The S100 version is needed so as to use the updated definition of
    knots

    :ivar knot: A knot is a breakpoint on a piecewise spline curve.
        value is the value of the parameter at the knot of the spline
        (see ISO 19107:2003, 6.4.24.2). multiplicity is the multiplicity
        of this knot used in the definition of the spline (with the same
        weight). weight is the value of the averaging weight used for
        this knot of the spline.
    """

    class Meta:
        target_namespace = "http://www.iho.int/s100gml/5.0"

    knot: Optional[S100GmKnotType] = field(
        default=None,
        metadata={
            "name": "Knot",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )


@dataclass
class ComplianceLevel:
    """
    Level 1 = Level 2 =
    """

    class Meta:
        name = "complianceLevel"
        namespace = "http://www.iho.int/s100gml/5.0"

    value: Optional[ComplianceLevelValue] = field(default=None)


@dataclass
class AbstractCurveSegment(AbstractCurveSegmentType):
    """A curve segment defines a homogeneous segment of a curve.

    The attributes numDerivativesAtStart, numDerivativesAtEnd and
    numDerivativesInterior specify the type of continuity as specified
    in ISO 19107:2003, 6.4.9.3. The AbstractCurveSegment element is the
    abstract head of the substituition group for all curve segment
    elements, i.e. continuous segments of the same interpolation
    mechanism. All curve segments shall have an attribute interpolation
    with type gml:CurveInterpolationType specifying the curve
    interpolation mechanism used for this segment. This mechanism uses
    the control points and control parameters to determine the position
    of this curve segment.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AbstractGml(AbstractGmltype):
    """The abstract element gml:AbstractGML is "any GML object having identity".

    It acts as the head of an XML Schema substitution group, which may
    include any element which is a GML feature, or other object, with
    identity. This is used as a variable in content models in GML core
    and application schemas. It is effectively an abstract superclass
    for all GML objects.
    """

    class Meta:
        name = "AbstractGML"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AbstractGeometryType(AbstractGmltype):
    """All geometry elements are derived directly or indirectly from this abstract
    supertype. A geometry element may have an identifying attribute (gml:id), one
    or more names (elements identifier and name) and a description (elements
    description and descriptionReference) . It may be associated with a spatial.

    reference system (attribute group gml:SRSReferenceGroup). The following rules shall
    be adhered to: - Every geometry type shall derive from this abstract type. - Every
    geometry element (i.e. an element of a geometry type) shall be directly or
    indirectly in the substitution group of AbstractGeometry.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    srs_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "srsName",
            "type": "Attribute",
        },
    )
    srs_dimension: Optional[int] = field(
        default=None,
        metadata={
            "name": "srsDimension",
            "type": "Attribute",
        },
    )


@dataclass
class AbstractRing(AbstractRingType):
    """An abstraction of a ring to support surface boundaries of different
    complexity.

    The AbstractRing element is the abstract head of the substituition
    group for all closed boundaries of a surface patch.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AbstractSurfacePatch(AbstractSurfacePatchType):
    """A surface patch defines a homogenuous portion of a surface.

    The AbstractSurfacePatch element is the abstract head of the
    substituition group for all surface patch elements describing a
    continuous portion of a surface. All surface patches shall have an
    attribute interpolation (declared in the types derived from
    gml:AbstractSurfacePatchType) specifying the interpolation mechanism
    used for the patch using gml:SurfaceInterpolationType.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AngleType(MeasureType):
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AssociationRoleType:
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    any_element: Optional[object] = field(
        default=None,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
        },
    )
    owns: bool = field(
        default=False,
        metadata={
            "type": "Attribute",
        },
    )
    type_value: TypeType = field(
        init=False,
        default=TypeType.SIMPLE,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    href: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    arcrole: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    show: Optional[ShowType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    actuate: Optional[ActuateType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    nil_reason: Optional[Union[str, NilReasonEnumerationValue]] = field(
        default=None,
        metadata={
            "name": "nilReason",
            "type": "Attribute",
            "pattern": r"other:/w{2,}",
        },
    )


@dataclass
class Boolean:
    class Meta:
        nillable = True
        namespace = "http://www.opengis.net/gml/3.2"

    value: Optional[bool] = field(
        default=None,
        metadata={
            "nillable": True,
        },
    )
    nil_reason: Optional[Union[str, NilReasonEnumerationValue]] = field(
        default=None,
        metadata={
            "name": "nilReason",
            "type": "Attribute",
            "pattern": r"other:/w{2,}",
        },
    )


@dataclass
class CodeWithAuthorityType(CodeType):
    """
    Gml:CodeWithAuthorityType requires that the codeSpace attribute is provided in
    an instance.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    code_space: Optional[str] = field(
        default=None,
        metadata={
            "name": "codeSpace",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class EnvelopeType:
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    lower_corner: Optional[DirectPositionType] = field(
        default=None,
        metadata={
            "name": "lowerCorner",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
            "required": True,
        },
    )
    upper_corner: Optional[DirectPositionType] = field(
        default=None,
        metadata={
            "name": "upperCorner",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
            "required": True,
        },
    )
    srs_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "srsName",
            "type": "Attribute",
        },
    )
    srs_dimension: Optional[int] = field(
        default=None,
        metadata={
            "name": "srsDimension",
            "type": "Attribute",
        },
    )


@dataclass
class FeaturePropertyType:
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    owns: bool = field(
        default=False,
        metadata={
            "type": "Attribute",
        },
    )
    type_value: TypeType = field(
        init=False,
        default=TypeType.SIMPLE,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    href: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    arcrole: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    show: Optional[ShowType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    actuate: Optional[ActuateType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    nil_reason: Optional[Union[str, NilReasonEnumerationValue]] = field(
        default=None,
        metadata={
            "name": "nilReason",
            "type": "Attribute",
            "pattern": r"other:/w{2,}",
        },
    )


@dataclass
class LengthType(MeasureType):
    """This is a prototypical definition for a specific measure type defined as a
    vacuous extension (i.e. aliases) of gml:MeasureType.

    In this case, the content model supports the description of a length
    (or distance) quantity, with its units. The unit of measure
    referenced by uom shall be suitable for a length, such as metres or
    feet.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class ReferenceType:
    """
    Gml:ReferenceType is intended to be used in application schemas directly, if a
    property element shall use a "by-reference only" encoding.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    owns: bool = field(
        default=False,
        metadata={
            "type": "Attribute",
        },
    )
    type_value: TypeType = field(
        init=False,
        default=TypeType.SIMPLE,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    href: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    arcrole: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    show: Optional[ShowType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    actuate: Optional[ActuateType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    nil_reason: Optional[Union[str, NilReasonEnumerationValue]] = field(
        default=None,
        metadata={
            "name": "nilReason",
            "type": "Attribute",
            "pattern": r"other:/w{2,}",
        },
    )


@dataclass
class VolumeType(MeasureType):
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AbstractInlineProperty(InlinePropertyType):
    """
    Gml:abstractInlineProperty may be used as the head of a subtitution group of
    more specific elements providing a value inline.
    """

    class Meta:
        name = "abstractInlineProperty"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class Measure(MeasureType):
    """
    The value of a physical quantity, together with its unit.
    """

    class Meta:
        name = "measure"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class Pos(DirectPositionType):
    class Meta:
        name = "pos"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class PosList(DirectPositionListType):
    class Meta:
        name = "posList"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class ArcType:
    """
    :ivar type_value:
    :ivar arcrole:
    :ivar title:
    :ivar show:
    :ivar actuate:
    :ivar from_value:
    :ivar to: from and to have default behavior when values are missing
    """

    class Meta:
        name = "arcType"
        target_namespace = "http://www.w3.org/1999/xlink"

    type_value: TypeType = field(
        init=False,
        default=TypeType.ARC,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "required": True,
        },
    )
    arcrole: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    show: Optional[ShowType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    actuate: Optional[ActuateType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    from_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "from",
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    to: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )


@dataclass
class Extended:
    """Intended for use as the type of user-declared elements to make them extended
    links.

    Note that the elements referenced in the content model are all
    abstract. The intention is that by simply declaring elements with
    these as their substitutionGroup, all the right things will happen.
    """

    class Meta:
        name = "extended"
        target_namespace = "http://www.w3.org/1999/xlink"

    type_value: TypeType = field(
        init=False,
        default=TypeType.EXTENDED,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "required": True,
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )


@dataclass
class LocatorType:
    """
    :ivar type_value:
    :ivar href:
    :ivar role:
    :ivar title:
    :ivar label: label is not required, but locators have no particular
        XLink function if they are not labeled.
    """

    class Meta:
        name = "locatorType"
        target_namespace = "http://www.w3.org/1999/xlink"

    type_value: TypeType = field(
        init=False,
        default=TypeType.LOCATOR,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "required": True,
        },
    )
    href: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "required": True,
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    label: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )


@dataclass
class ResourceType:
    class Meta:
        name = "resourceType"
        target_namespace = "http://www.w3.org/1999/xlink"

    type_value: TypeType = field(
        init=False,
        default=TypeType.RESOURCE,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "required": True,
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    label: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    content: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
        },
    )


@dataclass
class Simple:
    """
    Intended for use as the type of user-declared elements to make them simple
    links.
    """

    class Meta:
        name = "simple"
        target_namespace = "http://www.w3.org/1999/xlink"

    type_value: TypeType = field(
        init=False,
        default=TypeType.SIMPLE,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    href: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    arcrole: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    show: Optional[ShowType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    actuate: Optional[ActuateType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    content: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
        },
    )


@dataclass
class TitleEltType:
    """
    :ivar type_value:
    :ivar lang: xml:lang is not required, but provides much of the
        motivation for title elements in addition to attributes, and so
        is provided here for convenience.
    :ivar content:
    """

    class Meta:
        name = "titleEltType"
        target_namespace = "http://www.w3.org/1999/xlink"

    type_value: TypeType = field(
        init=False,
        default=TypeType.TITLE,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "required": True,
        },
    )
    lang: Optional[Union[str, LangValue]] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )
    content: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
        },
    )


@dataclass
class InformationTypeType(AbstractInformationType):
    """
    Generalized information type which carry all the common attributes.
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class ObscuredSectorType:
    """-

    :ivar sector_limit: A sector is the part of a circle between two
        straight lines drawn from the centre to the circumference. The
        sector limit specifies the limits of the sector In a clockwise
        direction around the central feature (for example a light).
    :ivar sector_information: Additional textual information about a
        light sector.
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    sector_limit: Optional[SectorLimitType] = field(
        default=None,
        metadata={
            "name": "sectorLimit",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    sector_information: Optional[SectorInformationType] = field(
        default=None,
        metadata={
            "name": "sectorInformation",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class LightSectorType:
    """
    A sector is the part of a circle between two straight lines drawn from the
    centre to the circumference.

    :ivar colour: The property possessed by an object of producing
        different sensations on the eye as a result of the way it
        reflects or emits light.
    :ivar directional_character: A directional light is a light
        illuminating a sector of very narrow angle and intended to mark
        a direction to follow.
    :ivar light_visibility: The specific visibility of a light, with
        respect to the light's intensity and ease of recognition.
    :ivar sector_limit: A sector is the part of a circle between two
        straight lines drawn from the centre to the circumference. The
        sector limit specifies the limits of the sector In a clockwise
        direction around the central feature (for example a light).
    :ivar value_of_nominal_range: The luminous range of a light in a
        homogenous atmosphere in which the meteorological visibility is
        10 sea miles.
    :ivar sector_information: Additional textual information about a
        light sector.
    :ivar sector_arc_extension: Distance in screen millimetres (mm) by
        which a sector arc is extended beyond the default.
    """

    class Meta:
        name = "lightSectorType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    colour: list[ColourType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )
    directional_character: Optional[DirectionalCharacterType] = field(
        default=None,
        metadata={
            "name": "directionalCharacter",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    light_visibility: list[LightVisibilityType] = field(
        default_factory=list,
        metadata={
            "name": "lightVisibility",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    sector_limit: Optional[SectorLimitType] = field(
        default=None,
        metadata={
            "name": "sectorLimit",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    value_of_nominal_range: Optional[float] = field(
        default=None,
        metadata={
            "name": "valueOfNominalRange",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    sector_information: list[SectorInformationType] = field(
        default_factory=list,
        metadata={
            "name": "sectorInformation",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    sector_arc_extension: Optional[bool] = field(
        default=None,
        metadata={
            "name": "sectorArcExtension",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class RhythmOfLightType:
    """
    The sequence of times occupied by intervals of light/sound and eclipse/silence
    for all light characteristics or sound signals.

    :ivar light_characteristic: The distinct character, such as fixed,
        flashing, or occulting, which is given to each light to avoid
        confusion with neighbouring ones.
    :ivar signal_group: The number of signals, the combination of
        signals or the morse character(s) within one period of full
        sequence.
    :ivar signal_period: The time occupied by an entire cycle of
        intervals of light and eclipse.
    :ivar signal_sequence: The sequence of times occupied by intervals
        of light and eclipse for all light characteristics.
    """

    class Meta:
        name = "rhythmOfLightType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    light_characteristic: Optional[LightCharacteristicType] = field(
        default=None,
        metadata={
            "name": "lightCharacteristic",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    signal_group: list[str] = field(
        default_factory=list,
        metadata={
            "name": "signalGroup",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "max_occurs": 10,
        },
    )
    signal_period: Optional[float] = field(
        default=None,
        metadata={
            "name": "signalPeriod",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    signal_sequence: list[SignalSequenceType] = field(
        default_factory=list,
        metadata={
            "name": "signalSequence",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "max_occurs": 10,
        },
    )


@dataclass
class SpatialAccuracyType:
    """
    Provides an indication of the vertical and horizontal positional uncertainty of
    bathymetric data, optionally within a specified date range.

    :ivar fixed_date_range: An active period of a single fixed event or
        occurrence, as the date range between discrete start and end
        dates.
    :ivar horizontal_position_uncertainty: The best estimate of the
        accuracy of a position.
    :ivar vertical_uncertainty: The best estimate of the vertical
        accuracy of depths, heights, vertical distances and vertical
        clearances.
    """

    class Meta:
        name = "spatialAccuracyType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    fixed_date_range: Optional[FixedDateRangeType] = field(
        default=None,
        metadata={
            "name": "fixedDateRange",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    horizontal_position_uncertainty: Optional[
        HorizontalPositionUncertaintyType
    ] = field(
        default=None,
        metadata={
            "name": "horizontalPositionUncertainty",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_uncertainty: Optional[VerticalUncertaintyType] = field(
        default=None,
        metadata={
            "name": "verticalUncertainty",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class S100SpatialAttributeType:
    """
    S-100 Base type for the geometry of a feature.
    """

    class Meta:
        name = "S100_SpatialAttributeType"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    mask_reference: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "maskReference",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    type_value: TypeType = field(
        init=False,
        default=TypeType.SIMPLE,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    href: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    arcrole: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    show: Optional[ShowType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    actuate: Optional[ActuateType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    nil_reason: Optional[Union[str, NilReasonEnumerationValue]] = field(
        default=None,
        metadata={
            "name": "nilReason",
            "type": "Attribute",
            "pattern": r"other:/w{2,}",
        },
    )
    scale_minimum: Optional[int] = field(
        default=None,
        metadata={
            "name": "scaleMinimum",
            "type": "Attribute",
        },
    )
    scale_maximum: Optional[int] = field(
        default=None,
        metadata={
            "name": "scaleMaximum",
            "type": "Attribute",
        },
    )


@dataclass
class InformationAssociation(ReferenceType):
    class Meta:
        name = "informationAssociation"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class AbstractGeometricAggregateType(AbstractGeometryType):
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    aggregation_type: Optional[AggregationType] = field(
        default=None,
        metadata={
            "name": "aggregationType",
            "type": "Attribute",
        },
    )


@dataclass
class AbstractGeometricPrimitiveType(AbstractGeometryType):
    """Gml:AbstractGeometricPrimitiveType is the abstract root type of the
    geometric primitives.

    A geometric primitive is a geometric object that is not decomposed
    further into other primitives in the system. All primitives are
    oriented in the direction implied by the sequence of their
    coordinate tuples.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AbstractGeometry(AbstractGeometryType):
    """The AbstractGeometry element is the abstract head of the substitution group
    for all geometry elements of GML.

    This includes pre-defined and user-defined geometry elements. Any
    geometry element shall be a direct or indirect extension/restriction
    of AbstractGeometryType and shall be directly or indirectly in the
    substitution group of AbstractGeometry.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class Envelope(EnvelopeType):
    """Envelope defines an extent using a pair of positions defining opposite
    corners in arbitrary dimensions.

    The first direct position is the "lower corner" (a coordinate
    position consisting of all the minimal ordinates for each dimension
    for all points within the envelope), the second one the "upper
    corner" (a coordinate position consisting of all the maximal
    ordinates for each dimension for all points within the envelope).
    The use of the properties "coordinates" and "pos" has been
    deprecated. The explicitly named properties "lowerCorner" and
    "upperCorner" shall be used instead.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AbstractAssociationRole(AssociationRoleType):
    """Applying this pattern shall restrict the multiplicity of objects in a
    property element using this content model to exactly one. An instance of this
    type shall contain an element representing an object, or serve as a pointer to
    a remote.

    object. Applying the pattern to define an application schema specific property type
    allows to restrict - the inline object to specified object types, - the encoding to
    "by-reference only" (see 7.2.3.7), - the encoding to "inline only" (see 7.2.3.8).
    """

    class Meta:
        name = "abstractAssociationRole"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AbstractReference(ReferenceType):
    """
    Gml:abstractReference may be used as the head of a subtitution group of more
    specific elements providing a value by-reference.
    """

    class Meta:
        name = "abstractReference"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class Angle(AngleType):
    """
    The gml:angle property element is used to record the value of an angle quantity
    as a single number, with its units.
    """

    class Meta:
        name = "angle"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class Arc(ArcType):
    class Meta:
        name = "arc"
        namespace = "http://www.w3.org/1999/xlink"


@dataclass
class Locator(LocatorType):
    class Meta:
        name = "locator"
        namespace = "http://www.w3.org/1999/xlink"


@dataclass
class Resource(ResourceType):
    class Meta:
        name = "resource"
        namespace = "http://www.w3.org/1999/xlink"


@dataclass
class Title(TitleEltType):
    class Meta:
        name = "title"
        namespace = "http://www.w3.org/1999/xlink"


@dataclass
class AtoNfixingMethodType(InformationTypeType):
    """
    Method used for fixing the position of an aid to navigation.

    :ivar reference_point: -
    :ivar horizontal_datum: Horizontal reference surface or the
        reference coordinate system used for geodetic control in the
        calculation of coordinates of points on the earth.
    :ivar source_date: The production date of the source; for example
        the date of measurement.
    :ivar positioning_procedure: -
    """

    class Meta:
        name = "AtoNFixingMethodType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    reference_point: Optional[str] = field(
        default=None,
        metadata={
            "name": "referencePoint",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    horizontal_datum: Optional[HorizontalDatumType] = field(
        default=None,
        metadata={
            "name": "horizontalDatum",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    source_date: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "sourceDate",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    positioning_procedure: Optional[str] = field(
        default=None,
        metadata={
            "name": "positioningProcedure",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )


@dataclass
class AtonStatusInformationType(InformationTypeType):
    """-

    :ivar change_details: -
    :ivar change_types: -
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    change_details: Optional[ChangeDetailsType] = field(
        default=None,
        metadata={
            "name": "ChangeDetails",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    change_types: Optional[ChangeTypesType] = field(
        default=None,
        metadata={
            "name": "ChangeTypes",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class InformationTypeAbstract(InformationTypeType):
    class Meta:
        name = "InformationType"
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class PositioningInformationType(InformationTypeType):
    """Information about how a position was obtained.

    (proposed by CCG)

    :ivar positioning_device: -
    :ivar positioning_method: A description of the method used to obtain
        a position.(proposed by CCG)
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    positioning_device: Optional[str] = field(
        default=None,
        metadata={
            "name": "positioningDevice",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    positioning_method: Optional[PositioningMethodType] = field(
        default=None,
        metadata={
            "name": "positioningMethod",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class SpatialQualityType(InformationTypeType):
    """
    The indication of the quality of the locational information for features in a
    dataset.

    :ivar quality_of_horizontal_measurement: The degree of reliability
        attributed to a position.
    :ivar spatial_accuracy: Provides an indication of the vertical and
        horizontal positional uncertainty of bathymetric data,
        optionally within a specified date range.
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    quality_of_horizontal_measurement: Optional[
        QualityOfHorizontalMeasurementType
    ] = field(
        default=None,
        metadata={
            "name": "qualityOfHorizontalMeasurement",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    spatial_accuracy: Optional[SpatialAccuracyType] = field(
        default=None,
        metadata={
            "name": "spatialAccuracy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class SectorCharacteristicsType:
    """
    Describes the characteristics of a light sector.

    :ivar light_characteristic: The distinct character, such as fixed,
        flashing, or occulting, which is given to each light to avoid
        confusion with neighbouring ones.
    :ivar light_sector: A sector is the part of a circle between two
        straight lines drawn from the centre to the circumference.
    :ivar signal_group: The number of signals, the combination of
        signals or the morse character(s) within one period of full
        sequence.
    :ivar signal_period: The time occupied by an entire cycle of
        intervals of light and eclipse.
    :ivar signal_sequence: The sequence of times occupied by intervals
        of light and eclipse for all light characteristics.
    """

    class Meta:
        name = "sectorCharacteristicsType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    light_characteristic: Optional[LightCharacteristicType] = field(
        default=None,
        metadata={
            "name": "lightCharacteristic",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    light_sector: list[LightSectorType] = field(
        default_factory=list,
        metadata={
            "name": "lightSector",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
            "max_occurs": 10,
        },
    )
    signal_group: list[str] = field(
        default_factory=list,
        metadata={
            "name": "signalGroup",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "max_occurs": 10,
        },
    )
    signal_period: Optional[float] = field(
        default=None,
        metadata={
            "name": "signalPeriod",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    signal_sequence: list[SignalSequenceType] = field(
        default_factory=list,
        metadata={
            "name": "signalSequence",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "max_occurs": 10,
        },
    )


@dataclass
class AbstractCurveType(AbstractGeometricPrimitiveType):
    """Gml:AbstractCurveType is an abstraction of a curve to support the different
    levels of complexity.

    The curve may always be viewed as a geometric primitive, i.e. is
    continuous.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AbstractGeometricAggregate(AbstractGeometricAggregateType):
    """
    Gml:AbstractGeometricAggregate is the abstract head of the substitution group
    for all geometric aggregates.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AbstractGeometricPrimitive(AbstractGeometricPrimitiveType):
    """
    The AbstractGeometricPrimitive element is the abstract head of the substitution
    group for all (pre- and user-defined) geometric primitives.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AbstractSurfaceType(AbstractGeometricPrimitiveType):
    """Gml:AbstractSurfaceType is an abstraction of a surface to support the
    different levels of complexity.

    A surface is always a continuous region of a plane.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class BoundingShapeType:
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    envelope: Optional[Envelope] = field(
        default=None,
        metadata={
            "name": "Envelope",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
            "required": True,
        },
    )
    nil_reason: Optional[Union[str, NilReasonEnumerationValue]] = field(
        default=None,
        metadata={
            "name": "nilReason",
            "type": "Attribute",
            "pattern": r"other:/w{2,}",
        },
    )


@dataclass
class PointType1(AbstractGeometricPrimitiveType):
    """S-100 XML supports two different ways to specify the direct positon of a
    point.

    1. The "pos" element is of type DirectPositionType.
    """

    class Meta:
        name = "PointType"
        target_namespace = "http://www.opengis.net/gml/3.2"

    pos: Optional[Pos] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
            "required": True,
        },
    )


@dataclass
class AtoNfixingMethod(AtoNfixingMethodType):
    class Meta:
        name = "AtoNFixingMethod"
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class AtonStatusInformation(AtonStatusInformationType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class PositioningInformation(PositioningInformationType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class SpatialQuality(SpatialQualityType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class PointType2(PointType1):
    """
    S-100 point type adds an information association to the GML spatial type Point.
    """

    class Meta:
        name = "PointType"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    information_association: list[InformationAssociation] = field(
        default_factory=list,
        metadata={
            "name": "informationAssociation",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )


@dataclass
class AbstractCurve(AbstractCurveType):
    """
    The AbstractCurve element is the abstract head of the substitution group for
    all (continuous) curve elements.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AbstractSurface(AbstractSurfaceType):
    """
    The AbstractSurface element is the abstract head of the substitution group for
    all (continuous) surface elements.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class Point1(PointType1):
    """A Point is defined by a single coordinate tuple.

    The direct position of a point is specified by the pos element which
    is of type DirectPositionType.
    """

    class Meta:
        name = "Point"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class BoundedBy(BoundingShapeType):
    """
    This property describes the minimum bounding box or rectangle that encloses the
    entire feature.
    """

    class Meta:
        name = "boundedBy"
        nillable = True
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class Point2(PointType2):
    class Meta:
        name = "Point"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class AbstractFeatureTypeAbstract(AbstractGmltype):
    """The basic feature model is given by the gml:AbstractFeatureType.

    The content model for gml:AbstractFeatureType adds two specific
    properties suitable for geographic features to the content model
    defined in gml:AbstractGMLType. The value of the gml:boundedBy
    property describes an envelope that encloses the entire feature
    instance, and is primarily useful for supporting rapid searching for
    features that occur in a particular location. The value of the
    gml:location property describes the extent, position or relative
    location of the feature.
    """

    class Meta:
        name = "AbstractFeatureType"
        target_namespace = "http://www.opengis.net/gml/3.2"

    bounded_by: Optional[BoundedBy] = field(
        default=None,
        metadata={
            "name": "boundedBy",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
            "nillable": True,
        },
    )


@dataclass
class PointPropertyType1:
    """A property that has a point as its value domain may either be an appropriate
    geometry element encapsulated in an element of this type or an XLink reference
    to a remote geometry element (where remote includes geometry elements located
    elsewhere in the same document).

    Either the reference or the contained element shall be given, but
    neither both nor none.
    """

    class Meta:
        name = "PointPropertyType"
        target_namespace = "http://www.opengis.net/gml/3.2"

    point: Optional[Point1] = field(
        default=None,
        metadata={
            "name": "Point",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    type_value: TypeType = field(
        init=False,
        default=TypeType.SIMPLE,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    href: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    arcrole: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    show: Optional[ShowType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    actuate: Optional[ActuateType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    nil_reason: Optional[Union[str, NilReasonEnumerationValue]] = field(
        default=None,
        metadata={
            "name": "nilReason",
            "type": "Attribute",
            "pattern": r"other:/w{2,}",
        },
    )
    owns: bool = field(
        default=False,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class AbstractFeatureType(AbstractFeatureTypeAbstract):
    """Abstract type for an S-100 feature.

    This is the base type from which domain application schemas derive
    definitions for their individual features. It derives from GML
    AbstractFeatureType.
    """

    class Meta:
        target_namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class PointPropertyType2(S100SpatialAttributeType):
    """
    Point property using the S-100 point type.
    """

    class Meta:
        name = "PointPropertyType"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    point: Optional[Point2] = field(
        default=None,
        metadata={
            "name": "Point",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )


@dataclass
class AbstractFeature(AbstractFeatureTypeAbstract):
    """This abstract element serves as the head of a substitution group which may
    contain any elements whose content model is derived from
    gml:AbstractFeatureType.

    This may be used as a variable in the construction of content
    models. gml:AbstractFeature may be thought of as "anything that is a
    GML feature" and may be used to define variables or templates in
    which the value of a GML property is "any feature". This occurs in
    particular in a GML feature collection where the feature member
    properties contain one or multiple copies of gml:AbstractFeature
    respectively.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class PointMember(PointPropertyType1):
    """
    This property element either references a Point via the XLink-attributes or
    contains the Point element.
    """

    class Meta:
        name = "pointMember"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class PointProperty1(PointPropertyType1):
    """This property element either references a point via the XLink-attributes or
    contains the point element.

    pointProperty is the predefined property which may be used by GML
    Application Schemas whenever a GML feature has a property with a
    value that is substitutable for Point.
    """

    class Meta:
        name = "pointProperty"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class AidsToNavigationType(AbstractFeatureType):
    """A visual, acoustical, or radio device, external to a ship, designed to
    assist in determining a safe course or a vessel's position, or to warn of
    dangers and/or obstructions.

    Aids to navigation usually include buoys, beacons, fog signals,
    lights, radio beacons, leading marks, radio position fixing systems
    and GNSS which are chart-related and assist safe navigation.

    :ivar i_dcode: Identification code as specified in predefined
        system. Also called identification number.
    :ivar information: Textual information about the feature. The
        information may be provided as a string of text or as a file
        name of a single external text file that contains the text.
    :ivar feature_name: Provides the name of an entity, defines the
        national language of the name, and provides the option to
        display the name at various system display settings.
    :ivar scale_minimum: The minimum scale at which the feature may be
        used for example for ECDIS presentation.
    :ivar source_date: The production date of the source; for example
        the date of measurement.
    :ivar source: The publication, document, or reference work from
        which information comes or is acquired.
    :ivar pictorial_representation: Indicates whether a pictorial
        representation of the feature is available.
    :ivar inspection_frequency: A statement of how frequently an item is
        inspected.
    :ivar inspection_requirements: A statement of what requirements are
        in place for how inspection of an item is carried out.
    :ivar a_to_nmaintenance_record: A reference following the Uniform
        Resource Identifier (URI) principles to a record of maintenance.
    :ivar installation_date: The date when an item was installed.
    :ivar fixed_date_range: An active period of a single fixed event or
        occurrence, as the date range between discrete start and end
        dates.
    :ivar periodic_date_range: The active period of a recurring event or
        occurrence.
    :ivar seasonal_action_required: -
    :ivar statuspart:
    :ivar peer_aton_aggregation:
    :ivar peer_aton_association:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    i_dcode: Optional[str] = field(
        default=None,
        metadata={
            "name": "iDCode",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    information: list[InformationType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    feature_name: list[FeatureNameType] = field(
        default_factory=list,
        metadata={
            "name": "featureName",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    scale_minimum: Optional[int] = field(
        default=None,
        metadata={
            "name": "scaleMinimum",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    source_date: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "sourceDate",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    source: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    pictorial_representation: Optional[str] = field(
        default=None,
        metadata={
            "name": "pictorialRepresentation",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    inspection_frequency: Optional[str] = field(
        default=None,
        metadata={
            "name": "inspectionFrequency",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    inspection_requirements: Optional[str] = field(
        default=None,
        metadata={
            "name": "inspectionRequirements",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    a_to_nmaintenance_record: Optional[str] = field(
        default=None,
        metadata={
            "name": "aToNMaintenanceRecord",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    installation_date: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "installationDate",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    fixed_date_range: Optional[FixedDateRangeType] = field(
        default=None,
        metadata={
            "name": "fixedDateRange",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    periodic_date_range: Optional[PeriodicDateRangeType] = field(
        default=None,
        metadata={
            "name": "periodicDateRange",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    seasonal_action_required: list[str] = field(
        default_factory=list,
        metadata={
            "name": "SeasonalActionRequired",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    statuspart: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "Statuspart",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    peer_aton_aggregation: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "peerAtonAggregation",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    peer_aton_association: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "peerAtonAssociation",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class AtonAggregationType(AbstractFeatureType):
    """Used to identify an aggregation of two or more objects.

    This aggregation may be named content of categoryOfAggregation
    should be put in information attribute when converting to S-57.

    :ivar category_of_aggregation: named aggregations between two or
        more aids to navigation and/or navigationally relevant features
    :ivar aton_aggregation_by:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_aggregation: Optional[CategoryOfAggregationType] = field(
        default=None,
        metadata={
            "name": "CategoryOfAggregation",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    aton_aggregation_by: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "atonAggregationBy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class AtonAssociationType(AbstractFeatureType):
    """Used to identify an association between two or more objects.

    The association may be named content of categoryOfAssociation should
    be put in information attribute when converting to S-57

    :ivar category_of_association: named associations between two or
        more aids to navigation and/or navigationally relevant features
    :ivar danger:
    :ivar aton_association_by:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_association: Optional[CategoryOfAssociationType] = field(
        default=None,
        metadata={
            "name": "CategoryOfAssociation",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    danger: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    aton_association_by: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "atonAssociationBy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class S100ArcByCenterPointType(AbstractCurveSegmentType):
    """
    Type for S-100 arc by center point geometry.
    """

    class Meta:
        name = "S100_ArcByCenterPointType"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    pos: Optional[Pos] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    point_property: Optional[PointProperty1] = field(
        default=None,
        metadata={
            "name": "pointProperty",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    radius: Optional[LengthType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )
    start_angle: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "startAngle",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "min_inclusive": Decimal("0.0"),
            "max_inclusive": Decimal("360.0"),
            "fraction_digits": 1,
        },
    )
    angular_distance: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "angularDistance",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "min_inclusive": Decimal("-360.0"),
            "max_inclusive": Decimal("360.0"),
            "fraction_digits": 1,
        },
    )
    interpolation: CurveInterpolationType = field(
        init=False,
        default=CurveInterpolationType.CIRCULAR_ARC_CENTER_POINT_WITH_RADIUS,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class S100GmCurveType(AbstractCurveSegmentType):
    """<xs:documentation xmlns:xs="http://www.w3.org/2001/XMLSchema">Type for curve segments with other interpolations</xs:documentation>"""

    class Meta:
        name = "S100_GM_CurveType"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    pos: list[Pos] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    point_property: list[PointProperty1] = field(
        default_factory=list,
        metadata={
            "name": "pointProperty",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    pos_list: Optional[PosList] = field(
        default=None,
        metadata={
            "name": "posList",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    interpolation: Optional[CurveInterpolationType] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class S100GmSplineCurveType(AbstractCurveSegmentType):
    """<xs:documentation xmlns:xs="http://www.w3.org/2001/XMLSchema">Type for general splines including b-splines</xs:documentation>"""

    class Meta:
        name = "S100_GM_SplineCurveType"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    pos: list[Pos] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    point_property: list[PointProperty1] = field(
        default_factory=list,
        metadata={
            "name": "pointProperty",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    pos_list: Optional[PosList] = field(
        default=None,
        metadata={
            "name": "posList",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    degree: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )
    knot: list[KnotPropertyType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    knot_spec: Optional[S100GmKnotTypeType] = field(
        default=None,
        metadata={
            "name": "knotSpec",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    is_rational: Optional[Union[str, NilReasonEnumerationValue]] = field(
        default=None,
        metadata={
            "name": "isRational",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
            "pattern": r"other:/w{2,}",
        },
    )
    interpolation: Optional[CurveInterpolationType] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class VectorType:
    """
    Defintion of the Vector datatype used in splines.

    :ivar origin:
    :ivar dimension:
    :ivar offset: The number of values must be the same as "dimension"
        value
    """

    class Meta:
        target_namespace = "http://www.iho.int/s100gml/5.0"

    origin: Optional["VectorType.Origin"] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )
    dimension: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )
    offset: list[float] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "tokens": True,
        },
    )

    @dataclass
    class Origin:
        pos: Optional[Pos] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.opengis.net/gml/3.2",
            },
        )
        point_property: Optional[PointProperty1] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.opengis.net/gml/3.2",
            },
        )


@dataclass
class PointProperty2(PointPropertyType2):
    class Meta:
        name = "pointProperty"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class GeodesicStringType(AbstractCurveSegmentType):
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    pos_list: Optional[PosList] = field(
        default=None,
        metadata={
            "name": "posList",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    pos: list[Pos] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    point_property: list[PointProperty1] = field(
        default_factory=list,
        metadata={
            "name": "pointProperty",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    interpolation: CurveInterpolationType = field(
        init=False,
        default=CurveInterpolationType.GEODESIC,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class LineStringSegmentType(AbstractCurveSegmentType):
    """GML supports two different ways to specify the control points of a line
    string.

    1. A sequence of "pos" (DirectPositionType) or "pointProperty"
    (PointPropertyType) elements. "pos" elements are control points that are only part
    of this curve, "pointProperty" elements contain a point that may be referenced from
    other geometry elements or reference another point defined outside of this curve
    (reuse of existing points). 2. The "posList" element allows for a compact way to
    specifiy the coordinates of the control points, if all control points are in the
    same coordinate reference systems and belong to this curve only. The number of
    direct positions in the list must be at least two.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    pos: list[Pos] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    point_property: list[PointProperty1] = field(
        default_factory=list,
        metadata={
            "name": "pointProperty",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    pos_list: Optional[PosList] = field(
        default=None,
        metadata={
            "name": "posList",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    interpolation: CurveInterpolationType = field(
        init=False,
        default=CurveInterpolationType.LINEAR,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class LineStringType(AbstractCurveType):
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    pos: list[Pos] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    point_property: list[PointProperty1] = field(
        default_factory=list,
        metadata={
            "name": "pointProperty",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    pos_list: Optional[PosList] = field(
        default=None,
        metadata={
            "name": "posList",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )


@dataclass
class LinearRingType(AbstractRingType):
    """S-100 XML supports two different ways to specify the control points of a
    linear ring.

    1. A sequence of "pos" (DirectPositionType) or "pointProperty"
    (PointPropertyType) elements. "pos" elements are control points that are only part
    of this ring, "pointProperty" elements contain a point that may be referenced from
    other geometry elements or reference another point defined outside of this ring
    (reuse of existing points). 2. The "posList" element allows for a compact way to
    specifiy the coordinates of the control points, if all control points are in the
    same coordinate reference systems and belong to this ring only. The number of direct
    positions in the list must be at least four.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    pos: list[Pos] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    point_property: list[PointProperty1] = field(
        default_factory=list,
        metadata={
            "name": "pointProperty",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    pos_list: Optional[PosList] = field(
        default=None,
        metadata={
            "name": "posList",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )


@dataclass
class MultiPointType1(AbstractGeometricAggregateType):
    class Meta:
        name = "MultiPointType"
        target_namespace = "http://www.opengis.net/gml/3.2"

    point_member: list[PointMember] = field(
        default_factory=list,
        metadata={
            "name": "pointMember",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )


@dataclass
class AidsToNavigation(AidsToNavigationType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class AtonAggregation(AtonAggregationType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class AtonAssociation(AtonAssociationType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class BridleType(AidsToNavigationType):
    """Two lengths of chain connected by a central ring and used for lifting wide
    loads.

    (IALA Dictionary,8-3-195)

    :ivar bridle_link_type: -
    :ivar legs_details: -
    :ivar bridle_holds:
    :ivar bridle_hangs:
    :ivar shackle_to_bridle_connected:
    :ivar bridle_attached:
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    bridle_link_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "bridleLinkType",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    legs_details: Optional[str] = field(
        default=None,
        metadata={
            "name": "legsDetails",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    bridle_holds: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "bridleHolds",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    bridle_hangs: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "bridleHangs",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    shackle_to_bridle_connected: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "shackleToBridleConnected",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    bridle_attached: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "bridleAttached",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["BridleType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class CableSubmarineType(AidsToNavigationType):
    """
    An assembly of wires or fibres, or a wire rope or chain, which has been laid
    underwater or buried beneath the sea floor.

    :ivar cable_dimensions: The dimensions of a cable to give its length
        and diameter.
    :ivar category_of_cable: Classification of the cable based on the
        services provided.
    :ivar status: The condition of an object at a given instant in time.
    :ivar cableholds:
    :ivar shackle_to_cable_connected:
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    cable_dimensions: Optional[CableDimensionsType] = field(
        default=None,
        metadata={
            "name": "CableDimensions",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    category_of_cable: Optional[CategoryOfCableType] = field(
        default=None,
        metadata={
            "name": "categoryOfCable",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    cableholds: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
            "max_occurs": 2,
        },
    )
    shackle_to_cable_connected: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "shackleToCableConnected",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    geometry: list["CableSubmarineType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class CounterWeightType(AidsToNavigationType):
    """-

    :ivar nature_of_construction: The building's primary construction
        material.
    :ivar weight: -
    :ivar counter_weight_type: -
    :ivar counter_weightholds:
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    nature_of_construction: Optional[NatureOfConstructionType] = field(
        default=None,
        metadata={
            "name": "natureOfConstruction",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    weight: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    counter_weight_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "counterWeightType",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    counter_weightholds: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "counterWeightholds",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    geometry: list["CounterWeightType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class DangerousFeatureType(AbstractFeatureType):
    """-

    :ivar interoperability_identifier: A common unique identifier for
        entities which describe a single real-world feature, and which
        is used to identify instances of the feature in end-user systems
        where the feature may be included in multiple data product
        types.
    :ivar information: Textual information about the feature. The
        information may be provided as a string of text or as a file
        name of a single external text file that contains the text.
    :ivar marking_aton:
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    interoperability_identifier: Optional[str] = field(
        default=None,
        metadata={
            "name": "interoperabilityIdentifier",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    information: list[InformationType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    marking_aton: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "markingAton",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )
    geometry: list["DangerousFeatureType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class ElectronicAtonType(AidsToNavigationType):
    """
    TBD.

    :ivar ato_nnumber: Identifier from a list of Aids to Navigation
        publication, such as List of Lights.
    :ivar m_msicode: The Maritime Mobile Service Identity (MMSI) Code is
        formed of a series of nine digits which are transmitted over the
        radio path in order to uniquely identify ship stations, ship
        earth stations,coast stations, coast earth stations, and group
        calls. These identities are formed in such a way that the
        identity or part thereof can be used by telephone and telex
        subscribers connected to the general telecommunications network
        principally to call ships automatically.
    :ivar status: The condition of an object at a given instant in time.
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    ato_nnumber: Optional[str] = field(
        default=None,
        metadata={
            "name": "AtoNNumber",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    m_msicode: Optional[str] = field(
        default=None,
        metadata={
            "name": "mMSICode",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class EquipmentType(AidsToNavigationType):
    """
    The implements used in an operation or activity.

    :ivar remote_monitoring_system: Classification or name of system
        used to remotely monitor a feature.
    :ivar parent:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    remote_monitoring_system: list[str] = field(
        default_factory=list,
        metadata={
            "name": "remoteMonitoringSystem",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    parent: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )


@dataclass
class MooringShackleType(AidsToNavigationType):
    """A shackle at the lower end of a mooring chain, for attachment to an anchor
    or sinker.

    (IALA Dictionary, 8-5-150)

    :ivar nature_of_construction: The building's primary construction
        material.
    :ivar shackle_type: Types of shackle.
    :ivar weight: -
    :ivar shackle_to_buoyconnected_to:
    :ivar shackle_to_bridleconnected_to:
    :ivar shackle_to_cable_connected_to:
    :ivar shackle_to_swivelconnected_to:
    :ivar shackle_to_anchorconnected_to:
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    nature_of_construction: Optional[NatureOfConstructionType] = field(
        default=None,
        metadata={
            "name": "natureOfConstruction",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    shackle_type: Optional[ShackleTypeType] = field(
        default=None,
        metadata={
            "name": "ShackleType",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    weight: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    shackle_to_buoyconnected_to: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "shackleToBuoyconnectedTo",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    shackle_to_bridleconnected_to: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "shackleToBridleconnectedTo",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    shackle_to_cable_connected_to: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "shackleToCableConnectedTo",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    shackle_to_swivelconnected_to: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "shackleToSwivelconnectedTo",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    shackle_to_anchorconnected_to: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "shackleToAnchorconnectedTo",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["MooringShackleType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class SinkerAnchorType(AidsToNavigationType):
    """A heavy weight (of concrete, cast-iron, etc..) that rests on the sea bed and
    to which a mooring line can be attached.

    (IALA Dictionary, 8-5-025)

    :ivar nature_of_construction: The building's primary construction
        material.
    :ivar sinker_dimensions: The dimensions of a sinker/anchor to give
        its three dimensional shape measurements.
    :ivar weight: -
    :ivar sinker_type: -
    :ivar shackle_to_anchor_connected:
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    nature_of_construction: Optional[NatureOfConstructionType] = field(
        default=None,
        metadata={
            "name": "natureOfConstruction",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    sinker_dimensions: Optional[SinkerDimensionsType] = field(
        default=None,
        metadata={
            "name": "sinkerDimensions",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    weight: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    sinker_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "sinkerType",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    shackle_to_anchor_connected: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "shackleToAnchorConnected",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    geometry: list["SinkerAnchorType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class StructureObjectType(AidsToNavigationType):
    """
    Something (such as a house, tower, bridge, etc.) that is built by putting parts
    together and that usually stands on its own.

    :ivar ato_nnumber: Identifier from a list of Aids to Navigation
        publication, such as List of Lights.
    :ivar aid_availability_category: A Category denoting the
        significance of an Aid to Navigation, expressed in terms of the
        probability that an AtoN or system of AtoN, as defined by the
        Competent Authority, is performing its specified function at any
        randomly chosen time. This is expressed as a percentage of total
        time that an AtoN or system of AtoN should be performing their
        specified function.
    :ivar condition: The various conditions of buildings and other
        constructions.
    :ivar contact_address: Direction or superscription of a letter,
        package, etc., specifying the name of the place to which it is
        directed, and optionally a contact person or organisation who
        should receive it.
    :ivar positioning_method:
    :ivar fixing_method:
    :ivar child:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    ato_nnumber: Optional[str] = field(
        default=None,
        metadata={
            "name": "AtoNNumber",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    aid_availability_category: Optional[AidAvailabilityCategoryType] = field(
        default=None,
        metadata={
            "name": "aidAvailabilityCategory",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    condition: Optional[ConditionType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    contact_address: Optional[ContactAddressType] = field(
        default=None,
        metadata={
            "name": "contactAddress",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    positioning_method: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "positioningMethod",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    fixing_method: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "fixingMethod",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    child: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class SwivelType(AidsToNavigationType):
    """A chain link that provides for rotary motion between the lengths of chain
    that it connects.

    (IALA Dictionary, 8-5-165)

    :ivar nature_of_construction: The building's primary construction
        material.
    :ivar weight: -
    :ivar swivel_type: -
    :ivar swivel_holds:
    :ivar swivel_attached:
    :ivar shackle_to_swivel_connected:
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    nature_of_construction: Optional[NatureOfConstructionType] = field(
        default=None,
        metadata={
            "name": "natureOfConstruction",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    weight: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    swivel_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "swivelType",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    swivel_holds: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "swivelHolds",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    swivel_attached: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "swivelAttached",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    shackle_to_swivel_connected: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "shackleToSwivelConnected",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    geometry: list["SwivelType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class TopmarkType(AidsToNavigationType):
    """A characteristic shape secured at the top of a buoy or beacon to aid in its
    identification.

    (IHO Dictionary, S-32, 5th Edition, 5548)

    :ivar colour: The property possessed by an object of producing
        different sensations on the eye as a result of the way it
        reflects or emits light.
    :ivar colour_pattern: A regular repeated design containing more than
        one colour.
    :ivar status: The condition of an object at a given instant in time.
    :ivar topmark_daymark_shape: The shape a topmark or daymark
        exhibits.
    :ivar vertical_length: The total vertical length of a feature.
    :ivar buoy_part:
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    colour: list[ColourType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    colour_pattern: list[ColourPatternType] = field(
        default_factory=list,
        metadata={
            "name": "colourPattern",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    topmark_daymark_shape: Optional[TopmarkDaymarkShapeType] = field(
        default=None,
        metadata={
            "name": "topmarkDaymarkShape",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    vertical_length: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    buoy_part: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "buoyPart",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    geometry: list["TopmarkType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class MultiPointType2(MultiPointType1):
    """
    S-100 multipoint type adds an information association to the GML spatial type
    MultiPoint.
    """

    class Meta:
        name = "MultiPointType"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    information_association: list[InformationAssociation] = field(
        default_factory=list,
        metadata={
            "name": "informationAssociation",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )


@dataclass
class S100ArcByCenterPoint(S100ArcByCenterPointType):
    """This variant of the arc requires that the points on the arc shall be
    computed instead of storing the coordinates directly.

    The single control point is the center point of the arc. The other
    parameters are the radius, the bearing at start, and the angle from
    the start to the end relative to the center of the arc. This
    representation can be used only in 2D. The element radius specifies
    the radius of the arc. The element startAngle specifies the bearing
    of the arc at the start. The element angularDistance specifies the
    difference in bearing from the start to the end. The sign of
    angularDistance specifies the direction of the arc, positive values
    mean the direction is clockwise from start to end looking down from
    a point vertically above the center of the arc. Drawing starts at a
    bearing of 0.0 from the ray pointing due north from the center. If
    the center is at a pole the reference direction follows the prime
    meridian starting from the pole. The interpolation is fixed as
    "circularArcCenterPointWithRadius". Since this type always describes
    a single arc, the GML attribute "numArc" is not used.
    """

    class Meta:
        name = "S100_ArcByCenterPoint"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class S100CircleByCenterPointType(S100ArcByCenterPointType):
    class Meta:
        name = "S100_CircleByCenterPointType"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    start_angle: Decimal = field(
        default=Decimal("0.0"),
        metadata={
            "name": "startAngle",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
            "min_inclusive": Decimal("0.0"),
            "max_inclusive": Decimal("360.0"),
            "fraction_digits": 1,
        },
    )
    angular_distance: S100CircleByCenterPointTypeAngularDistance = field(
        default=S100CircleByCenterPointTypeAngularDistance.VALUE_360_0,
        metadata={
            "name": "angularDistance",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )


@dataclass
class S100GmCurve(S100GmCurveType):
    """<xs:documentation xmlns:xs="http://www.w3.org/2001/XMLSchema">Curve segments with other interpolations</xs:documentation>"""

    class Meta:
        name = "S100_GM_Curve"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class S100GmPolynomialSplineType(S100GmSplineCurveType):
    """<xs:documentation xmlns:xs="http://www.w3.org/2001/XMLSchema">Type for polynomial splines</xs:documentation>"""

    class Meta:
        name = "S100_GM_PolynomialSplineType"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    derivative_at_start: list[VectorType] = field(
        default_factory=list,
        metadata={
            "name": "derivativeAtStart",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    derivative_at_end: list[VectorType] = field(
        default_factory=list,
        metadata={
            "name": "derivativeAtEnd",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    num_derivative_interior: Optional[int] = field(
        default=None,
        metadata={
            "name": "numDerivativeInterior",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "required": True,
        },
    )


@dataclass
class S100GmSplineCurve(S100GmSplineCurveType):
    class Meta:
        name = "S100_GM_SplineCurve"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class GeodesicString(GeodesicStringType):
    """A sequence of geodesic segments.

    The number of control points shall be at least two. interpolation is
    fixed as "geodesic". The content model follows the general pattern
    for the encoding of curve segments.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class GeodesicType(GeodesicStringType):
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class LineString(LineStringType):
    """A LineString is a special curve that consists of a single segment with
    linear interpolation.

    It is defined by two or more coordinate tuples, with linear
    interpolation between them. The number of direct positions in the
    list shall be at least two.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class LineStringSegment(LineStringSegmentType):
    """A LineStringSegment is a curve segment that is defined by two or more
    control points including the start and end point, with linear interpolation
    between them.

    The content model follows the general pattern for the encoding of
    curve segments.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class LinearRing(LinearRingType):
    """A LinearRing is defined by four or more coordinate tuples, with linear
    interpolation between them; the first and last coordinates shall be coincident.

    The number of direct positions in the list shall be at least four.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class MultiPoint1(MultiPointType1):
    """A gml:MultiPoint consists of one or more gml:Points.

    The members of the geometric aggregate may be specified either using
    the "standard" property (gml:pointMember) or the array property
    (gml:pointMembers). It is also valid to use both the "standard" and
    the array properties in the same collection.
    """

    class Meta:
        name = "MultiPoint"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class BridgeType(StructureObjectType):
    """(1) An elevated structure extending across or over the weather deck of a
    vessel, or part of such a structure.

    The term is sometimes modified to indicate the intended use, such as
    navigating bridge or signal bridge.  (2) A structure erected over a
    depression or an obstacle such as a body of water, railroad, etc.,
    to provide a roadway for vehicles or pedestrians.
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    geometry: list["BridgeType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class Bridle(BridleType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class BuildingType(StructureObjectType):
    """
    A free-standing self-supporting construction that is roofed, usually walled,
    and is intended for human occupancy (for example: a place of work or
    recreation) and/or habitation.
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    geometry: list["BuildingType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class CableSubmarine(CableSubmarineType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class CounterWeight(CounterWeightType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class DangerousFeature(DangerousFeatureType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class DaymarkType(EquipmentType):
    """(1) The identifying characteristics of an aid to navigation which serve to
    facilitate its recognition against a daylight viewing background.

    On those structures that do not by themselves present an adequate
    viewing area to be seen at the required distance, the aid is made
    more visible by affixing a daymark to the structure. A daymark so
    affixed has a distinctive colour and shape depending on the purpose
    of the aid. (2) An unlighted navigational mark.

    :ivar category_of_special_purpose_mark: Classification of an aid to
        navigation which signifies some special purpose.
    :ivar colour: The property possessed by an object of producing
        different sensations on the eye as a result of the way it
        reflects or emits light.
    :ivar colour_pattern: A regular repeated design containing more than
        one colour.
    :ivar elevation: The altitude of the ground level of an object,
        measured from a specified vertical datum.
    :ivar height: The value of the vertical distance to the highest
        point of the object, measured from a specified vertical datum.
    :ivar nature_of_construction: The building's primary construction
        material.
    :ivar orientation_value: The angular distance measured from true
        north to the major axis of the feature.
    :ivar status: The condition of an object at a given instant in time.
    :ivar topmark_daymark_shape: The shape a topmark or daymark
        exhibits.
    :ivar vertical_datum: The reference level used for expressing the
        vertical measurements of points on the earth's surface. Also
        called datum level, reference plane, levelling datum, datum for
        sounding reduction, datum for heights.
    :ivar vertical_length: The total vertical length of a feature.
    :ivar shape_information: Textual information about the shape of a
        non-standard topmark.
    :ivar is_slatted: -
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_special_purpose_mark: Optional[
        CategoryOfSpecialPurposeMarkType
    ] = field(
        default=None,
        metadata={
            "name": "categoryOfSpecialPurposeMark",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    colour: list[ColourType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )
    colour_pattern: list[ColourPatternType] = field(
        default_factory=list,
        metadata={
            "name": "colourPattern",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    elevation: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    nature_of_construction: list[NatureOfConstructionType] = field(
        default_factory=list,
        metadata={
            "name": "natureOfConstruction",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    orientation_value: Optional[float] = field(
        default=None,
        metadata={
            "name": "orientationValue",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    topmark_daymark_shape: Optional[TopmarkDaymarkShapeType] = field(
        default=None,
        metadata={
            "name": "topmarkDaymarkShape",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    vertical_datum: Optional[VerticalDatumType] = field(
        default=None,
        metadata={
            "name": "verticalDatum",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_length: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    shape_information: Optional[ShapeInformationType] = field(
        default=None,
        metadata={
            "name": "shapeInformation",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    is_slatted: Optional[bool] = field(
        default=None,
        metadata={
            "name": "isSlatted",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    geometry: list["DaymarkType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class ElectronicAton(ElectronicAtonType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class EnvironmentObservationEquipmentType(EquipmentType):
    """
    A sensor used to observe the environment.

    :ivar height: The value of the vertical distance to the highest
        point of the object, measured from a specified vertical datum.
    :ivar status: The condition of an object at a given instant in time.
    :ivar type_of_environmental_observation_equipment: Type of sensor
        used to observe the environment. For example Anemometer, fog
        monitor, etc.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    type_of_environmental_observation_equipment: list[str] = field(
        default_factory=list,
        metadata={
            "name": "typeOfEnvironmentalObservationEquipment",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )
    geometry: list["EnvironmentObservationEquipmentType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class Equipment(EquipmentType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class FogSignalType(EquipmentType):
    """A warning signal transmitted by a vessel, or aid to navigation, during
    periods of low visibility.

    Also, the device producing such a signal.

    :ivar category_of_fog_signal: Classification of the various means of
        generating the fog signal.
    :ivar signal_frequency: The frequency of a signal.
    :ivar signal_generation: The mechanism used to generate a fog or
        light signal.
    :ivar signal_group: The number of signals, the combination of
        signals or the morse character(s) within one period of full
        sequence.
    :ivar signal_output: Strength of signal output.
    :ivar signal_period: The time occupied by an entire cycle of
        intervals of light and eclipse.
    :ivar status: The condition of an object at a given instant in time.
    :ivar value_of_maximum_range: The extreme distance at which an
        feature can be seen or a signal detected.
    :ivar signal_sequence: The sequence of times occupied by intervals
        of light and eclipse for all light characteristics.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_fog_signal: Optional[CategoryOfFogSignalType] = field(
        default=None,
        metadata={
            "name": "categoryOfFogSignal",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    signal_frequency: Optional[int] = field(
        default=None,
        metadata={
            "name": "signalFrequency",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    signal_generation: Optional[SignalGenerationType] = field(
        default=None,
        metadata={
            "name": "signalGeneration",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    signal_group: Optional[str] = field(
        default=None,
        metadata={
            "name": "signalGroup",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    signal_output: Optional[float] = field(
        default=None,
        metadata={
            "name": "signalOutput",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    signal_period: Optional[float] = field(
        default=None,
        metadata={
            "name": "signalPeriod",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    value_of_maximum_range: Optional[float] = field(
        default=None,
        metadata={
            "name": "valueOfMaximumRange",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    signal_sequence: Optional[SignalSequenceType] = field(
        default=None,
        metadata={
            "name": "signalSequence",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["FogSignalType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class GenericBeaconType(StructureObjectType):
    """A fixed artificial navigation mark that can be recognized by its shape,
    colour, pattern, topmark or light character, or a combination of these.

    It may carry various additional aids to navigation.

    :ivar beacon_shape: Describes the characteristic geometric form of
        the beacon.
    :ivar colour: The property possessed by an object of producing
        different sensations on the eye as a result of the way it
        reflects or emits light.
    :ivar colour_pattern: A regular repeated design containing more than
        one colour.
    :ivar elevation: The altitude of the ground level of an object,
        measured from a specified vertical datum.
    :ivar height: The value of the vertical distance to the highest
        point of the object, measured from a specified vertical datum.
    :ivar marks_navigational_system_of: The system of navigational
        buoyage a region complies with.
    :ivar nature_of_construction: The building's primary construction
        material.
    :ivar radar_conspicuous: A feature which returns a strong radar
        echo.
    :ivar status: The condition of an object at a given instant in time.
    :ivar vertical_length: The total vertical length of a feature.
    :ivar visual_prominence: The extent to which a feature, either
        natural or artificial, is visible from seaward.
    :ivar vertical_accuracy: -
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    beacon_shape: Optional[BeaconShapeType] = field(
        default=None,
        metadata={
            "name": "beaconShape",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    colour: list[ColourType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )
    colour_pattern: list[ColourPatternType] = field(
        default_factory=list,
        metadata={
            "name": "colourPattern",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    elevation: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    marks_navigational_system_of: Optional[MarksNavigationalSystemOfType] = (
        field(
            default=None,
            metadata={
                "name": "marksNavigationalSystemOf",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
    )
    nature_of_construction: list[NatureOfConstructionType] = field(
        default_factory=list,
        metadata={
            "name": "natureOfConstruction",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    radar_conspicuous: Optional[bool] = field(
        default=None,
        metadata={
            "name": "radarConspicuous",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_length: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    visual_prominence: Optional[VisualProminenceType] = field(
        default=None,
        metadata={
            "name": "visualProminence",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_accuracy: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalAccuracy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class GenericBuoyType(StructureObjectType):
    """
    A floating object moored to the bottom in a particular (charted) place, as an
    aid to navigation or for other specific purposes.

    :ivar buoy_shape: The principal shape and/or design of a buoy.
    :ivar colour: The property possessed by an object of producing
        different sensations on the eye as a result of the way it
        reflects or emits light.
    :ivar colour_pattern: A regular repeated design containing more than
        one colour.
    :ivar marks_navigational_system_of: The system of navigational
        buoyage a region complies with.
    :ivar nature_of_construction: The building's primary construction
        material.
    :ivar radar_conspicuous: A feature which returns a strong radar
        echo.
    :ivar status: The condition of an object at a given instant in time.
    :ivar type_of_buoy: Type equipment used as a buoy in a particular
        installation.
    :ivar vertical_length: The total vertical length of a feature.
    :ivar vertical_accuracy: -
    :ivar topmark_part:
    :ivar shackle_to_buoy_connected:
    :ivar buoy_hangs:
    :ivar buoya_attached:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    buoy_shape: Optional[BuoyShapeType] = field(
        default=None,
        metadata={
            "name": "buoyShape",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    colour: list[ColourType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )
    colour_pattern: list[ColourPatternType] = field(
        default_factory=list,
        metadata={
            "name": "colourPattern",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    marks_navigational_system_of: Optional[MarksNavigationalSystemOfType] = (
        field(
            default=None,
            metadata={
                "name": "marksNavigationalSystemOf",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
    )
    nature_of_construction: list[NatureOfConstructionType] = field(
        default_factory=list,
        metadata={
            "name": "natureOfConstruction",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    radar_conspicuous: Optional[bool] = field(
        default=None,
        metadata={
            "name": "radarConspicuous",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    type_of_buoy: Optional[str] = field(
        default=None,
        metadata={
            "name": "typeOfBuoy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_length: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_accuracy: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalAccuracy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    topmark_part: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "topmarkPart",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    shackle_to_buoy_connected: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "shackleToBuoyConnected",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    buoy_hangs: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "buoyHangs",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    buoya_attached: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "buoyaAttached",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class GenericLightType(EquipmentType):
    """-

    :ivar height: The value of the vertical distance to the highest
        point of the object, measured from a specified vertical datum.
    :ivar status: The condition of an object at a given instant in time.
    :ivar vertical_datum: The reference level used for expressing the
        vertical measurements of points on the earth's surface. Also
        called datum level, reference plane, levelling datum, datum for
        sounding reduction, datum for heights.
    :ivar vertical_length: The total vertical length of a feature.
    :ivar effective_intensity: The luminous intensity of a fictitious
        juxtaposed steady-burning point light source that would appear
        to exhibit a luminosity equal to that of the rhythmic point
        light source it describes. The apparent reduction in intensity
        of the rhythmic light is subjective and is due to the nature of
        the response of the eye of the observer.
    :ivar peak_intensity: The maximum luminous intensity of a light
        during its flash cycle.
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_datum: Optional[VerticalDatumType] = field(
        default=None,
        metadata={
            "name": "verticalDatum",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_length: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    effective_intensity: Optional[float] = field(
        default=None,
        metadata={
            "name": "effectiveIntensity",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    peak_intensity: Optional[float] = field(
        default=None,
        metadata={
            "name": "peakIntensity",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )


@dataclass
class LightFloatType(StructureObjectType):
    """
    A boat-like structure used instead of a light buoy in waters where strong
    streams or currents are experienced, or when a greater elevation than that of a
    light buoy is necessary.

    :ivar colour: The property possessed by an object of producing
        different sensations on the eye as a result of the way it
        reflects or emits light.
    :ivar colour_pattern: A regular repeated design containing more than
        one colour.
    :ivar horizontal_length: A measurement of the longer of two linear
        axis.
    :ivar horizontal_width: A measurement of the shorter of two linear
        axis.
    :ivar manned_structure: An expression of the feature being
        permanently manned or not.
    :ivar nature_of_construction: The building's primary construction
        material.
    :ivar radar_conspicuous: A feature which returns a strong radar
        echo.
    :ivar status: The condition of an object at a given instant in time.
    :ivar vertical_length: The total vertical length of a feature.
    :ivar visual_prominence: The extent to which a feature, either
        natural or artificial, is visible from seaward.
    :ivar vertical_accuracy: -
    :ivar horizontal_accuracy: -
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    colour: list[ColourType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )
    colour_pattern: list[ColourPatternType] = field(
        default_factory=list,
        metadata={
            "name": "colourPattern",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    horizontal_length: Optional[float] = field(
        default=None,
        metadata={
            "name": "horizontalLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    horizontal_width: Optional[float] = field(
        default=None,
        metadata={
            "name": "horizontalWidth",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    manned_structure: Optional[bool] = field(
        default=None,
        metadata={
            "name": "mannedStructure",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    nature_of_construction: list[NatureOfConstructionType] = field(
        default_factory=list,
        metadata={
            "name": "natureOfConstruction",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    radar_conspicuous: Optional[bool] = field(
        default=None,
        metadata={
            "name": "radarConspicuous",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_length: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    visual_prominence: Optional[VisualProminenceType] = field(
        default=None,
        metadata={
            "name": "visualProminence",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_accuracy: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalAccuracy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    horizontal_accuracy: Optional[float] = field(
        default=None,
        metadata={
            "name": "horizontalAccuracy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["LightFloatType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class LightVesselType(StructureObjectType):
    """A distinctively marked vessel anchored or moored at a charted point, to
    serve as an aid to navigation.

    By night, it displays a characteristic light(s) and is usually
    equipped with other devices, such as fog signal, submarine sound
    signal, and radio-beacon, to assist navigation.

    :ivar colour: The property possessed by an object of producing
        different sensations on the eye as a result of the way it
        reflects or emits light.
    :ivar colour_pattern: A regular repeated design containing more than
        one colour.
    :ivar horizontal_length: A measurement of the longer of two linear
        axis.
    :ivar horizontal_width: A measurement of the shorter of two linear
        axis.
    :ivar manned_structure: An expression of the feature being
        permanently manned or not.
    :ivar nature_of_construction: The building's primary construction
        material.
    :ivar radar_conspicuous: A feature which returns a strong radar
        echo.
    :ivar status: The condition of an object at a given instant in time.
    :ivar vertical_length: The total vertical length of a feature.
    :ivar visual_prominence: The extent to which a feature, either
        natural or artificial, is visible from seaward.
    :ivar vertical_accuracy: -
    :ivar horizontal_accuracy: -
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    colour: list[ColourType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )
    colour_pattern: list[ColourPatternType] = field(
        default_factory=list,
        metadata={
            "name": "colourPattern",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    horizontal_length: Optional[float] = field(
        default=None,
        metadata={
            "name": "horizontalLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    horizontal_width: Optional[float] = field(
        default=None,
        metadata={
            "name": "horizontalWidth",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    manned_structure: Optional[bool] = field(
        default=None,
        metadata={
            "name": "mannedStructure",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    nature_of_construction: list[NatureOfConstructionType] = field(
        default_factory=list,
        metadata={
            "name": "natureOfConstruction",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    radar_conspicuous: Optional[bool] = field(
        default=None,
        metadata={
            "name": "radarConspicuous",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_length: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    visual_prominence: Optional[VisualProminenceType] = field(
        default=None,
        metadata={
            "name": "visualProminence",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_accuracy: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalAccuracy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    horizontal_accuracy: Optional[float] = field(
        default=None,
        metadata={
            "name": "horizontalAccuracy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["LightVesselType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class MooringShackle(MooringShackleType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class PhysicalAisaidToNavigationType(ElectronicAtonType):
    """
    An Automatic Identification System (AIS) message 21 transmitted from a physical
    Aid to Navigation, or transmitted from an AIS station for an Aid to Navigation
    which physically exists.

    :ivar category_of_physical_aisaid_to_navigation: A classification of
        AIS AtoNs that correspond to an actual, physical Aid to
        Navigation at a real-world location.
    :ivar physical_aisbroadcasts:
    :ivar geometry:
    """

    class Meta:
        name = "PhysicalAISAidToNavigationType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_physical_aisaid_to_navigation: Optional[
        CategoryOfPhysicalAisaidToNavigationType
    ] = field(
        default=None,
        metadata={
            "name": "CategoryOfPhysicalAISAidToNavigation",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    physical_aisbroadcasts: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "physicalAISbroadcasts",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["PhysicalAisaidToNavigationType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class PileType(StructureObjectType):
    """
    A long heavy timber or section of steel, wood, concrete, etc., forced into the
    earth or sea floor to serve as a support, as for a pier, or to resist lateral
    pressure; or as a free standing pole within a marine environment.

    :ivar category_of_pile: Classification of pile, driven into the
        earth as a foundation or support for a structure.
    :ivar colour: The property possessed by an object of producing
        different sensations on the eye as a result of the way it
        reflects or emits light.
    :ivar colour_pattern: A regular repeated design containing more than
        one colour.
    :ivar height: The value of the vertical distance to the highest
        point of the object, measured from a specified vertical datum.
    :ivar vertical_datum: The reference level used for expressing the
        vertical measurements of points on the earth's surface. Also
        called datum level, reference plane, levelling datum, datum for
        sounding reduction, datum for heights.
    :ivar vertical_length: The total vertical length of a feature.
    :ivar visual_prominence: The extent to which a feature, either
        natural or artificial, is visible from seaward.
    :ivar vertical_accuracy: -
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_pile: Optional[CategoryOfPileType] = field(
        default=None,
        metadata={
            "name": "categoryOfPile",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    colour: list[ColourType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    colour_pattern: list[ColourPatternType] = field(
        default_factory=list,
        metadata={
            "name": "colourPattern",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_datum: Optional[VerticalDatumType] = field(
        default=None,
        metadata={
            "name": "verticalDatum",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_length: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    visual_prominence: Optional[VisualProminenceType] = field(
        default=None,
        metadata={
            "name": "visualProminence",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_accuracy: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalAccuracy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["PileType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class PowerSourceType(EquipmentType):
    """-

    :ivar category_of_power_source: -
    :ivar status: The condition of an object at a given instant in time.
    :ivar manufacturer: -
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_power_source: Optional[CategoryOfPowerSourceType] = field(
        default=None,
        metadata={
            "name": "CategoryOfPowerSource",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    manufacturer: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["PowerSourceType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class RadarReflectorType(EquipmentType):
    """
    A device capable of, or intended for, reflecting radar signals.

    :ivar height: The value of the vertical distance to the highest
        point of the object, measured from a specified vertical datum.
    :ivar status: The condition of an object at a given instant in time.
    :ivar vertical_datum: The reference level used for expressing the
        vertical measurements of points on the earth's surface. Also
        called datum level, reference plane, levelling datum, datum for
        sounding reduction, datum for heights.
    :ivar vertical_accuracy: -
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_datum: Optional[VerticalDatumType] = field(
        default=None,
        metadata={
            "name": "verticalDatum",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_accuracy: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalAccuracy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["RadarReflectorType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class RadarTransponderBeaconType(EquipmentType):
    """
    A transponder beacon transmitting a coded signal on radar frequency, permitting
    an interrogating craft to determine the bearing and range of the transponder.

    :ivar category_of_radar_transponder_beacon: Classification of radar
        transponder beacon based on functionality.
    :ivar radar_wave_length: The distance between two successive peaks
        (or other points of identical phase) on an electromagnetic wave
        in the radar band of the electromagnetic spectrum.
    :ivar signal_group: The number of signals, the combination of
        signals or the morse character(s) within one period of full
        sequence.
    :ivar status: The condition of an object at a given instant in time.
    :ivar value_of_nominal_range: The luminous range of a light in a
        homogenous atmosphere in which the meteorological visibility is
        10 sea miles.
    :ivar manufacturer: -
    :ivar sector_limit_one: A sector is the part of a circle between two
        straight lines drawn from the centre to the circumference.
        Sector limit one specifies the first limit of the sector. The
        order of sector limit one and sector limit two is clockwise
        around the central feature (for example a light).
    :ivar sector_limit_two: A sector is the part of a circle between two
        straight lines drawn from the centre to the circumference.
        Sector limit two specifies the second limit of the sector. The
        order of sector limit one and sector limit two is clockwise
        around the central feature (for example a light).
    :ivar signal_sequence: The sequence of times occupied by intervals
        of light and eclipse for all light characteristics.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_radar_transponder_beacon: Optional[
        CategoryOfRadarTransponderBeaconType
    ] = field(
        default=None,
        metadata={
            "name": "categoryOfRadarTransponderBeacon",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    radar_wave_length: Optional[RadarWaveLengthType] = field(
        default=None,
        metadata={
            "name": "radarWaveLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    signal_group: Optional[str] = field(
        default=None,
        metadata={
            "name": "signalGroup",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    value_of_nominal_range: Optional[float] = field(
        default=None,
        metadata={
            "name": "valueOfNominalRange",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    manufacturer: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    sector_limit_one: Optional[SectorLimitOneType] = field(
        default=None,
        metadata={
            "name": "sectorLimitOne",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    sector_limit_two: Optional[SectorLimitTwoType] = field(
        default=None,
        metadata={
            "name": "sectorLimitTwo",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    signal_sequence: Optional[SignalSequenceType] = field(
        default=None,
        metadata={
            "name": "signalSequence",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["RadarTransponderBeaconType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class RadioStationType(EquipmentType):
    """A place equipped to transmit radio waves.

    Such a station may be either stationary or mobile, and may also be
    provided with a radio receiver.

    :ivar category_of_radio_station: Classification of radio services
        offered by a radio station.
    :ivar estimated_range_of_transmission: The estimated range of a non-
        optical electromagnetic transmission.
    :ivar status: The condition of an object at a given instant in time.
    :ivar physical_aisbroadcast_by:
    :ivar synthetic_aisbroadcast_by:
    :ivar virtual_aisbroadcast_by:
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_radio_station: Optional[CategoryOfRadioStationType] = field(
        default=None,
        metadata={
            "name": "categoryOfRadioStation",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    estimated_range_of_transmission: Optional[float] = field(
        default=None,
        metadata={
            "name": "estimatedRangeOfTransmission",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    status: Optional[StatusType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    physical_aisbroadcast_by: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "physicalAISbroadcastBy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    synthetic_aisbroadcast_by: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "syntheticAISbroadcastBy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    virtual_aisbroadcast_by: Optional[ReferenceType] = field(
        default=None,
        metadata={
            "name": "virtualAISbroadcastBy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["RadioStationType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class RetroreflectorType(EquipmentType):
    """A means of distinguishing unlighted marks at night.

    Retro-reflective material is secured to the mark in a particular
    pattern to reflect back light.

    :ivar colour: The property possessed by an object of producing
        different sensations on the eye as a result of the way it
        reflects or emits light.
    :ivar colour_pattern: A regular repeated design containing more than
        one colour.
    :ivar marks_navigational_system_of: The system of navigational
        buoyage a region complies with.
    :ivar status: The condition of an object at a given instant in time.
    :ivar vertical_datum: The reference level used for expressing the
        vertical measurements of points on the earth's surface. Also
        called datum level, reference plane, levelling datum, datum for
        sounding reduction, datum for heights.
    :ivar height: The value of the vertical distance to the highest
        point of the object, measured from a specified vertical datum.
    :ivar vertical_accuracy: -
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    colour: list[ColourType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    colour_pattern: list[ColourPatternType] = field(
        default_factory=list,
        metadata={
            "name": "colourPattern",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    marks_navigational_system_of: Optional[MarksNavigationalSystemOfType] = (
        field(
            default=None,
            metadata={
                "name": "marksNavigationalSystemOf",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_datum: Optional[VerticalDatumType] = field(
        default=None,
        metadata={
            "name": "verticalDatum",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_accuracy: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalAccuracy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["RetroreflectorType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class SinkerAnchor(SinkerAnchorType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class StructureObject(StructureObjectType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class Swivel(SwivelType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class SyntheticAisaidToNavigationType(ElectronicAtonType):
    """-

    :ivar category_of_synthetic_aisaidto_navigation: -
    :ivar virtual_aisaid_to_navigation_type: A purpose of a virtual AIS
        Aid to Navigation.
    :ivar synthetic_aisbroadcasts:
    :ivar geometry:
    """

    class Meta:
        name = "SyntheticAISAidToNavigationType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_synthetic_aisaidto_navigation: Optional[
        CategoryOfSyntheticAisaidtoNavigationType
    ] = field(
        default=None,
        metadata={
            "name": "categoryOfSyntheticAISAidtoNavigation",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    virtual_aisaid_to_navigation_type: Optional[
        VirtualAisaidToNavigationTypeType
    ] = field(
        default=None,
        metadata={
            "name": "virtualAISAidToNavigationType",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    synthetic_aisbroadcasts: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "syntheticAISbroadcasts",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["SyntheticAisaidToNavigationType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class Topmark(TopmarkType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class VirtualAisaidToNavigationType(ElectronicAtonType):
    """
    An Automatic Identification System (AIS) message 21 transmitted from an AIS
    station to simulate on navigation systems an Aid to Navigation which does not
    physically exist.

    :ivar virtual_aisaid_to_navigation_type: A purpose of a virtual AIS
        Aid to Navigation.
    :ivar virtual_aisbroadcasts:
    :ivar geometry:
    """

    class Meta:
        name = "VirtualAISAidToNavigationType"
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    virtual_aisaid_to_navigation_type: Optional[
        VirtualAisaidToNavigationTypeType
    ] = field(
        default=None,
        metadata={
            "name": "virtualAISAidToNavigationType",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    virtual_aisbroadcasts: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "virtualAISbroadcasts",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["VirtualAisaidToNavigationType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class MultiPoint2(MultiPointType2):
    class Meta:
        name = "MultiPoint"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class S100CircleByCenterPoint(S100CircleByCenterPointType):
    """An S100_CircleByCenterPoint is an S100_ArcByCenterPoint with angular
    distance +/- 360.0 degrees to form a full circle.

    Angular distance is assumed to be +360.0 degrees if it is missing.
    The interpolation is fixed as "circularArcCenterPointWithRadius".
    This representation can be used only in 2D.
    """

    class Meta:
        name = "S100_CircleByCenterPoint"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class S100GmPolynomialSpline(S100GmPolynomialSplineType):
    class Meta:
        name = "S100_GM_PolynomialSpline"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class Geodesic(GeodesicType):
    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class LinearRingPropertyType:
    """
    A property with the content model of gml:LinearRingPropertyType encapsulates a
    linear ring to represent a component of a surface boundary.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    linear_ring: Optional[LinearRing] = field(
        default=None,
        metadata={
            "name": "LinearRing",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
            "required": True,
        },
    )


@dataclass
class Bridge(BridgeType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class Building(BuildingType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class CardinalBeaconType(GenericBeaconType):
    """A cardinal beacon is used in conjunction with the compass to indicate where
    the mariner may find the best navigable water.

    It is placed in one of the four quadrants (North, East, South and
    West), bounded by inter-cardinal bearings from the point marked.

    :ivar category_of_cardinal_mark: The four quadrants (north, east,
        south and west) are bounded by the true bearings NW-NE, NE-SE,
        SE-SW and SW-NW taken from the point of interest. A cardinal
        mark is named after the quadrant in which it is placed. The name
        of the cardinal mark indicates that it should be passed to the
        named side of the mark.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_cardinal_mark: Optional[CategoryOfCardinalMarkType] = field(
        default=None,
        metadata={
            "name": "categoryOfCardinalMark",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    geometry: list["CardinalBeaconType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class CardinalBuoyType(GenericBuoyType):
    """A cardinal buoy is used in conjunction with the compass to indicate where
    the mariner may find the best navigable water.

    It is placed in one of the four quadrants (North, East, South and
    West), bounded by inter-cardinal bearings from the point marked.

    :ivar category_of_cardinal_mark: The four quadrants (north, east,
        south and west) are bounded by the true bearings NW-NE, NE-SE,
        SE-SW and SW-NW taken from the point of interest. A cardinal
        mark is named after the quadrant in which it is placed. The name
        of the cardinal mark indicates that it should be passed to the
        named side of the mark.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_cardinal_mark: Optional[CategoryOfCardinalMarkType] = field(
        default=None,
        metadata={
            "name": "categoryOfCardinalMark",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    geometry: list["CardinalBuoyType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class Daymark(DaymarkType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class EmergencyWreckMarkingBuoyType(GenericBuoyType):
    """An emergency wreck marking buoy is a buoy moored on or above a new wreck,
    designed to provide a prominent (both visual and radio) and easily identifiable
    temporary (24-72 hours) first response.

    (IHO Registry)
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    geometry: list["EmergencyWreckMarkingBuoyType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class EnvironmentObservationEquipment(EnvironmentObservationEquipmentType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class FogSignal(FogSignalType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class GenericBeacon(GenericBeaconType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class GenericBuoy(GenericBuoyType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class GenericLight(GenericLightType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class InstallationBuoyType(GenericBuoyType):
    """A buoy is a floating object moored to the bottom in a particular place, as
    an aid to navigation or for other specific purposes.

    (IHO Dictionary, S-32, 5th Edition, 565). An installation buoy is a
    buoy used for loading tankers with gas or oil. (IHO Chart
    Specifications, M-4)

    :ivar category_of_installation_buoy: Classification of fixed
        installation buoy.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_installation_buoy: Optional[CategoryOfInstallationBuoyType] = (
        field(
            default=None,
            metadata={
                "name": "categoryOfInstallationBuoy",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
                "required": True,
            },
        )
    )
    geometry: list["InstallationBuoyType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class IsolatedDangerBeaconType(GenericBeaconType):
    """
    An isolated danger beacon is a beacon erected on an isolated danger of limited
    extent, which has navigable water all around it.
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    geometry: list["IsolatedDangerBeaconType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class IsolatedDangerBuoyType(GenericBuoyType):
    """
    An isolated danger buoy is a buoy moored on or above an isolated danger of
    limited extent, which has navigable water all around it.
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    geometry: list["IsolatedDangerBuoyType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class LateralBeaconType(GenericBeaconType):
    """A lateral beacon is used to indicate the port or starboard hand side of the
    route to be followed.

    They are generally used for well defined channels and are used in
    conjunction with a conventional direction of buoyage.

    :ivar category_of_lateral_mark: Classification of lateral marks in
        the IALA Buoyage System.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_lateral_mark: Optional[CategoryOfLateralMarkType] = field(
        default=None,
        metadata={
            "name": "categoryOfLateralMark",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    geometry: list["LateralBeaconType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class LateralBuoyType(GenericBuoyType):
    """A lateral buoy is used to indicate the port or starboard hand side of the
    route to be followed.

    They are generally used for well-defined channels and are used in
    conjunction with a conventional direction of buoyage.

    :ivar category_of_lateral_mark: Classification of lateral marks in
        the IALA Buoyage System.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_lateral_mark: Optional[CategoryOfLateralMarkType] = field(
        default=None,
        metadata={
            "name": "categoryOfLateralMark",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    geometry: list["LateralBuoyType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class LightAirObstructionType(GenericLightType):
    """
    An air obstruction light is a light marking an obstacle which constitutes a
    danger to air navigation.

    :ivar exhibition_condition_of_light: The outward display of the
        light.
    :ivar light_visibility: The specific visibility of a light, with
        respect to the light's intensity and ease of recognition.
    :ivar value_of_nominal_range: The luminous range of a light in a
        homogenous atmosphere in which the meteorological visibility is
        10 sea miles.
    :ivar multiplicity_of_features: The number of features of identical
        character that exist as a colocated group.
    :ivar rhythm_of_light: The sequence of times occupied by intervals
        of light/sound and eclipse/silence for all light characteristics
        or sound signals.
    :ivar flare_bearing: The bearing about which the light flare symbol
        is rotated to be displayed in ECDIS.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    exhibition_condition_of_light: list[ExhibitionConditionOfLightType] = (
        field(
            default_factory=list,
            metadata={
                "name": "exhibitionConditionOfLight",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
    )
    light_visibility: list[LightVisibilityType] = field(
        default_factory=list,
        metadata={
            "name": "lightVisibility",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    value_of_nominal_range: Optional[float] = field(
        default=None,
        metadata={
            "name": "valueOfNominalRange",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    multiplicity_of_features: Optional[MultiplicityOfFeaturesType] = field(
        default=None,
        metadata={
            "name": "multiplicityOfFeatures",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    rhythm_of_light: Optional[RhythmOfLightType] = field(
        default=None,
        metadata={
            "name": "rhythmOfLight",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    flare_bearing: Optional[int] = field(
        default=None,
        metadata={
            "name": "flareBearing",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["LightAirObstructionType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class LightAllAroundType(GenericLightType):
    """
    An all around light is a light that is visible over the whole horizon of
    interest to marine navigation and having no change in the characteristics of
    the light.

    :ivar colour: The property possessed by an object of producing
        different sensations on the eye as a result of the way it
        reflects or emits light.
    :ivar category_of_light: Classification of different light types.
    :ivar exhibition_condition_of_light: The outward display of the
        light.
    :ivar light_visibility: The specific visibility of a light, with
        respect to the light's intensity and ease of recognition.
    :ivar major_light: A statement expressing if a light is considered
        to be a major light in terms of ECDIS display in a particular
        area.
    :ivar marks_navigational_system_of: The system of navigational
        buoyage a region complies with.
    :ivar signal_generation: The mechanism used to generate a fog or
        light signal.
    :ivar value_of_nominal_range: The luminous range of a light in a
        homogenous atmosphere in which the meteorological visibility is
        10 sea miles.
    :ivar multiplicity_of_features: The number of features of identical
        character that exist as a colocated group.
    :ivar rhythm_of_light: The sequence of times occupied by intervals
        of light/sound and eclipse/silence for all light characteristics
        or sound signals.
    :ivar flare_bearing: The bearing about which the light flare symbol
        is rotated to be displayed in ECDIS.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    colour: list[ColourType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )
    category_of_light: list[CategoryOfLightType] = field(
        default_factory=list,
        metadata={
            "name": "categoryOfLight",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    exhibition_condition_of_light: Optional[ExhibitionConditionOfLightType] = (
        field(
            default=None,
            metadata={
                "name": "exhibitionConditionOfLight",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
    )
    light_visibility: Optional[LightVisibilityType] = field(
        default=None,
        metadata={
            "name": "lightVisibility",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    major_light: Optional[bool] = field(
        default=None,
        metadata={
            "name": "majorLight",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    marks_navigational_system_of: Optional[MarksNavigationalSystemOfType] = (
        field(
            default=None,
            metadata={
                "name": "marksNavigationalSystemOf",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
    )
    signal_generation: Optional[SignalGenerationType] = field(
        default=None,
        metadata={
            "name": "signalGeneration",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    value_of_nominal_range: Optional[float] = field(
        default=None,
        metadata={
            "name": "valueOfNominalRange",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    multiplicity_of_features: Optional[MultiplicityOfFeaturesType] = field(
        default=None,
        metadata={
            "name": "multiplicityOfFeatures",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    rhythm_of_light: Optional[RhythmOfLightType] = field(
        default=None,
        metadata={
            "name": "rhythmOfLight",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    flare_bearing: Optional[int] = field(
        default=None,
        metadata={
            "name": "flareBearing",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["LightAllAroundType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class LightFloat(LightFloatType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class LightFogDetectorType(GenericLightType):
    """
    A fog detector light is a light used to automatically determine conditions of
    visibility which warrant the turning on or off of a sound signal.

    :ivar signal_generation: The mechanism used to generate a fog or
        light signal.
    :ivar rhythm_of_light: The sequence of times occupied by intervals
        of light/sound and eclipse/silence for all light characteristics
        or sound signals.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    signal_generation: Optional[SignalGenerationType] = field(
        default=None,
        metadata={
            "name": "signalGeneration",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    rhythm_of_light: Optional[RhythmOfLightType] = field(
        default=None,
        metadata={
            "name": "rhythmOfLight",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    geometry: list["LightFogDetectorType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class LightSectoredType(GenericLightType):
    """
    A light presenting different appearances (in particular, different colours)
    over various parts of the horizon of interest to maritime navigation.

    :ivar colour: The property possessed by an object of producing
        different sensations on the eye as a result of the way it
        reflects or emits light.
    :ivar category_of_light: Classification of different light types.
    :ivar exhibition_condition_of_light: The outward display of the
        light.
    :ivar marks_navigational_system_of: The system of navigational
        buoyage a region complies with.
    :ivar signal_generation: The mechanism used to generate a fog or
        light signal.
    :ivar obscured_sector: -
    :ivar sector_characteristics: Describes the characteristics of a
        light sector.
    :ivar multiplicity_of_features: The number of features of identical
        character that exist as a colocated group.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    colour: list[ColourType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )
    category_of_light: list[CategoryOfLightType] = field(
        default_factory=list,
        metadata={
            "name": "categoryOfLight",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    exhibition_condition_of_light: Optional[ExhibitionConditionOfLightType] = (
        field(
            default=None,
            metadata={
                "name": "exhibitionConditionOfLight",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
    )
    marks_navigational_system_of: Optional[MarksNavigationalSystemOfType] = (
        field(
            default=None,
            metadata={
                "name": "marksNavigationalSystemOf",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
    )
    signal_generation: Optional[SignalGenerationType] = field(
        default=None,
        metadata={
            "name": "signalGeneration",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    obscured_sector: list[ObscuredSectorType] = field(
        default_factory=list,
        metadata={
            "name": "ObscuredSector",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    sector_characteristics: list[SectorCharacteristicsType] = field(
        default_factory=list,
        metadata={
            "name": "sectorCharacteristics",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )
    multiplicity_of_features: Optional[MultiplicityOfFeaturesType] = field(
        default=None,
        metadata={
            "name": "multiplicityOfFeatures",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["LightSectoredType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class LightVessel(LightVesselType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class MooringBuoyType(GenericBuoyType):
    """The equipment or structure used to secure a vessel.

    (IHO Registry)
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    geometry: list["MooringBuoyType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class PhysicalAisaidToNavigation(PhysicalAisaidToNavigationType):
    class Meta:
        name = "PhysicalAISAidToNavigation"
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class Pile(PileType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class PowerSource(PowerSourceType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class RadarReflector(RadarReflectorType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class RadarTransponderBeacon(RadarTransponderBeaconType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class RadioStation(RadioStationType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class Retroreflector(RetroreflectorType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class SafeWaterBeaconType(GenericBeaconType):
    """
    A safe water beacon is used to indicate that there is navigable water around
    the mark.
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    geometry: list["SafeWaterBeaconType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class SafeWaterBuoyType(GenericBuoyType):
    """
    A safe water buoy is used to indicate that there is navigable water around the
    mark.
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    geometry: list["SafeWaterBuoyType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class SpecialPurposeGeneralBeaconType(GenericBeaconType):
    """
    A special purpose beacon is primarily used to indicate an area or feature, the
    nature of which is apparent from reference to a chart, Sailing Directions or
    Notices to Mariners.

    :ivar category_of_special_purpose_mark: Classification of an aid to
        navigation which signifies some special purpose.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_special_purpose_mark: list[
        CategoryOfSpecialPurposeMarkType
    ] = field(
        default_factory=list,
        metadata={
            "name": "categoryOfSpecialPurposeMark",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )
    geometry: list["SpecialPurposeGeneralBeaconType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class SpecialPurposeGeneralBuoyType(GenericBuoyType):
    """
    A special purpose buoy is primarily used to indicate an area or feature, the
    nature of which is apparent from reference to a chart, Sailing Directions or
    Notices to Mariners.

    :ivar category_of_special_purpose_mark: Classification of an aid to
        navigation which signifies some special purpose.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_special_purpose_mark: list[
        CategoryOfSpecialPurposeMarkType
    ] = field(
        default_factory=list,
        metadata={
            "name": "categoryOfSpecialPurposeMark",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )
    geometry: list["SpecialPurposeGeneralBuoyType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class SyntheticAisaidToNavigation(SyntheticAisaidToNavigationType):
    class Meta:
        name = "SyntheticAISAidToNavigation"
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class VirtualAisaidToNavigation(VirtualAisaidToNavigationType):
    class Meta:
        name = "VirtualAISAidToNavigation"
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class MultiPointPropertyType(S100SpatialAttributeType):
    """
    MultiPoint property using the S-100 multipoint type.
    """

    class Meta:
        target_namespace = "http://www.iho.int/s100gml/5.0"

    multi_point: Optional[MultiPoint2] = field(
        default=None,
        metadata={
            "name": "MultiPoint",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )


@dataclass
class CurveSegmentArrayPropertyType:
    """
    Gml:CurveSegmentArrayPropertyType is a container for an array of curve
    segments.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    s100_gm_curve: list[S100GmCurve] = field(
        default_factory=list,
        metadata={
            "name": "S100_GM_Curve",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "sequence": 1,
        },
    )
    s100_gm_polynomial_spline: list[S100GmPolynomialSpline] = field(
        default_factory=list,
        metadata={
            "name": "S100_GM_PolynomialSpline",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "sequence": 1,
        },
    )
    s100_gm_spline_curve: list[S100GmSplineCurve] = field(
        default_factory=list,
        metadata={
            "name": "S100_GM_SplineCurve",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "sequence": 1,
        },
    )
    s100_circle_by_center_point: list[S100CircleByCenterPoint] = field(
        default_factory=list,
        metadata={
            "name": "S100_CircleByCenterPoint",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "sequence": 1,
        },
    )
    s100_arc_by_center_point: list[S100ArcByCenterPoint] = field(
        default_factory=list,
        metadata={
            "name": "S100_ArcByCenterPoint",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
            "sequence": 1,
        },
    )
    geodesic: list[Geodesic] = field(
        default_factory=list,
        metadata={
            "name": "Geodesic",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
            "sequence": 1,
        },
    )
    geodesic_string: list[GeodesicString] = field(
        default_factory=list,
        metadata={
            "name": "GeodesicString",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
            "sequence": 1,
        },
    )
    line_string_segment: list[LineStringSegment] = field(
        default_factory=list,
        metadata={
            "name": "LineStringSegment",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
            "sequence": 1,
        },
    )


@dataclass
class CardinalBeacon(CardinalBeaconType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class CardinalBuoy(CardinalBuoyType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class EmergencyWreckMarkingBuoy(EmergencyWreckMarkingBuoyType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class InstallationBuoy(InstallationBuoyType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class IsolatedDangerBeacon(IsolatedDangerBeaconType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class IsolatedDangerBuoy(IsolatedDangerBuoyType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class LateralBeacon(LateralBeaconType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class LateralBuoy(LateralBuoyType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class LightAirObstruction(LightAirObstructionType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class LightAllAround(LightAllAroundType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class LightFogDetector(LightFogDetectorType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class LightSectored(LightSectoredType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class MooringBuoy(MooringBuoyType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class SafeWaterBeacon(SafeWaterBeaconType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class SafeWaterBuoy(SafeWaterBuoyType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class SpecialPurposeGeneralBeacon(SpecialPurposeGeneralBeaconType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class SpecialPurposeGeneralBuoy(SpecialPurposeGeneralBuoyType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class MultiPointProperty(MultiPointPropertyType):
    class Meta:
        name = "multiPointProperty"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class Segments(CurveSegmentArrayPropertyType):
    """This property element contains a list of curve segments.

    The order of the elements is significant and shall be preserved when
    processing the array.
    """

    class Meta:
        name = "segments"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class CurveType1(AbstractCurveType):
    class Meta:
        name = "CurveType"
        target_namespace = "http://www.opengis.net/gml/3.2"

    segments: Optional[Segments] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
            "required": True,
        },
    )


@dataclass
class CurveType2(CurveType1):
    """
    S-100 curve type adds an information association to the GML spatial type Curve.
    """

    class Meta:
        name = "CurveType"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    information_association: list[InformationAssociation] = field(
        default_factory=list,
        metadata={
            "name": "informationAssociation",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )


@dataclass
class Curve1(CurveType1):
    """A curve is a 1-dimensional primitive.

    Curves are continuous, connected, and have a measurable length in
    terms of the coordinate system. A curve is composed of one or more
    curve segments. Each curve segment within a curve may be defined
    using a different interpolation method. The curve segments are
    connected to one another, with the end point of each segment except
    the last being the start point of the next segment in the segment
    list. The orientation of the curve is positive. The element segments
    encapsulates the segments of the curve.
    """

    class Meta:
        name = "Curve"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class Curve2(CurveType2):
    class Meta:
        name = "Curve"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class CurvePropertyType1:
    """A property that has a curve as its value domain may either be an appropriate
    geometry element encapsulated in an element of this type or an XLink reference
    to a remote geometry element (where remote includes geometry elements located
    elsewhere in the same document).

    Either the reference or the contained element shall be given, but
    neither both nor none.
    """

    class Meta:
        name = "CurvePropertyType"
        target_namespace = "http://www.opengis.net/gml/3.2"

    orientable_curve: Optional["OrientableCurve2"] = field(
        default=None,
        metadata={
            "name": "OrientableCurve",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    composite_curve: Optional["CompositeCurve2"] = field(
        default=None,
        metadata={
            "name": "CompositeCurve",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    opengis_net_gml_3_2_composite_curve: Optional["CompositeCurve1"] = field(
        default=None,
        metadata={
            "name": "CompositeCurve",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    opengis_net_gml_3_2_orientable_curve: Optional["OrientableCurve1"] = field(
        default=None,
        metadata={
            "name": "OrientableCurve",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    curve: Optional[Curve2] = field(
        default=None,
        metadata={
            "name": "Curve",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    opengis_net_gml_3_2_curve: Optional[Curve1] = field(
        default=None,
        metadata={
            "name": "Curve",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    line_string: Optional[LineString] = field(
        default=None,
        metadata={
            "name": "LineString",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    type_value: TypeType = field(
        init=False,
        default=TypeType.SIMPLE,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    href: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    arcrole: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    show: Optional[ShowType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    actuate: Optional[ActuateType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    nil_reason: Optional[Union[str, NilReasonEnumerationValue]] = field(
        default=None,
        metadata={
            "name": "nilReason",
            "type": "Attribute",
            "pattern": r"other:/w{2,}",
        },
    )
    owns: bool = field(
        default=False,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class BaseCurve(CurvePropertyType1):
    """The property baseCurve references or contains the base curve, i.e. it either
    references the base curve via the XLink-attributes or contains the curve
    element.

    A curve element is any element which is substitutable for
    AbstractCurve. The base curve has positive orientation.
    """

    class Meta:
        name = "baseCurve"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class CurveMember(CurvePropertyType1):
    class Meta:
        name = "curveMember"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class CompositeCurveType1(AbstractCurveType):
    class Meta:
        name = "CompositeCurveType"
        target_namespace = "http://www.opengis.net/gml/3.2"

    curve_member: list[CurveMember] = field(
        default_factory=list,
        metadata={
            "name": "curveMember",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
            "min_occurs": 1,
        },
    )
    aggregation_type: Optional[AggregationType] = field(
        default=None,
        metadata={
            "name": "aggregationType",
            "type": "Attribute",
        },
    )


@dataclass
class OrientableCurveType(AbstractCurveType):
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    base_curve: Optional[BaseCurve] = field(
        default=None,
        metadata={
            "name": "baseCurve",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
            "required": True,
        },
    )
    orientation: SignType = field(
        default=SignType.PLUS_SIGN,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class RingType(AbstractRingType):
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    curve_member: list[CurveMember] = field(
        default_factory=list,
        metadata={
            "name": "curveMember",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
            "min_occurs": 1,
        },
    )
    aggregation_type: Optional[AggregationType] = field(
        default=None,
        metadata={
            "name": "aggregationType",
            "type": "Attribute",
        },
    )


@dataclass
class CompositeCurveType2(CompositeCurveType1):
    """
    S-100 composite curve type adds an information association to the GML spatial
    type CompositeCurve.
    """

    class Meta:
        name = "CompositeCurveType"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    information_association: list[InformationAssociation] = field(
        default_factory=list,
        metadata={
            "name": "informationAssociation",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )


@dataclass
class OrientableCurve2(OrientableCurveType):
    """S-100 orientable curve is the same as GML orientable curve.

    Added for consistency.
    """

    class Meta:
        name = "OrientableCurve"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class CompositeCurve1(CompositeCurveType1):
    """A gml:CompositeCurve is represented by a sequence of (orientable) curves
    such that each curve in the sequence terminates at the start point of the
    subsequent curve in the list.

    curveMember references or contains inline one curve in the composite
    curve. The curves are contiguous, the collection of curves is
    ordered. Therefore, if provided, the aggregationType attribute shall
    have the value "sequence".
    """

    class Meta:
        name = "CompositeCurve"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class OrientableCurve1(OrientableCurveType):
    """OrientableCurve consists of a curve and an orientation.

    If the orientation is "+", then the OrientableCurve is identical to
    the baseCurve. If the orientation is "-", then the OrientableCurve
    is related to another AbstractCurve with a parameterization that
    reverses the sense of the curve traversal.
    """

    class Meta:
        name = "OrientableCurve"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class Ring(RingType):
    """A ring is used to represent a single connected component of a surface
    boundary as specified in ISO 19107:2003, 6.3.6.

    Every gml:curveMember references or contains one curve, i.e. any
    element which is substitutable for gml:AbstractCurve. In the context
    of a ring, the curves describe the boundary of the surface. The
    sequence of curves shall be contiguous and connected in a cycle. If
    provided, the aggregationType attribute shall have the value
    "sequence".
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class CompositeCurve2(CompositeCurveType2):
    class Meta:
        name = "CompositeCurve"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class AbstractRingPropertyType:
    """
    A property with the content model of gml:AbstractRingPropertyType encapsulates
    a ring to represent the surface boundary property of a surface.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    ring: Optional[Ring] = field(
        default=None,
        metadata={
            "name": "Ring",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    linear_ring: Optional[LinearRing] = field(
        default=None,
        metadata={
            "name": "LinearRing",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )


@dataclass
class CurvePropertyType2(S100SpatialAttributeType):
    """
    Curve property using the S-100 curve type.
    """

    class Meta:
        name = "CurvePropertyType"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    curve: Optional[Curve2] = field(
        default=None,
        metadata={
            "name": "Curve",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    composite_curve: Optional[CompositeCurve2] = field(
        default=None,
        metadata={
            "name": "CompositeCurve",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    orientable_curve: Optional[OrientableCurve2] = field(
        default=None,
        metadata={
            "name": "OrientableCurve",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )


@dataclass
class Exterior(AbstractRingPropertyType):
    """A boundary of a surface consists of a number of rings.

    In the normal 2D case, one of these rings is distinguished as being
    the exterior boundary. In a general manifold this is not always
    possible, in which case all boundaries shall be listed as interior
    boundaries, and the exterior will be empty.
    """

    class Meta:
        name = "exterior"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class Interior(AbstractRingPropertyType):
    """A boundary of a surface consists of a number of rings.

    The "interior" rings separate the surface / surface patch from the
    area enclosed by the rings.
    """

    class Meta:
        name = "interior"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class CurveProperty(CurvePropertyType2):
    class Meta:
        name = "curveProperty"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class PolygonPatchType(AbstractSurfacePatchType):
    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    exterior: Optional[Exterior] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    interior: list[Interior] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    interpolation: SurfaceInterpolationType = field(
        init=False,
        default=SurfaceInterpolationType.PLANAR,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class PolygonType1(AbstractSurfaceType):
    class Meta:
        name = "PolygonType"
        target_namespace = "http://www.opengis.net/gml/3.2"

    exterior: Optional[Exterior] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    interior: list[Interior] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )


@dataclass
class NavigationLineType(AidsToNavigationType):
    """
    A straight line extending towards an area of navigational interest and
    generally generated by two navigational aids or one navigational aid and a
    bearing.

    :ivar category_of_navigation_line: Classification of route guidance
        given to vessels.
    :ivar status: The condition of an object at a given instant in time.
    :ivar orientation: (1) The angular distance measured from true north
        to the major axis of the feature. (2) In ECDIS, the mode in
        which information on the ECDIS is being presented. Typical modes
        include: north-up - as shown on a nautical chart, north is at
        the top of the display; Ships head-up - based on the actual
        heading of the ship, (e.g. Ships gyrocompass); course-up display
        - based on the course or route being taken.
    :ivar navigable_track:
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_navigation_line: Optional[CategoryOfNavigationLineType] = (
        field(
            default=None,
            metadata={
                "name": "categoryOfNavigationLine",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
                "required": True,
            },
        )
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    orientation: Optional[OrientationType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    navigable_track: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "navigableTrack",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["NavigationLineType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        curve_property: Optional[CurveProperty] = field(
            default=None,
            metadata={
                "name": "curveProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class RecommendedTrackType(AidsToNavigationType):
    """
    A route which has been specially examined to ensure so far as possible that it
    is free of dangers and along which ships are advised to navigate.

    :ivar based_on_fixed_marks: A straight route (known as a recommended
        track, range or leading line), which comprises: a. at least two
        structures (usually beacons or daymarks) and/or natural
        features, which may carry lights and/or top-marks. The
        structures/features are positioned so that when observed to be
        in line, a vessel can follow a known bearing with safety.
        (Adapted from International Association of Marine Aids to
        Navigation and Lighthouse Authorities - IALA Aids to Navigation
        Guide, 1990); or b. a single structure or natural feature, which
        may carry lights and/or a topmark, and a specified bearing which
        can be followed with safety. (S-57 Edition 3.1, Appendix A
        Chapter 2, Page 2.72, November 2000, as amended).
    :ivar depth_range_minimum_value: The minimum (shoalest) value of a
        depth range.
    :ivar maximal_permitted_draught: The maximal permitted draught of a
        vessel or convoy according to the particular article/clause of
        the applicable law/regulation.
    :ivar status: The condition of an object at a given instant in time.
    :ivar vertical_datum: The reference level used for expressing the
        vertical measurements of points on the earth's surface. Also
        called datum level, reference plane, levelling datum, datum for
        sounding reduction, datum for heights.
    :ivar orientation: (1) The angular distance measured from true north
        to the major axis of the feature. (2) In ECDIS, the mode in
        which information on the ECDIS is being presented. Typical modes
        include: north-up - as shown on a nautical chart, north is at
        the top of the display; Ships head-up - based on the actual
        heading of the ship, (e.g. Ships gyrocompass); course-up display
        - based on the course or route being taken.
    :ivar vertical_uncertainty: The best estimate of the vertical
        accuracy of depths, heights, vertical distances and vertical
        clearances.
    :ivar quality_of_vertical_measurement: The reliability of the value
        of a sounding.
    :ivar technique_of_vertical_measurement: Survey method used to
        obtain depth information.
    :ivar traffic_flow: Direction of vessels passing a reference point.
    :ivar navigation_line:
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    based_on_fixed_marks: Optional[bool] = field(
        default=None,
        metadata={
            "name": "basedOnFixedMarks",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    depth_range_minimum_value: Optional[float] = field(
        default=None,
        metadata={
            "name": "depthRangeMinimumValue",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    maximal_permitted_draught: Optional[float] = field(
        default=None,
        metadata={
            "name": "maximalPermittedDraught",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_datum: Optional[VerticalDatumType] = field(
        default=None,
        metadata={
            "name": "verticalDatum",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    orientation: Optional[OrientationType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    vertical_uncertainty: Optional[VerticalUncertaintyType] = field(
        default=None,
        metadata={
            "name": "verticalUncertainty",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    quality_of_vertical_measurement: list[QualityOfVerticalMeasurementType] = (
        field(
            default_factory=list,
            metadata={
                "name": "qualityOfVerticalMeasurement",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
    )
    technique_of_vertical_measurement: list[
        TechniqueOfVerticalMeasurementType
    ] = field(
        default_factory=list,
        metadata={
            "name": "techniqueOfVerticalMeasurement",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    traffic_flow: Optional[TrafficFlowType] = field(
        default=None,
        metadata={
            "name": "trafficFlow",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    navigation_line: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "navigationLine",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )
    geometry: list["RecommendedTrackType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        curve_property: Optional[CurveProperty] = field(
            default=None,
            metadata={
                "name": "curveProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class PolygonType2(PolygonType1):
    """
    S-100 polygon type adds an information association to the GML spatial type
    Polygon.
    """

    class Meta:
        name = "PolygonType"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    information_association: list[InformationAssociation] = field(
        default_factory=list,
        metadata={
            "name": "informationAssociation",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )


@dataclass
class PolygonPatch(PolygonPatchType):
    """A gml:PolygonPatch is a surface patch that is defined by a set of boundary
    curves and an underlying surface to which these curves adhere.

    The curves shall be coplanar and the polygon uses planar
    interpolation in its interior. interpolation is fixed to "planar",
    i.e. an interpolation shall return points on a single plane. The
    boundary of the patch shall be contained within that plane.
    """

    class Meta:
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class Polygon1(PolygonType1):
    """A Polygon is a special surface that is defined by a single surface patch
    (see D.3.6).

    The boundary of this patch is coplanar and the polygon uses planar
    interpolation in its interior. The elements exterior and interior
    describe the surface boundary of the polygon.
    """

    class Meta:
        name = "Polygon"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class NavigationLine(NavigationLineType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class RecommendedTrack(RecommendedTrackType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class Polygon2(PolygonType2):
    """
    S100 version of polygon type.
    """

    class Meta:
        name = "Polygon"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class SurfacePatchArrayPropertyType:
    """
    Gml:SurfacePatchArrayPropertyType is a container for a sequence of surface
    patches.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    polygon_patch: list[PolygonPatch] = field(
        default_factory=list,
        metadata={
            "name": "PolygonPatch",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )


@dataclass
class PolygonPropertyType:
    """
    Polygon property using the S-100 polygon type.
    """

    class Meta:
        target_namespace = "http://www.iho.int/s100gml/5.0"

    polygon: Optional[Polygon2] = field(
        default=None,
        metadata={
            "name": "Polygon",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    type_value: TypeType = field(
        init=False,
        default=TypeType.SIMPLE,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    href: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    arcrole: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    show: Optional[ShowType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    actuate: Optional[ActuateType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    nil_reason: Optional[Union[str, NilReasonEnumerationValue]] = field(
        default=None,
        metadata={
            "name": "nilReason",
            "type": "Attribute",
            "pattern": r"other:/w{2,}",
        },
    )


@dataclass
class Patches(SurfacePatchArrayPropertyType):
    """The patches property element contains the sequence of surface patches.

    The order of the elements is significant and shall be preserved when
    processing the array.
    """

    class Meta:
        name = "patches"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class PolygonProperty(PolygonPropertyType):
    class Meta:
        name = "polygonProperty"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class SurfaceType1(AbstractSurfaceType):
    class Meta:
        name = "SurfaceType"
        target_namespace = "http://www.opengis.net/gml/3.2"

    patches: Optional[Patches] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
            "required": True,
        },
    )


@dataclass
class SurfaceType2(SurfaceType1):
    """
    S-100 surface type adds an information association to the GML spatial type
    Surface.
    """

    class Meta:
        name = "SurfaceType"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    information_association: list[InformationAssociation] = field(
        default_factory=list,
        metadata={
            "name": "informationAssociation",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )


@dataclass
class Surface1(SurfaceType1):
    """A Surface is a 2-dimensional primitive and is composed of one or more
    surface patches as specified in ISO 19107:2003, 6.3.17.1.

    The surface patches are connected to one another. patches
    encapsulates the patches of the surface.
    """

    class Meta:
        name = "Surface"
        namespace = "http://www.opengis.net/gml/3.2"


@dataclass
class Surface2(SurfaceType2):
    class Meta:
        name = "Surface"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class DatasetType(AbstractFeatureTypeAbstract):
    """
    Dataset element for dataset as "GML document".

    :ivar dataset_identification_information: Dataset identification
        information
    :ivar point:
    :ivar multi_point:
    :ivar curve:
    :ivar composite_curve:
    :ivar orientable_curve:
    :ivar surface:
    :ivar polygon:
    """

    class Meta:
        target_namespace = "http://www.iho.int/s100gml/5.0"

    dataset_identification_information: Optional[DataSetIdentificationType] = (
        field(
            default=None,
            metadata={
                "name": "DatasetIdentificationInformation",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )
    )
    point: list[Point2] = field(
        default_factory=list,
        metadata={
            "name": "Point",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    multi_point: list[MultiPoint2] = field(
        default_factory=list,
        metadata={
            "name": "MultiPoint",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    curve: list[Curve2] = field(
        default_factory=list,
        metadata={
            "name": "Curve",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    composite_curve: list[CompositeCurve2] = field(
        default_factory=list,
        metadata={
            "name": "CompositeCurve",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    orientable_curve: list[OrientableCurve2] = field(
        default_factory=list,
        metadata={
            "name": "OrientableCurve",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    surface: list[Surface2] = field(
        default_factory=list,
        metadata={
            "name": "Surface",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    polygon: list[Polygon2] = field(
        default_factory=list,
        metadata={
            "name": "Polygon",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )


@dataclass
class SurfacePropertyType2(S100SpatialAttributeType):
    """
    Surface property using the S-100 surface type.
    """

    class Meta:
        name = "SurfacePropertyType"
        target_namespace = "http://www.iho.int/s100gml/5.0"

    surface: Optional[Surface2] = field(
        default=None,
        metadata={
            "name": "Surface",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )


@dataclass
class GeometricPrimitivePropertyType:
    """A property that has a geometric primitive as its value domain may either be
    an appropriate geometry element encapsulated in an element of this type or an
    XLink reference to a remote geometry element (where remote includes geometry
    elements located elsewhere in the same document).

    Either the reference or the contained element shall be given, but
    neither both nor none.
    """

    class Meta:
        target_namespace = "http://www.opengis.net/gml/3.2"

    point: Optional[Point2] = field(
        default=None,
        metadata={
            "name": "Point",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    surface: Optional[Surface2] = field(
        default=None,
        metadata={
            "name": "Surface",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    opengis_net_gml_3_2_surface: Optional[Surface1] = field(
        default=None,
        metadata={
            "name": "Surface",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    polygon: Optional[Polygon2] = field(
        default=None,
        metadata={
            "name": "Polygon",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    opengis_net_gml_3_2_polygon: Optional[Polygon1] = field(
        default=None,
        metadata={
            "name": "Polygon",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    orientable_curve: Optional[OrientableCurve2] = field(
        default=None,
        metadata={
            "name": "OrientableCurve",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    composite_curve: Optional[CompositeCurve2] = field(
        default=None,
        metadata={
            "name": "CompositeCurve",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    opengis_net_gml_3_2_composite_curve: Optional[CompositeCurve1] = field(
        default=None,
        metadata={
            "name": "CompositeCurve",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    opengis_net_gml_3_2_orientable_curve: Optional[OrientableCurve1] = field(
        default=None,
        metadata={
            "name": "OrientableCurve",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    curve: Optional[Curve2] = field(
        default=None,
        metadata={
            "name": "Curve",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    opengis_net_gml_3_2_curve: Optional[Curve1] = field(
        default=None,
        metadata={
            "name": "Curve",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    line_string: Optional[LineString] = field(
        default=None,
        metadata={
            "name": "LineString",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    opengis_net_gml_3_2_point: Optional[Point1] = field(
        default=None,
        metadata={
            "name": "Point",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    owns: bool = field(
        default=False,
        metadata={
            "type": "Attribute",
        },
    )
    type_value: TypeType = field(
        init=False,
        default=TypeType.SIMPLE,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    href: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    arcrole: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    show: Optional[ShowType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    actuate: Optional[ActuateType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    nil_reason: Optional[Union[str, NilReasonEnumerationValue]] = field(
        default=None,
        metadata={
            "name": "nilReason",
            "type": "Attribute",
            "pattern": r"other:/w{2,}",
        },
    )


@dataclass
class SurfacePropertyType1:
    """A property that has a surface as its value domain may either be an
    appropriate geometry element encapsulated in an element of this type or an
    XLink reference to a remote geometry element (where remote includes geometry
    elements located elsewhere in the same document).

    Either the reference or the contained element shall be given, but
    neither both nor none.
    """

    class Meta:
        name = "SurfacePropertyType"
        target_namespace = "http://www.opengis.net/gml/3.2"

    surface: Optional[Surface2] = field(
        default=None,
        metadata={
            "name": "Surface",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    opengis_net_gml_3_2_surface: Optional[Surface1] = field(
        default=None,
        metadata={
            "name": "Surface",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    polygon: Optional[Polygon2] = field(
        default=None,
        metadata={
            "name": "Polygon",
            "type": "Element",
            "namespace": "http://www.iho.int/s100gml/5.0",
        },
    )
    opengis_net_gml_3_2_polygon: Optional[Polygon1] = field(
        default=None,
        metadata={
            "name": "Polygon",
            "type": "Element",
            "namespace": "http://www.opengis.net/gml/3.2",
        },
    )
    type_value: TypeType = field(
        init=False,
        default=TypeType.SIMPLE,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    href: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    arcrole: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
            "min_length": 1,
        },
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    show: Optional[ShowType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    actuate: Optional[ActuateType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/1999/xlink",
        },
    )
    nil_reason: Optional[Union[str, NilReasonEnumerationValue]] = field(
        default=None,
        metadata={
            "name": "nilReason",
            "type": "Attribute",
            "pattern": r"other:/w{2,}",
        },
    )
    owns: bool = field(
        default=False,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class ThisDatasetType(DatasetType):
    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    members: Optional["ThisDatasetType.Members"] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )

    @dataclass
    class Members(AbstractFeatureMemberType):
        ato_nfixing_method: list[object] = field(
            default_factory=list,
            metadata={
                "name": "AtoNFixingMethod",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        aton_status_information: list[object] = field(
            default_factory=list,
            metadata={
                "name": "AtonStatusInformation",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        positioning_information: list[object] = field(
            default_factory=list,
            metadata={
                "name": "PositioningInformation",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        spatial_quality: list[object] = field(
            default_factory=list,
            metadata={
                "name": "SpatialQuality",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        aids_to_navigation: list[object] = field(
            default_factory=list,
            metadata={
                "name": "AidsToNavigation",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        structure_object: list[object] = field(
            default_factory=list,
            metadata={
                "name": "StructureObject",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        equipment: list[object] = field(
            default_factory=list,
            metadata={
                "name": "Equipment",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        electronic_aton: list[object] = field(
            default_factory=list,
            metadata={
                "name": "ElectronicAton",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        generic_beacon: list[object] = field(
            default_factory=list,
            metadata={
                "name": "GenericBeacon",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        generic_buoy: list[object] = field(
            default_factory=list,
            metadata={
                "name": "GenericBuoy",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        generic_light: list[object] = field(
            default_factory=list,
            metadata={
                "name": "GenericLight",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        landmark: list[object] = field(
            default_factory=list,
            metadata={
                "name": "Landmark",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        lateral_beacon: list[object] = field(
            default_factory=list,
            metadata={
                "name": "LateralBeacon",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        lateral_buoy: list[object] = field(
            default_factory=list,
            metadata={
                "name": "LateralBuoy",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        navigation_line: list[object] = field(
            default_factory=list,
            metadata={
                "name": "NavigationLine",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        recommended_track: list[object] = field(
            default_factory=list,
            metadata={
                "name": "RecommendedTrack",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        light_sectored: list[object] = field(
            default_factory=list,
            metadata={
                "name": "LightSectored",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        light_all_around: list[object] = field(
            default_factory=list,
            metadata={
                "name": "LightAllAround",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        light_air_obstruction: list[object] = field(
            default_factory=list,
            metadata={
                "name": "LightAirObstruction",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        light_fog_detector: list[object] = field(
            default_factory=list,
            metadata={
                "name": "LightFogDetector",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        radar_reflector: list[object] = field(
            default_factory=list,
            metadata={
                "name": "RadarReflector",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        fog_signal: list[object] = field(
            default_factory=list,
            metadata={
                "name": "FogSignal",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        environment_observation_equipment: list[object] = field(
            default_factory=list,
            metadata={
                "name": "EnvironmentObservationEquipment",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        radio_station: list[object] = field(
            default_factory=list,
            metadata={
                "name": "RadioStation",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        daymark: list[object] = field(
            default_factory=list,
            metadata={
                "name": "Daymark",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        retroreflector: list[object] = field(
            default_factory=list,
            metadata={
                "name": "Retroreflector",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        radar_transponder_beacon: list[object] = field(
            default_factory=list,
            metadata={
                "name": "RadarTransponderBeacon",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        virtual_aisaid_to_navigation: list[object] = field(
            default_factory=list,
            metadata={
                "name": "VirtualAISAidToNavigation",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        physical_aisaid_to_navigation: list[object] = field(
            default_factory=list,
            metadata={
                "name": "PhysicalAISAidToNavigation",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        synthetic_aisaid_to_navigation: list[object] = field(
            default_factory=list,
            metadata={
                "name": "SyntheticAISAidToNavigation",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        power_source: list[object] = field(
            default_factory=list,
            metadata={
                "name": "PowerSource",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        isolated_danger_beacon: list[object] = field(
            default_factory=list,
            metadata={
                "name": "IsolatedDangerBeacon",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        cardinal_beacon: list[object] = field(
            default_factory=list,
            metadata={
                "name": "CardinalBeacon",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        isolated_danger_buoy: list[object] = field(
            default_factory=list,
            metadata={
                "name": "IsolatedDangerBuoy",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        cardinal_buoy: list[object] = field(
            default_factory=list,
            metadata={
                "name": "CardinalBuoy",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        installation_buoy: list[object] = field(
            default_factory=list,
            metadata={
                "name": "InstallationBuoy",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        mooring_buoy: list[object] = field(
            default_factory=list,
            metadata={
                "name": "MooringBuoy",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        emergency_wreck_marking_buoy: list[object] = field(
            default_factory=list,
            metadata={
                "name": "EmergencyWreckMarkingBuoy",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        lighthouse: list[object] = field(
            default_factory=list,
            metadata={
                "name": "Lighthouse",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        light_float: list[object] = field(
            default_factory=list,
            metadata={
                "name": "LightFloat",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        light_vessel: list[object] = field(
            default_factory=list,
            metadata={
                "name": "LightVessel",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        offshore_platform: list[object] = field(
            default_factory=list,
            metadata={
                "name": "OffshorePlatform",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        silo_tank: list[object] = field(
            default_factory=list,
            metadata={
                "name": "SiloTank",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        pile: list[object] = field(
            default_factory=list,
            metadata={
                "name": "Pile",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        building: list[object] = field(
            default_factory=list,
            metadata={
                "name": "Building",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        bridge: list[object] = field(
            default_factory=list,
            metadata={
                "name": "Bridge",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        sinker_anchor: list[object] = field(
            default_factory=list,
            metadata={
                "name": "SinkerAnchor",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        mooring_shackle: list[object] = field(
            default_factory=list,
            metadata={
                "name": "MooringShackle",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        cable_submarine: list[object] = field(
            default_factory=list,
            metadata={
                "name": "CableSubmarine",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        swivel: list[object] = field(
            default_factory=list,
            metadata={
                "name": "Swivel",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        bridle: list[object] = field(
            default_factory=list,
            metadata={
                "name": "Bridle",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        counter_weight: list[object] = field(
            default_factory=list,
            metadata={
                "name": "CounterWeight",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        topmark: list[object] = field(
            default_factory=list,
            metadata={
                "name": "Topmark",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        safe_water_beacon: list[object] = field(
            default_factory=list,
            metadata={
                "name": "SafeWaterBeacon",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        special_purpose_general_beacon: list[object] = field(
            default_factory=list,
            metadata={
                "name": "SpecialPurposeGeneralBeacon",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        safe_water_buoy: list[object] = field(
            default_factory=list,
            metadata={
                "name": "SafeWaterBuoy",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        special_purpose_general_buoy: list[object] = field(
            default_factory=list,
            metadata={
                "name": "SpecialPurposeGeneralBuoy",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        dangerous_feature: list[object] = field(
            default_factory=list,
            metadata={
                "name": "DangerousFeature",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        aton_aggregation: list[object] = field(
            default_factory=list,
            metadata={
                "name": "AtonAggregation",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        aton_association: list[object] = field(
            default_factory=list,
            metadata={
                "name": "AtonAssociation",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        quality_of_non_bathymetric_data: list[object] = field(
            default_factory=list,
            metadata={
                "name": "QualityOfNonBathymetricData",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        data_coverage: list[object] = field(
            default_factory=list,
            metadata={
                "name": "DataCoverage",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        local_direction_of_buoyage: list[object] = field(
            default_factory=list,
            metadata={
                "name": "LocalDirectionOfBuoyage",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        navigational_system_of_marks: list[object] = field(
            default_factory=list,
            metadata={
                "name": "NavigationalSystemOfMarks",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        sounding_datum: list[object] = field(
            default_factory=list,
            metadata={
                "name": "SoundingDatum",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
        vertical_datum_of_data: list[object] = field(
            default_factory=list,
            metadata={
                "name": "VerticalDatumOfData",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )


@dataclass
class SurfaceProperty(SurfacePropertyType2):
    class Meta:
        name = "surfaceProperty"
        namespace = "http://www.iho.int/s100gml/5.0"


@dataclass
class DataCoverageType(AbstractFeatureType):
    """
    A geographical area that describes the coverage and extent of spatial objects.

    :ivar maximum_display_scale: The value considered by the Data
        Producer to be the maximum (largest) scale at which the data is
        to be displayed before it can be considered to be “grossly
        overscaled”.
    :ivar minimum_display_scale: The smallest intended viewing scale for
        the data.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    maximum_display_scale: Optional[int] = field(
        default=None,
        metadata={
            "name": "maximumDisplayScale",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    minimum_display_scale: Optional[int] = field(
        default=None,
        metadata={
            "name": "minimumDisplayScale",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    geometry: list["DataCoverageType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        surface_property: Optional[SurfaceProperty] = field(
            default=None,
            metadata={
                "name": "surfaceProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class Dataset(ThisDatasetType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class LandmarkType(StructureObjectType):
    """
    A prominent object at a fixed location on land which can be used in determining
    a location or a direction.

    :ivar category_of_landmark: Classification of prominent cultural and
        natural features in the landscape.
    :ivar colour: The property possessed by an object of producing
        different sensations on the eye as a result of the way it
        reflects or emits light.
    :ivar colour_pattern: A regular repeated design containing more than
        one colour.
    :ivar function: A specific role that describes a feature.
    :ivar nature_of_construction: The building's primary construction
        material.
    :ivar radar_conspicuous: A feature which returns a strong radar
        echo.
    :ivar status: The condition of an object at a given instant in time.
    :ivar vertical_datum: The reference level used for expressing the
        vertical measurements of points on the earth's surface. Also
        called datum level, reference plane, levelling datum, datum for
        sounding reduction, datum for heights.
    :ivar visual_prominence: The extent to which a feature, either
        natural or artificial, is visible from seaward.
    :ivar elevation: The altitude of the ground level of an object,
        measured from a specified vertical datum.
    :ivar height: The value of the vertical distance to the highest
        point of the object, measured from a specified vertical datum.
    :ivar manned_structure: An expression of the feature being
        permanently manned or not.
    :ivar vertical_length: The total vertical length of a feature.
    :ivar vertical_accuracy: -
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_landmark: list[CategoryOfLandmarkType] = field(
        default_factory=list,
        metadata={
            "name": "categoryOfLandmark",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )
    colour: list[ColourType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    colour_pattern: list[ColourPatternType] = field(
        default_factory=list,
        metadata={
            "name": "colourPattern",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    function: list[FunctionType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    nature_of_construction: list[NatureOfConstructionType] = field(
        default_factory=list,
        metadata={
            "name": "natureOfConstruction",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    radar_conspicuous: Optional[bool] = field(
        default=None,
        metadata={
            "name": "radarConspicuous",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_datum: Optional[VerticalDatumType] = field(
        default=None,
        metadata={
            "name": "verticalDatum",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    visual_prominence: Optional[VisualProminenceType] = field(
        default=None,
        metadata={
            "name": "visualProminence",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    elevation: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    manned_structure: Optional[bool] = field(
        default=None,
        metadata={
            "name": "mannedStructure",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_length: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_accuracy: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalAccuracy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["LandmarkType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
            },
        )
        curve_property: Optional[CurveProperty] = field(
            default=None,
            metadata={
                "name": "curveProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
            },
        )
        surface_property: Optional[SurfaceProperty] = field(
            default=None,
            metadata={
                "name": "surfaceProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
            },
        )


@dataclass
class LocalDirectionOfBuoyageType(AbstractFeatureType):
    """
    An area within which the navigational system of marks has been established in
    relation to a specific direction.

    :ivar orientation: (1) The angular distance measured from true north
        to the major axis of the feature. (2) In ECDIS, the mode in
        which information on the ECDIS is being presented. Typical modes
        include: north-up - as shown on a nautical chart, north is at
        the top of the display; Ships head-up - based on the actual
        heading of the ship, (e.g. Ships gyrocompass); course-up display
        - based on the course or route being taken.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    orientation: Optional[OrientationType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    geometry: list["LocalDirectionOfBuoyageType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        surface_property: Optional[SurfaceProperty] = field(
            default=None,
            metadata={
                "name": "surfaceProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class NavigationalSystemOfMarksType(AbstractFeatureType):
    """
    An area within which the navigational system of marks has been established in
    relation to a specific direction.

    :ivar marks_navigational_system_of: The system of navigational
        buoyage a region complies with.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    marks_navigational_system_of: Optional[MarksNavigationalSystemOfType] = (
        field(
            default=None,
            metadata={
                "name": "marksNavigationalSystemOf",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
                "required": True,
            },
        )
    )
    geometry: list["NavigationalSystemOfMarksType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        surface_property: Optional[SurfaceProperty] = field(
            default=None,
            metadata={
                "name": "surfaceProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class OffshorePlatformType(StructureObjectType):
    """
    A permanent offshore structure, either fixed or floating.

    :ivar category_of_offshore_platform: Classification of an offshore
        raised structure.
    :ivar colour: The property possessed by an object of producing
        different sensations on the eye as a result of the way it
        reflects or emits light.
    :ivar colour_pattern: A regular repeated design containing more than
        one colour.
    :ivar height: The value of the vertical distance to the highest
        point of the object, measured from a specified vertical datum.
    :ivar manned_structure: An expression of the feature being
        permanently manned or not.
    :ivar nature_of_construction: The building's primary construction
        material.
    :ivar product: The various substances which are transported, stored
        or exploited.
    :ivar radar_conspicuous: A feature which returns a strong radar
        echo.
    :ivar status: The condition of an object at a given instant in time.
    :ivar vertical_datum: The reference level used for expressing the
        vertical measurements of points on the earth's surface. Also
        called datum level, reference plane, levelling datum, datum for
        sounding reduction, datum for heights.
    :ivar vertical_length: The total vertical length of a feature.
    :ivar visual_prominence: The extent to which a feature, either
        natural or artificial, is visible from seaward.
    :ivar vertical_accuracy: -
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_offshore_platform: list[CategoryOfOffshorePlatformType] = (
        field(
            default_factory=list,
            metadata={
                "name": "categoryOfOffshorePlatform",
                "type": "Element",
                "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            },
        )
    )
    colour: list[ColourType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    colour_pattern: list[ColourPatternType] = field(
        default_factory=list,
        metadata={
            "name": "colourPattern",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    manned_structure: Optional[bool] = field(
        default=None,
        metadata={
            "name": "mannedStructure",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    nature_of_construction: list[NatureOfConstructionType] = field(
        default_factory=list,
        metadata={
            "name": "natureOfConstruction",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    product: list[ProductType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    radar_conspicuous: Optional[bool] = field(
        default=None,
        metadata={
            "name": "radarConspicuous",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_datum: Optional[VerticalDatumType] = field(
        default=None,
        metadata={
            "name": "verticalDatum",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_length: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    visual_prominence: Optional[VisualProminenceType] = field(
        default=None,
        metadata={
            "name": "visualProminence",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_accuracy: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalAccuracy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["OffshorePlatformType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
            },
        )
        surface_property: Optional[SurfaceProperty] = field(
            default=None,
            metadata={
                "name": "surfaceProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
            },
        )


@dataclass
class QualityOfNonBathymetricDataType(AbstractFeatureType):
    """
    An area within which a uniform assessment of the quality of the non-bathymetric
    data exists.

    :ivar category_of_temporal_variation: An assessment of the
        likelihood of change over time.
    :ivar orientation_uncertainty: The best estimate of the accuracy of
        a bearing.
    :ivar horizontal_distance_uncertainty: The best estimate of the
        horizontal accuracy of horizontal clearances and distances.
    :ivar horizontal_position_uncertainty: The best estimate of the
        accuracy of a position.
    :ivar information: Textual information about the feature. The
        information may be provided as a string of text or as a file
        name of a single external text file that contains the text.
    :ivar information_in_national_language: Textual information in
        national language characters.
    :ivar textual_description: Encodes the file name of a single
        external text file that contains the text in a defined language,
        which provides additional textual information that cannot be
        provided using other allowable attributes for the feature.
    :ivar vertical_uncertainty: The best estimate of the vertical
        accuracy of depths, heights, vertical distances and vertical
        clearances.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    category_of_temporal_variation: Optional[
        CategoryOfTemporalVariationType
    ] = field(
        default=None,
        metadata={
            "name": "categoryOfTemporalVariation",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    orientation_uncertainty: Optional[float] = field(
        default=None,
        metadata={
            "name": "orientationUncertainty",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    horizontal_distance_uncertainty: Optional[float] = field(
        default=None,
        metadata={
            "name": "horizontalDistanceUncertainty",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    horizontal_position_uncertainty: Optional[
        HorizontalPositionUncertaintyType
    ] = field(
        default=None,
        metadata={
            "name": "horizontalPositionUncertainty",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    information: Optional[InformationType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    information_in_national_language: Optional[str] = field(
        default=None,
        metadata={
            "name": "informationInNationalLanguage",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    textual_description: Optional[TextualDescriptionType] = field(
        default=None,
        metadata={
            "name": "textualDescription",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_uncertainty: Optional[VerticalUncertaintyType] = field(
        default=None,
        metadata={
            "name": "verticalUncertainty",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["QualityOfNonBathymetricDataType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        surface_property: Optional[SurfaceProperty] = field(
            default=None,
            metadata={
                "name": "surfaceProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class SiloTankType(StructureObjectType):
    """
    A large storage structure used for storing loose materials, liquids and/or
    gases.

    :ivar building_shape: The specific shape of the building.
    :ivar category_of_silo_tank: Classification based on the product for
        which a silo or tank is used.
    :ivar colour: The property possessed by an object of producing
        different sensations on the eye as a result of the way it
        reflects or emits light.
    :ivar colour_pattern: A regular repeated design containing more than
        one colour.
    :ivar elevation: The altitude of the ground level of an object,
        measured from a specified vertical datum.
    :ivar height: The value of the vertical distance to the highest
        point of the object, measured from a specified vertical datum.
    :ivar nature_of_construction: The building's primary construction
        material.
    :ivar radar_conspicuous: A feature which returns a strong radar
        echo.
    :ivar status: The condition of an object at a given instant in time.
    :ivar vertical_datum: The reference level used for expressing the
        vertical measurements of points on the earth's surface. Also
        called datum level, reference plane, levelling datum, datum for
        sounding reduction, datum for heights.
    :ivar vertical_length: The total vertical length of a feature.
    :ivar visual_prominence: The extent to which a feature, either
        natural or artificial, is visible from seaward.
    :ivar vertical_accuracy: -
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    building_shape: Optional[BuildingShapeType] = field(
        default=None,
        metadata={
            "name": "buildingShape",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    category_of_silo_tank: Optional[CategoryOfSiloTankType] = field(
        default=None,
        metadata={
            "name": "categoryOfSiloTank",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    colour: list[ColourType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    colour_pattern: list[ColourPatternType] = field(
        default_factory=list,
        metadata={
            "name": "colourPattern",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    elevation: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    nature_of_construction: list[NatureOfConstructionType] = field(
        default_factory=list,
        metadata={
            "name": "natureOfConstruction",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    radar_conspicuous: Optional[bool] = field(
        default=None,
        metadata={
            "name": "radarConspicuous",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    status: list[StatusType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_datum: Optional[VerticalDatumType] = field(
        default=None,
        metadata={
            "name": "verticalDatum",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_length: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalLength",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    visual_prominence: Optional[VisualProminenceType] = field(
        default=None,
        metadata={
            "name": "visualProminence",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    vertical_accuracy: Optional[float] = field(
        default=None,
        metadata={
            "name": "verticalAccuracy",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
        },
    )
    geometry: list["SiloTankType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        point_property: Optional[PointProperty2] = field(
            default=None,
            metadata={
                "name": "pointProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
            },
        )
        surface_property: Optional[SurfaceProperty] = field(
            default=None,
            metadata={
                "name": "surfaceProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
            },
        )


@dataclass
class SoundingDatumType(AbstractFeatureType):
    """The horizontal plane or tidal datum to which soundings have been reduced.

    Also called datum for sounding reduction.

    :ivar vertical_datum: The reference level used for expressing the
        vertical measurements of points on the earth's surface. Also
        called datum level, reference plane, levelling datum, datum for
        sounding reduction, datum for heights.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    vertical_datum: Optional[VerticalDatumType] = field(
        default=None,
        metadata={
            "name": "verticalDatum",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    geometry: list["SoundingDatumType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        surface_property: Optional[SurfaceProperty] = field(
            default=None,
            metadata={
                "name": "surfaceProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class VerticalDatumOfDataType(AbstractFeatureType):
    """Any level surface (for example Mean Sea Level) taken as a surface of
    reference to which the elevations within a data set are reduced.

    Also called datum level, reference level, reference plane, levelling
    datum, datum for heights.

    :ivar vertical_datum: The reference level used for expressing the
        vertical measurements of points on the earth's surface. Also
        called datum level, reference plane, levelling datum, datum for
        sounding reduction, datum for heights.
    :ivar geometry:
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"

    vertical_datum: Optional[VerticalDatumType] = field(
        default=None,
        metadata={
            "name": "verticalDatum",
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "required": True,
        },
    )
    geometry: list["VerticalDatumOfDataType.Geometry"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.iho.int/S-201/gml/cs0/2.0",
            "min_occurs": 1,
        },
    )

    @dataclass
    class Geometry:
        surface_property: Optional[SurfaceProperty] = field(
            default=None,
            metadata={
                "name": "surfaceProperty",
                "type": "Element",
                "namespace": "http://www.iho.int/s100gml/5.0",
                "required": True,
            },
        )


@dataclass
class DataCoverage(DataCoverageType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class Landmark(LandmarkType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class LighthouseType(LandmarkType):
    """
    A distinctive structure on or off a coast exhibiting a major light designed to
    serve as an aid to navigation.
    """

    class Meta:
        target_namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class LocalDirectionOfBuoyage(LocalDirectionOfBuoyageType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class NavigationalSystemOfMarks(NavigationalSystemOfMarksType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class OffshorePlatform(OffshorePlatformType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class QualityOfNonBathymetricData(QualityOfNonBathymetricDataType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class SiloTank(SiloTankType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class SoundingDatum(SoundingDatumType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class VerticalDatumOfData(VerticalDatumOfDataType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"


@dataclass
class Lighthouse(LighthouseType):
    class Meta:
        namespace = "http://www.iho.int/S-201/gml/cs0/2.0"
