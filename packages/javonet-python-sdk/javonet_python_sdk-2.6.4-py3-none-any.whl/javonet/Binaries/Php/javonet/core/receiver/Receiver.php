<?php

declare(strict_types=1);

namespace core\receiver;

use core\interpreter\Interpreter;
use core\protocol\CommandSerializer;


use Throwable;
use utils\Command;
use utils\ExceptionSerializer;
use utils\RuntimeLogger;
use utils\RuntimeName;
use utils\type\CommandType;

final class Receiver
{

    public function sendCommand(array $messageByteArray): array
    {
        try {
            $result = (new Interpreter())->process($messageByteArray);
            return CommandSerializer::serialize($result, null);
        } catch (Throwable $ex) {
            $exceptionCommand = ExceptionSerializer::serializeException(
                $ex,
                new Command(RuntimeName::PHP(), CommandType::EXCEPTION(), [])
            );
            return CommandSerializer::serialize($exceptionCommand, null);
        }
    }

    public function heartBeat(array $messageByteArray): array
    {
        return [$messageByteArray[11], $messageByteArray[12] - 2];
    }

    public function getRuntimeInfo(): string
    {
        return RuntimeLogger::getRuntimeInfo();
    }
}
