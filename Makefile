pythonqa:
	docker run --rm -v ${PWD}:/code dbarbar/pythonqa:latest
test:
	docker run --rm -v ${PWD}:/code -w /code python:2.7 python setup.py test
