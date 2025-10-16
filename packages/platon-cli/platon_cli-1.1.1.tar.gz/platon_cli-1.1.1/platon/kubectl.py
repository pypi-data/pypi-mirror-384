"""Kubernetes operations wrapper"""

import subprocess
import json
from typing import List, Dict, Optional
from datetime import datetime, timezone


class KubectlManager:
    """Manages kubectl operations"""

    def __init__(self, repo):
        self.repo = repo
        self.namespace = repo.namespace or self.get_current_namespace()

    def _run(self, *args, capture=True, namespace=None) -> Optional[str]:
        """Run kubectl command"""
        ns = namespace or self.namespace
        cmd = ["kubectl", "-n", ns] + list(args)
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        else:
            subprocess.run(cmd, check=True)
            return None

    def _run_global(self, *args, capture=True) -> Optional[str]:
        """Run kubectl command without namespace"""
        cmd = ["kubectl"] + list(args)
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        else:
            subprocess.run(cmd, check=True)
            return None

    def _calculate_age(self, timestamp: str) -> str:
        """Calculate human-readable age from ISO timestamp"""
        created = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        delta = now - created

        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        if days > 0:
            return f"{days}d{hours}h"
        elif hours > 0:
            return f"{hours}h{minutes}m"
        else:
            return f"{minutes}m"

    def get_pods(self, selector: Optional[str] = None, namespace: Optional[str] = None) -> List[Dict]:
        """List pods in namespace"""
        args = ["get", "pods", "-o=json"]
        if selector:
            args.extend(["-l", selector])

        output = self._run(*args, namespace=namespace)
        data = json.loads(output)

        pods = []
        for item in data.get("items", []):
            pods.append(
                {
                    "name": item["metadata"]["name"],
                    "namespace": item["metadata"]["namespace"],
                    "status": item["status"]["phase"],
                    "restarts": sum(
                        c.get("restartCount", 0)
                        for c in item["status"].get("containerStatuses", [])
                    ),
                    "age": self._calculate_age(item["metadata"]["creationTimestamp"]),
                    "created": item["metadata"]["creationTimestamp"],
                }
            )
        return pods

    def get_current_namespace(self) -> str:
        """Get current namespace from kubectl context"""
        try:
            output = self._run_global("config", "view", "--minify", "-o", "jsonpath={.contexts[0].context.namespace}")
            namespace = output.strip() if output else ""
            return namespace or "default"
        except Exception:
            return "default"

    def get_current_context(self) -> str:
        """Get current kubectl context"""
        try:
            output = self._run_global("config", "current-context")
            return output.strip() if output else "unknown"
        except Exception:
            return "unknown"

    def verify_namespace_access(self, namespace: Optional[str] = None) -> bool:
        """Verify user has access to specified namespace"""
        ns = namespace or self.namespace
        try:
            result = subprocess.run(
                ["kubectl", "auth", "can-i", "list", "pods", "-n", ns],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.stdout.strip() == "yes"
        except Exception:
            return False

    def delete_pod(self, pod_name: str, namespace: Optional[str] = None, force: bool = False) -> None:
        """Delete a pod"""
        args = ["delete", "pod", pod_name]
        if force:
            args.extend(["--grace-period=0", "--force"])

        self._run(*args, capture=False, namespace=namespace)

    def delete_pods_by_label(self, label: str, namespace: Optional[str] = None) -> None:
        """Delete all pods matching a label selector"""
        args = ["delete", "pods", "-l", label]
        self._run(*args, capture=False, namespace=namespace)

    def describe_pod(self, pod_name: str, namespace: Optional[str] = None) -> str:
        """Get detailed information about a pod"""
        return self._run("describe", "pod", pod_name, namespace=namespace)

    def logs(
        self,
        pod: str,
        follow: bool = False,
        previous: bool = False,
        tail: int = 100,
        container: Optional[str] = None,
    ):
        """View pod logs"""
        args = ["logs", pod, f"--tail={tail}"]
        if follow:
            args.append("-f")
        if previous:
            args.append("--previous")
        if container:
            args.extend(["-c", container])

        self._run(*args, capture=False)

    def exec(self, pod: str, command: str, container: Optional[str] = None):
        """Execute command in pod"""
        args = ["exec", "-it", pod]
        if container:
            args.extend(["-c", container])
        args.extend(["--", command])

        self._run(*args, capture=False)

    def scale(self, deployment: str, replicas: int):
        """Scale deployment"""
        self._run("scale", f"deployment/{deployment}", f"--replicas={replicas}")

    def restart(self, deployment: str):
        """Restart deployment"""
        self._run("rollout", "restart", f"deployment/{deployment}")

    def get_deployments(self, namespace: Optional[str] = None) -> List[Dict]:
        """List deployments in namespace"""
        args = ["get", "deployments", "-o=json"]
        output = self._run(*args, namespace=namespace)
        data = json.loads(output)

        deployments = []
        for item in data.get("items", []):
            spec = item.get("spec", {})
            status = item.get("status", {})
            deployments.append({
                "name": item["metadata"]["name"],
                "namespace": item["metadata"]["namespace"],
                "replicas": spec.get("replicas", 0),
                "ready": status.get("readyReplicas", 0),
                "available": status.get("availableReplicas", 0),
                "age": self._calculate_age(item["metadata"]["creationTimestamp"]),
                "created": item["metadata"]["creationTimestamp"],
            })
        return deployments

    def get_deployment(self, deployment_name: str, namespace: Optional[str] = None) -> Dict:
        """Get detailed deployment information"""
        args = ["get", "deployment", deployment_name, "-o=json"]
        output = self._run(*args, namespace=namespace)
        data = json.loads(output)

        spec = data.get("spec", {})
        status = data.get("status", {})
        template_spec = spec.get("template", {}).get("spec", {})
        containers = template_spec.get("containers", [])

        return {
            "name": data["metadata"]["name"],
            "namespace": data["metadata"]["namespace"],
            "replicas": spec.get("replicas", 0),
            "ready": status.get("readyReplicas", 0),
            "available": status.get("availableReplicas", 0),
            "updated": status.get("updatedReplicas", 0),
            "age": self._calculate_age(data["metadata"]["creationTimestamp"]),
            "created": data["metadata"]["creationTimestamp"],
            "containers": [
                {
                    "name": c.get("name"),
                    "image": c.get("image"),
                    "ports": c.get("ports", []),
                }
                for c in containers
            ],
            "selector": spec.get("selector", {}).get("matchLabels", {}),
            "strategy": spec.get("strategy", {}).get("type", ""),
        }

    def describe_deployment(self, deployment_name: str, namespace: Optional[str] = None) -> str:
        """Get detailed description of a deployment"""
        return self._run("describe", "deployment", deployment_name, namespace=namespace)

    def health_check(self) -> Dict:
        """Check cluster health"""
        try:
            pods = self.get_pods()
            deployments = self.get_deployments()
            return {
                "healthy": True,
                "cluster": "Connected",
                "pod_count": len(pods),
                "deployment_count": len(deployments),
            }
        except Exception:
            return {
                "healthy": False,
                "cluster": "Disconnected",
                "pod_count": 0,
                "deployment_count": 0,
            }

