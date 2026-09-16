# Infraestructura como código

Manifiestos de Kubernetes gestionados con **kustomize** (incluido en `kubectl`).

```
infra/k8s/
├── base/                 # recursos comunes a todos los entornos
│   ├── namespace.yaml
│   ├── configmap.yaml    # configuración no sensible
│   ├── secret.example.yaml  # plantilla; el Secret real nunca se versiona
│   ├── deployment.yaml   # 2 réplicas, probes, hardening del contenedor
│   ├── service.yaml      # LoadBalancer → balancea entre las réplicas
│   ├── hpa.yaml          # crecimiento dinámico 2..6 réplicas por CPU
│   └── pdb.yaml          # garantiza al menos 1 pod durante mantenimientos
└── overlays/
    ├── dev/              # namespace devops-service-dev, HPA acotado
    └── prod/             # producción (rama main)
```

## Despliegue manual

```bash
kubectl create namespace devops-service
kubectl -n devops-service create secret generic devops-service-secrets \
  --from-literal=API_KEY="$API_KEY" \
  --from-literal=JWT_SECRET="$JWT_SECRET"

cd infra/k8s/overlays/prod
kustomize edit set image ghcr.io/OWNER/devops-service=ghcr.io/<tu-usuario>/devops-service:<tag>
kubectl apply -k .
kubectl -n devops-service rollout status deployment/devops-service
kubectl -n devops-service get svc devops-service   # EXTERNAL-IP del balanceador
```

El HPA necesita `metrics-server` en el clúster (en minikube: `minikube addons enable metrics-server`).
