from spyne.model.complex import ComplexModel
from spyne.model.primitive import Unicode

class Password(ComplexModel):
    Value = Unicode

class UsernameToken(ComplexModel):
    Username = Unicode
    Password = Password

class Security(ComplexModel):
    UsernameToken = UsernameToken

    @classmethod
    def resolve_namespace(cls, default_ns, tags=None):
        # Workaround for spyne bug #419: the wsdl:message for an in-header
        # must live in the WSDL target namespace, but spyne references it
        # by the class namespace, which no SOAP client can resolve.
        cls.__namespace__ = "serverroom.soap"

class RegisterUserRequest(ComplexModel):
    __namespace__ = "serverroom.soap"
    username = Unicode(min_len=3)
    password = Unicode(min_len=6)
    role = Unicode