import os
import platform
import toml


class Config:
    def __init__(self):
        self.__config = self.__get_file_config()

    def get_active_env(self) -> str:
        return self.__config.get('default')

    @staticmethod
    def __get_file_config():
        user_dir = os.getenv("HOME", '') if platform.system() != 'Windows' else os.getenv("HOMEPATH", '')
        config_path = os.path.join(user_dir, '.hopara', 'default.toml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as fp:
                return toml.load(fp)
        return None

    def get_value(self, name):
        return self.__config[self.get_active_env()].get(name)

    def get_auth_url(self) -> str:
        auth_url = os.getenv("HOPARA_AUTH_URL")
        if auth_url is None and self.__config:
            auth_url = self.get_value('authEndpoint')
        return auth_url

    def get_dataset_url(self) -> str:
        dataset_url = os.getenv("HOPARA_DATASET_URL")
        if dataset_url is None and self.__config:
            dataset_url = self.get_value('datasetEndpoint')
        return dataset_url

    def get_template_url(self) -> str:
        template_url = os.getenv("HOPARA_TEMPLATE_URL")
        if template_url is None and self.__config:
            template_url = self.get_value('templateEndpoint')
        return template_url

    def get_visualization_url(self) -> str:
        visualization_url = os.getenv("HOPARA_VISUALIZATION_URL")
        if visualization_url is None and self.__config:
            visualization_url = self.get_value('visualizationEndpoint')
        return visualization_url

    def get_resource_url(self) -> str:
        email = os.getenv("HOPARA_RESOURCE_URL")
        if email is None and self.__config:
            email = self.get_value('resourceEndpoint')
        return email

    def get_email(self) -> str:
        email = os.getenv("HOPARA_EMAIL")
        if email is None and self.__config:
            email = self.get_value('email')
        return email

    def get_password(self) -> str:
        password = os.getenv("HOPARA_PASSWORD")
        if password is None and self.__config:
            password = self.get_value('password')
        return password

    @staticmethod
    def get_client_id() -> str:
        return os.getenv("HOPARA_CLIENT_ID")

    @staticmethod
    def get_client_secret() -> str:
        return os.getenv("HOPARA_CLIENT_SECRET")

    def get_credentials(self) -> str:
        client_id, client_secret = self.get_client_id(), self.get_client_secret()
        if client_id and client_secret:
            return {'clientId': client_id, 'clientSecret': client_secret}
        else:
            email, password = self.get_email(), self.get_password()
            if email and password:
                return {'email': email, 'password': password}
        return None


if __name__ == "__main__":
    config = Config()
    print(config.get_dataset_url())
    print(config.get_email())
    print(config.get_client_id())
    print(config.get_client_secret())
    print(config.get_credentials())
