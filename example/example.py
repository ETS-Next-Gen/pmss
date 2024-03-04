import pss.schema
import pss.psstypes

settings = pss.Settings(
    prog="lo",
    description="A system for monitoring",
    epilog="For more information, see PSS documentation."
)

settings.register_field(
    name="server_port",
    command_line_flags=["-p", "--port"],
    type=pss.psstypes.TYPES.port,
    description="The port Learning Observer should run on.",
    default=8888
)
# for i in 'xyzabcdefgh':
#     settings.register_field(
#         name=i,
#         command_line_flags=[f'-{i}', f'--{i}'],
#         type=pss.psstypes.TYPES.port if i != 'a' else pss.psstypes.TYPES.boolean,
#         description="The port Learning Observer should run on.",
#     )

settings.load()
settings.validate()

print('# settings.server_port')
print(settings.server_port)
print("# settings.get('server_port')")
print(settings.get('server_port'))
print("# settings.get('server_port', {'attributes': {'school': 'middlesex'}})")
print(settings.get('server_port', {'attributes': {'school': 'middlesex'}}))
