environment: requirements.txt
	@python -m venv environment
	@source environment/bin/activate && pip install -r requirements.txt
