{{/*
Expand the name of the chart.
*/}}
{{- define "astron-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "astron-agent.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "astron-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "astron-agent.labels" -}}
helm.sh/chart: {{ include "astron-agent.chart" . }}
{{ include "astron-agent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "astron-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "astron-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "astron-agent.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "astron-agent.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
PostgreSQL host
*/}}
{{- define "astron-agent.postgresql.host" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "%s-postgres" (include "astron-agent.fullname" .) }}
{{- else }}
{{- .Values.postgresql.external.host }}
{{- end }}
{{- end }}

{{/*
MySQL host
*/}}
{{- define "astron-agent.mysql.host" -}}
{{- if .Values.mysql.enabled }}
{{- printf "%s-mysql" (include "astron-agent.fullname" .) }}
{{- else }}
{{- .Values.mysql.external.host }}
{{- end }}
{{- end }}

{{/*
Redis host
*/}}
{{- define "astron-agent.redis.host" -}}
{{- if .Values.redis.enabled }}
{{- printf "%s-redis" (include "astron-agent.fullname" .) }}
{{- else }}
{{- .Values.redis.external.host }}
{{- end }}
{{- end }}

{{/*
Casdoor host
*/}}
{{- define "astron-agent.casdoor.host" -}}
{{- if .Values.casdoor.enabled }}
{{- printf "%s-casdoor" (include "astron-agent.fullname" .) }}
{{- else }}
{{- .Values.casdoor.external.host }}
{{- end }}
{{- end }}

{{/*
Core service URLs - 用于生成完整的服务 URL（包括协议和端口）
*/}}
{{- define "astron-agent.coreTenant.url" -}}
{{- printf "http://%s-core-tenant:%d" (include "astron-agent.fullname" .) (.Values.coreTenant.service.port | int) }}
{{- end }}

{{- define "astron-agent.coreDatabase.url" -}}
{{- printf "http://%s-core-database:%d" (include "astron-agent.fullname" .) (.Values.coreDatabase.service.port | int) }}
{{- end }}

{{- define "astron-agent.coreRpa.url" -}}
{{- printf "http://%s-core-rpa:%d" (include "astron-agent.fullname" .) (.Values.coreRpa.service.port | int) }}
{{- end }}

{{- define "astron-agent.coreLink.url" -}}
{{- printf "http://%s-core-link:%d" (include "astron-agent.fullname" .) (.Values.coreLink.service.port | int) }}
{{- end }}

{{- define "astron-agent.coreAitools.url" -}}
{{- printf "http://%s-core-aitools:%d" (include "astron-agent.fullname" .) (.Values.coreAitools.service.port | int) }}
{{- end }}

{{- define "astron-agent.coreAgent.url" -}}
{{- printf "http://%s-core-agent:%d" (include "astron-agent.fullname" .) (.Values.coreAgent.service.port | int) }}
{{- end }}

{{- define "astron-agent.coreKnowledge.url" -}}
{{- printf "http://%s-core-knowledge:%d" (include "astron-agent.fullname" .) (.Values.coreKnowledge.service.port | int) }}
{{- end }}

{{- define "astron-agent.coreWorkflow.url" -}}
{{- printf "http://%s-core-workflow:%d" (include "astron-agent.fullname" .) (.Values.coreWorkflow.service.port | int) }}
{{- end }}

{{/*
Resolve the single pre-created object-storage Secret shared by MinIO and all S3
clients. Inline credentials are intentionally unsupported: Helm stores rendered
Secrets in release state, so even a Kubernetes Secret manifest would disclose
the credential to every release-manifest reader.
*/}}
{{- define "astron-agent.minioSecretName" -}}
{{- $auth := default (dict) .Values.minio.auth -}}
{{- $existing := default "" (get $auth "existingSecret") | toString | trim -}}
{{- $inlineUser := default "" (get $auth "rootUser") | toString | trim -}}
{{- $inlinePassword := default "" (get $auth "rootPassword") | toString | trim -}}
{{- if $existing -}}
{{- $existing -}}
{{- else -}}
{{- if or $inlineUser $inlinePassword -}}
{{- $userLower := lower $inlineUser -}}
{{- $passwordLower := lower $inlinePassword -}}
{{- if or (has $userLower (list "minioadmin" "admin" "administrator" "root" "changeme")) (has $passwordLower (list "minioadmin" "minioadmin123" "admin" "admin123" "password" "password123" "changeme")) -}}
{{- fail "minio.auth contains a well-known default credential; create a strong Kubernetes Secret and set minio.auth.existingSecret" -}}
{{- end -}}
{{- if or (lt (len $inlineUser) 8) (lt (len $inlinePassword) 16) -}}
{{- fail "minio.auth inline credentials are empty or weak; create a Kubernetes Secret with a user of at least 8 characters and a password of at least 16 characters" -}}
{{- end -}}
{{- fail "minio.auth inline credentials are not rendered because Helm release manifests would disclose them; set minio.auth.existingSecret" -}}
{{- else -}}
{{- fail "minio.auth.existingSecret is required; inline or empty MinIO credentials are not allowed" -}}
{{- end -}}
{{- end -}}
{{- end }}

{{- define "astron-agent.minioSecretUserKey" -}}
{{- $auth := default (dict) .Values.minio.auth -}}
{{- required "minio.auth.rootUserKey is required when using minio.auth.existingSecret" (get $auth "rootUserKey") -}}
{{- end }}

{{- define "astron-agent.minioSecretPasswordKey" -}}
{{- $auth := default (dict) .Values.minio.auth -}}
{{- required "minio.auth.rootPasswordKey is required when using minio.auth.existingSecret" (get $auth "rootPasswordKey") -}}
{{- end }}

{{/* Stable non-secret rollout marker for the shared object-storage Secret. */}}
{{- define "astron-agent.minioSecretChecksum" -}}
{{- $auth := default (dict) .Values.minio.auth -}}
{{- printf "%s:%s:%s:%s" (include "astron-agent.minioSecretName" .) (include "astron-agent.minioSecretUserKey" .) (include "astron-agent.minioSecretPasswordKey" .) (default "" (get $auth "existingSecretChecksum")) | sha256sum -}}
{{- end }}

{{/* Cluster-internal S3 endpoint, or an explicit endpoint when MinIO is external. */}}
{{- define "astron-agent.minioEndpoint" -}}
{{- $endpoint := "" -}}
{{- if .Values.minio.enabled -}}
{{- $endpoint = printf "http://%s-minio:%d" (include "astron-agent.fullname" .) (.Values.minio.service.apiPort | int) -}}
{{- else -}}
{{- $external := default (dict) .Values.minio.external -}}
{{- $endpoint = required "minio.external.endpoint is required when minio.enabled=false and an enabled service uses object storage" (get $external "endpoint") | toString | trim -}}
{{- end -}}
{{- if not (regexMatch "^https?://(\\[[0-9A-Fa-f:.]+\\]|[A-Za-z0-9._-]+)(:[0-9]+)?/?$" $endpoint) -}}
{{- fail "the configured MinIO/S3 endpoint must be an exact http(s) origin without userinfo, path, query parameters, or fragments" -}}
{{- end -}}
{{- $endpoint | trimSuffix "/" -}}
{{- end }}

{{/* Endpoint embedded in presigned/download URLs; never implies Service exposure. */}}
{{- define "astron-agent.minioPublicEndpoint" -}}
{{- $configured := default "" .Values.minio.publicEndpoint | toString | trim -}}
{{- if not .Values.minio.enabled -}}
{{- $external := default (dict) .Values.minio.external -}}
{{- $externalPublic := default "" (get $external "publicEndpoint") | toString | trim -}}
{{- if $externalPublic -}}{{- $configured = $externalPublic -}}{{- end -}}
{{- end -}}
{{- if not $configured -}}{{- $configured = include "astron-agent.minioEndpoint" . -}}{{- end -}}
{{- if not (regexMatch "^https?://(\\[[0-9A-Fa-f:.]+\\]|[A-Za-z0-9._-]+)(:[0-9]+)?/?$" $configured) -}}
{{- fail "minio.publicEndpoint/minio.external.publicEndpoint must be an exact http(s) origin without userinfo, path, query parameters, or fragments" -}}
{{- end -}}
{{- $configured | trimSuffix "/" -}}
{{- end }}

{{/* Resolve the artifact-upload credential Secret without cluster lookup. */}}
{{- define "astron-agent.artifactUploadSecretName" -}}
{{- $config := default (dict) .Values.consoleHub.artifactUpload -}}
{{- $token := default "" (get $config "token") | toString | trim -}}
{{- if $token -}}
{{- printf "%s-console-hub-artifact-upload" (include "astron-agent.fullname" .) -}}
{{- else -}}
{{- required "consoleHub.artifactUpload.existingSecret is required when consoleHub.artifactUpload.token is empty" (get $config "existingSecret") -}}
{{- end -}}
{{- end }}

{{- define "astron-agent.artifactUploadSecretKey" -}}
{{- $config := default (dict) .Values.consoleHub.artifactUpload -}}
{{- $token := default "" (get $config "token") | toString | trim -}}
{{- if $token -}}artifact-upload-token{{- else -}}
{{- required "consoleHub.artifactUpload.existingSecretKey is required when using an existing Secret" (get $config "existingSecretKey") -}}
{{- end -}}
{{- end }}

{{/*
Hash either the explicit credential or the external Secret identity plus an
operator-supplied rotation checksum. This is stable for offline GitOps renders.
*/}}
{{- define "astron-agent.artifactUploadSecretChecksum" -}}
{{- $config := default (dict) .Values.consoleHub.artifactUpload -}}
{{- $token := default "" (get $config "token") | toString | trim -}}
{{- if $token -}}
{{- printf "%s:%s" (include "astron-agent.artifactUploadSecretName" .) $token | sha256sum -}}
{{- else -}}
{{- printf "%s:%s:%s" (include "astron-agent.artifactUploadSecretName" .) (include "astron-agent.artifactUploadSecretKey" .) (default "" (get $config "existingSecretChecksum")) | sha256sum -}}
{{- end -}}
{{- end }}

{{/* Resolve the independent sandbox runtime-credential Secret. */}}
{{- define "astron-agent.sandboxRuntimeCredentialSecretName" -}}
{{- $config := default (dict) .Values.consoleHub.sandboxRuntimeCredential -}}
{{- $token := default "" (get $config "token") | toString | trim -}}
{{- if $token -}}
{{- printf "%s-console-hub-sandbox-runtime-credential" (include "astron-agent.fullname" .) -}}
{{- else -}}
{{- required "consoleHub.sandboxRuntimeCredential.existingSecret is required when consoleHub.sandboxRuntimeCredential.token is empty" (get $config "existingSecret") -}}
{{- end -}}
{{- end }}

{{- define "astron-agent.sandboxRuntimeCredentialSecretKey" -}}
{{- $config := default (dict) .Values.consoleHub.sandboxRuntimeCredential -}}
{{- $token := default "" (get $config "token") | toString | trim -}}
{{- if $token -}}sandbox-runtime-credential-token{{- else -}}
{{- required "consoleHub.sandboxRuntimeCredential.existingSecretKey is required when using an existing Secret" (get $config "existingSecretKey") -}}
{{- end -}}
{{- end }}

{{- define "astron-agent.sandboxRuntimeCredentialSecretChecksum" -}}
{{- $config := default (dict) .Values.consoleHub.sandboxRuntimeCredential -}}
{{- $token := default "" (get $config "token") | toString | trim -}}
{{- if $token -}}
{{- printf "%s:%s" (include "astron-agent.sandboxRuntimeCredentialSecretName" .) $token | sha256sum -}}
{{- else -}}
{{- printf "%s:%s:%s" (include "astron-agent.sandboxRuntimeCredentialSecretName" .) (include "astron-agent.sandboxRuntimeCredentialSecretKey" .) (default "" (get $config "existingSecretChecksum")) | sha256sum -}}
{{- end -}}
{{- end }}
