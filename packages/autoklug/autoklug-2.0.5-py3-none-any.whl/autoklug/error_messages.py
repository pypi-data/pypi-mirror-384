"""
User-Friendly Error Messages for Autoklug

Provides clear, actionable error messages instead of cryptic technical errors.
"""

from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, ProfileNotFound, NoCredentialsError
import os


class ErrorMessageProvider:
    """Provides user-friendly error messages for common issues"""
    
    @staticmethod
    def get_aws_profile_error(profile_name: str) -> str:
        """Get user-friendly AWS profile error message"""
        if not profile_name or profile_name.strip() == "":
            return """🔧 AWS Profile Not Configured

The AWS profile is not set in your .tool file. Here's how to fix it:

1. Set up AWS credentials:
   • Run: aws configure
   • Or set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

2. Update your .tool file:
   AWS_PROFILE_BUILD=default
   (or your profile name)

3. Verify your setup:
   • Run: aws sts get-caller-identity
   • Run: autoklug config

💡 Need help? Check: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html"""
        else:
            return f"""🔧 AWS Profile '{profile_name}' Not Found

The AWS profile '{profile_name}' doesn't exist. Here's how to fix it:

1. Check available profiles:
   • Run: aws configure list-profiles
   • Run: cat ~/.aws/config

2. Create the profile:
   • Run: aws configure --profile {profile_name}
   • Or update .tool file: AWS_PROFILE_BUILD=default

3. Verify your setup:
   • Run: aws sts get-caller-identity --profile {profile_name}
   • Run: autoklug config

💡 Need help? Check: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html"""
    
    @staticmethod
    def get_aws_credentials_error() -> str:
        """Get user-friendly AWS credentials error message"""
        return """🔐 AWS Credentials Not Found

AWS credentials are not configured. Here's how to fix it:

1. Set up AWS credentials:
   • Run: aws configure
   • Or set environment variables:
     export AWS_ACCESS_KEY_ID=your_access_key
     export AWS_SECRET_ACCESS_KEY=your_secret_key
     export AWS_DEFAULT_REGION=your_region

2. Verify your setup:
   • Run: aws sts get-caller-identity
   • Run: autoklug config

💡 Need help? Check: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html"""
    
    @staticmethod
    def get_aws_permission_error(service: str, operation: str) -> str:
        """Get user-friendly AWS permission error message"""
        return f"""🚫 AWS Permission Denied

You don't have permission to {operation} on {service}. Here's how to fix it:

1. Check your IAM permissions:
   • Run: aws iam get-user
   • Run: aws iam list-attached-user-policies --user-name your-username

2. Required permissions for {service}:
   • {service}:{operation}
   • {service}:List*
   • {service}:Describe*

3. Contact your AWS administrator or add the permissions to your IAM policy

💡 Need help? Check: https://docs.aws.amazon.com/IAM/latest/UserGuide/access.html"""
    
    @staticmethod
    def get_config_file_error(file_path: str, file_type: str) -> str:
        """Get user-friendly config file error message"""
        return f"""📁 {file_type} File Issue

There's a problem with your {file_type} file: {file_path}

1. Check if the file exists:
   • Run: ls -la {file_path}

2. Check file permissions:
   • Run: ls -la {file_path}

3. Verify file format:
   • Make sure it's a valid {file_type} file
   • Check for syntax errors

4. Recreate if needed:
   • Run: autoklug template init

💡 Need help? Check the documentation for {file_type} file format."""
    
    @staticmethod
    def get_network_error(operation: str) -> str:
        """Get user-friendly network error message"""
        return f"""🌐 Network Connection Error

Failed to {operation} due to network issues. Here's how to fix it:

1. Check your internet connection:
   • Run: ping google.com
   • Run: curl -I https://aws.amazon.com

2. Check AWS service status:
   • Visit: https://status.aws.amazon.com/

3. Try again in a few minutes:
   • Network issues are often temporary

4. Check firewall/proxy settings:
   • Ensure AWS endpoints are not blocked

💡 Need help? Check: https://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html"""
    
    @staticmethod
    def get_validation_error(field: str, value: str, expected: str) -> str:
        """Get user-friendly validation error message"""
        return f"""⚠️ Configuration Validation Error

Invalid value for '{field}': '{value}'

Expected: {expected}

1. Check your .tool file:
   • Open: {field}={value}
   • Update to: {field}={expected}

2. Common valid values:
   • AWS_REGION: us-east-1, eu-west-1, ap-southeast-1, etc.
   • LAMBDA_RUNTIME: python3.11, python3.12, python3.13
   • LAMBDA_ROLE: arn:aws:iam::ACCOUNT:role/ROLE_NAME

3. Verify your configuration:
   • Run: autoklug config

💡 Need help? Check the documentation for valid configuration values."""
    
    @staticmethod
    def get_generic_error(error: Exception, context: str = "") -> str:
        """Get user-friendly generic error message"""
        error_type = type(error).__name__
        error_msg = str(error)
        
        base_message = f"""❌ Unexpected Error

Error Type: {error_type}
Error Message: {error_msg}"""
        
        if context:
            base_message += f"\nContext: {context}"
        
        base_message += """

1. Check your configuration:
   • Run: autoklug config
   • Verify .tool and .env files

2. Check AWS setup:
   • Run: aws sts get-caller-identity
   • Verify permissions

3. Try running with verbose output:
   • Add --verbose flag if available

4. Check the logs for more details

💡 If this error persists, please report it with the full error message."""
        
        return base_message


def get_user_friendly_error(error: Exception, context: str = "", **kwargs) -> str:
    """Get a user-friendly error message for any exception"""
    
    # AWS Profile errors
    if isinstance(error, ProfileNotFound):
        profile_name = kwargs.get('profile_name', '')
        return ErrorMessageProvider.get_aws_profile_error(profile_name)
    
    # AWS Credentials errors
    if isinstance(error, NoCredentialsError):
        return ErrorMessageProvider.get_aws_credentials_error()
    
    # AWS Client errors
    if isinstance(error, ClientError):
        error_code = error.response.get('Error', {}).get('Code', '')
        service = kwargs.get('service', 'AWS Service')
        operation = kwargs.get('operation', 'perform operation')
        
        if error_code in ['AccessDenied', 'UnauthorizedOperation']:
            return ErrorMessageProvider.get_aws_permission_error(service, operation)
        elif error_code in ['ThrottlingException', 'ServiceUnavailable']:
            return ErrorMessageProvider.get_network_error(operation)
    
    # File not found errors
    if isinstance(error, FileNotFoundError):
        file_path = str(error).split("'")[1] if "'" in str(error) else "unknown"
        if '.tool' in file_path:
            return ErrorMessageProvider.get_config_file_error(file_path, ".tool")
        elif '.env' in file_path:
            return ErrorMessageProvider.get_config_file_error(file_path, ".env")
    
    # Generic error
    return ErrorMessageProvider.get_generic_error(error, context)
