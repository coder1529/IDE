extension_name = "Example Extension"


def activate(api):

    api.register_command(
        "hello",
        lambda: api.print_terminal("Hello from extension!")
    )

    api.add_button(
        "Hello Extension",
        lambda: api.run_command("hello")
    )