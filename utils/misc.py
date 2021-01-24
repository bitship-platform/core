
class PythonAppConfig:
    python_versions = {
        "3.6": "python-3.6.12",
        "3.7": "python-3.7.9",
        "3.8": "python-3.8.7",
        "3.9": "python-3.9.1",
    }
    buildpacks = [
        "heroku/python",
    ]


sample_app_json = {
  "name": "",
  "description": "",
  "keywords": [
  ],
  "env": {

  },
  "formation": {
    "worker": {
      "quantity": 1,
      "size": "free"
    }
  },
  "image": "heroku/python",
  "addons": [

  ],
  "buildpacks": [

  ],
  "environments": {

  }
}
