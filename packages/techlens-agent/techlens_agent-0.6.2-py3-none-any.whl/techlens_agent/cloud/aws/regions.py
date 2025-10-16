regions = [
    "us-east-2",
    "us-east-1",
    "us-west-1",
    "us-west-2",
    "af-south-1",
    "ap-east-1",
    "ap-south-2",
    "ap-southeast-3",
    "ap-southeast-4",
    "ap-south-1",
    "ap-northeast-3",
    "ap-northeast-2",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-northeast-1",
    "ca-central-1",
    "eu-central-1",
    "eu-west-1",
    "eu-west-2",
    "eu-south-1",
    "eu-west-3",
    "eu-south-2",
    "eu-north-1",
    "eu-central-2",
    "me-south-1",
    "me-central-1",
    "sa-east-1",
]
gov_regions = [
    "us-gov-east-1",
    "us-gov-west-1",
]


def is_govcloud_account(session):
    try:
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        arn = identity["Arn"]
        return arn.startswith("arn:aws-us-gov:")
    except Exception as e:
        print(f"Error checking partition for {profile_name or 'default'}: {e}")
        return False


def get_regions_for_session(session):
    if is_govcloud_account(session):
        return gov_regions
    else:
        return regions
