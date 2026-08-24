#!/usr/bin/env python3
"""Verify the rendered Compose contract for sandbox credential handoff."""

import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import (
    Any,
    Callable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
)


SERVICES = ("console-hub", "core-agent", "core-workflow")
CONSUMERS = ("core-agent", "core-workflow")

CREDENTIALS = (
    {
        "volume": "artifact_upload_secrets",
        "target": "/app/secrets/artifact",
        "file_env": "SKILL_SANDBOX_ARTIFACT_UPLOAD_TOKEN_FILE",
        "file_path": "/app/secrets/artifact/artifact-upload-token",
    },
    {
        "volume": "sandbox_runtime_credential_secrets",
        "target": "/app/secrets/runtime",
        "file_env": "SKILL_SANDBOX_RUNTIME_CREDENTIAL_TOKEN_FILE",
        "file_path": "/app/secrets/runtime/sandbox-runtime-credential-token",
    },
)

INTERNAL_URLS = {
    "SKILL_SANDBOX_ARTIFACT_UPLOAD_URL": (
        "http://console-hub:8080/workflow/artifacts/internal-upload"
    ),
    "SKILL_SANDBOX_RUNTIME_CONFIG_URL": (
        "http://console-hub:8080/skill-sandbox/internal-runtime-config"
    ),
}

HUB_HEALTHCHECK_TEST = [
    "CMD-SHELL",
    "curl --fail --silent --show-error http://localhost:8080/health >/dev/null",
]

# CI has no deployment .env. These deliberately non-secret values satisfy only
# Compose's required-variable interpolation so the rendered topology can be
# checked. Deployment preflight must omit --ci-placeholder-required-env.
CI_PLACEHOLDER_ENV = {
    "MINIO_ROOT_USER": "ci-contract-user",
    "MINIO_ROOT_PASSWORD": "ci-contract-password-2026",
    "OSS_REMOTE_ENDPOINT": "http://minio.localhost:18998",
    "OSS_ACCESS_KEY_ID": "ci-contract-access-key",
    "OSS_ACCESS_KEY_SECRET": "ci-contract-credential-value",
    "OSS_BUCKET_CONSOLE": "ci-contract-bucket",
}


class GateError(RuntimeError):
    """A safe-to-print gate error which never contains rendered values."""


def _render_compose(
    compose_file: Path, *, ci_placeholder_required_env: bool
) -> Mapping[str, Any]:
    environment = os.environ.copy()
    if ci_placeholder_required_env:
        for name, value in CI_PLACEHOLDER_ENV.items():
            environment.setdefault(name, value)

    command = [
        "docker",
        "compose",
        "-f",
        compose_file.name,
        "config",
        "--format",
        "json",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=str(compose_file.parent),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GateError("Docker CLI is unavailable") from exc

    if completed.returncode != 0:
        # Compose stderr can contain interpolated deployment data. Do not echo it.
        raise GateError(
            "docker compose config failed; Docker Compose v2 with "
            "'config --format json' and all required deployment variables is required"
        )

    try:
        rendered = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        raise GateError("docker compose config did not return valid JSON") from exc
    if not isinstance(rendered, dict):
        raise GateError("docker compose config returned an unexpected JSON root")
    return rendered


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, dict) else {}


def _mounts(service: Mapping[str, Any], target: str) -> List[Mapping[str, Any]]:
    volumes = service.get("volumes", [])
    if not isinstance(volumes, list):
        return []
    return [
        volume
        for volume in volumes
        if isinstance(volume, dict) and volume.get("target") == target
    ]


def validate_contract(config: Mapping[str, Any]) -> List[str]:
    """Return field-only contract errors without including configured values."""

    errors: List[str] = []
    services = _mapping(config.get("services"))
    volumes = _mapping(config.get("volumes"))

    for service_name in SERVICES:
        if not isinstance(services.get(service_name), dict):
            errors.append(f"services.{service_name}: missing")

    for credential in CREDENTIALS:
        volume_name = credential["volume"]
        if not isinstance(volumes.get(volume_name), dict):
            errors.append(f"volumes.{volume_name}: missing named volume")

    resolved_volume_names: List[str] = []
    for credential in CREDENTIALS:
        volume_name = credential["volume"]
        definition = volumes.get(volume_name)
        if isinstance(definition, dict):
            resolved_name = definition.get("name", volume_name)
            if isinstance(resolved_name, str) and resolved_name:
                resolved_volume_names.append(resolved_name)
    if (
        len(resolved_volume_names) == len(CREDENTIALS)
        and len(set(resolved_volume_names)) != len(CREDENTIALS)
    ):
        errors.append("volumes.*.name: credential volumes must be independent")

    for service_name in SERVICES:
        service = _mapping(services.get(service_name))
        environment = _mapping(service.get("environment"))

        for credential in CREDENTIALS:
            env_name = credential["file_env"]
            if environment.get(env_name) != credential["file_path"]:
                errors.append(
                    f"services.{service_name}.environment.{env_name}: "
                    "missing or unexpected"
                )

            target = credential["target"]
            matching_mounts = _mounts(service, target)
            mount_field = f"services.{service_name}.volumes[{target}]"
            if len(matching_mounts) != 1:
                errors.append(f"{mount_field}: missing or duplicated")
                continue

            mount = matching_mounts[0]
            if (
                mount.get("type") != "volume"
                or mount.get("source") != credential["volume"]
            ):
                errors.append(f"{mount_field}.source/type: unexpected named volume")

            expected_read_only = service_name in CONSUMERS
            actual_read_only = mount.get("read_only", False) is True
            if actual_read_only != expected_read_only:
                expected_mode = "ro" if expected_read_only else "rw"
                errors.append(f"{mount_field}.mode: expected {expected_mode}")

    for service_name in CONSUMERS:
        service = _mapping(services.get(service_name))
        environment = _mapping(service.get("environment"))
        for env_name, expected_url in INTERNAL_URLS.items():
            if environment.get(env_name) != expected_url:
                errors.append(
                    f"services.{service_name}.environment.{env_name}: "
                    "missing or unexpected"
                )

        hub_dependency = _mapping(_mapping(service.get("depends_on")).get("console-hub"))
        if hub_dependency.get("condition") != "service_healthy":
            errors.append(
                f"services.{service_name}.depends_on.console-hub: "
                "expected service_healthy"
            )
        if hub_dependency.get("required") is False:
            errors.append(
                f"services.{service_name}.depends_on.console-hub.required: "
                "must not be false"
            )

    hub = _mapping(services.get("console-hub"))
    healthcheck = hub.get("healthcheck")
    healthcheck_field = "services.console-hub.healthcheck"
    if not isinstance(healthcheck, dict):
        errors.append(f"{healthcheck_field}: missing")
    else:
        test = healthcheck.get("test")
        test_is_disabled = (
            isinstance(test, str) and test.strip().upper() == "NONE"
        ) or (
            isinstance(test, list)
            and bool(test)
            and str(test[0]).strip().upper() == "NONE"
        )
        if healthcheck.get("disable") is True or test_is_disabled:
            errors.append(f"{healthcheck_field}: disabled")
        elif test != HUB_HEALTHCHECK_TEST:
            errors.append(f"{healthcheck_field}.test: unexpected command or endpoint")

    return errors


def _set_mount_mode(
    config: MutableMapping[str, Any], service_name: str, target: str, read_only: bool
) -> None:
    service = config["services"][service_name]
    for mount in service["volumes"]:
        if isinstance(mount, dict) and mount.get("target") == target:
            mount["read_only"] = read_only
            return
    raise GateError("negative self-test fixture is incomplete")


def _negative_cases() -> Sequence[
    Tuple[str, Callable[[MutableMapping[str, Any], str], None], str]
]:
    def wrong_token_path(config: MutableMapping[str, Any], marker: str) -> None:
        config["services"]["core-agent"]["environment"][
            "SKILL_SANDBOX_ARTIFACT_UPLOAD_TOKEN_FILE"
        ] = marker

    def missing_token_file(config: MutableMapping[str, Any], _marker: str) -> None:
        config["services"]["core-workflow"]["environment"].pop(
            "SKILL_SANDBOX_RUNTIME_CREDENTIAL_TOKEN_FILE", None
        )

    def writable_consumer(config: MutableMapping[str, Any], _marker: str) -> None:
        _set_mount_mode(config, "core-workflow", "/app/secrets/artifact", False)

    def readonly_producer(config: MutableMapping[str, Any], _marker: str) -> None:
        _set_mount_mode(config, "console-hub", "/app/secrets/runtime", True)

    def wrong_internal_url(config: MutableMapping[str, Any], marker: str) -> None:
        config["services"]["core-agent"]["environment"][
            "SKILL_SANDBOX_RUNTIME_CONFIG_URL"
        ] = marker

    def merged_volumes(config: MutableMapping[str, Any], _marker: str) -> None:
        artifact_name = config["volumes"]["artifact_upload_secrets"].get(
            "name", "artifact_upload_secrets"
        )
        config["volumes"]["sandbox_runtime_credential_secrets"][
            "name"
        ] = artifact_name

    def disabled_healthcheck(config: MutableMapping[str, Any], _marker: str) -> None:
        config["services"]["console-hub"]["healthcheck"] = {"disable": True}

    def missing_hub_dependency(config: MutableMapping[str, Any], _marker: str) -> None:
        config["services"]["core-workflow"]["depends_on"].pop("console-hub", None)

    def optional_hub_dependency(config: MutableMapping[str, Any], _marker: str) -> None:
        config["services"]["core-agent"]["depends_on"]["console-hub"][
            "required"
        ] = False

    def wrong_hub_healthcheck_endpoint(
        config: MutableMapping[str, Any], _marker: str
    ) -> None:
        config["services"]["console-hub"]["healthcheck"]["test"] = [
            "CMD-SHELL",
            "curl --fail --silent --show-error http://localhost:8080/not-health >/dev/null",
        ]

    def noop_hub_healthcheck(config: MutableMapping[str, Any], _marker: str) -> None:
        config["services"]["console-hub"]["healthcheck"]["test"] = [
            "CMD",
            "true",
        ]

    return (
        (
            "wrong-token-file-path",
            wrong_token_path,
            "services.core-agent.environment.SKILL_SANDBOX_ARTIFACT_UPLOAD_TOKEN_FILE",
        ),
        (
            "missing-token-file",
            missing_token_file,
            "services.core-workflow.environment.SKILL_SANDBOX_RUNTIME_CREDENTIAL_TOKEN_FILE",
        ),
        (
            "writable-consumer-volume",
            writable_consumer,
            "services.core-workflow.volumes[/app/secrets/artifact].mode",
        ),
        (
            "readonly-producer-volume",
            readonly_producer,
            "services.console-hub.volumes[/app/secrets/runtime].mode",
        ),
        (
            "wrong-internal-url",
            wrong_internal_url,
            "services.core-agent.environment.SKILL_SANDBOX_RUNTIME_CONFIG_URL",
        ),
        ("merged-named-volumes", merged_volumes, "volumes.*.name"),
        (
            "disabled-hub-healthcheck",
            disabled_healthcheck,
            "services.console-hub.healthcheck",
        ),
        (
            "missing-healthy-hub-dependency",
            missing_hub_dependency,
            "services.core-workflow.depends_on.console-hub",
        ),
        (
            "optional-healthy-hub-dependency",
            optional_hub_dependency,
            "services.core-agent.depends_on.console-hub.required",
        ),
        (
            "wrong-hub-healthcheck-endpoint",
            wrong_hub_healthcheck_endpoint,
            "services.console-hub.healthcheck.test",
        ),
        (
            "noop-hub-healthcheck",
            noop_hub_healthcheck,
            "services.console-hub.healthcheck.test",
        ),
    )


def run_negative_self_tests(config: Mapping[str, Any]) -> None:
    marker = "negative-self-test-sensitive-marker"
    for case_name, mutate, expected_field in _negative_cases():
        candidate = copy.deepcopy(config)
        if not isinstance(candidate, dict):
            raise GateError("negative self-test fixture is incomplete")

        # A marker models unrelated sensitive environment data. Validation
        # diagnostics must never serialize it, even when the candidate fails.
        candidate["services"]["console-hub"]["environment"][
            "SKILL_SANDBOX_ARTIFACT_UPLOAD_TOKEN"
        ] = marker
        mutate(candidate, marker)
        errors = validate_contract(candidate)
        if not any(error.startswith(expected_field) for error in errors):
            raise GateError(f"negative self-test did not fail: {case_name}")
        if marker in "\n".join(errors):
            raise GateError(f"negative self-test diagnostics were unsafe: {case_name}")


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    default_compose_file = (
        Path(__file__).resolve().parent.parent / "docker-compose-with-auth.yaml"
    )
    parser = argparse.ArgumentParser(
        description="Verify sandbox credential and health contracts in rendered Compose JSON."
    )
    parser.add_argument(
        "--compose-file",
        type=Path,
        default=default_compose_file,
        help="Compose entrypoint (default: docker-compose-with-auth.yaml next to scripts/)",
    )
    parser.add_argument(
        "--ci-placeholder-required-env",
        action="store_true",
        help="Use non-secret placeholders for required deployment variables in CI only",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    compose_file = args.compose_file.expanduser().resolve()
    if not compose_file.is_file():
        print("security contract gate: FAIL: compose file is missing", file=sys.stderr)
        return 1

    try:
        config = _render_compose(
            compose_file,
            ci_placeholder_required_env=args.ci_placeholder_required_env,
        )
        errors = validate_contract(config)
        if errors:
            for error in errors:
                print(f"security contract gate: FAIL: {error}", file=sys.stderr)
            return 1
        run_negative_self_tests(config)
    except GateError as exc:
        print(f"security contract gate: FAIL: {exc}", file=sys.stderr)
        return 1
    except Exception:
        # Never serialize an unexpected object which could include rendered env.
        print("security contract gate: FAIL: internal validation error", file=sys.stderr)
        return 1

    print(
        "security contract gate: PASS "
        f"(3 services, 2 independent credential volumes, {len(_negative_cases())} negative cases)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
