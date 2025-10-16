<?php

declare(strict_types=1);

namespace utils;

use Throwable;
use utils\type\CommandType;
use utils\type\ExceptionType;

final class ExceptionSerializer
{
    public static function serializeException(Throwable $exception, CommandInterface $command): CommandInterface
    {
        $exceptionCommand = new Command($command->getRuntimeName(), CommandType::EXCEPTION(), []);
        $isDebug = false;

        $stackClasses = $stackMethods = $stackLines = $stackFiles = '';

        $trace = $exception->getTrace();
        if (!$isDebug) {
            $trace = self::getStackTraceAfterReflection($trace);
        }

        self::serializeStackTrace($trace, $stackClasses, $stackMethods, $stackLines, $stackFiles);

        $exceptionName = basename(str_replace('\\', '/', get_class($exception)));

        $exceptionCommand = $exceptionCommand->addArgToPayload(ExceptionType::getExceptionCodeByExceptionName($exceptionName));
        $exceptionCommand = $exceptionCommand->addArgToPayload((string)$command);
        $exceptionCommand = $exceptionCommand->addArgToPayload($exceptionName);
        $exceptionCommand = $exceptionCommand->addArgToPayload($exception->getMessage());
        $exceptionCommand = $exceptionCommand->addArgToPayload($stackClasses);
        $exceptionCommand = $exceptionCommand->addArgToPayload($stackMethods);
        $exceptionCommand = $exceptionCommand->addArgToPayload($stackLines);
        $exceptionCommand = $exceptionCommand->addArgToPayload($stackFiles);

        return $exceptionCommand;
    }

    private static function serializeStackTrace(
        array $trace,
        string &$stackClasses,
        string &$stackMethods,
        string &$stackLines,
        string &$stackFiles
    ): void {
        $classes = $methods = $lines = $files = [];

        foreach ($trace as $frame) {
            $classes[] = $frame['class']    ?? 'undefined';
            $methods[] = $frame['function'] ?? 'undefined';
            $lines[]   = isset($frame['line']) ? (string)$frame['line'] : '0';
            $files[]   = $frame['file']     ?? 'undefined';
        }

        $stackClasses = implode('|', $classes);
        $stackMethods = implode('|', $methods);
        $stackLines   = implode('|', $lines);
        $stackFiles   = implode('|', $files);
    }

    private static function getStackTraceAfterReflection(array $trace): array
    {
        $index = 0;
        foreach ($trace as $frame) {
            $class = $frame['class'] ?? '';
            if (strpos($class, 'javonet') !== false || strpos($class, 'Reflector') !== false) {
                break;
            }
            $index++;
        }

        return array_slice($trace, 0, $index);
    }
}
