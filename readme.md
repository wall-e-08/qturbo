## QUOTE TURBO ##

**full docs and details info will be updated later**

##

[dev url](http://qturbo.dev.concitus.com)

Project Run Steps:

- Step 0: go to the project root folder
- Step 1: create virtual env: `virtualenv -p python3 env`
- Step 2: activate virtual env: `source env/bin/activate`
- Step 3: make sure venv created: `pip install -r requirements.txt`
- Step 4: create database: `./db/create_db`
- Step 5: get some dummy data: `./dokku_postdeploy.sh`
- Step 6: contact developer to get the media folder for some dummy images

Celery run steps:
- Step 0: run celery worker:
```bash
 celery -A core worker -l info -Q stm,lim,anc,esign_check -c 4
```
- Step 1: run celery beat:
```bash
 celery -A core beat -l info
```

Todo:
 - Hashbang solution for SPA. Solution: [vue router](https://router.vuejs.org/guide/essentials/history-mode.html#example-server-configurations) @debu @ahsan
 - Add `Error message` in context of all ajax request in SPA @torsho