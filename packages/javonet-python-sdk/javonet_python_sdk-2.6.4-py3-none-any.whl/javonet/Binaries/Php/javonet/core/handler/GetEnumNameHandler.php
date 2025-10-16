<?php

declare(strict_types=1);

namespace core\handler;

use utils\CommandInterface;

final class GetEnumNameHandler extends AbstractHandler
{
    public function process(CommandInterface $command)
    {
        throw new \Exception(__CLASS__ . ' is not implemented in PHP');
    }
}

