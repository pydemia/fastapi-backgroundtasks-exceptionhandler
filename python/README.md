
```bash
CONTAINER_NAME=pydemia/fastapi-demo:latest
docker build . -f app.Dockerfile -t ${CONTAINER_NAME} && \
docker push ${CONTAINER_NAME}
```

```bash
kubectl create secret generic docker-cred \
    -n default \
    --from-file=.dockerconfigjson="${HOME}/.docker/config.json" \
    --type=kubernetes.io/dockerconfigjson
```

```bash
kubectl apply -f sa-with-imagepullsecret.yaml
```

```bash
kubectl apply -f deployment.yaml
```