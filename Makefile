.PHONY: help pep8 install deploy release startdev
.DEFAULT_GOAL= help

#include .env
#export $(shell sed 's/=.*//' envfile)
PORT?=8000
HOST?=127.0.0.1
COM_COLOR   = \033[0;34m
OBJ_COLOR   = \033[0;36m
OK_COLOR    = \033[0;32m
ERROR_COLOR = \033[0;31m
WARN_COLOR  = \033[0;33m
NO_COLOR    = \033[m

APP_VERSION = $(shell date +"%Y%m%d%H%M")
APP_NAME = "mynto.io_bot"
HEROKU_APP_NAME = "whatsappecommerce"
LATEST_RELEASE = $(shell ls -tp -w 1 *zip | head --lines=1)


help:
	@awk 'BEGIN {FS = ":.*##"; } /^[a-zA-Z_-]+:.*?##/ { printf "$(PRIMARY_COLOR)%-20s$(NO_COLOR) %s\n", $$1, $$2 }' $(MAKEFILE_LIST) | sort


clean-pyc: ## Clean all the pyc or pyo files
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~' -exec rm --force  {} + 
	find ./resources -name '*.pyc' -exec rm --force {} +
	find ./resources -name '*~' -exec rm --force  {} + 
	find ./resources -name '*.pyo' -exec rm --force  {} + 

clean-build: ## Delete the build and dist folders
	rm --force --recursive build/
	rm --force --recursive dist/
	rm --force --recursive *.egg-info

clean: clean-pyc clean-build # Clean the build, dist, pyo, pyc folders/files
	rm --force --recursive logs/*.txt

pep8: ## Run pep8 code stylz check on the codepath
	pep8 $(CODEPATH)

pep8-full: ## Run full pep8 style checking
	pep8 --show-source --show-pep8 $(CODEPATH)

pep8-stats: ## Show pep8 stats
	pep8 --statistics -qq $(CODEPATH)

stats: pep8-stats ## Show all the code styling stats.

isort:
	sh -c "isort --skip-glob=.tox --recursive . "

lint:
	flake8 --exclude=.tox

test: clean-pyc ## Run the tests
	#py.test --verbose --color=yes $(TEST_PATH)
	nosetests


install-and-test: install test ## Install the dependencies and run the tests


install: ## Install the dependencies
	virtualenv .venv -p /usr/bin/python3.5
	. ./.venv/bin/activate
	pip install -r requirements.txt

release: Readme.pdf requirements.txt ## Generate a zip file containing the files to deploy
	@echo App version is ${APP_VERSION}
	#cp config.json config.${APP_VERSION}.dev.json
	@echo Generating the documentation from the markdown file
	#pandoc Readme.md -o Readme.pdf
	@zip -r ${APP_NAME}_v${APP_VERSION}.zip Pipfile bot fleastore_bot settings static staticfiles *.py *.customer *.pdf *.cfg .env.example requirements.txt --exclude @exclude.lst

deploy: ## Push the zip file to the remote server.
	
	@echo Latest release : ${LATEST_RELEASE}
	@echo Uploading the released archive ${LATEST_RELEASE} to the server
	@scp ${LATEST_RELEASE} jeedom@192.168.1.24:/home/jeedom/customers/toniconstant343/vocabularybot

startdev: ## Start the development server using nodemon watcher
	@echo "Starting $(OK_COLOR)nodemon$(NO_COLOR) process to ease development"
	#@nodemon vocabulary_bot.py
	docker run -it --rm -v ${PWD}:/app -p 8002:8002  fullbright/python3.6.11-buster pipenv run python manage.py runserver 0.0.0.0:8002

requirements.txt: Pipfile
	pip freeze > requirements.txt

Readme.pdf: Readme.md
	#docker run -v `pwd`:/source fullbright/pandoc:0.1 Readme.md -o Readme.pdf
	./generate_pdf.sh

docker-test: ## Run tests in a docker container
	docker run --rm --env SLEEP_DURATION=30 -v $(MEDIAPATH):/home/fullbright/fr-replay-downloader/youtube -v $(LOGSPATH):/home/fullbright/fr-replay-downloader/logs -v $(CODEPATH)/tests/settings.yaml:/home/fullbright/fr-replay-downloader/settings.yaml  fullbright/replay-downloader
	
docker-debug: ## Run the application in a docker container in debug mode
	docker run -it --rm -v ${PWD}:/app fullbright/python3.6.11-buster /bin/bash

docker-build: ## Build the application in a docker container
	docker build -t fullbright/replay-downloader .

docker-run: ## Run the application in a docker container
	docker run -it --env SLEEP_DURATION=30 -v $(MEDIAPATH):/home/fullbright/fr-replay-downloader/youtube -v $(LOGSPATH):/home/fullbright/fr-replay-downloader/logs fullbright/replay-downloader


local-migrate-db:
	@echo "Migrating data in the db of the $(OK_COLOR) local dev $(NO_COLOR)"
	docker run -it --rm -v ${PWD}:/app -p 8002:8002  fullbright/python3.6.11-buster /bin/sh -c "pipenv run python manage.py makemigrations && sleep 3 && pipenv run python manage.py migrate"

heroku-migrate-db:
	@echo "Migrating data in the db of the application $(OK_COLOR) ${HEROKU_APP_NAME} $(NO_COLOR)"
	heroku run --app ${HEROKU_APP_NAME} /bin/sh -c "python manage.py makemigrations && sleep 3 && python manage.py migrate"
	#heroku run --app ${HEROKU_APP_NAME} python manage.py makemigrations
	#sleep 3
	#heroku run --app ${HEROKU_APP_NAME} python manage.py migrate
