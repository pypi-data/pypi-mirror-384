from enum import Enum


class Account(Enum):
    free = 'FREE'
    custom = 'CUSTOM'


usage_limits = {
    Account.free: 10000,
    Account.custom: 50000000,
}

CUSTOM_ACCOUNT_EMAIL_DOMAINS = [
    "visual-layer.com",
    "intuitivo.com"
]

CUSTOM_ACCOUNT_EMAILS = {
    "intuitivo-ai-development"
    "intuitivo-ai-staging",
    "intuitivo-ai-production",
    "intuitivo-showroom",
    "dickson.neoh@gmail.com",
    "sergiubrega@gmail.com",
    "eldad.vizel@gmail.com",
    "bereket.sharew@mhsglobal.com",
    "yuval.solaz@gmail.com",
    "maxxxis123@gmail.com"
}


class LimitType(str, Enum):
    MAX_DATASET_RAW_SIZE = 'MAX_DATASET_RAW_SIZE'
    MAX_FILE_SIZE = 'MAX_FILE_SIZE'
    MAX_USER_QUOTA = 'MAX_USER_QUOTA'
