from __future__ import annotations

import sys
import json
import textwrap
import importlib
from pathlib import Path
from typing import Optional, Any

from rich.console import Console

console = Console()


def validate_in_modal(
    *,
    bundle_dir: Path,
    repo_url: str,
    commit: str,
    runner: dict[str, Any],
    dependency: dict[str, Any],
    fail_dir_rel: str,
    pass_dir_rel: str,
    full_config: dict[str, Any] | None,
    run_full: bool,
    github_token: Optional[str] = None,
) -> int:
    """Run validation inside a Modal sandbox (clone, install deps, execute tests)."""
    try:
        import modal
    except Exception as e:  # pragma: no cover - import guard
        console.print("[red]Modal is not installed. Run `pip install modal`.[/red]")
        return 2

    if run_full and not full_config:
        console.print("[red]Manifest missing tests.full configuration required for --full validation.[/red]")
        return 1

    bundle_dir = bundle_dir.resolve()
    patch_path = bundle_dir / "gold_patch.diff"
    if not patch_path.exists():
        console.print(f"[red]Missing gold_patch.diff at {patch_path}[/red]")
        return 1

    dependency_rel = dependency.get("path")
    if dependency_rel:
        dependency_path = bundle_dir / dependency_rel
        if not dependency_path.exists():
            console.print(f"[red]Missing dependency artifact at {dependency_path}[/red]")
            return 1
    runner_type = (runner.get("type") or "").lower()
    runner_cmd = runner.get("command", "")
    runner_env = runner.get("env") or {}
    if not runner_cmd:
        console.print("[red]Runner command is required for Modal validation.[/red]")
        return 1
    if runner_type in {"node", "npm", "yarn"}:
        lockfile_rel = (dependency.get("data") or {}).get("lockfile")
        if lockfile_rel:
            lockfile_path = bundle_dir / lockfile_rel
            if not lockfile_path.exists():
                console.print(f"[yellow]Lockfile {lockfile_path} missing; continuing without it.[/yellow]")

    secret = None
    if github_token:
        secret = modal.Secret.from_dict({"GITHUB_TOKEN": github_token})

    manifest = json.loads((bundle_dir / "task.json").read_text(encoding="utf-8"))
    environment = manifest.get("environment", {})
    modal_image_name = environment.get("modal_image")
    modal_image_id = environment.get("modal_image_id")
    modal_python_version = environment.get("modal_python_version", "3.10")

    try:
        image_api = modal.Image
    except AttributeError:
        try:
            image_module = importlib.import_module("modal.image")
            image_api = getattr(image_module, "Image")
        except Exception as exc:
            console.print(
                "[red]Modal's Python image API is unavailable. Please install or upgrade the `modal` SDK (e.g. `pip install --upgrade modal`).[/red]"
            )
            return 1

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
            .add_local_dir(str(bundle_dir), remote_path="/bundle")
        )

    app = modal.App.lookup("sweap-cli", create_if_missing=True)
    with modal.enable_output():
        sb = modal.Sandbox.create(app=app, image=image, secrets=[secret] if secret else [])
    try:
        # Configure git auth if token is present
        if github_token:
            # Use token via HTTPS auth header for git
            setup = sb.exec(
                "bash",
                "-lc",
                "git config --global http.https://github.com/.extraheader 'Authorization: Basic '$(echo -n x-access-token:$GITHUB_TOKEN | base64 -w0)",
                timeout=30,
            )
            setup.wait()

        clone = sb.exec("bash", "-lc", f"set -euo pipefail; git clone {repo_url} repo && cd repo && git checkout {commit}")
        for line in clone.stdout:
            console.print(line, end="")
        rc = clone.wait()
        if rc != 0:
            console.print("[red]Git clone/checkout failed in Modal Sandbox.[/red]")
            return rc

        chk = sb.exec("bash", "-lc", "cd repo && git apply --check /bundle/gold_patch.diff")
        for line in chk.stdout:
            console.print(line, end="")
        rc = chk.wait()
        if rc != 0:
            console.print("[red]Patch does not apply cleanly in Modal Sandbox.[/red]")
            return rc
        runner_cmd = runner.get("command", "")
        runner_env = runner.get("env") or {}

        validation_script = _render_validation_script(
            runner_type=runner_type,
            runner_cmd=runner_cmd,
            runner_env=runner_env,
            dependency=dependency,
            fail_dir_rel=fail_dir_rel,
            pass_dir_rel=pass_dir_rel,
            full_config=full_config if run_full else None,
            run_full=run_full,
        )
        command = f"python3 - <<'PY'\n{validation_script}\nPY"
        validate_proc = sb.exec(
            "bash",
            "-lc",
            command,
            timeout=1800,
        )
        for line in validate_proc.stdout:
            console.print(line, end="")
        stderr_output = ""
        if validate_proc.stderr is not None:
            stderr_output = validate_proc.stderr.read()
            if stderr_output:
                console.print(stderr_output, end="")
        rc = validate_proc.wait()
        if rc != 0:
            console.print("[red]Modal validation failed.[/red]")
        else:
            console.print("[green]OK[/green] Modal validation succeeded.")
        return rc
    finally:
        try:
            sb.terminate()
        except Exception:
            pass


def _render_validation_script(
    *,
    runner_type: str,
    runner_cmd: str,
    runner_env: dict[str, Any],
    dependency: dict[str, Any],
    fail_dir_rel: str,
    pass_dir_rel: str,
    full_config: dict[str, Any] | None,
    run_full: bool,
) -> str:
    runner_type_literal = json.dumps(runner_type)
    runner_cmd_literal = json.dumps(runner_cmd)
    runner_env_literal = json.dumps({key: str(value) for key, value in runner_env.items()})
    dependency_literal = json.dumps(dependency)
    fail_dir_literal = json.dumps(fail_dir_rel)
    pass_dir_literal = json.dumps(pass_dir_rel)
    full_config_literal = repr(full_config) if full_config is not None else "None"
    run_full_literal = "True" if run_full else "False"

    script = textwrap.dedent(
        """
        import json
        import os
        import shlex
        import shutil
        import subprocess
        import sys
        import venv
        from pathlib import Path

        bundle_dir = Path('/bundle')
        repo_dir = Path('repo')
        patch_path = bundle_dir / 'gold_patch.diff'

        runner_type = json.loads(__RUNNER_TYPE__).lower()
        runner_cmd = json.loads(__RUNNER_CMD__)
        runner_env = json.loads(__RUNNER_ENV__)
        dependency = json.loads(__DEPENDENCY__)
        fail_dir_rel = Path(json.loads(__FAIL_DIR__))
        pass_dir_rel = Path(json.loads(__PASS_DIR__))
        run_full = __RUN_FULL__
        full_config = __FULL_CONFIG__

        def log(message: str) -> None:
            print(message, flush=True)

        def run(cmd, *, cwd=None, check=True, env=None):
            shown = " ".join(cmd)
            log("$ " + shown)
            process = subprocess.run(
                cmd,
                cwd=cwd,
                env=env,
                text=True,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            if check and process.returncode != 0:
                raise RuntimeError(f"Command failed with exit code {process.returncode}: {shown}")
            return process.returncode

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
            return destination

        def copy_dir(src: Path, dest: Path) -> None:
            if not src.exists():
                log(f"Skipping copy (missing): {src}")
                return
            if dest.exists():
                shutil.rmtree(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dest)

        def has_tests(path: Path) -> bool:
            return path.exists() and any(child.is_file() for child in path.rglob('*'))

        def run_full_suite(full_cfg, base_env):
            workdir = (repo_dir / Path(full_cfg.get('working_dir', '.'))).resolve()
            repo_root = repo_dir.resolve()
            if not str(workdir).startswith(str(repo_root)):
                raise RuntimeError('tests.full.working_dir must remain within the repository checkout.')

            env_map = base_env.copy()
            extra_env = full_cfg.get('env') or {}
            if not isinstance(extra_env, dict):
                raise RuntimeError('tests.full.env must be a mapping of strings to strings.')
            for key, value in extra_env.items():
                env_map[str(key)] = str(value)

            def _run_shell(command: str, *, check: bool = True):
                return run(['bash', '-lc', command], cwd=workdir, env=env_map, check=check)

            try:
                for prereq in full_cfg.get('prerequisites', []) or []:
                    log(f"Prerequisite: {prereq}")
                    _run_shell(prereq)

                full_command = full_cfg['command']
                log(f"Full command: {full_command}")
                exit_code = _run_shell(full_command, check=False)
                if exit_code != 0:
                    raise RuntimeError(f"Full test command failed with exit code {exit_code}: {full_command}")
            finally:
                for cleanup_cmd in full_cfg.get('cleanup', []) or []:
                    try:
                        log(f"Cleanup: {cleanup_cmd}")
                        _run_shell(cleanup_cmd, check=False)
                    except Exception as cleanup_err:  # pragma: no cover - best effort
                        log(f"Cleanup command failed: {cleanup_cmd} ({cleanup_err})")

        def setup_runner_environment() -> tuple[dict[str, str], list[str]]:
            env_map = os.environ.copy()
            for key, value in runner_env.items():
                env_map[str(key)] = str(value)

            dep_path = dependency.get('path') or ''
            runner_kind = dependency.get('kind', '').lower()
            data = dependency.get('data') or {}

            if runner_type in {'pytest', 'python'}:
                if not dep_path:
                    raise RuntimeError('Python runner requires environment.dependencies entry with a path.')
                requirements_target = copy_artifact(dep_path)
                if requirements_target is None:
                    raise RuntimeError('Failed to materialise requirements file.')

                log(f'Using requirements file at {requirements_target}')
                venv_dir = Path('/opt/sweap-venv')
                if venv_dir.exists():
                    log(f'Using prebuilt virtualenv at {venv_dir}')
                    bin_dir = venv_dir / ('Scripts' if os.name == 'nt' else 'bin')
                    env_map['VIRTUAL_ENV'] = str(venv_dir)
                    env_map['PATH'] = str(bin_dir) + os.pathsep + env_map.get('PATH', '')
                else:
                    venv_dir = Path('/tmp/modal-validation-venv')
                    if venv_dir.exists():
                        shutil.rmtree(venv_dir)
                    venv.create(venv_dir, with_pip=True)
                    bin_dir = venv_dir / ('Scripts' if os.name == 'nt' else 'bin')
                    env_map['VIRTUAL_ENV'] = str(venv_dir)
                    env_map['PATH'] = str(bin_dir) + os.pathsep + env_map.get('PATH', '')
                    pip_exe = bin_dir / ('pip.exe' if os.name == 'nt' else 'pip')
                    run([str(pip_exe), 'install', '--upgrade', 'pip'], cwd=repo_dir, env=env_map)
                    install_cmd = dependency.get('install')
                    if install_cmd:
                        formatted = install_cmd.format(
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
                    raise RuntimeError('Failed to materialise package.json for node runner.')

                lockfile_rel = data.get('lockfile')
                lockfile_target = None
                if lockfile_rel:
                    lockfile_target = copy_artifact(lockfile_rel, optional=True)

                install_cmd = dependency.get('install')
                if install_cmd:
                    formatted = install_cmd.format(
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

        def main() -> None:
            if not patch_path.exists():
                raise RuntimeError(f"Missing golden patch at {patch_path}")

            env_map, cmd_parts = setup_runner_environment()

            run(['git', 'apply', '--check', str(patch_path)], cwd=repo_dir)
            copy_dir(bundle_dir / pass_dir_rel, repo_dir / pass_dir_rel)
            copy_dir(bundle_dir / fail_dir_rel, repo_dir / fail_dir_rel)

            pass_dir = repo_dir / pass_dir_rel
            fail_dir = repo_dir / fail_dir_rel

            if has_tests(pass_dir):
                rc = run(cmd_parts + [str(pass_dir_rel)], cwd=repo_dir, env=env_map, check=False)
                if rc != 0:
                    raise RuntimeError('Pass2pass tests failed before applying patch.')
            else:
                log('No pass2pass tests found; skipping baseline pass check.')

            if has_tests(fail_dir):
                rc = run(cmd_parts + [str(fail_dir_rel)], cwd=repo_dir, env=env_map, check=False)
                if rc == 0:
                    raise RuntimeError('Fail2pass tests unexpectedly passed before applying patch.')
            else:
                log('No fail2pass tests found; skipping baseline fail check.')

            run(['git', 'apply', str(patch_path)], cwd=repo_dir)

            if has_tests(pass_dir):
                rc = run(cmd_parts + [str(pass_dir_rel)], cwd=repo_dir, env=env_map, check=False)
                if rc != 0:
                    raise RuntimeError('Pass2pass tests failed after applying patch.')

            if has_tests(fail_dir):
                rc = run(cmd_parts + [str(fail_dir_rel)], cwd=repo_dir, env=env_map, check=False)
                if rc != 0:
                    raise RuntimeError('Fail2pass tests still failing after applying patch.')

            if run_full:
                if not full_config:
                    raise RuntimeError('Manifest missing tests.full configuration required for --full validation.')
                log('Running full test command...')
                run_full_suite(full_config, env_map)

            log('Modal validation succeeded.')

        if __name__ == '__main__':
            try:
                main()
            except Exception as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                sys.exit(1)
        """
    )

    script = script.replace("__RUNNER_TYPE__", runner_type_literal)
    script = script.replace("__RUNNER_CMD__", runner_cmd_literal)
    script = script.replace("__RUNNER_ENV__", runner_env_literal)
    script = script.replace("__DEPENDENCY__", dependency_literal)
    script = script.replace("__FAIL_DIR__", fail_dir_literal)
    script = script.replace("__PASS_DIR__", pass_dir_literal)
    script = script.replace("__RUN_FULL__", run_full_literal)
    script = script.replace("__FULL_CONFIG__", full_config_literal)

    return script
