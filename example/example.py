import pss.schema
import pss.psstypes
from pss.settings import Settings



settings = Settings(
    prog="lo",
    description="A system for monitoring",
    epilog="For more information, see PSS documentation."
)

pss.schema.register_field(
    name="server_port",
    command_line_flags=["-p", "--port"],
    type=pss.psstypes.TYPES.port,
    description="The port Learning Observer should run on.",
    default=8888
)

pss.schema.register_field(
    name="hostname",
    type=pss.psstypes.TYPES.hostname,
    description="The hostname",
    required=True
)


settings.load()
pss.schema.validate(settings)

print('# settings.server_port')
print(settings.server_port)
print("# settings.get('server_port')")
print(settings.get('server_port'))
print("# settings.get('server_port', {'attributes': {'school': 'middlesex'}})")
print(settings.get('server_port', {'attributes': {'school': 'middlesex'}}))
print(settings.debug_dump())
