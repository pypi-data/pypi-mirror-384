import boto3
from botocore.exceptions import ClientError


class AwsParameterStore:
    """
    Python implementation of AWS Parameter Store client with role assumption capabilities.
    """

    INTEGRATIONS_PARAMETER_PATH = "/codemie/autotests/integrations/"
    _instance = None

    def __init__(self, access_key: str, secret_key: str, session_token: str = ""):
        """
        Initialize AWS Parameter Store with credentials and optional session token.

        Args:
            access_key (str): AWS access key ID
            secret_key (str): AWS secret access key
            session_token (str): AWS session token (optional)
        """
        self.region = "eu-central-1"

        # Initialize the session with basic credentials
        if not session_token:
            credentials = {
                "aws_access_key_id": access_key,
                "aws_secret_access_key": secret_key,
                "region_name": self.region,
            }
        else:
            credentials = {
                "aws_access_key_id": access_key,
                "aws_secret_access_key": secret_key,
                "aws_session_token": session_token,
                "region_name": self.region,
            }

            # Assume role if session token is provided
            sts_client = boto3.client("sts", **credentials)
            assumed_role = sts_client.assume_role(
                RoleArn="arn:aws:iam::025066278959:role/CodeMieAutotestsIntegrations",  # Replace with actual role ARN
                RoleSessionName="AutotestsUser",
            )

            # Update credentials with assumed role
            credentials = {
                "aws_access_key_id": assumed_role["Credentials"]["AccessKeyId"],
                "aws_secret_access_key": assumed_role["Credentials"]["SecretAccessKey"],
                "aws_session_token": assumed_role["Credentials"]["SessionToken"],
                "region_name": self.region,
            }

        # Initialize SSM client
        self.ssm_client = boto3.client("ssm", **credentials)

    @classmethod
    def get_instance(
        cls, access_key: str, secret_key: str, session_token: str = ""
    ) -> "AwsParameterStore":
        """
        Get singleton instance of AwsParameterStore.

        Args:
            access_key (str): AWS access key ID
            secret_key (str): AWS secret access key
            session_token (str): AWS session token (optional)

        Returns:
            AwsParameterStore: Singleton instance
        """
        if cls._instance is None:
            cls._instance = cls(access_key, secret_key, session_token)
        return cls._instance

    def get_parameter(self, parameter_name: str) -> str:
        """
        Get a parameter value from Parameter Store.

        Args:
            parameter_name (str): Name of the parameter to retrieve

        Returns:
            str: Parameter value

        Raises:
            ClientError: If parameter cannot be retrieved
        """
        try:
            response = self.ssm_client.get_parameter(Name=parameter_name)
            return response["Parameter"]["Value"]
        except ClientError as e:
            print(f"Error getting parameter: {parameter_name}! Error message: {str(e)}")
            raise
