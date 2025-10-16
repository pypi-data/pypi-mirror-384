package Javonet::Core::Interpreter::Interpreter;
use strict;
use warnings;
use lib 'lib';
use aliased 'Javonet::Core::Handler::PerlHandler' => 'PerlHandler';
use aliased 'Javonet::Core::Protocol::CommandSerializer' => 'CommandSerializer';
use aliased 'Javonet::Core::Protocol::CommandDeserializer' => 'CommandDeserializer';

use Exporter qw(import);
our @EXPORT = qw(execute_ process);

my $handler = PerlHandler->new();

sub execute_ {
    my $self = shift;
    my $command = shift;
    my $connection_type = shift;
    my $tcp_address = shift;
    my @serialized_command = Javonet::Core::Protocol::CommandSerializer->serialize($command, $connection_type, $tcp_address, 0);
    my $response_byte_array_ref;
    if ($command->{runtime} eq Javonet::Sdk::Core::RuntimeLib::get_runtime('Perl')) {
        require Javonet::Core::Receiver::Receiver;
        $response_byte_array_ref = Javonet::Core::Receiver::Receiver->send_command(\@serialized_command);
    } else {
        require Javonet::Core::Transmitter::PerlTransmitter;
        $response_byte_array_ref = Javonet::Core::Transmitter::PerlTransmitter->t_send_command(\@serialized_command);
    }

    my $commandDeserializer = CommandDeserializer->new($response_byte_array_ref);
    return $commandDeserializer->decode();
}

sub process {
    my ($self, $message_byte_array_ref) = @_;
    my @message_byte_array = @$message_byte_array_ref;
    my $commandDeserializer = CommandDeserializer->new(\@message_byte_array);
    my $command = $commandDeserializer->decode();
    my $response = $handler->handle_command($command);
    my $commandSerializer = CommandSerializer->new();
    my @response_byte_array = $commandSerializer->serialize($response, 0, 0, 0);
    return @response_byte_array;
}

1;
