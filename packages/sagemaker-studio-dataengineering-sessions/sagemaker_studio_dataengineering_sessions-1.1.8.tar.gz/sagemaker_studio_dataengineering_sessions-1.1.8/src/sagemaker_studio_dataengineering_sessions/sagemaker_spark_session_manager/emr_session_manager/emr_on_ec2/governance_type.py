from enum import unique, Enum


@unique
class GovernanceType(Enum):
    AWS_MANAGED = "AWS_MANAGED"
    USER_MANAGED = "USER_MANAGED"
