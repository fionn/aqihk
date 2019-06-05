VENV ?= venv

$(VENV): requirements.txt
	@python -m venv $@ --prompt $@::aq
	@source $@/bin/activate && pip install -r $<
