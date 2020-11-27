FLAKE8?=	flake8
MYPY?=		mypy

lint:: flake8 mypy

flake8:
	${FLAKE8} --application-import-names=pypicache pypicache

mypy:
	${MYPY} pypicache
