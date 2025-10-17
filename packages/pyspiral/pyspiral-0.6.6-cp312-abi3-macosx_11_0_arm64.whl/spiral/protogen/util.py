import betterproto
from betterproto.grpc.grpclib_server import ServiceBase


def patch_protos(proto_module, our_module_globals):
    """Calculate __all__ to re-export protos from a module."""

    betterproto_types = (betterproto.Message, betterproto.Enum, betterproto.ServiceStub, ServiceBase)

    proto_overrides = {}
    missing = set()
    for ident in dir(proto_module):
        var = getattr(proto_module, ident)
        if isinstance(var, type) and issubclass(var, betterproto_types):
            if ident in our_module_globals:
                override = id(our_module_globals.get(ident)) != id(var)
            else:
                override = False
                missing.add(ident)
            proto_overrides[ident] = override

    if missing:
        print(f"from {proto_module.__name__} import (")
        for ident, override in proto_overrides.items():
            if override:
                print(f"    {ident} as {ident}_,")
            else:
                print(f"    {ident},")
        print(")")
        print("\n")
        print("__all__ = [")
        for ident in proto_overrides:
            print(f'    "{ident}",')
        print("]")

        raise ValueError(f"Missing types that need to be re-exported: {missing}")

    # Patch any local subclasses back into the original module so the gRPC client will use them
    for ident, override in proto_overrides.items():
        if override:
            setattr(proto_module, ident, our_module_globals[ident])
