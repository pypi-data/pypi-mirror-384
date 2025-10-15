# Development

This page targets the betterproto maintainers.

## Recompiling the lib proto files

After some updates in the compiler, it might be useful to recompile the standard Google proto files used by the
compiler. The output of the `compiler_lib` test should be used.

!!! warning
    These proto files are written with the `proto2` syntax, which is not supported by betterproto. For the compiler to
    work, you need to manually patch the generated file to mark the field `oneof_index` in `Field` and
    `FieldDescriptorProto` optional.

In the compiler, you also need to compile the [plugin.proto](https://github.com/protocolbuffers/protobuf/blob/main/src/google/protobuf/compiler/plugin.proto)
file in `src/betterproto2_compiler/lib/google.protobug/compiler/__init__.py`.
