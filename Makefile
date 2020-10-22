FLAKE8?=	flake8
MYPY?=		mypy
BLACK?=		black

lint:: flake8 mypy black-check

flake8:
	${FLAKE8} pypicache

mypy:
	${MYPY} pypicache

black:
	${BLACK} -S pypicache/*.py

black-check:
	${BLACK} -S --check pypicache/*.py
