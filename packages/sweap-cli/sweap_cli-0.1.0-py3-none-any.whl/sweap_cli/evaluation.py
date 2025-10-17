"""Evaluation helpers for `task run`."""

from __future__ import annotations

import inspect
import importlib
import base64
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional

from rich.console import Console

from .manifest_utils import (
    ManifestError,
    parse_runner,
    resolve_runner_dependency,
)

console = Console()


@dataclass
class EvaluationResult:
    model: str
    task_id: str
    status: str
    baseline: Dict[str, str]
    patched: Dict[str, str]
    patch_applied: bool
    stages: Optional[List[Dict[str, Any]]] = None
    transcript: Optional[str] = None
    transcript_path: Optional[str] = None
    transcript_format: str = "text"
    skip_baseline: bool = False

    def as_dict(self) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "task_id": self.task_id,
            "status": self.status,
            "baseline": self.baseline,
            "patched": self.patched,
            "patch_applied": self.patch_applied,
            "skip_baseline": self.skip_baseline,
        }
        if self.stages is not None:
            payload["stages"] = self.stages
        if self.transcript_path:
            payload["transcript"] = {
                "path": self.transcript_path,
                "format": self.transcript_format,
            }
        return payload


def run_modal_evaluation(
    *,
    bundle_dir: Path,
    manifest: Dict[str, Any],
    model: str,
    llm_command: str | None = None,
    skip_baseline: bool = False,
) -> EvaluationResult:
    """Evaluate the task bundle inside a Modal sandbox with a mocked model attempt."""

    try:
        import modal
    except ImportError as exc:  # pragma: no cover - import guard
        raise RuntimeError("Modal library not installed. Run `pip install modal`." ) from exc

    import importlib
    try:
        image_api = modal.Image
    except AttributeError:
        try:
            image_module = importlib.import_module("modal.image")
            image_api = getattr(image_module, "Image")
        except Exception as exc:
            raise RuntimeError(
                "Modal's Python image API is unavailable. Please install or upgrade the `modal` SDK (e.g. `pip install --upgrade modal`)."
            ) from exc

    task_id = manifest.get("task_id", "unknown-task")
    repo = manifest["repo"]
    tests = manifest["tests"]
    environment = manifest.get("environment", {})

    bundle_dir = bundle_dir.resolve()
    fail_dir_rel = tests.get("fail2pass_dir", "tests/fail2pass")
    pass_dir_rel = tests.get("pass2pass_dir", "tests/pass2pass")
    try:
        runner_info = parse_runner(manifest.get("runner"))
    except ManifestError as exc:
        raise RuntimeError(f"Invalid runner configuration: {exc}") from exc

    try:
        dependency_descriptor = resolve_runner_dependency(manifest, runner_info)
    except ManifestError as exc:
        raise RuntimeError(f"Invalid environment configuration: {exc}") from exc

    runner_type = runner_info.type.lower()
    runner_cmd = runner_info.command
    runner_env = runner_info.env
    dependency_payload = asdict(dependency_descriptor)

    dependency_rel = dependency_descriptor.path or ""
    if dependency_rel:
        dependency_path = bundle_dir / dependency_rel
        if not dependency_path.exists():
            raise RuntimeError(f"Missing dependency artifact at {dependency_path}")
    modal_image_name = environment.get("modal_image")
    modal_image_id = environment.get("modal_image_id")
    modal_python_version = environment.get("modal_python_version", "3.10")
    runner_cmd = runner_info.command

    packages = ["git", "python3-venv"]
    if runner_type in {"node", "npm", "yarn"}:
        packages.extend(["nodejs", "npm"])
    packages = list(dict.fromkeys(packages))

    image = None
    if modal_image_id:
        try:
            image = image_api.from_id(modal_image_id)
        except Exception:
            image = None
    if image is None and modal_image_name:
        try:
            image = image_api.from_name(modal_image_name)
        except AttributeError:
            try:
                image = image_api.from_registry(modal_image_name)
            except Exception:
                image = None
    if image is None:
        image = (
            image_api.debian_slim(python_version=modal_python_version)
            .apt_install(*packages)
            .run_commands("npm install -g @openai/codex")
            .add_local_dir(str(bundle_dir), remote_path="/bundle")
        )

    app = modal.App.lookup("sweap-cli", create_if_missing=True)

    secrets = _collect_modal_secrets()
    if secrets:
        console.print('[cyan]Passing secrets to Modal sandbox.[/cyan]')
    else:
        secrets = []
    with modal.enable_output():
        sb = modal.Sandbox.create(
            app=app,
            image=image,
            secrets=secrets,
            timeout=3600,
        )
    try:
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            sb.exec(
                "bash",
                "-lc",
                "git config --global http.https://github.com/.extraheader 'Authorization: Basic '$(echo -n x-access-token:$GITHUB_TOKEN | base64 -w0)",
                timeout=30,
            ).wait()

        sb.exec(
            "bash",
            "-lc",
            f"set -euo pipefail; git clone {repo['url']} repo && cd repo && git checkout {repo['commit']}",
        ).wait()

        evaluation_script = _render_evaluation_script(
            runner_type=runner_type,
            runner_cmd=runner_cmd,
            runner_env=runner_env,
            dependency=dependency_payload,
            fail_dir_rel=fail_dir_rel,
            pass_dir_rel=pass_dir_rel,
            description_rel=manifest.get("problem", {}).get("description_file", "description.md"),
            task_id=task_id,
            model_name=model,
            llm_command=llm_command or os.environ.get("SWEEP_LLM_COMMAND"),
            skip_baseline=skip_baseline,
        )

        command = f"python3 - <<'PY'\n{evaluation_script}\nPY"
        process = sb.exec("bash", "-lc", command, timeout=1800)

        stdout = process.stdout.read()
        stderr = process.stderr.read()
        rc = process.wait()

        transcript_parts: List[str] = []
        if stdout:
            console.print(stdout)
            transcript_parts.append(stdout)
        if stderr:
            console.print(stderr)
            transcript_parts.append(stderr)
        transcript_text = "".join(transcript_parts) if transcript_parts else None

        result_payload: Dict[str, Any] = {}
        for line in stdout.splitlines() if stdout else []:
            if line.startswith("RESULT_JSON::"):
                try:
                    result_payload = json.loads(line.split("RESULT_JSON::", 1)[1])
                except json.JSONDecodeError:
                    console.print("[evaluation] Failed to decode JSON payload from evaluation script.")
                break

        baseline = result_payload.get("baseline", {"pass2pass": "unknown", "fail2pass": "unknown"})
        patched = result_payload.get("patched", baseline)
        patch_applied = bool(result_payload.get("patch_applied", False))
        stages = result_payload.get("stages")
        skip_baseline_flag = bool(result_payload.get("skip_baseline", False))

        status = "success"
        if patched.get("fail2pass") != "pass":
            status = "failed"
        if rc != 0:
            status = "error"
        if not skip_baseline_flag:
            if baseline.get("pass2pass") not in {"pass", "skip"}:
                status = "error"
            if baseline.get("fail2pass") not in {"fail", "skip"}:
                status = "error"

        return EvaluationResult(
            model=model,
            task_id=task_id,
            status=status,
            baseline=baseline,
            patched=patched,
            patch_applied=patch_applied,
            stages=stages,
            transcript=transcript_text,
            skip_baseline=skip_baseline_flag,
        )
    finally:
        try:
            sb.terminate()
        except Exception:  # pragma: no cover
            pass


def _render_evaluation_script(
    *,
    runner_type: str,
    runner_cmd: str,
    runner_env: dict[str, Any],
    dependency: dict[str, Any],
    fail_dir_rel: str,
    pass_dir_rel: str,
    description_rel: str,
    task_id: str,
    model_name: str,
    llm_command: str | None,
    skip_baseline: bool,
) -> str:
    template = inspect.cleandoc(
        """
        import os
        import json
        import base64
        import re
        import shlex
        import shutil
        import subprocess
        import sys
        import venv
        from contextlib import contextmanager
        from pathlib import Path
        from string import Template

        bundle_dir = Path('/bundle')
        repo_dir = Path('repo')
        runner_type = __RUNNER_TYPE__.lower()
        runner_cmd = __RUNNER_CMD__
        runner_env = __RUNNER_ENV__
        dependency = __DEPENDENCY__
        dependency_payload = dependency
        fail_dir_rel = Path(__FAIL_DIR__)
        pass_dir_rel = Path(__PASS_DIR__)
        description_rel = Path(__DESC__)
        task_id = __TASK_ID__
        model_name = __MODEL_NAME__
        llm_command = Template(__LLM_COMMAND__).safe_substitute(os.environ) if __LLM_COMMAND__ else ""
        skip_baseline = __SKIP_BASELINE__

        stages = []
        _stage_stack = []

        def log(message: str, *, note: bool = True) -> None:
            print(message, flush=True)
            if note and _stage_stack:
                _stage_stack[-1]['notes'].append(message)

        @contextmanager
        def stage(name: str, title: str | None = None):
            record = {
                'name': name,
                'title': title or name,
                'status': 'pending',
                'steps': [],
                'notes': [],
            }
            stages.append(record)
            _stage_stack.append(record)
            log(f"== {record['title']} ==", note=False)
            try:
                yield record
                if record['status'] == 'pending':
                    record['status'] = 'succeeded'
            except Exception as stage_exc:
                record['status'] = 'error'
                record['notes'].append(f'Stage failed: {stage_exc}')
                raise
            finally:
                _stage_stack.pop()

        def run(cmd, *, cwd=None, check=True, env=None, step_name=None, display_cmd=None):
            shown_command = display_cmd or " ".join(cmd)
            log("$ " + shown_command, note=False)
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            output_lines = []
            assert process.stdout is not None
            for raw_line in process.stdout:
                line = raw_line.rstrip('\n')
                output_lines.append(line)
                log(line, note=False)
            return_code = process.wait()
            step_record = {
                'command': shown_command,
                'exit_code': return_code,
            }
            if cwd is not None:
                step_record['cwd'] = str(cwd)
            if step_name:
                step_record['name'] = step_name
            if output_lines:
                step_record['output'] = output_lines
            if _stage_stack:
                _stage_stack[-1]['steps'].append(step_record)
            if check and return_code != 0:
                raise RuntimeError("Command failed with exit code {}: {}".format(return_code, shown_command))
            return return_code, output_lines

        def copy_artifact(rel_path: str, *, optional: bool = False) -> Path | None:
            if not rel_path:
                return None
            source = bundle_dir / rel_path
            if not source.exists():
                if optional:
                    log(f"Skipping optional artifact missing at {source}")
                    return None
                raise RuntimeError(f"Missing dependency artifact at {source}")
            destination = repo_dir / rel_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            log(f"Copied dependency {source} -> {destination}")
            return destination

        def copy_dir(src: Path, dest: Path) -> None:
            if not src.exists():
                log("Skipping copy (missing): {}".format(src))
                return
            if dest.exists():
                shutil.rmtree(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dest)
            log('Copied {} -> {}'.format(src, dest))

        def remove_dir(path: Path) -> None:
            if path.exists():
                shutil.rmtree(path)
                log('Removed {}'.format(path))

        def has_tests(path: Path) -> bool:
            return path.exists() and any(child.is_file() for child in path.rglob('*'))

        def load_secret(env_map, plain_key: str, base64_keys: tuple[str, ...]) -> str | None:
            value = env_map.get(plain_key)
            if value:
                return value
            for key in base64_keys:
                encoded = env_map.get(key)
                if not encoded:
                    continue
                try:
                    return base64.b64decode(encoded).decode('utf-8')
                except Exception as decode_err:
                    log('Failed to decode {}: {}'.format(key, decode_err))
            return None

        def _extract_model(config_text: str) -> str | None:
            match = re.search(r'model\\s*=\\s*"([^\"]+)"', config_text)
            if match:
                return match.group(1)
            return None

        def ensure_profile(config_path: Path, env_map) -> None:
            profile_name = env_map.get('CODEX_PROFILE') or 'default'
            model_name = env_map.get('CODEX_MODEL') or None
            if not config_path.exists():
                model_value = model_name or 'gpt-5-codex'
                config_path.write_text(
                    f"[profiles.{profile_name}]\\nmodel = \\\"{model_value}\\\"\\n",
                    encoding='utf-8',
                )
                return

            config_text = config_path.read_text(encoding='utf-8')
            if f"[profiles.{profile_name}]" in config_text:
                return

            model_value = model_name or _extract_model(config_text) or 'gpt-5-codex'
            with config_path.open('a', encoding='utf-8') as handle:
                handle.write("\\n[profiles.{}]\\nmodel = \\\"{}\\\"\\n".format(profile_name, model_value))

        def prepare_codex_home(env_map, codex_home_path: Path) -> bool:
            codex_home_path.mkdir(parents=True, exist_ok=True)
            wrote = False

            auth_content = load_secret(env_map, 'CODEX_AUTH_JSON', ('CODEX_AUTH_JSON_B64', 'CODEX_AUTH_JSON_BASE64'))
            if auth_content:
                (codex_home_path / 'auth.json').write_text(auth_content, encoding='utf-8')
                wrote = True

            config_content = load_secret(env_map, 'CODEX_CONFIG_TOML', ('CODEX_CONFIG_TOML_B64', 'CODEX_CONFIG_TOML_BASE64'))
            if config_content:
                (codex_home_path / 'config.toml').write_text(config_content, encoding='utf-8')
                wrote = True

            ensure_profile(codex_home_path / 'config.toml', env_map)

            return wrote

        def setup_runner_environment():
            env_map = os.environ.copy()
            for key, value in runner_env.items():
                env_map[str(key)] = str(value)

            dep_path = dependency.get('path') or ''
            data = dependency.get('data') or {}

            if runner_type in {'pytest', 'python'}:
                if not dep_path:
                    raise RuntimeError('Python runner requires environment.dependencies entry with a path.')
                requirements_target = copy_artifact(dep_path)
                if requirements_target is None:
                    raise RuntimeError('Failed to copy requirements file for pytest runner.')

                try:
                    log(f"Using requirements file at {requirements_target}")
                    log(requirements_target.read_text())
                except Exception as req_err:
                    log(f'Failed to read requirements file: {req_err}')

                venv_dir = Path('/opt/sweap-venv')
                if venv_dir.exists():
                    log(f'Using prebuilt virtualenv at {venv_dir}')
                    bin_dir = venv_dir / ('Scripts' if os.name == 'nt' else 'bin')
                    env_map['VIRTUAL_ENV'] = str(venv_dir)
                    env_map['PATH'] = str(bin_dir) + os.pathsep + env_map.get('PATH', '')
                else:
                    venv_dir = Path('/tmp/modal-eval-venv')
                    if venv_dir.exists():
                        shutil.rmtree(venv_dir)
                    venv.create(venv_dir, with_pip=True)
                    bin_dir = venv_dir / ('Scripts' if os.name == 'nt' else 'bin')
                    env_map['VIRTUAL_ENV'] = str(venv_dir)
                    env_map['PATH'] = str(bin_dir) + os.pathsep + env_map.get('PATH', '')
                    pip_exe = bin_dir / ('pip.exe' if os.name == 'nt' else 'pip')
                    run([str(pip_exe), 'install', '--upgrade', 'pip'], cwd=repo_dir, env=env_map)
                    install_cmd_override = dependency.get('install')
                    if install_cmd_override:
                        formatted = install_cmd_override.format(
                            path=str(requirements_target),
                            repo=str(repo_dir),
                            requirements=str(requirements_target),
                        )
                        run(['bash', '-lc', formatted], cwd=repo_dir, env=env_map)
                    else:
                        run([str(pip_exe), 'install', '-r', str(requirements_target)], cwd=repo_dir, env=env_map)

            elif runner_type in {'node', 'npm', 'yarn'}:
                if not dep_path:
                    raise RuntimeError('Node runner requires environment.dependencies entry with path to package.json.')
                package_target = copy_artifact(dep_path)
                if package_target is None:
                    raise RuntimeError('Failed to copy package.json for node runner.')

                lockfile_rel = data.get('lockfile')
                lockfile_target = None
                if lockfile_rel:
                    lockfile_target = copy_artifact(lockfile_rel, optional=True)

                install_cmd_override = dependency.get('install')
                if install_cmd_override:
                    formatted = install_cmd_override.format(
                        path=str(package_target),
                        repo=str(repo_dir),
                        package_json=str(package_target),
                        lockfile=str(lockfile_target) if lockfile_target else '',
                    )
                    run(['bash', '-lc', formatted], cwd=repo_dir, env=env_map)
                else:
                    package_manager = data.get('package_manager', 'npm')
                    default_install = 'npm ci' if package_manager == 'npm' else f"{package_manager} install"
                    run(['bash', '-lc', default_install], cwd=repo_dir, env=env_map)

            else:
                raise RuntimeError(f"Unsupported runner type: {runner_type}")

            cmd_parts = shlex.split(runner_cmd)
            return env_map, cmd_parts

        def run_llm_agent(env, stage_record):
            command = llm_command
            if not command:
                log('SWEEP_LLM_COMMAND not set; skipping LLM edit step.')
                stage_record['status'] = 'skipped'
                return False

            log('Running LLM command: {}'.format(command))
            llm_env = env.copy()
            llm_env['SWEEP_TASK_ID'] = task_id
            llm_env['SWEEP_MODEL'] = model_name
            api_key = llm_env.get('OPENAI_API_KEY') or os.environ.get('OPENAI_API_KEY')
            codex_home = bundle_dir / '.codex'
            llm_env['CODEX_HOME'] = str(codex_home)
            prepared = prepare_codex_home(llm_env, codex_home)
            if prepared:
                log('Loaded Codex credentials from environment secrets into {}'.format(codex_home))

            skip_login = llm_env.get('CODEX_SKIP_LOGIN', '').lower() in {'1', 'true', 'yes'}

            if skip_login:
                log('CODEX_SKIP_LOGIN set; skipping Codex login step.')
            elif api_key:
                sanitized = 'codex login --api-key ****'
                rc, _ = run(
                    ['codex', 'login', '--api-key', api_key],
                    cwd=repo_dir,
                    env=llm_env,
                    display_cmd=sanitized,
                    step_name='codex login',
                )
                if rc != 0:
                    raise RuntimeError('codex login failed with exit code {}'.format(rc))
                log('Codex login succeeded using API key.')
            else:
                log('OPENAI_API_KEY not found in environment')

            llm_env['SWEEP_PROBLEM_PATH'] = str(bundle_dir / description_rel)
            llm_env['SWEEP_REPO_DIR'] = str(repo_dir)
            llm_env['SWEEP_OUTPUT_DIR'] = str(repo_dir / '.sweap_outputs')
            Path(llm_env['SWEEP_OUTPUT_DIR']).mkdir(parents=True, exist_ok=True)
            cmd_template = Template(command)
            command_expanded = cmd_template.safe_substitute(llm_env)
            rc, _ = run(shlex.split(command_expanded), cwd=repo_dir, env=llm_env, step_name='llm command')
            if rc != 0:
                raise RuntimeError('LLM command failed with exit code {}'.format(rc))
            _, diff_output = run(
                ['git', 'diff', '--stat'],
                cwd=repo_dir,
                env=llm_env,
                check=False,
                step_name='git diff --stat',
            )
            diff_text = "\n".join(diff_output).strip()
            stage_record['patch_detected'] = bool(diff_text)
            if diff_text:
                stage_record['notes'].append('Changes detected by git diff.')
            else:
                stage_record['notes'].append('No changes detected by git diff.')
            return bool(diff_text)

        def main() -> None:
            # Keep guardrail tests out of the repository while the model edits files.
            env = None
            cmd_parts: list[str] = []
            with stage('environment_setup', 'Environment Setup'):
                env, cmd_parts = setup_runner_environment()

            pass_dir = repo_dir / pass_dir_rel
            fail_dir = repo_dir / fail_dir_rel

            def command_for_suite(suite: Path) -> list[str]:
                if runner_type in {'node', 'npm', 'yarn', 'pytest', 'python'}:
                    return cmd_parts + [str(suite)]
                return cmd_parts

            baseline_results = {'pass2pass': 'not_run', 'fail2pass': 'not_run'}

            if skip_baseline:
                with stage('baseline', 'Baseline tests') as baseline_stage:
                    baseline_stage['status'] = 'skipped'
                    baseline_results['pass2pass'] = 'skip'
                    baseline_results['fail2pass'] = 'skip'
            else:
                with stage('baseline.stage_guardrails', 'Baseline: stage guardrails'):
                    copy_dir(bundle_dir / pass_dir_rel, pass_dir)
                    copy_dir(bundle_dir / fail_dir_rel, fail_dir)

                with stage('baseline.pass2pass', 'Baseline pass2pass suite') as base_pass_stage:
                    if has_tests(pass_dir):
                        rc, _ = run(
                            command_for_suite(pass_dir_rel),
                            cwd=repo_dir,
                            env=env,
                            check=False,
                            step_name=f'{runner_type} baseline pass2pass',
                        )
                        baseline_results['pass2pass'] = 'pass' if rc == 0 else 'fail'
                        base_pass_stage['status'] = 'passed' if rc == 0 else 'failed'
                        base_pass_stage['notes'].append('Expected pass2pass to pass.')
                    else:
                        baseline_results['pass2pass'] = 'skip'
                        base_pass_stage['status'] = 'skipped'

                with stage('baseline.fail2pass', 'Baseline fail2pass suite') as base_fail_stage:
                    if has_tests(fail_dir):
                        rc, _ = run(
                            command_for_suite(fail_dir_rel),
                            cwd=repo_dir,
                            env=env,
                            check=False,
                            step_name=f'{runner_type} baseline fail2pass',
                        )
                        baseline_results['fail2pass'] = 'pass' if rc == 0 else 'fail'
                        base_fail_stage['status'] = 'passed' if rc != 0 else 'failed'
                        base_fail_stage['notes'].append('Expected fail2pass to fail (non-zero exit).')
                    else:
                        baseline_results['fail2pass'] = 'skip'
                        base_fail_stage['status'] = 'skipped'

                with stage('baseline.cleanup', 'Baseline cleanup'):
                    remove_dir(pass_dir)
                    remove_dir(fail_dir)

            patch_applied = False
            with stage('model_attempt', 'Model Attempt') as model_stage:
                patch_applied = run_llm_agent(env, model_stage)

            with stage('guardrail_sync', 'Stage guardrail suites'):
                copy_dir(bundle_dir / pass_dir_rel, pass_dir)
                copy_dir(bundle_dir / fail_dir_rel, fail_dir)

            evaluation_results = {}
            with stage('tests.pass2pass', 'Run pass2pass suite') as pass_stage:
                if has_tests(pass_dir):
                    rc, _ = run(
                        command_for_suite(pass_dir_rel),
                        cwd=repo_dir,
                        env=env,
                        check=False,
                        step_name=f'{runner_type} pass2pass',
                    )
                    evaluation_results['pass2pass'] = 'pass' if rc == 0 else 'fail'
                    pass_stage['status'] = 'passed' if rc == 0 else 'failed'
                else:
                    log('No pass2pass tests found; skipping baseline pass check.')
                    pass_stage['status'] = 'skipped'
                    evaluation_results['pass2pass'] = 'skip'

            with stage('tests.fail2pass', 'Run fail2pass suite') as fail_stage:
                if has_tests(fail_dir):
                    rc, _ = run(
                        command_for_suite(fail_dir_rel),
                        cwd=repo_dir,
                        env=env,
                        check=False,
                        step_name=f'{runner_type} fail2pass',
                    )
                    evaluation_results['fail2pass'] = 'pass' if rc == 0 else 'fail'
                    fail_stage['status'] = 'passed' if rc == 0 else 'failed'
                else:
                    log('No fail2pass tests found; skipping baseline fail check.')
                    fail_stage['status'] = 'skipped'
                    evaluation_results['fail2pass'] = 'skip'

            result_payload = {
                'baseline': baseline_results,
                'patched': evaluation_results,
                'patch_applied': patch_applied,
                'stages': stages,
                'skip_baseline': skip_baseline,
            }
            print('RESULT_JSON::' + json.dumps(result_payload))

        if __name__ == '__main__':
            try:
                main()
            except Exception as exc:
                print("ERROR: {}".format(exc), file=sys.stderr)
                sys.exit(1)
        """
    )

    dependency_payload = dependency

    script = template.replace("__RUNNER_TYPE__", repr(runner_type))
    script = script.replace("__RUNNER_CMD__", repr(runner_cmd))
    script = script.replace("__RUNNER_ENV__", repr({key: str(value) for key, value in runner_env.items()}))
    script = script.replace("__DEPENDENCY__", repr(dependency_payload))
    script = script.replace("__FAIL_DIR__", repr(fail_dir_rel))
    script = script.replace("__PASS_DIR__", repr(pass_dir_rel))
    script = script.replace("__DESC__", repr(description_rel))
    script = script.replace("__TASK_ID__", repr(task_id))
    script = script.replace("__MODEL_NAME__", repr(model_name))
    script = script.replace("__LLM_COMMAND__", repr(llm_command or ""))
    script = script.replace("__SKIP_BASELINE__", "True" if skip_baseline else "False")

    cleaned = inspect.cleandoc(script)
    cleaned = cleaned.replace("'\n'", "'\\n'")
    cleaned = cleaned.replace('"\n"', '"\\n"')
    normalized_chunks: list[str] = []
    for line in cleaned.splitlines(keepends=True):
        if line.startswith("        "):
            normalized_chunks.append(line[8:])
        else:
            normalized_chunks.append(line)
    return "".join(normalized_chunks)


def _collect_modal_secrets():
    try:
        import modal
    except ImportError:
        return None

    secret_values = {}
    secret_keys = [
        "OPENAI_API_KEY",
        "CODEX_AUTH_JSON",
        "CODEX_AUTH_JSON_B64",
        "CODEX_AUTH_JSON_BASE64",
        "CODEX_CONFIG_TOML",
        "CODEX_CONFIG_TOML_B64",
        "CODEX_CONFIG_TOML_BASE64",
        "CODEX_SKIP_LOGIN",
        "CODEX_PROFILE",
        "CODEX_MODEL",
    ]
    for key in secret_keys:
        value = os.environ.get(key)
        if value is not None:
            secret_values[key] = value
    if not secret_values:
        return None
    return [modal.Secret.from_dict(secret_values)]
