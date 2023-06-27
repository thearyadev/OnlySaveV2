import json

authors = set()

with open("data.json", "r+") as file:
    data = json.load(file)["data"]


count = 0
nunce = 0
posts = list()
for postSet in data:
    postsx = postSet["list"]
    for post in postsx:
        for m in post.get("media"):
            print(m.get("full"))
