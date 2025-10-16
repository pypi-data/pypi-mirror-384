require_relative '../protocol/command_serializer'
require_relative '../protocol/command_deserializer'
require_relative '../handler/handler'

class Interpreter
  @@handler = Handler.new

  def execute(command, connection_type, connection_data)
    message_byte_array = CommandSerializer.new.serialize(command, connection_data)
    if command.runtime_name == RuntimeNameJavonet::RUBY && connection_type == ConnectionType::IN_MEMORY
      require_relative '../receiver/receiver'
      response_byte_array = Receiver.new.send_command(message_byte_array, message_byte_array.length)
    elsif connection_type == ConnectionType::WEB_SOCKET
      require_relative '../web_socket_client/web_socket_client'
      response_byte_array = WebSocketClient.send_message(connection_data.hostname, message_byte_array)
    else
      require_relative '../transmitter/transmitter'
      response_byte_array = Transmitter.send_command(message_byte_array, message_byte_array.length)
    end

    CommandDeserializer.new(response_byte_array).deserialize
  end

  def process(byte_array)
    received_command = CommandDeserializer.new(byte_array).deserialize
    @@handler.handle_command(received_command)
  end
end
