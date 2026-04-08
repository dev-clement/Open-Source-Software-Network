from enum import Enum

class ContributionStatus(str, Enum):
    INTERESTED = "interested"
    CONTRIBUTE = "contribute"
    LEADER = "leader"
    APPROVER = "approver"
