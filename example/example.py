import pmss

settings = pmss.init(
    prog="lo",
    description="A system for monitoring",
    epilog="For more information, see PMSS documentation."
)

pmss.register_field(
    name="server_port",
    command_line_flags=["-p", "--port"],
    type=pmss.TYPES.port,
    description="The port Learning Observer should run on.",
    default=8888
)

pmss.register_field(
    name="hostname",
    type=pmss.TYPES.hostname,
    description="The hostname",
    required=True
)

pmss.validate(settings)

print('# settings.server_port()')
print(settings.server_port())
print("# settings.get('server_port')")
print(settings.get('server_port'))
print("# settings.get('server_port', attributes={'school': 'middlesex'}))")
print(settings.get('server_port', attributes={'school': 'middlesex'}))
print(settings.debug_dump())
pmss.usage()
