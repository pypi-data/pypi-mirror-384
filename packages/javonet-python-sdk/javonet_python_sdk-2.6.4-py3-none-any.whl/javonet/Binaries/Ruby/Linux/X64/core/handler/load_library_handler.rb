require_relative 'abstract_command_handler'

class LoadLibraryHandler < AbstractCommandHandler

  @@loaded_libraries = []

  def initialize
    @required_parameters_count = 1
  end

  def process(command)
    begin
      if command.payload.length < @required_parameters_count
        raise ArgumentError.new "Load library parameters mismatch"
      end
      if command.payload.length > @required_parameters_count
        assembly_name = command.payload[1]
      else
        assembly_name = command.payload[0]
      end
      
      # Check if the library exists:
      raise LoadError.new("Library not found: #{assembly_name}") unless File.exist?(assembly_name)
      #noinspection RubyResolve
      require(assembly_name)
      @@loaded_libraries.push(assembly_name)
      return 0
    rescue Exception => e
      return e
    end
  end

  def self.get_loaded_libraries
    @@loaded_libraries
  end
end
