require_relative 'abstract_command_handler'

class AsRefHandler < AbstractCommandHandler
  def process(command)
    begin
      raise "#{self.class} is not implemented in Ruby"
    rescue Exception => e
      return e
    end
  end
end
