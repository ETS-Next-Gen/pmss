fields = {}

def canonical_field_name(field_name):
    return ".".join(field_name)

def register_field(
        field,
        data_type,
        validation,
        info,
        required,
        default
):
    pass

register_field(
    field = "hostname",
    data_type = 
)

"""
hostname:
  type:
    python: str
  validation:
    regexp: [a-zA-Z0-9\-\.]+
  info:
    short_en: Host name
    desc_en: The URL of the server. This may be used for e.g. generating links.
    example: localhost
  required: true
  default: localhost
protocol:
  python_type: str
  validation:
    options:
      - http
      - https
  required: true
  default: http
auth:
  type:
    python: dict
  validation:
    required_key: [google_oath, password_file, http_basic_auth]  # AND versus OR?
auth.google_oauth:
"""
