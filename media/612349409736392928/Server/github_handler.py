from github import Github

# using username and password
g = Github("237fde3a9d93d3f7388657bbbde0a86152b0714f")

user = g.get_user()


repo = user.create_repo("API-Test")

