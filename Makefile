PROJECT = trade
PYTHON_VERSION=3.6
venv_name = py${PYTHON_VERSION}-${PROJECT}
venv = .venv/${venv_name}

export DEVELOPMENT=false

default: ${venv}
.PHONY: default

${venv}: requirements.txt
	python${PYTHON_VERSION} -m venv ${venv}
	. ${venv}/bin/activate; pip install --upgrade pip Cython==0.28 --cache .tmp/
	. ${venv}/bin/activate; pip install -r requirements.txt --cache .tmp/
	@echo Success, to activate the development environment, run:
	@echo "\tsource .venv/${venv_name}/bin/activate"

install_deps:
	pip install --upgrade --force-reinstall -r requirements.txt

