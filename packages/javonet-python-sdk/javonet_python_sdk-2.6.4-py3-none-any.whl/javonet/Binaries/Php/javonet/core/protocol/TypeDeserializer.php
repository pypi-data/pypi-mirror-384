<?php

declare(strict_types=1);

namespace core\protocol;

use utils\StringEncodingMode;

final class TypeDeserializer
{
    private function __construct()
    {
    }

    public static function deserializeString(StringEncodingMode $stringEncodingMode, array $bytes): string
    {
        $str = pack("C*", ...$bytes);
        switch ($stringEncodingMode->getValue()) {
            case StringEncodingMode::JAVONET_ASCII:
                return iconv('ASCII', 'ASCII', $str);
            case StringEncodingMode::JAVONET_UTF8:
                return iconv('UTF-8', 'UTF-8', $str);
            case StringEncodingMode::JAVONET_UTF16:
                return iconv('UTF-16LE', 'UTF-16LE', $str);
            case StringEncodingMode::JAVONET_UTF32:
                return iconv('UTF-32LE', 'UTF-32LE', $str);
            default:
                return iconv('UTF-8', 'UTF-8', $str);
        }
    }


    public static function deserializeInt(array $bytes): int
    {
        $int = ($bytes[0] & 0xFF)
            | (($bytes[1] & 0xFF) << 8)
            | (($bytes[2] & 0xFF) << 16)
            | (($bytes[3] & 0xFF) << 24);

        return $int & 0x80000000 ? $int - 0x100000000 : $int;
    }

    public static function deserializeBool(array $bytes): bool
    {
        return $bytes[0] === 1;
    }

    public static function deserializeFloat(array $bytes): float
    {
        return (float) substr(
            number_format(
                unpack(
                    'f',
                    pack(
                        'l',
                        self::deserializeInt($bytes)
                    )
                )[1],
                7, '.', ''),
            0, -1
        );
    }

    public static function deserializeByte(int $byteVal): int
    {
        return $byteVal & 0xFF;
    }

    public static function deserializeChar(int $byteVal): string
    {
        return chr($byteVal & 0xFF);
    }

    public static function deserializeLong(array $bytes): int
    {
        return (($bytes[0] & 0xFF)
            | (($bytes[1] & 0xFF) << 8)
            | (($bytes[2] & 0xFF) << 16)
            | (($bytes[3] & 0xFF) << 24)
            | (($bytes[4] & 0xFF) << 32)
            | (($bytes[5] & 0xFF) << 40)
            | (($bytes[6] & 0xFF) << 48)
            | (($bytes[7] & 0xFF) << 56));
    }

    public static function deserializeDouble(array $bytes): float
    {
        return unpack('d',
            pack('P', self::deserializeLong($bytes))
        )[1];
    }

    public static function deserializeNull()
    {
        return null;
    }
}
