FLAKE8?=	flake8
MYPY?=		mypy
ISORT?=		isort

lint:: flake8 mypy isort

flake8:
	${FLAKE8} pypicache

mypy:
	${MYPY} pypicache

isort::
	${ISORT} ${ISORT_ARGS} --check --diff pypicache

isort-fix::
	${ISORT} ${ISORT_ARGS} pypicache
