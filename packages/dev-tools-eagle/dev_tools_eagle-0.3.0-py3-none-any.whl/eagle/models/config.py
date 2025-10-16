import os
from eagle.utils.configs import find_env_upwards

class Config:
    def __init__(self):
        find_env_upwards(".test.env")
        
        # SSL configs
        self.ssl_cert_file2 = os.getenv('SSL_CERT_FILE2', None)
        os.environ['SSL_CERT_FILE'] = self.ssl_cert_file2
        os.environ['PRIMP_CA_BUNDLE'] = self.ssl_cert_file2
        self.ssl_cert_file = os.getenv('SSL_CERT_FILE', None)

        # OpenAI configs
        self.openai_api_key = os.getenv('OPENAI_API_KEY', None)
        self.openai_base_url = os.getenv('OPENAI_BASE_URL', None)
        self.openai_api_type = os.getenv('OPENAI_API_TYPE', None)
        self.openai_api_version = os.getenv('OPENAI_API_VERSION', None)

        if self.openai_api_type == 'azure':
            os.environ['AZURE_OPENAI_API_KEY'] = self.openai_api_key
            os.environ['AZURE_OPENAI_ENDPOINT'] = self.openai_base_url

        # Azure OpenAI configs
        self.azure_openai_api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.azure_openai_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')

        # Langfuse configs
        self.langfuse_host = os.getenv('LANGFUSE_HOST', 'http://localhost:3000')
        self.langfuse_public_key = os.getenv('LANGFUSE_PUBLIC_KEY', '')
        self.langfuse_secret_key = os.getenv('LANGFUSE_SECRET_KEY', '')

    def get_configs(self):
        return {
            'SSL_CERT_FILE': self.ssl_cert_file,
            'AZURE_OPENAI_API_KEY': self.openai_api_key,
            'AZURE_OPENAI_ENDPOINT': self.openai_base_url,
            'OPENAI_API_KEY': self.openai_api_key,
            'OPENAI_BASE_URL': self.openai_base_url,
            'OPENAI_API_TYPE': self.openai_api_type,
            'OPENAI_API_VERSION': self.openai_api_version,
            'LANGFUSE_HOST': self.langfuse_host,
            'LANGFUSE_PUBLIC_KEY': self.langfuse_public_key,
            'LANGFUSE_SECRET_KEY': self.langfuse_secret_key
        }
