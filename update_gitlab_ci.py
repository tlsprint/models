import requests
import json
import os


def main():
    # Query private token
    private_token = os.environ["GITLAB_PRIVATE_TOKEN"]
    project_id = "13046295"

    headers = {
        "PRIVATE-TOKEN": private_token,
    }

    payload = {
        "id": project_id,
        "branch": "test",
        "commit_message": "This is a test",
        "actions": [
            {
                "action": "create",
                "file_path": "test_bla",
                "content": "teststetstststetset",
            }
        ]
    }

    req = requests.post(f"https://gitlab.com/api/v4/projects/{project_id}/repository/commits", headers=headers, json=payload)
    print(req)
    print(json.dumps(json.loads(req.content.decode()), indent=4))


if __name__ == "__main__":
    main()
