from acri.sandbox import sandboxed


def test_wraps_the_command_in_docker_run_with_limits():
    params = sandboxed(["npx", "-y", "some-server"], "node:20-slim", memory="128m", cpus=0.25)
    assert params.command == "docker"
    assert params.args == [
        "run", "-i", "--rm", "--memory=128m", "--cpus=0.25",
        "node:20-slim", "npx", "-y", "some-server",
    ]


def test_network_true_by_default_since_most_mcp_servers_need_it():
    params = sandboxed(["cmd"], "img")
    assert "--network=none" not in params.args


def test_network_false_adds_the_restriction():
    params = sandboxed(["cmd"], "img", network=False)
    assert "--network=none" in params.args


def test_volumes_become_dash_v_flags_before_the_image():
    params = sandboxed(["cmd"], "img", volumes={"/host/project": "/repo", "/host/ro": "/data:ro"})
    assert "-v" in params.args
    i = params.args.index("img")
    assert params.args[:i].count("-v") == 2
    assert "/host/project:/repo" in params.args
    assert "/host/ro:/data:ro" in params.args  # caller appends :ro itself -- no separate flag


def test_no_volumes_adds_no_dash_v_flags():
    params = sandboxed(["cmd"], "img")
    assert "-v" not in params.args
