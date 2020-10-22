PYTHON?=	python3
FLAKE8?=	flake8
MYPY?=		mypy

lint:: flake8 mypy

flake8:
	${FLAKE8} pypicache

mypy:
	${MYPY} ${MYPY_ARGS} pypicache
