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
./manage.py loaddata db/fixtures/general_topic.json

./manage.py loaddata db/fixtures/carrier.json


unzip -o benefits-img.zip -d /var/dokku_apps/qturbo/media/benefits/
unzip -o benefits-img.zip -d media/benefits/
./manage.py loaddata db/fixtures/feature.json
./manage.py loaddata db/fixtures/benefits.json
./manage.py loaddata db/fixtures/disclaimers.json
