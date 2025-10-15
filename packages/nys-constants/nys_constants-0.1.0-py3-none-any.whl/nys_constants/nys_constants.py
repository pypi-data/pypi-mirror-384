from enum import Enum, IntEnum

class JobType(str, Enum):
    # Logistic Requests
    BUFFERING = "BUFFERING"
    RETRIEVING = "RETRIEVING"
    STORING = "STORING"

    PICKING = "PICKING"
    REFILLING = "REFILLING"
    CHECKING = "CHECKING"
    PACKING = "PACKING"

    # Onboard a Bot
    ONBOARDING = "ONBOARDING" # this is the one displayed in the UI
    ONBOARDING_BD = "ONBOARDING_BD"
    ONBOARDING_BC = "ONBOARDING_BC"
    CLEARING_BALCONY = "CLEARING_BALCONY"
    PLACING_NOYESBOT = "PLACING_NOYESBOT"
    STARTING_NOYESBOT = "STARTING_NOYESBOT"
    SENDING_NOYESBOT_IN = "SENDING_NOYESBOT_IN"


    # Offboard a Bot
    OFFBOARDING = "OFFBOARDING" # this is the one displayed in the UI
    OFFBOARDING_BD = "OFFBOARDING_BD"
    OFFBOARDING_BC = "OFFBOARDING_BC"
    WAITING_FOR_NOYESBOT = "WAITING_FOR_NOYESBOT"
    TURNING_OFF_NOYESBOT = "TURNING_OFF_NOYESBOT"
    REMOVING_NOYESBOT = "REMOVING_NOYESBOT"
    
    # Pause / Resume all Bots
    PAUSING = "PAUSING"
    RESUMING = "RESUMING"

    # Move Bot to target
    MOVING_BOT = "MOVING_BOT"

    # Level Initializization
    CONNECTING_TO_BOTS = "CONNECTING_TO_BOTS"
    REFRESHING_LEVEL = "REFRESHING_LEVEL"
    UNCHARGING_ALL = "UNCHARGING_ALL"
    CLEARING_AUTOBAHN = "CLEARING_AUTOBAHN"

    # System Control
    CHARGING = "CHARGING"
    UNCHARGING = "UNCHARGING"

    # RFID
    WRITING_RFID_TAG = "WRITING_RFID_TAG"
    CHECKING_RFID_TAG = "CHECKING_RFID_TAG"
    CHANGING_RFID_WRITING_MODE = "CHANGING_RFID_WRITING_MODE"

    # Default
    NOT_DEFINED = "JOB_TYPE_NOT_FOUND"

    # Default enum member if the value is defined
    @classmethod
    def default(cls):
        return cls.NOT_DEFINED  # You can specify a different default enum

    _descriptions = {
        "BUFFERING" : "Moves a Carrier to a Buffer Space on the same Level.",
        "RETRIEVING" : "Moves a Carrier to a Balcony on the same Level.",
        "STORING" : "Moves a Carrier from the Balcony.",
        "PICKING" : "Let's the User pick a given amount out of a Box.",
        "REFILLING" : "Let's the User refill a given amount into a Box.",
        "CHECKING" : "Let's the User check a given Carrier Label.",
        "PACKING" : "Let's the User check the summary of a Request after all Entities have been worked on.",
        "ONBOARDING" : "Let's the User onboard a Bot to any level.",
        "ONBOARDING_BD" : "Adds a Bot to the Data Base and informs all Brain Components about it.",
        "CLEARING_BALCONY" : "Gives the User the instruction to confirm that the Balcony is free. Used during Onboarding.",        
        "PLACING_NOYESBOT" : "Gives the User the instruction to place the Bot on the Balcony. Used during Onboarding.",
        "STARTING_NOYESBOT" : "Gives the User the instruction to start the Bot. Used during Onboarding.",
        "SENDING_NOYESBOT_IN": "Gives the User the instruction to send the Bot inside the Storage.",
        "ONBOARDING_BC" : "Moves a Bot from the Balcony inside the Storage. Used during Onboarding.",
        "OFFBOARDING" : "Moves a Bot to the Balcony.",
        "OFFBOARDING_BD" : "Let's the User remove a Bot from the Balcony.",
        "OFFBOARDING_BC" : "Moves a Bot to the Balcony.",
        "PAUSING" : "Makes sure no Bot gets new commands.",
        "RESUMING" : "Allows all Bots to get new commands after PAUSE.",
        "MOVING_BOT" : "Moves a Bot to a target location / rotation / lifting state.",
        "CONNECTING_TO_BOTS" : "Establishes a connection to all Bots that are in the Database.",
        "REFRESHING_LEVEL" : "Updates the digital twin in the Bot Coordinator to the Database.",
        "UNCHARGING_ALL" : "Removes all Bots from the Charging Station.",
        "CLEARING_AUTOBAHN" : "Removes all Carriers from the Highway.",
        "CHARGING" : "Moves a given bot to a Charging Station.",
        "UNCHARGING" : "Removes a given bot from the Charging Station.",
        "CHECKING_RFID_TAG" : "Checks the values written on a RFID Tag at the given Location and Rotation.",
        "WRITING_RFID_TAG" : "Writes values to a RFID Tag at the given Location and Rotation.",
        "CHANGING_RFID_WRITING_MODE" : "Changes whether or not a bot should ignore the values on a RFID Tag while driving.",
        "WAITING_FOR_NOYESBOT" : "Informs the User that he needs to wait for the bot to come to the balcony. Used during offboarding.",
        "TURNING_OFF_NOYESBOT" : "Informs the User that the bot needs to be turned off before it can be removed from the balcony. Used during offboarding.",
        "REMOVING_NOYESBOT" : "Informs the User that the bot is being removed from the balcony. Used during offboarding.",

    }

    @property
    def description(self):
        # Return the description or the default value if not found
        return self._descriptions.get(self.value, "No Description available.")
    


# Job types shown in the UI (used by nys_brain and nys_store_db)
UI_JOB_TYPES = [
    JobType.PICKING, 
    JobType.REFILLING, 
    JobType.CHECKING, 
    JobType.ONBOARDING, 
    JobType.OFFBOARDING,
    JobType.PACKING,
    JobType.CLEARING_BALCONY,
    JobType.PLACING_NOYESBOT,
    JobType.STARTING_NOYESBOT,
    JobType.SENDING_NOYESBOT_IN,
    JobType.WAITING_FOR_NOYESBOT,
    JobType.TURNING_OFF_NOYESBOT,
    JobType.REMOVING_NOYESBOT,
]

class JobStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    ERROR = "ERROR" # deprecated, update AGG, Tests and Cloud
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    ABORTED = "ABORTED" 

    _descriptions = {
        "ACCEPTED" : "Job is ACCEPTED. These transitions are allowed: EXECUTING, ERROR, CANCELLING, ABORTED.",
        "EXECUTING" : "Job is EXECUTING and waiting to be triggered. These transitions are allowed: ERROR, CANCELLING, ABORTED.",
        "SUCCEEDED" : "Job is SUCCEEDED. No transitions are allowed. This is a final state.",
        "CANCELLING" : "Job is CANCELLING. A user requested this job to be cancelled. These transisitions are allowed: CANCELLED, ABORTED.",
        "CANCELLED" : "Job is CANCELLED. A user requested this job to be cancelled. The CANCELLING was successfull. This is final state.",
        "ABORTED" : "Job is ABORTED due to a system problem. The System will try to recover from this. This is a final state."
    }

    @property
    def description(self):
        # Return the description or the default value if not found
        return self._descriptions.get(self.value, "No Description available.")

# depracate in future, should only be used in nys_test to model customer integrations
class JobStatusV1(str, Enum):
    """depracate in future, should only be used in nys_test to model customer integrations"""
    HOLD = "HOLD"
    SUCCEEDED = "SUCCEEDED"
    CREATED = "CREATED"
    ACCEPTED = "ACCEPTED" #TODO depracate
    EXECUTING = "EXECUTING"
    QUEUED = "QUEUED" #TODO depracate
    ABORTED = "ABORTED"
    CANCELLED = "CANCELLED"
    READY = "READY" #TODO what the heck is this
    WAITING_ON_WING = "WAITING_ON_WING" # TODO depracate
    RECOVERED = "RECOVERED" #TODO

class RequestType(str, Enum):
    # Logistic Requests
    FULFILLMENT = "FULFILLMENT"
    REPLENISHMENT = "REPLENISHMENT"
    FETCH = "FETCH"

    # System Control
    RFID_MAINTENANCE = "RFID_MAINTENANCE"
    ONBOARD = "ONBOARD"
    OFFBOARD = "OFFBOARD"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    CHARGING = "CHARGING"
    UNCHARGING = "UNCHARGING"
    UPDATE_CONTENT_CODE = "UPDATE_CONTENT_CODE"

    # internal
    LEVEL_INITIALIZATION = "LEVEL_INITIALIZATION"
    UNCHARGE_ALL = "UNCHARGE_ALL"

    RECHARGE = "RECHARGE"

    _description = {
        "FULFILLMENT": "A Logistic Request consisting of Pick-Entities (SkuEntity).", 
        "REPLENISHMENT": "A Logistic Request consisting of Refill-Entities (SkuEntity).",
        "FETCH": "A Logistic Request consisting of Fetch-Carrier-Entities.",
        "RFID_MAINTENANCE": "A System Control Request to write and / or check RFID Tags on a specified Level.",
        "ONBOARD": "A System Control Request to add a Noyes Bot to any Level.",
        "OFFBOARD":  "A System Control Request to remove a specific Noyes Bot from a Level.",
        "PAUSE":  "A System Control Request to remove a specific Noyes Bot from a Level.",
        "RESUME":  "A System Control Request to allow all Bots to get new commands after a PAUSE Request.",
        "CHARGING": "A System Control Request to move a Noyes Bot to a Charging Station.",
        "UNCHARGING": "A System Control Request to remove a Noyes Bot from a Charging Station.",
        "UPDATE_CONTENT_CODE": "A Request to update the content code of a carrier.",
        "RECHARGE": "A System internal Request sent from the Charging Manager to the Store Orchestrator.",
        "LEVEL_INITIALIZATION": "An internal Request Type used for initializing each Level of a Storage by Connecting to the bots, Updating the Database and Clearing the Highway."
    }

    @property
    def description(self):
        # Return the description or the default value if not found
        return self._descriptions.get(self.value, "No Description available.")





class RequestStatus(str, Enum):
    CREATED = "CREATED"
    ACCEPTED = "ACCEPTED"
    QUEUED = "QUEUED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    CANCELLED = "CANCELLED"
    ABORTED = "ABORTED"

class RequestStatusV1(str, Enum):
    """depracate in future, should only be used in nys_test to model customer integrations"""
    CREATED = "CREATED"
    ACCEPTED = "ACCEPTED"
    QUEUED = "QUEUED" # deprecated
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    COMPLETED = "COMPLETED" # deprecated
    IN_PROGRESS = "IN_PROGRESS"  # deprecated
    STOPPED = "STOPPED" #TODO
    CANCELLED = "CANCELLED" #TODO combine with stopped
    ABORTED = "ABORTED" # backward compatibility to V1

# TODO: Actually use this enum
class RequestPriority(IntEnum):
    LOW = 5
    MEDIUM = 10
    HIGH = 20

class ContentCode(IntEnum):
    NONE_CONTENT_CODE = 0
    EMPTY = 10
    FULL = 11
    LOW_LEVEL = 20
    HIGH_LEVEL = 21
    BIG_BOX = 30
    MEDIUM_BOX = 31
    SMALL_BOX = 32
    MINI_BOX = 33
    COOLING_BOX = 3

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.name == value:
                    return member
            raise ValueError(f"{value} is not a valid {cls.__name__}")
        

class ContentCodeUpdateStatus(str, Enum):
    NONE_CONTENT_CODE_UPDATE = "NONE_CONTENT_CODE_UPDATE"
    FAILED_CONTENT_CODE_UPDATE = "FAILED_CONTENT_CODE_UPDATE"
    SUCCEEDED_CONTENT_CODE_UPDATE = "SUCCEEDED_CONTENT_CODE_UPDATE"


class TriggerType(str, Enum):
    # TODO: Remove the concept of trigger type. The triggers are sent by job id
    NOT_SPECIFIED = "NOT_SPECIFIED"
    PICKING_TRIGGER = "PICKING_TRIGGER"
    REFILLING_TRIGGER = "REFILLING_TRIGGER"
    ONBOARDING_TRIGGER = "ONBOARDING_TRIGGER"
    OFFBOARDING_TRIGGER = "OFFBOARDING_TRIGGER"
    BRING_CARRIER_TO_BALCONY_TRIGGER = "BRING_CARRIER_TO_BALCONY_TRIGGER"
    FETCH_TRIGGER = "FETCH_TRIGGER"
    UNPLUG_TRIGGER = "UNPLUG_TRIGGER"


class TriggerStatus(str, Enum):
    SUCCEEDED_TRIGGER = "SUCCEEDED_TRIGGER"
    CANCELLED_TRIGGER = "CANCELLED_TRIGGER"


class EntityType(str, Enum):
    SKU = "Sku"
    PRODUCT = "Product" # TODO remove once the B2B API is updated to only use SKUs
    CARRIER = "Carrier"
    CONTENT_CODES = "CONTENT_CODES" #TODO deprecate
    BOX = "Box"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class SortByQuantity(str, Enum):
    FULFILLABLE = "fulfillable"
    REPLENISHABLE = "replenishable"

class GroupByOptions(str, Enum):
    REQUESTS = "Requests"
    SKUS = "SKUs"

class OnEmptySKUAction(str, Enum):
    DO_NOTHING = "DO_NOTHING"  # Keep the SKU assigned even if empty
    UNASSIGN = "UNASSIGN"      # Remove the SKU from the box when empty

class MeasurementUnit(str, Enum):
    PIECE = "PIECE"
    EACH = "EACH"
    GRAM = "GRAM"
    CENTIMETER = "CENTIMETER"
    MILLILITER = "MILLILITER"

class MeasurementUnitShort(str, Enum):
    PIECE = "Pcs."
    EACH = "Ea."
    GRAM = "g"
    CENTIMETER = "cm"
    MILLILITER = "ml"

class StorageModuleType(str, Enum):
    """Different types of storage modules in the system"""
    WALL = "wall"
    BALCONY = "balcony" 
    WING = "wing"
    STORING_POSITION = "storing_position"
    HIGHWAY = "highway"
    ELEVATOR = "elevator"
    CHARGING_STATION = "charging_station"
    BAY = "bay"
    UNKNOWN = "unknown"
    
    @classmethod
    def default(cls):
        return cls.UNKNOWN
    
class LevelStatus(str, Enum):
    # Priority mapping for level statuses, kept inside the class
    __PRIORITIES__ = {
        "RUNNING": 1,
        "PAUSED": 2,
        "STARTING_UP": 3,
        "MAINTENANCE": 4,
        "ERROR": 5,
        "OFF": 6,
        "SHUTTING_DOWN": 7
    }

    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    MAINTENANCE = "MAINTENANCE"
    STARTING_UP = "STARTING_UP"
    ERROR = "ERROR"
    OFF = "OFF"
    SHUTTING_DOWN = "SHUTTING_DOWN"

    @property
    def priority(self) -> int:
        return type(self).__PRIORITIES__[self.value]

class StorageStatus(str, Enum):
    """Storage status, ordered depending on their "weight". 
    While calculating overall storage status: 
        - if all the levels are in the same status, that will be the overall storage status;
        - if at least one level is in a status with a bigger "weight", that will become the overall storage status.
    """
    __PRIORITIES__ = {
        "RUNNING": 1,
        "PAUSED": 2,
        "STARTING_UP": 3,
        "MAINTENANCE": 4,
        "ERROR": 5,
        "OFF": 6,
        "SHUTTING_DOWN": 7
    }
    
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    MAINTENANCE = "MAINTENANCE"
    ERROR = "ERROR"
    OFF = "OFF"
    STARTING_UP = "STARTING_UP"
    SHUTTING_DOWN = "SHUTTING_DOWN"
 
    @property
    def priority(self) -> int:
        return type(self).__PRIORITIES__[self.value]


AUTOBAHN_MODULE_TYPES = [
        StorageModuleType.HIGHWAY,
        StorageModuleType.WING,
        StorageModuleType.BALCONY,
        StorageModuleType.STORING_POSITION
    ]

# Set of storage module types that should have RFID tags written to them
WRITABLE_MODULE_TYPES = {
    StorageModuleType.BALCONY,
    StorageModuleType.WING,
    StorageModuleType.STORING_POSITION,
    StorageModuleType.HIGHWAY,
    StorageModuleType.CHARGING_STATION,
    StorageModuleType.BAY
}

class LogLevel(IntEnum):
    """ Log level for logs describing their severity. """
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    

