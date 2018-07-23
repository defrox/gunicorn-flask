kubectl proxy -p 8080 & curl -L --data '{"Another": "Echo"}' \
  --header "Content-Type:application/json" \
  localhost:8080/api/v1/namespaces/default/services/hello:http-function-port/proxy/
{"Another": "Echo"}


# Connect to EC2 using SSH #
ssh -L30000:localhost:30000 -L30001:172.31.10.3:31520 -L8443:172.31.10.3:8443 -i ~/aws/aws-test.pem ubuntu@34.247.215.202

# Install Docker #
sudo apt-get update -y && sudo apt-get install -y docker.io

# Install minikube #
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 && chmod +x minikube && sudo mv minikube /usr/local/bin/

# Verify version #
minikube version

# Install or Upgrade Kubectl CLI #
curl -Lo kubectl https://storage.googleapis.com/kubernetes-release/release/v1.8.0/bin/linux/amd64/kubectl && chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Add kubectl autocompletion to your current shell #
source <(kubectl completion bash)

# Start minikube (in EC2 must be with --vm-driver=none and sudo) #
sudo minikube start --vm-driver=none

# Check status #
minikube status

# Open minikube dashboard #
http://127.0.0.1:30000/

# Deploy kubeless #
export RELEASE=$(curl -s https://api.github.com/repos/kubeless/kubeless/releases/latest | grep tag_name | cut -d '"' -f 4)
kubectl create ns kubeless
kubectl create -f https://github.com/kubeless/kubeless/releases/download/$RELEASE/kubeless-$RELEASE.yaml

# Install unzip if not installed #
sudo apt install unzip

# Install kubeless-cli #
export OS=$(uname -s| tr '[:upper:]' '[:lower:]')
curl -OL https://github.com/kubeless/kubeless/releases/download/$RELEASE/kubeless_$OS-amd64.zip && \
  unzip kubeless_$OS-amd64.zip && \
  sudo mv bundles/kubeless_$OS-amd64/kubeless /usr/local/bin/

# Deploy kubeless-ui #
kubectl create -f https://raw.githubusercontent.com/kubeless/kubeless-ui/master/k8s.yaml

# Get kubeless-ui url and open it in browser #
minikube service ui -n kubeless --url

# If EC2, close ssh connection and add a new port routing to the ip:port #
ssh -L30001:kubeless-ip:kubeless-port

# Open kubeless-ui #
http://localhost:30001

# or #
https://127.0.0.1:8443/api/v1/namespaces/kubeless/services/ui:31520/proxy/

# Pattern tip #
http://kubernetes_master_address/api/v1/namespaces/namespace_name/services/service_name[:port_name]/proxy

mkdir /opt/registry/auth
docker run --entrypoint htpasswd registry:2 -Bbn admin design >> /opt/registry/auth/htpasswd

# Launch local docker registry #
docker run -d -p 5000:5000 --restart=always --name registry registry:2

# Build docker image #
docker build . -f Dockerfile.runtime -t defrox/runtime:v0.3

# Tag docker image #
docker tag runtime:v0.1 defrox/runtime:v0.1

# Push docker image to local registry #
docker push defrox/runtime:v0.1

# Create test function in python #
nano test.py

# Paste code and save #
def score(event, context):
  print event
  return event['data']

# Deploy test function to kubeless #
kubeless function deploy --from-file test.py --handler test.score --runtime python2.8 score

# Check if the funtion has been deployed and is ready #
kubeless function ls hello

# Call the function with #
kubeless function call score --data '{"file": "lib/test.csv"}'

# Or curl directly with #
kubectl proxy -p 8080 & \
curl -L --data '{"file": "lib/test.csv"}' \
  --header "Content-Type:application/json" \
  localhost:8080/api/v1/namespaces/default/services/hello:http-function-port/proxy/
{"Another": "Echo"}

# Shutdown cluster #
minikube stop

# Delete cluster #
minikube delete


