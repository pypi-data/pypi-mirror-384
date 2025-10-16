package Javonet::Sdk::Core::PerlCommandType;
use strict;
use warnings;
use Moose;
use Exporter qw(import);
our @EXPORT = qw(get_command_type);

my %command_type = (
    'Value'                       => 0,
    'LoadLibrary'                 => 1,
    'InvokeStaticMethod'          => 2,
    'GetStaticField'              => 3,
    'SetStaticField'              => 4,
    'CreateClassInstance'         => 5,
    'GetType'                     => 6,
    'Reference'                   => 7,
    'GetModule'                   => 8,
    'InvokeInstanceMethod'        => 9,
    'Exception'                   => 10,
    'HeartBeat'                   => 11,
    'Cast'                        => 12,
    'GetInstanceField'            => 13,
    'Optimize'                    => 14,
    'GenerateLib'                 => 15,
    'InvokeGlobalFunction'        => 16,
    'DestructReference'           => 17,
    'Array'                       => 18,
    'ArrayGetItem'                => 19,
    'ArrayGetSize'                => 20,
    'ArrayGetRank'                => 21,
    'ArraySetItem'                => 22,
    'Array'                       => 23,
    'RetrieveArray'               => 24,
    'SetInstanceField'            => 25,
    'InvokeGenericStaticMethod'   => 26,
    'InvokeGenericMethod'         => 27,
    'GetEnumItem'                 => 28,
    'GetEnumName'                 => 29,
    'GetEnumValue'                => 30,
    'AsRef'                       => 31,
    'AsOut'                       => 32,
    'GetRefValue'                 => 33,
    'EnableNamespace'             => 34,
    'EnableType'                  => 35,
    'CreateNull'                  => 36,
    'GetStaticMethodAsDelegate'   => 37,
    'GetInstanceMethodAsDelegate' => 38,
    'PassDelegate'                => 39,
    'InvokeDelegate'              => 40,
    'ConvertType'                 => 41,
    'AddEventListener'            => 42,
    'PluginWrapper'               => 43,
    'GetAsyncOperationResult'     => 44,
    'AsKwargs'                    => 45,
    'GetResultType'               => 46,
    'GetGlobalField'              => 47,

);

sub get_command_type {
    my $command = shift;
    return $command_type{$command};
}

1;
