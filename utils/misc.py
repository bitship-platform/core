
class PythonAppConfig:
    versions = {
        "3.6": "python-3.6.12",
        "3.7": "python-3.7.9",
        "3.8": "python-3.8.7",
        "3.9": "python-3.9.1",
    }
    buildpacks = [
        "heroku/python",
    ]


class NodeAppConfig:
    versions = {
        "10": "10.x",
        "12": "12.x",
        "14": "14.x",
        "15": "15.x",
    }
    buildpacks = [
        "heroku/nodejs",
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
      "size": "free"  # For Testing, Will accept all types after working alpha release, (heroku only)
    }
  },
  "addons": [

  ],
  "buildpacks": [

  ],
  "environments": {

  }
}
