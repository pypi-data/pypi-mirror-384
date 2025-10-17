import json

import requests
from github import Github
from pydantic import Field

from platzky.db.db import DBConfig
from platzky.db.json_db import Json as JsonDB


def db_config_type():
    return GithubJsonDbConfig


class GithubJsonDbConfig(DBConfig):
    github_token: str = Field(alias="GITHUB_TOKEN")
    repo_name: str = Field(alias="REPO_NAME")
    path_to_file: str = Field(alias="PATH_TO_FILE")
    branch_name: str = Field(alias="BRANCH_NAME", default="main")


def db_from_config(config: GithubJsonDbConfig):
    return GithubJsonDb(
        config.github_token, config.repo_name, config.branch_name, config.path_to_file
    )


def get_db(config):
    github_json_db_config = GithubJsonDbConfig.model_validate(config)
    return GithubJsonDb(
        github_json_db_config.github_token,
        github_json_db_config.repo_name,
        github_json_db_config.branch_name,
        github_json_db_config.path_to_file,
    )


class GithubJsonDb(JsonDB):
    def __init__(self, github_token: str, repo_name: str, branch_name: str, path_to_file: str):
        self.branch_name = branch_name
        self.repo = Github(github_token).get_repo(repo_name)
        self.file_path = path_to_file

        try:
            file_content = self.repo.get_contents(self.file_path, ref=self.branch_name)

            if isinstance(file_content, list):
                raise ValueError(f"Path '{self.file_path}' points to a directory, not a file")

            if file_content.content:
                raw_data = file_content.decoded_content.decode("utf-8")
            else:

                download_url = file_content.download_url
                response = requests.get(download_url, timeout=40)
                response.raise_for_status()
                raw_data = response.text

            self.data = json.loads(raw_data)

        except (json.JSONDecodeError, requests.RequestException) as e:
            raise ValueError(f"Error parsing JSON content: {e}")
        except Exception as e:
            raise ValueError(f"Error retrieving GitHub content: {e}")

        super().__init__(self.data)

        self.module_name = "github_json_db"
        self.db_name = "GithubJsonDb"
