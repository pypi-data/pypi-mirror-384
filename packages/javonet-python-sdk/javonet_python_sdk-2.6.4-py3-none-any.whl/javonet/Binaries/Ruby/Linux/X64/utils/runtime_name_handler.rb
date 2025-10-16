# frozen_string_literal: true
require_relative './runtime_name_javonet'

class RuntimeNameHandler
  def self.get_name(runtime_name)
    if runtime_name == RuntimeNameJavonet::CLR
      return 'clr'
    end
    if runtime_name == RuntimeNameJavonet::GO
      return 'go'
    end
    if runtime_name == RuntimeNameJavonet::JVM
      return 'jvm'
    end
    if runtime_name == RuntimeNameJavonet::NETCORE
      return 'netcore'
    end
    if runtime_name == RuntimeNameJavonet::PERL
      return 'perl'
    end
    if runtime_name == RuntimeNameJavonet::PYTHON
      return 'python'
    end
    if runtime_name == RuntimeNameJavonet::RUBY
      return 'ruby'
    end
    if runtime_name == RuntimeNameJavonet::NODEJS
      return 'nodejs'
    end
    if runtime_name == RuntimeNameJavonet::CPP
      return 'cpp'
    end
    if runtime_name == RuntimeNameJavonet::PHP
      return 'php'
    end
    if runtime_name == RuntimeNameJavonet::PYTHON27
      return 'python27'
    end
  end
end
