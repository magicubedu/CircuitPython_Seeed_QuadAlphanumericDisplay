from adafruit_ht16k33 import segments
from busio import I2C
from typing import Union, List, Tuple

class SeeedQuadAlphanumericDisplay(segments.Seg14x4):
    def __init__(
        self,
        i2c: I2C,
        address: Union[int, List[int], Tuple[int, ...]] = 0x71,
        auto_write: bool = True
    ) -> None:
        self._upper_dot_on = False
        self._lower_dot_on = False
        super().__init__(i2c, address, auto_write, 4)

    def _adjusted_index(self, index: int) -> int:
        return segments.Seg14x4._adjusted_index(self, index) + 2

    def set_dots(self, upper: bool, lower: bool) -> None:
        self._upper_dot_on = upper
        self._lower_dot_on = lower
        if self._auto_write:
            self.show()

    def _transform_bits(self, buffer: bytearray, start_index: int) -> None:
        aux_start_index = start_index + 2 * 4
        aux_bitmask = 0 | (0b0000_0000_1000_0000 if self._upper_dot_on else 0) | (0b0010_0000_0000_0000 if self._lower_dot_on else 0)
        for i in range(4):
            index = start_index + i * 2
            bitmask = buffer[index + 1] << 8 | buffer[index]

            j_bit = bitmask & 0b0000_0100_0000_0000
            m_bit = bitmask & 0b0010_0000_0000_0000
            match i:
                case 0:
                    aux_bitmask |= j_bit >> 6 | m_bit >> 10
                case 1:
                    aux_bitmask |= j_bit >> 4 | m_bit << 1
                case 2:
                    aux_bitmask |= j_bit >> 5 | m_bit >> 4
                case 3:
                    aux_bitmask |= j_bit | m_bit >> 5

            bitmask = 0 | (bitmask & 0b0000_0000_0000_0001) << 4 | (bitmask & 0b0000_0000_0000_0010) << 5 | (bitmask & 0b0000_0000_0000_0100) << 3 | (bitmask & 0b0000_0000_0000_1000) << 7 | (bitmask & 0b0000_0000_0001_0000) >> 1 | (bitmask & 0b0000_0000_0010_0000) << 9 | (bitmask & 0b0000_0000_0100_0000) << 3 | (bitmask & 0b0000_0000_1000_0000) << 1 | (bitmask & 0b0000_0001_0000_0000) >> 1 | (bitmask & 0b0000_0010_0000_0000) << 4 | (bitmask & 0b0000_1000_0000_0000) << 1 | (bitmask & 0b0001_0000_0000_0000) >> 1

            buffer[index] = bitmask & 0xFF
            buffer[index + 1] = (bitmask >> 8) & 0xFF

        buffer[aux_start_index] = aux_bitmask & 0xFF
        buffer[aux_start_index + 1] = (aux_bitmask >> 8) & 0xFF

    def show(self) -> None:
        device_buffer = self._buffer[:]
        self._transform_bits(device_buffer, 1 + 2)
        for index, i2c_dev in enumerate(self.i2c_device):
            with i2c_dev:
                offset = index * self._buffer_size
                buffer = device_buffer[offset : offset + self._buffer_size]
                i2c_dev.write(buffer)