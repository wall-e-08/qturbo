#!/bin/bash

./manage.py migrate


#./manage.py loaddata db/fixtures/auth_user.json
#./manage.py loaddata db/fixtures/profile.json
#./manage.py loaddata db/fixtures/section.json
#./manage.py loaddata db/fixtures/category.json
#./manage.py loaddata db/fixtures/post.json
#./manage.py loaddata db/fixtures/article.json
#./manage.py loaddata db/fixtures/blog.json
#./manage.py loaddata db/fixtures/categorize.json
#./manage.py loaddata db/fixtures/general_topic.json

./manage.py loaddata db/fixtures/carrier.json
