.PHONY: docker

docker/requirements.txt:
	cp requirements.txt docker/requirements.txt

docker: docker/requirements.txt
	docker build -t kit docker