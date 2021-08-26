FROM python:3.8
COPY requirements.txt requirements.txt
CMD ["/bin/bash"]
RUN apt-get update
RUN apt-get -y install gnupg2
RUN apt-get -y install curl
RUN apt-get -y install software-properties-common
RUN apt-get update && apt-get install -y lsb-release && apt-get clean all
RUN yes | apt-get install openssh-server
RUN curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add -
RUN apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
RUN apt-get update && apt-get -y install vault
RUN setcap cap_ipc_lock= /usr/bin/vault
# RUN docker run --cap-add=IPC_LOCK -d --name=dev-vault vault
RUN pip install -r requirements.txt
