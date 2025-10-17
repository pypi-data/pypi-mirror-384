.PHONY: clean deploy-pypi run

clean:
	rm -rf dist

deploy-pypi: clean
	python3 -m build
	python3 -m twine upload dist/*

run:
	python3 -m raphson_music_headless -c config.json
