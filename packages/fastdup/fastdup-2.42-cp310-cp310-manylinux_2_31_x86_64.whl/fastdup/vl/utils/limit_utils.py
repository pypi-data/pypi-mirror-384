from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from fastdup.vl.common.const import INT_MAX_64
from fastdup.vl.common.settings import Settings
from fastdup.vldbaccess.models.limits import Account, usage_limits, CUSTOM_ACCOUNT_EMAIL_DOMAINS, LimitType, \
    CUSTOM_ACCOUNT_EMAILS
from fastdup.vldbaccess.user import User, UserDB


def get_email_domain(email) -> Optional[str]:
    if email is None:
        return None
    if not isinstance(email, str):
        return None
    if '@' not in email:
        return None
    domain = email[email.index('@') + 1:]
    if not domain:
        return None
    return domain


def get_user_account(email: Optional[str]) -> Account:
    if email in CUSTOM_ACCOUNT_EMAILS:
        return Account.custom
    if get_email_domain(email) in CUSTOM_ACCOUNT_EMAIL_DOMAINS:
        return Account.custom
    return Account.free


def is_free_user(email: Optional[str]) -> bool:
    return get_user_account(email) == Account.free


class UsageReport(BaseModel):
    user_id: Optional[UUID] = None
    email: Optional[str] = None
    account: Optional[Account] = Account.free
    image_usage: Optional[int] = None
    image_quota: Optional[int] = None
    remaining_quota: Optional[int] = None

    @classmethod
    def from_user(cls, user: User):
        user_account = get_user_account(user.email)

        image_quota_from_db = UserDB.get_image_quota(user.user_id)
        if image_quota_from_db is None:  # quota not set yet; fallback to usage_limits
            image_quota = usage_limits[user_account]
        else:
            image_quota = image_quota_from_db

        image_usage = UserDB.get_image_usage(user.user_id)
        remaining_quota = max(image_quota - image_usage, 0)

        return cls(
            user_id=user.user_id,
            email=user.email,
            account=user_account,
            image_usage=UserDB.get_image_usage(user.user_id),
            image_quota=image_quota,
            remaining_quota=remaining_quota

        )


def get_limit(user: User, limit_type: LimitType) -> int:
    email_domain = get_email_domain(user.email)

    if email_domain in ['visual-layer.com']:
        return INT_MAX_64

    else:
        if limit_type == LimitType.MAX_DATASET_RAW_SIZE:
            return Settings.DATA_INGESTION_MAX_SIZE_BYTES
        elif limit_type == LimitType.MAX_FILE_SIZE:
            return Settings.DATA_INGESTION_MAX_FILE_SIZE
        elif limit_type == LimitType.MAX_USER_QUOTA:
            return UsageReport.from_user(user).remaining_quota
