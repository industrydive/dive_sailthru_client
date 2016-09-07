pythonqa:
	docker run --rm -v ${PWD}:/code dbarbar/pythonqa:latest
test:
	docker run --rm -v ${PWD}:/code python:2.7 python /code/setup.py test
