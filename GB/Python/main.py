import json
import pygame

print()

with open('GB/opcodes.json') as f:
    opcodes = json.loads(f.read())

ROM_FILE = 'GB/ROM/snake.gb'
CARTRIDGE = bytearray()

# RAM = bytearray(16)

with open(ROM_FILE, 'rb') as f:
    for (cycle_count, b) in enumerate(f.read()):
        CARTRIDGE.append(b)


def hexstring_to_bytearray(hex_data):
    data = bytearray()
    for c in bytes.fromhex(hex_data):
        data.append(c)
    return data


def get_tile(byte_data):
    TILE_DATA = []
    for c in range(len(byte_data) - 1):
        if c % 2 == 1:
            continue

        BYTE_1 = byte_data[c]
        BYTE_2 = byte_data[c+1]

        colour_ids = []
        for i in range(8):
            b1 = bin(BYTE_1)[2:].zfill(8)
            b2 = bin(BYTE_2)[2:].zfill(8)
            calc = (b2[i] + b1[i])
            colour_ids.append(int(calc, 2))

        TILE_DATA.append(colour_ids)
    return TILE_DATA


# Debug RAM
# print(bytearray.hex(RAM, ' ').upper())

# region Graphics

pygame.init()

# Variables
PIXEL_SIZE = 4
TILE_SIZE = 8
CANVAS_SIZE = (160 * PIXEL_SIZE, 144 * PIXEL_SIZE)

# Pixel States
PIXEL_STATE = [(255, 255, 255), (170, 170, 170), (85, 85, 85), (0, 0, 0)]

# Canvas
canvas = pygame.display.set_mode(CANVAS_SIZE)
pygame.display.set_caption("GB Test")


def update_display():
    """Update the display to render the current canvas"""
    pygame.display.update()


def get_pixel(x_y):
    """True or False if pixel at x_y is ON or OFF"""
    x = x_y[0] * PIXEL_SIZE
    y = x_y[1] * PIXEL_SIZE

    return canvas.get_at((x, y)) != PIXEL_STATE[0]


def draw(x_y, colour_id):
    """Draw a pixel to the canvas"""
    x = x_y[0] * PIXEL_SIZE
    y = x_y[1] * PIXEL_SIZE

    canvas.fill(PIXEL_STATE[colour_id], pygame.Rect(
        x, y, PIXEL_SIZE, PIXEL_SIZE))


def draw_tile(x_y, tile_data):
    """Draw a Tile to the canvas"""
    x_offset = x_y[0] * TILE_SIZE
    y_offset = x_y[1] * TILE_SIZE
    for (y, t) in enumerate(tile_data):
        for (x, i) in enumerate(t):
            draw(((x + x_offset), y + y_offset), i)


def clear_display():
    """Clear the canvas"""
    canvas.fill(PIXEL_STATE[0], pygame.Rect(
        0, 0, CANVAS_SIZE[0], CANVAS_SIZE[1]))


# endregion

# region Registers

# 8 bit Registers
R = {
    'A': 0x35,
    'B': 0x00,
    'C': 0x00,
    'D': 0x00,
    'E': 0x00,
    'F': 0x00,
    'H': 0x00,
    'L': 0x00,
}

SP = 0x0000
PC = 0x0000

# region Combined 8 bit (16 bit) registers


def getSP():
    return SP['high'] << 8 | SP['low']

def setPC(value : int):
    global PC
    PC = value


def incPC(value : int):
    global PC
    setPC(PC + value)


def getAF():
    return R['A'] << 8 | R['F']


def getBC():
    return R['B'] << 8 | R['C']


def getDE():
    return R['D'] << 8 | R['E']


def getHL():
    return R['H'] << 8 | R['L']


def setHL(value):
    R['H'] = value >> 8
    R['L'] = value & 255  # 0b11111111


def getLowerNibble(value: int):
    return value & 0b1111


def debugRegAsHex():
    print(R)
    print([(c, hex(R[c])) for c in R])


def getFlags():
    flags = R['F'] >> 4
    return {'Z': flags >> 3 & 1, 'N': flags >> 2 & 1, 'H': flags >> 1 & 1, 'C': flags & 1}


def setFlag(Z: bool | None, N: bool | None, H: bool | None, C: bool | None):
    flags = getFlags()
    calc = (flags['Z'] if Z is None else int(Z)) << 7 | (flags['N'] if N is None else int(
        N)) << 6 | (flags['H'] if H is None else int(H)) << 5 | (flags['C'] if C is None else int(C)) << 4
    R['F'] = calc


# endregion

# endregion

# region Opcodes

def NOP_00():
    incPC(1)


def INC_R8(register):
    initial = R[register]
    calc = initial + 1
    final = calc % 256
    R[register] = final
    setFlag(final == 0, False, getLowerNibble(
        initial) > getLowerNibble(calc), None)
    incPC(1)


def INC_04():
    """INC B"""
    INC_R8('B')


def DEC_R8(register):
    initial = R[register]
    calc = initial - 1
    final = calc % 256
    R[register] = final
    setFlag(final == 0, True, getLowerNibble(
        calc) > getLowerNibble(initial), None)
    debugRegAsHex()


def DEC_05():
    """DEC B"""
    DEC_R8('B')


def LD_N8(register, value):
    R[register] = value
    debugRegAsHex()


def LD_06(value):
    """LD B,n8"""
    LD_N8('B', value)


def RLCA_07():
    initial = R['A']
    carryBit = (initial >> 7)
    calc = (initial << 1) & 0b11111110 | carryBit
    print(bin(initial))
    print(bin(carryBit))
    print(bin(calc))
    R['A'] = calc
    setFlag(False, False, False, carryBit)
    debugRegAsHex()


def ADD_09():
    """ADD HL,BC"""
    calc = getHL() + getBC()
    setHL(calc % 65536)
    setFlag(None, False, calc > 2047, calc > 65535)
    debugRegAsHex()


def INC_0C():
    """INC C"""
    INC_R8('C')


def DEC_0D():
    """DEC C"""
    DEC_R8('C')


def LD_0E(value):
    """LD C,n8"""
    LD_N8('C', value)


def RRCA_0F():
    initial = R['A']
    carryBit = (initial & 0b1)
    calc = (carryBit << 7) | initial >> 1
    R['A'] = calc
    setFlag(False, False, False, carryBit)
    debugRegAsHex()


def INC_14():
    """INC D"""
    INC_R8('D')


def DEC_15():
    """DEC D"""
    DEC_R8('D')


def LD_16(value):
    """LD D,n8"""
    LD_N8('D', value)


def RLA_17():
    initial = R['A']
    carryBit = (initial >> 7)
    c = getFlags()['C']
    calc = (initial << 1) & 0b11111110 | c
    R['A'] = calc
    setFlag(False, False, False, carryBit)
    debugRegAsHex()


def JR_18(value):
    """JR e8"""
    if (value & (1 << 7)) != 0:
        addr = -(128 - (value - (1 << 7)))
        incPC(PC + addr)
        return
    incPC(value)


def ADD_19():
    """ADD HL,DE"""
    calc = getHL() + getDE()
    setHL(calc % 65536)
    setFlag(None, False, calc > 2047, calc > 65535)
    debugRegAsHex()


def JR_20(value):
    """JR NZ,e8"""
    z = getFlags()['Z']
    if z == 0:
        JR_18(value)


def INC_1C():
    """INC E"""
    INC_R8('E')


def DEC_1D():
    """DEC E"""
    DEC_R8('E')


def LD_1E(value):
    """LD E,n8"""
    LD_N8('E', value)


def RRA_1F(register):
    initial = R[register]
    carryBit = (initial & 0b1)
    c = getFlags()['C']
    calc = (c << 7) | initial >> 1
    R[register] = calc
    setFlag(False, False, False, carryBit)
    debugRegAsHex()


def INC_24():
    """INC H"""
    INC_R8('H')


def DEC_25():
    """DEC H"""
    DEC_R8('H')


def LD_26(value):
    """LD H,n8"""
    LD_N8('H', value)


def JR_28(value):
    """JR Z,e8"""
    z = getFlags()['Z']
    if z == 1:
        JR_18(value)


def ADD_29():
    """ADD HL,HL"""
    calc = getHL() + getHL()
    setHL(calc % 65536)
    setFlag(None, False, calc > 2047, calc > 65535)
    debugRegAsHex()


def INC_2C():
    """INC L"""
    INC_R8('L')


def DEC_2D():
    """DEC L"""
    DEC_R8('L')


def LD_2E(value):
    """LD L,n8"""
    LD_N8('L', value)


def CPL_2F():
    """CPL"""
    R['A'] = R['A'] ^ 0b11111111
    setFlag(None, True, True, None)
    debugRegAsHex()


def JR_30(value):
    """JR NC,e8"""
    c = getFlags()['C']
    if c == 0:
        JR_18(value)


def INC_34():
    """INC [HL]"""
    pass


def DEC_35():
    """DEC [HL]"""
    pass


def LD_36(value):
    """LD [HL],n8"""
    pass


def SCF_37():
    """SCF"""
    setFlag(None, False, False, True)


def JR_38(value):
    """JR C,e8"""
    c = getFlags()['C']
    if c == 1:
        JR_18(value)


def ADD_39():
    """ADD HL,SP"""
    calc = getHL() + getSP()
    setHL(calc % 65536)
    setFlag(None, False, calc > 2047, calc > 65535)
    debugRegAsHex()


def INC_3C():
    """INC A"""
    INC_R8('A')


def DEC_3D():
    """DEC A"""
    DEC_R8('A')


def LD_3E(value):
    """LD A,n8"""
    LD_N8('A', value)


def CCF_3F():
    """CCF"""
    setFlag(None, False, False, getFlags()['C'] == 0)
    debugRegAsHex()


def LD_R8(register_1, register_2):
    R[register_1] = R[register_2]
    debugRegAsHex()


def LD_40():
    """LD B,B"""
    LD_R8('B', 'B')


def LD_41():
    """LD B,C"""
    LD_R8('B', 'C')


def LD_42():
    """LD B,D"""
    LD_R8('B', 'D')


def LD_43():
    """LD B,E"""
    LD_R8('B', 'E')


def LD_44():
    """LD B,H"""
    LD_R8('B', 'H')


def LD_45():
    """LD B,L"""
    LD_R8('B', 'L')


def LD_46():
    """LD B,[HL]"""
    pass


def LD_47():
    """LD B,A"""
    LD_R8('B', 'A')


def LD_48():
    """LD C,B"""
    LD_R8('C', 'B')


def LD_49():
    """LD C,C"""
    LD_R8('C', 'C')


def LD_4A():
    """LD C,D"""
    LD_R8('C', 'D')


def LD_4B():
    """LD C,E"""
    LD_R8('C', 'E')


def LD_4C():
    """LD C,H"""
    LD_R8('C', 'H')


def LD_4D():
    """LD C,L"""
    LD_R8('C', 'L')


def LD_4E():
    """LD C,[HL]"""
    pass


def LD_4F():
    """LD C,A"""
    LD_R8('C', 'A')


def LD_50():
    """LD D,B"""
    LD_R8('D', 'B')


def LD_51():
    """LD D,C"""
    LD_R8('D', 'C')


def LD_52():
    """LD D,D"""
    LD_R8('D', 'D')


def LD_53():
    """LD D,E"""
    LD_R8('D', 'E')


def LD_54():
    """LD D,H"""
    LD_R8('D', 'H')


def LD_55():
    """LD D,L"""
    LD_R8('D', 'L')


def LD_56():
    """LD D,[HL]"""
    pass


def LD_57():
    """LD D,A"""
    LD_R8('D', 'A')


def LD_58():
    """LD E,B"""
    LD_R8('E', 'B')


def LD_59():
    """LD E,C"""
    LD_R8('E', 'C')


def LD_5A():
    """LD E,D"""
    LD_R8('E', 'D')


def LD_5B():
    """LD E,E"""
    LD_R8('E', 'E')


def LD_5C():
    """LD E,H"""
    LD_R8('E', 'H')


def LD_5D():
    """LD E,L"""
    LD_R8('E', 'L')


def LD_5E():
    """LD E,[HL]"""
    pass


def LD_5F():
    """LD E,A"""
    LD_R8('E', 'A')


def LD_60():
    """LD H,B"""
    LD_R8('H', 'B')


def LD_61():
    """LD H,C"""
    LD_R8('H', 'C')


def LD_62():
    """LD H,D"""
    LD_R8('H', 'D')


def LD_63():
    """LD H,E"""
    LD_R8('H', 'E')


def LD_64():
    """LD H,H"""
    LD_R8('H', 'H')


def LD_65():
    """LD H,L"""
    LD_R8('H', 'L')


def LD_66():
    """LD H,[HL]"""
    pass


def LD_67():
    """LD H,A"""
    LD_R8('H', 'A')


def LD_68():
    """LD L,B"""
    LD_R8('L', 'B')


def LD_69():
    """LD L,C"""
    LD_R8('L', 'C')


def LD_6A():
    """LD L,D"""
    LD_R8('L', 'D')


def LD_6B():
    """LD L,E"""
    LD_R8('L', 'E')


def LD_6C():
    """LD L,H"""
    LD_R8('L', 'H')


def LD_6D():
    """LD L,L"""
    LD_R8('L', 'L')


def LD_6E():
    """LD L,[HL]"""
    pass


def LD_6F():
    """LD L,A"""
    LD_R8('L', 'A')


def LD_70():
    """LD [HL],B"""
    pass


def LD_71():
    """LD [HL],C"""
    pass


def LD_72():
    """LD [HL],D"""
    pass


def LD_73():
    """LD [HL],E"""
    pass


def LD_74():
    """LD [HL],H"""
    pass


def LD_75():
    """LD [HL],L"""
    pass


def HALT_76():
    """HALT"""
    pass


def LD_77():
    """LD [HL],A"""
    pass


def LD_78():
    """LD A,B"""
    LD_R8('A', 'B')


def LD_79():
    """LD A,C"""
    LD_R8('A', 'C')


def LD_7A():
    """LD A,D"""
    LD_R8('A', 'D')


def LD_7B():
    """LD A,B"""
    LD_R8('A', 'E')


def LD_7C():
    """LD A,H"""
    LD_R8('A', 'H')


def LD_7D():
    """LD A,L"""
    LD_R8('A', 'L')


def LD_7E():
    """LD A,[HL]"""
    pass


def LD_7F():
    """LD A,A"""
    LD_R8('A', 'A')


def ADD_A_N8(value):
    initial = R['A']
    calc = initial + value
    final = calc % 256
    R['A'] = final
    setFlag(final == 0, False, getLowerNibble(initial)
            > getLowerNibble(value), calc > 255)
    debugRegAsHex()


def ADD_80():
    """ADD A,B"""
    ADD_A_N8(R['B'])


def ADD_81():
    """ADD A,C"""
    ADD_A_N8(R['C'])


def ADD_82():
    """ADD A,D"""
    ADD_A_N8(R['D'])


def ADD_83():
    """ADD A,E"""
    ADD_A_N8(R['E'])


def ADD_84():
    """ADD A,H"""
    ADD_A_N8(R['H'])


def ADD_85():
    """ADD A,L"""
    ADD_A_N8(R['L'])


def ADD_86():
    """ADD A,[HL]"""
    pass


def ADD_87():
    """ADD A,A"""
    ADD_A_N8(R['A'])


def ADC_A_N8(value):
    initial = R['A']
    value = value + getFlags()['C']
    calc = initial + value
    final = calc % 256
    R['A'] = final
    setFlag(final == 0, False,
            getLowerNibble(initial) > getLowerNibble(value), calc > 255)
    debugRegAsHex()


def ADC_88():
    """ADC A,B"""
    ADC_A_N8(R['B'])


def ADC_89():
    """ADC A,C"""
    ADC_A_N8(R['C'])


def ADC_8A():
    """ADC A,D"""
    ADC_A_N8(R['D'])


def ADC_8B():
    """ADC A,E"""
    ADC_A_N8(R['E'])


def ADC_8C():
    """ADC A,H"""
    ADC_A_N8(R['H'])


def ADC_8D():
    """ADC A,L"""
    ADC_A_N8(R['L'])


def ADC_8E():
    """ADC A,[HL]"""
    pass


def ADC_8F():
    """ADC A,A"""
    ADC_A_N8(R['A'])


def SUB_A_N8(value):
    initial = R['A']
    calc = initial - value
    final = calc % 256
    R['A'] = final
    setFlag(final == 0, True, getLowerNibble(value)
            > getLowerNibble(initial), calc < 0)
    debugRegAsHex()


def SUB_90():
    """SUB A,B"""
    SUB_A_N8(R['B'])


def SUB_91():
    """SUB A,C"""
    SUB_A_N8(R['C'])


def SUB_92():
    """SUB A,D"""
    SUB_A_N8(R['D'])


def SUB_93():
    """SUB A,E"""
    SUB_A_N8(R['E'])


def SUB_94():
    """SUB A,H"""
    SUB_A_N8(R['H'])


def SUB_95():
    """SUB A,L"""
    SUB_A_N8(R['L'])


def SUB_96():
    """SUB A,[HL]"""
    pass


def SUB_97():
    """SUB A,A"""
    SUB_A_N8(R['A'])


def SBC_A_N8(value):
    initial = R['A']
    value = value + getFlags()['C']
    calc = initial - value
    final = calc % 256
    R['A'] = final
    setFlag(final == 0, True, getLowerNibble(value)
            > getLowerNibble(initial), calc < 0)
    debugRegAsHex()


def SBC_98():
    """SBC A,B"""
    SBC_A_N8(R["B"])


def SBC_99():
    """SBC A,C"""
    SBC_A_N8(R["C"])


def SBC_9A():
    """SBC A,D"""
    SBC_A_N8(R["D"])


def SBC_9B():
    """SBC A,E"""
    SBC_A_N8(R["E"])


def SBC_9C():
    """SBC A,H"""
    SBC_A_N8(R["H"])


def SBC_9D():
    """SBC A,L"""
    SBC_A_N8(R["L"])


def SBC_9E():
    """SBC A,[HL]"""
    pass


def SBC_9F():
    """SBC A,A"""
    SBC_A_N8(R["A"])


def AND_A_N8(value):
    initial = R['A']
    calc = initial & value
    R['A'] = calc
    setFlag(calc == 0, False, True, False)
    debugRegAsHex()


def AND_A0():
    """AND A,B"""
    AND_A_N8(R['B'])


def AND_A1():
    """AND A,C"""
    AND_A_N8(R['C'])


def AND_A2():
    """AND A,D"""
    AND_A_N8(R['D'])


def AND_A3():
    """AND A,E"""
    AND_A_N8(R['E'])


def AND_A4():
    """AND A,H"""
    AND_A_N8(R['H'])


def AND_A5():
    """AND A,L"""
    AND_A_N8(R['L'])


def AND_A6():
    """AND A,[HL]"""
    pass


def AND_A7():
    """AND A,A"""
    AND_A_N8(R['A'])


def XOR_A_N8(value):
    initial = R['A']
    calc = initial ^ value
    R['A'] = calc
    setFlag(calc == 0, False, False, False)
    debugRegAsHex()


def XOR_A8():
    """XOR A,B"""
    XOR_A_N8(R['B'])


def XOR_A9():
    """XOR A,C"""
    XOR_A_N8(R['C'])


def XOR_AA():
    """XOR A,D"""
    XOR_A_N8(R['D'])


def XOR_AB():
    """XOR A,E"""
    XOR_A_N8(R['E'])


def XOR_AC():
    """XOR A,H"""
    XOR_A_N8(R['H'])


def XOR_AD():
    """XOR A,L"""
    XOR_A_N8(R['L'])


def XOR_AE():
    """XOR A,[HL]"""
    pass


def XOR_AF():
    """XOR A,A"""
    XOR_A_N8(R['A'])


def OR_A_N8(value):
    initial = R['A']
    calc = initial | value
    R['A'] = calc
    setFlag(calc == 0, False, False, False)
    debugRegAsHex()


def OR_B0():
    """OR A,B"""
    OR_A_N8(R['B'])


def OR_B1():
    """OR A,C"""
    OR_A_N8(R['C'])


def OR_B2():
    """OR A,D"""
    OR_A_N8(R['D'])


def OR_B3():
    """OR A,E"""
    OR_A_N8(R['E'])


def OR_B4():
    """OR A,H"""
    OR_A_N8(R['H'])


def OR_B5():
    """OR A,L"""
    OR_A_N8(R['L'])


def OR_B6():
    """OR A,[HL]"""
    pass


def OR_B7():
    """OR A,A"""
    OR_A_N8(R['A'])


def CP_A_N8(value):
    initial = R['A']
    calc = initial - value
    final = calc % 256
    setFlag(final == 0, True, getLowerNibble(value)
            > getLowerNibble(initial), calc < 0)
    debugRegAsHex()


def CP_B8():
    """CP A,B"""
    CP_A_N8(R['B'])


def CP_B9():
    """CP A,C"""
    CP_A_N8(R['C'])


def CP_BA():
    """CP A,D"""
    CP_A_N8(R['D'])


def CP_BB():
    """CP A,E"""
    CP_A_N8(R['E'])


def CP_BC():
    """CP A,H"""
    CP_A_N8(R['H'])


def CP_BD():
    """CP A,L"""
    CP_A_N8(R['L'])


def CP_BE():
    """CP A,[HL]"""
    pass


def CP_BF():
    """CP A,A"""
    CP_A_N8(R['A'])


def JP_C2(value):
    """JP NZ,n16"""
    z = getFlags()['Z']
    if z == 0:
        setPC(value)


def JP_C3(value):
    """JP n16"""
    setPC(value)


def ADD_C6(value):
    """ADD A,n8"""
    ADD_A_N8(value)


def JP_CA(value):
    """JP Z,n16"""
    z = getFlags()['Z']
    if z == 1:
        setPC(value)


def RLC_R8(register):
    initial = R[register]
    carryBit = (initial >> 7)
    calc = (initial << 1) & 0b11111110 | carryBit
    R[register] = calc
    setFlag(calc == 0, False, False, carryBit)
    debugRegAsHex()


def RLC_CB00():
    """RLC B"""
    RLC_R8('B')


def RLC_CB01():
    """RLC C"""
    RLC_R8('C')


def RLC_CB02():
    """RLC D"""
    RLC_R8('D')


def RLC_CB03():
    """RLC E"""
    RLC_R8('E')


def RLC_CB04():
    """RLC H"""
    RLC_R8('H')


def RLC_CB05():
    """RLC L"""
    RLC_R8('L')


def RLC_CB06():
    """RLC [HL]"""
    pass


def RLC_CB07():
    """RLC A"""
    RLC_R8('A')


def RRC_R8(register):
    initial = R[register]
    carryBit = (initial & 0b1)
    calc = (carryBit << 7) | initial >> 1
    R[register] = calc
    setFlag(calc == 0, False, False, carryBit)
    debugRegAsHex()


def RRC_08():
    """RRC B"""
    RRC_R8('B')


def RRC_09():
    """RRC C"""
    RRC_R8('C')


def RRC_0A():
    """RRC D"""
    RRC_R8('D')


def RRC_0B():
    """RRC E"""
    RRC_R8('E')


def RRC_0C():
    """RRC H"""
    RRC_R8('H')


def RRC_0D():
    """RRC L"""
    RRC_R8('L')


def RRC_0E():
    """RRC [HL]"""
    pass


def RRC_0F():
    """RRC A"""
    RRC_R8('A')


def RL_R8(register):
    initial = R[register]
    carryBit = (initial >> 7)
    c = getFlags()['C']
    calc = (initial << 1) & 0b11111110 | c
    R[register] = calc
    setFlag(calc == 0, False, False, carryBit)
    debugRegAsHex()


def RL_CB10():
    """RL B"""
    RL_R8('B')


def RL_CB11():
    """RL C"""
    RL_R8('C')


def RL_CB12():
    """RL D"""
    RL_R8('D')


def RL_CB13():
    """RL E"""
    RL_R8('E')


def RL_CB14():
    """RL H"""
    RL_R8('H')


def RL_CB15():
    """RL L"""
    RL_R8('L')


def RL_CB16():
    """RL [HL]"""
    pass


def RL_CB17():
    """RL A"""
    RL_R8('A')


def RR_R8(register):
    initial = R[register]
    carryBit = (initial & 0b1)
    c = getFlags()['C']
    calc = (c << 7) | initial >> 1
    R[register] = calc
    setFlag(calc == 0, False, False, carryBit)
    debugRegAsHex()


def RR_CB18():
    """RR B"""
    RR_R8('B')


def RR_CB19():
    """RR C"""
    RR_R8('C')


def RR_CB1A():
    """RR D"""
    RR_R8('D')


def RR_CB1B():
    """RR E"""
    RR_R8('E')


def RR_CB1C():
    """RR H"""
    RR_R8('H')


def RR_CB1D():
    """RR L"""
    RR_R8('L')


def RR_CB1E():
    """RR [HL]"""
    pass


def RR_CB1F():
    """RR A"""
    RR_R8('A')


def SLA_R8(register):
    initial = R[register]
    carryBit = (initial >> 7)
    calc = (initial << 1) & 0b11111110
    R[register] = calc
    setFlag(calc == 0, False, False, carryBit)
    debugRegAsHex()


def SLA_CB20():
    """SLA B"""
    SLA_R8('B')


def SLA_CB21():
    """SLA C"""
    SLA_R8('C')


def SLA_CB22():
    """SLA D"""
    SLA_R8('D')


def SLA_CB23():
    """SLA E"""
    SLA_R8('E')


def SLA_CB24():
    """SLA H"""
    SLA_R8('H')


def SLA_CB25():
    """SLA L"""
    SLA_R8('L')


def SLA_CB26():
    """SLA [HL]"""
    pass


def SLA_CB27():
    """SLA A"""
    SLA_R8('A')


def SRA_R8(register):
    initial = R[register]
    carryBit = (initial & 0b1)
    calc = (initial >> 7) << 7 | initial >> 1
    R[register] = calc
    setFlag(calc == 0, False, False, carryBit)
    debugRegAsHex()


def SRA_CB28():
    """SRA B"""
    SRA_R8('B')


def SRA_CB29():
    """SRA C"""
    SRA_R8('C')


def SRA_CB2A():
    """SRA D"""
    SRA_R8('D')


def SRA_CB2B():
    """SRA E"""
    SRA_R8('E')


def SRA_CB2C():
    """SRA H"""
    SRA_R8('H')


def SRA_CB2D():
    """SRA L"""
    SRA_R8('L')


def SRA_CB2E():
    """SRA [HL]"""
    pass


def SRA_CB2F():
    """SRA A"""
    SRA_R8('A')


def SWAP_R8(register):
    initial = R[register]
    calc = (initial & 0b1111) << 4 | (initial >> 4)
    print(bin(calc))
    R[register] = calc
    setFlag(calc == 0, False, False, False)
    debugRegAsHex()


def SWAP_CB30():
    """SWAP B"""
    SWAP_R8('B')


def SWAP_CB31():
    """SWAP C"""
    SWAP_R8('C')


def SWAP_CB32():
    """SWAP D"""
    SWAP_R8('D')


def SWAP_CB33():
    """SWAP E"""
    SWAP_R8('E')


def SWAP_CB34():
    """SWAP H"""
    SWAP_R8('H')


def SWAP_CB35():
    """SWAP L"""
    SWAP_R8('L')


def SWAP_CB36():
    """SWAP [HL]"""
    pass


def SWAP_CB37():
    """SWAP A"""
    SWAP_R8('A')


def SRL_R8(register):
    initial = R[register]
    carryBit = (initial & 0b1)
    calc = initial >> 1 & 0b011111111
    R[register] = calc
    setFlag(calc == 0, False, False, carryBit)
    debugRegAsHex()


def SRL_CB38():
    """SRL B"""
    SRL_R8('B')


def SRL_CB39():
    """SRL C"""
    SRL_R8('C')


def SRL_CB3A():
    """SRL D"""
    SRL_R8('D')


def SRL_CB3B():
    """SRL E"""
    SRL_R8('E')


def SRL_CB3C():
    """SRL H"""
    SRL_R8('H')


def SRL_CB3D():
    """SRL L"""
    SRL_R8('L')


def SRL_CB3E():
    """SRL [HL]"""
    pass


def SRL_CB3F():
    """SRL A"""
    SRL_R8('A')


def BIT_U3R8(register, value):
    initial = R[register]
    calc = initial >> (value) & 0b1
    setFlag(calc == 0, False, True, None)
    debugRegAsHex()


def BIT_CB40():
    """BIT 0,B"""
    BIT_U3R8('B', 0)


def BIT_CB41():
    """BIT 0,C"""
    BIT_U3R8('C', 0)


def BIT_CB42():
    """BIT 0,D"""
    BIT_U3R8('D', 0)


def BIT_CB43():
    """BIT 0,E"""
    BIT_U3R8('E', 0)


def BIT_CB44():
    """BIT 0,H"""
    BIT_U3R8('H', 0)


def BIT_CB45():
    """BIT 0,L"""
    BIT_U3R8('L', 0)


def BIT_CB46():
    """BIT 0,[HL]"""
    pass


def BIT_CB47():
    """BIT 0,A"""
    BIT_U3R8('A', 0)


def BIT_CB48():
    """BIT 1,B"""
    BIT_U3R8('B', 1)


def BIT_CB49():
    """BIT 1,C"""
    BIT_U3R8('C', 1)


def BIT_CB4A():
    """BIT 1,D"""
    BIT_U3R8('D', 1)


def BIT_CB4B():
    """BIT 1,E"""
    BIT_U3R8('E', 1)


def BIT_CB4C():
    """BIT 1,H"""
    BIT_U3R8('H', 1)


def BIT_CB4D():
    """BIT 1,L"""
    BIT_U3R8('L', 1)


def BIT_CB4E():
    """BIT 1,[HL]"""
    pass


def BIT_CB4F():
    """BIT 1,A"""
    BIT_U3R8('A', 1)


def BIT_CB50():
    """BIT 2,B"""
    BIT_U3R8('B', 2)


def BIT_CB51():
    """BIT 2,C"""
    BIT_U3R8('C', 2)


def BIT_CB52():
    """BIT 2,D"""
    BIT_U3R8('D', 2)


def BIT_CB53():
    """BIT 2,E"""
    BIT_U3R8('E', 2)


def BIT_CB54():
    """BIT 2,H"""
    BIT_U3R8('H', 2)


def BIT_CB55():
    """BIT 2,L"""
    BIT_U3R8('L', 2)


def BIT_CB56():
    """BIT 2,[HL]"""
    pass


def BIT_CB57():
    """BIT 2,A"""
    BIT_U3R8('A', 2)


def BIT_CB58():
    """BIT 3,B"""
    BIT_U3R8('B', 3)


def BIT_CB59():
    """BIT 3,C"""
    BIT_U3R8('C', 3)


def BIT_CB5A():
    """BIT 3,D"""
    BIT_U3R8('D', 3)


def BIT_CB5B():
    """BIT 3,E"""
    BIT_U3R8('E', 3)


def BIT_CB5C():
    """BIT 3,H"""
    BIT_U3R8('H', 3)


def BIT_CB5D():
    """BIT 3,L"""
    BIT_U3R8('L', 3)


def BIT_CB5E():
    """BIT 3,[HL]"""
    pass


def BIT_CB5F():
    """BIT 3,A"""
    BIT_U3R8('A', 3)


def BIT_CB60():
    """BIT 4,B"""
    BIT_U3R8('B', 4)


def BIT_CB61():
    """BIT 4,C"""
    BIT_U3R8('C', 4)


def BIT_CB62():
    """BIT 4,D"""
    BIT_U3R8('D', 4)


def BIT_CB63():
    """BIT 4,E"""
    BIT_U3R8('E', 4)


def BIT_CB64():
    """BIT 4,H"""
    BIT_U3R8('H', 4)


def BIT_CB65():
    """BIT 4,L"""
    BIT_U3R8('L', 4)


def BIT_CB66():
    """BIT 4,[HL]"""
    pass


def BIT_CB67():
    """BIT 4,B"""
    BIT_U3R8('B', 4)


def BIT_CB68():
    """BIT 5,B"""
    BIT_U3R8('B', 5)


def BIT_CB69():
    """BIT 5,C"""
    BIT_U3R8('C', 5)


def BIT_CB6A():
    """BIT 5,D"""
    BIT_U3R8('D', 5)


def BIT_CB6B():
    """BIT 5,E"""
    BIT_U3R8('E', 5)


def BIT_CB6C():
    """BIT 5,H"""
    BIT_U3R8('H', 5)


def BIT_CB6D():
    """BIT 5,L"""
    BIT_U3R8('L', 5)


def BIT_CB6E():
    """BIT 5,[HL]"""
    pass


def BIT_CB6F():
    """BIT 5,A"""
    BIT_U3R8('A', 5)


def BIT_CB70():
    """BIT 6,B"""
    BIT_U3R8('B', 6)


def BIT_CB71():
    """BIT 6,C"""
    BIT_U3R8('C', 6)


def BIT_CB72():
    """BIT 6,D"""
    BIT_U3R8('D', 6)


def BIT_CB73():
    """BIT 6,E"""
    BIT_U3R8('E', 6)


def BIT_CB74():
    """BIT 6,H"""
    BIT_U3R8('H', 6)


def BIT_CB75():
    """BIT 6,L"""
    BIT_U3R8('L', 6)


def BIT_CB76():
    """BIT 6,[HL]"""
    pass


def BIT_CB77():
    """BIT 6,A"""
    BIT_U3R8('A', 6)


def BIT_CB78():
    """BIT 7,B"""
    BIT_U3R8('B', 7)


def BIT_CB79():
    """BIT 7,C"""
    BIT_U3R8('C', 7)


def BIT_CB7A():
    """BIT 7,D"""
    BIT_U3R8('D', 7)


def BIT_CB7B():
    """BIT 7,E"""
    BIT_U3R8('E', 7)


def BIT_CB7C():
    """BIT 7,H"""
    BIT_U3R8('H', 7)


def BIT_CB7D():
    """BIT 7,L"""
    BIT_U3R8('L', 7)


def BIT_CB7E():
    """BIT 7,[HL]"""
    pass


def BIT_CB7F():
    """BIT 7,A"""
    BIT_U3R8('A', 7)


def RES_U3R8(register, value):
    initial = R[register]
    higher = initial >> value + 1 << value + 1
    lower = ((initial << 8 - value) & 0xFF) >> 8-value
    calc = higher | lower
    R[register] = calc
    debugRegAsHex()


def RES_CB80():
    """RES 0,B"""
    RES_U3R8('B', 0)


def RES_CB81():
    """RES 0,C"""
    RES_U3R8('C', 0)


def RES_CB82():
    """RES 0,D"""
    RES_U3R8('D', 0)


def RES_CB83():
    """RES 0,E"""
    RES_U3R8('E', 0)


def RES_CB84():
    """RES 0,H"""
    RES_U3R8('H', 0)


def RES_CB85():
    """RES 0,L"""
    RES_U3R8('L', 0)


def RES_CB86():
    """RES 0,[HL]"""
    pass


def RES_CB87():
    """RES 0,A"""
    RES_U3R8('A', 0)


def RES_CB88():
    """RES 1,B"""
    RES_U3R8('B', 1)


def RES_CB89():
    """RES 1,C"""
    RES_U3R8('C', 1)


def RES_CB8A():
    """RES 1,D"""
    RES_U3R8('D', 1)


def RES_CB8B():
    """RES 1,E"""
    RES_U3R8('E', 1)


def RES_CB8C():
    """RES 1,H"""
    RES_U3R8('H', 1)


def RES_CB8D():
    """RES 1,L"""
    RES_U3R8('L', 1)


def RES_CB8E():
    """RES 1,[HL]"""
    pass


def RES_CB8F():
    """RES 1,A"""
    RES_U3R8('A', 1)


def RES_CB90():
    """RES 2,B"""
    RES_U3R8('B', 2)


def RES_CB91():
    """RES 2,C"""
    RES_U3R8('C', 2)


def RES_CB92():
    """RES 2,D"""
    RES_U3R8('D', 2)


def RES_CB93():
    """RES 2,E"""
    RES_U3R8('E', 2)


def RES_CB94():
    """RES 2,H"""
    RES_U3R8('H', 2)


def RES_CB95():
    """RES 2,L"""
    RES_U3R8('L', 2)


def RES_CB96():
    """RES 2,[HL]"""
    pass


def RES_CB97():
    """RES 2,A"""
    RES_U3R8('A', 2)


def RES_CB98():
    """RES 3,B"""
    RES_U3R8('B', 3)


def RES_CB99():
    """RES 3,C"""
    RES_U3R8('C', 3)


def RES_CB9A():
    """RES 3,D"""
    RES_U3R8('D', 3)


def RES_CB9B():
    """RES 3,E"""
    RES_U3R8('E', 3)


def RES_CB9C():
    """RES 3,H"""
    RES_U3R8('H', 3)


def RES_CB9D():
    """RES 3,L"""
    RES_U3R8('L', 3)


def RES_CB9E():
    """RES 3,[HL]"""
    pass


def RES_CB9F():
    """RES 3,A"""
    RES_U3R8('A', 3)


def RES_CBA0():
    """RES 4,B"""
    RES_U3R8('B', 4)


def RES_CBA1():
    """RES 4,C"""
    RES_U3R8('C', 4)


def RES_CBA2():
    """RES 4,D"""
    RES_U3R8('D', 4)


def RES_CBA3():
    """RES 4,E"""
    RES_U3R8('E', 4)


def RES_CBA4():
    """RES 4,H"""
    RES_U3R8('H', 4)


def RES_CBA5():
    """RES 4,L"""
    RES_U3R8('L', 4)


def RES_CBA6():
    """RES 4,[HL]"""
    pass


def RES_CBA7():
    """RES 4,B"""
    RES_U3R8('B', 4)


def RES_CBA8():
    """RES 5,B"""
    RES_U3R8('B', 5)


def RES_CBA9():
    """RES 5,C"""
    RES_U3R8('C', 5)


def RES_CBAA():
    """RES 5,D"""
    RES_U3R8('D', 5)


def RES_CBAB():
    """RES 5,E"""
    RES_U3R8('E', 5)


def RES_CBAC():
    """RES 5,H"""
    RES_U3R8('H', 5)


def RES_CBAD():
    """RES 5,L"""
    RES_U3R8('L', 5)


def RES_CBAE():
    """RES 5,[HL]"""
    pass


def RES_CBAF():
    """RES 5,A"""
    RES_U3R8('A', 5)


def RES_CBB0():
    """RES 6,B"""
    RES_U3R8('B', 6)


def RES_CBB1():
    """RES 6,C"""
    RES_U3R8('C', 6)


def RES_CBB2():
    """RES 6,D"""
    RES_U3R8('D', 6)


def RES_CBB3():
    """RES 6,E"""
    RES_U3R8('E', 6)


def RES_CBB4():
    """RES 6,H"""
    RES_U3R8('H', 6)


def RES_CBB5():
    """RES 6,L"""
    RES_U3R8('L', 6)


def RES_CBB6():
    """RES 6,[HL]"""
    pass


def RES_CBB7():
    """RES 6,A"""
    RES_U3R8('A', 6)


def RES_CBB8():
    """RES 7,B"""
    RES_U3R8('B', 7)


def RES_CBB9():
    """RES 7,C"""
    RES_U3R8('C', 7)


def RES_CBBA():
    """RES 7,D"""
    RES_U3R8('D', 7)


def RES_CBBB():
    """RES 7,E"""
    RES_U3R8('E', 7)


def RES_CBBC():
    """RES 7,H"""
    RES_U3R8('H', 7)


def RES_CBBD():
    """RES 7,L"""
    RES_U3R8('L', 7)


def RES_CBBE():
    """RES 7,[HL]"""
    pass


def RES_CBBF():
    """RES 7,A"""
    RES_U3R8('A', 7)


def SET_U3R8(register, value):
    initial = R[register]
    higher = ((initial >> value) | 1) << value
    lower = ((initial << 8 - value) & 0xFF) >> 8-value
    calc = higher | lower
    R[register] = calc
    debugRegAsHex()


def SET_CBC0():
    """SET 0,B"""
    SET_U3R8('B', 0)


def SET_CBC1():
    """SET 0,C"""
    SET_U3R8('C', 0)


def SET_CBC2():
    """SET 0,D"""
    SET_U3R8('D', 0)


def SET_CBC3():
    """SET 0,E"""
    SET_U3R8('E', 0)


def SET_CBC4():
    """SET 0,H"""
    SET_U3R8('H', 0)


def SET_CBC5():
    """SET 0,L"""
    SET_U3R8('L', 0)


def SET_CBC6():
    """SET 0,[HL]"""
    pass


def SET_CBC7():
    """SET 0,A"""
    SET_U3R8('A', 0)


def SET_CBC8():
    """SET 1,B"""
    SET_U3R8('B', 1)


def SET_CBC9():
    """SET 1,C"""
    SET_U3R8('C', 1)


def SET_CBCA():
    """SET 1,D"""
    SET_U3R8('D', 1)


def SET_CBCB():
    """SET 1,E"""
    SET_U3R8('E', 1)


def SET_CBCC():
    """SET 1,H"""
    SET_U3R8('H', 1)


def SET_CBCD():
    """SET 1,L"""
    SET_U3R8('L', 1)


def SET_CBCE():
    """SET 1,[HL]"""
    pass


def SET_CBCF():
    """SET 1,A"""
    SET_U3R8('A', 1)


def SET_CBD0():
    """SET 2,B"""
    SET_U3R8('B', 2)


def SET_CBD1():
    """SET 2,C"""
    SET_U3R8('C', 2)


def SET_CBD2():
    """SET 2,D"""
    SET_U3R8('D', 2)


def SET_CBD3():
    """SET 2,E"""
    SET_U3R8('E', 2)


def SET_CBD4():
    """SET 2,H"""
    SET_U3R8('H', 2)


def SET_CBD5():
    """SET 2,L"""
    SET_U3R8('L', 2)


def SET_CBD6():
    """SET 2,[HL]"""
    pass


def SET_CBD7():
    """SET 2,A"""
    SET_U3R8('A', 2)


def SET_CBD8():
    """SET 3,B"""
    SET_U3R8('B', 3)


def SET_CBD9():
    """SET 3,C"""
    SET_U3R8('C', 3)


def SET_CBDA():
    """SET 3,D"""
    SET_U3R8('D', 3)


def SET_CBDB():
    """SET 3,E"""
    SET_U3R8('E', 3)


def SET_CBDC():
    """SET 3,H"""
    SET_U3R8('H', 3)


def SET_CBDD():
    """SET 3,L"""
    SET_U3R8('L', 3)


def SET_CBDE():
    """SET 3,[HL]"""
    pass


def SET_CBDF():
    """SET 3,A"""
    SET_U3R8('A', 3)


def SET_CBE0():
    """SET 4,B"""
    SET_U3R8('B', 4)


def SET_CBE1():
    """SET 4,C"""
    SET_U3R8('C', 4)


def SET_CBE2():
    """SET 4,D"""
    SET_U3R8('D', 4)


def SET_CBE3():
    """SET 4,E"""
    SET_U3R8('E', 4)


def SET_CBE4():
    """SET 4,H"""
    SET_U3R8('H', 4)


def SET_CBE5():
    """SET 4,L"""
    SET_U3R8('L', 4)


def SET_CBE6():
    """SET 4,[HL]"""
    pass


def SET_CBE7():
    """SET 4,B"""
    SET_U3R8('B', 4)


def SET_CBE8():
    """SET 5,B"""
    SET_U3R8('B', 5)


def SET_CBE9():
    """SET 5,C"""
    SET_U3R8('C', 5)


def SET_CBEA():
    """SET 5,D"""
    SET_U3R8('D', 5)


def SET_CBEB():
    """SET 5,E"""
    SET_U3R8('E', 5)


def SET_CBEC():
    """SET 5,H"""
    SET_U3R8('H', 5)


def SET_CBED():
    """SET 5,L"""
    SET_U3R8('L', 5)


def SET_CBEE():
    """SET 5,[HL]"""
    pass


def SET_CBEF():
    """SET 5,A"""
    SET_U3R8('A', 5)


def SET_CBF0():
    """SET 6,B"""
    SET_U3R8('B', 6)


def SET_CBF1():
    """SET 6,C"""
    SET_U3R8('C', 6)


def SET_CBF2():
    """SET 6,D"""
    SET_U3R8('D', 6)


def SET_CBF3():
    """SET 6,E"""
    SET_U3R8('E', 6)


def SET_CBF4():
    """SET 6,H"""
    SET_U3R8('H', 6)


def SET_CBF5():
    """SET 6,L"""
    SET_U3R8('L', 6)


def SET_CBF6():
    """SET 6,[HL]"""
    pass


def SET_CBF7():
    """SET 6,A"""
    SET_U3R8('A', 6)


def SET_CBF8():
    """SET 7,B"""
    SET_U3R8('B', 7)


def SET_CBF9():
    """SET 7,C"""
    SET_U3R8('C', 7)


def SET_CBFA():
    """SET 7,D"""
    SET_U3R8('D', 7)


def SET_CBFB():
    """SET 7,E"""
    SET_U3R8('E', 7)


def SET_CBFC():
    """SET 7,H"""
    SET_U3R8('H', 7)


def SET_CBFD():
    """SET 7,L"""
    SET_U3R8('L', 7)


def SET_CBFE():
    """SET 7,[HL]"""
    pass


def SET_CBFF():
    """SET 7,A"""
    SET_U3R8('A', 7)


def ADC_CE(value):
    """ADC A,n8"""
    ADC_A_N8(value)


def JP_D2(value):
    """JP NC,n16"""
    c = getFlags()['C']
    if c == 0:
        setPC(value)


def SUB_D6(value):
    """SUB A,n8"""
    SUB_A_N8(value)


def JP_DA(value):
    """JP C,n16"""
    c = getFlags()['C']
    if c == 1:
        setPC(value)


def SBC_DE(value):
    """SBC A,n8"""
    SBC_A_N8(value)


def AND_E6(value):
    """AND A,n8"""
    AND_A_N8(value)


def JP_E9():
    """JP HL"""
    setPC(getHL())


def XOR_EE(value):
    """XOR A,n8"""
    XOR_A_N8(value)


def OR_F6(value):
    """OR A,n8"""
    OR_A_N8(value)


def CP_FE(value):
    """CP A,n8"""
    CP_A_N8(value)

# endregion


# region CPU Logic

def opcode_output(PC, opcode):
    ops = []
    for operand in opcode['operands']:
        if 'bytes' in operand:
            ops.append(int_to_hex(int.from_bytes(
                bytes(CARTRIDGE[PC+1:PC+1+int(operand['bytes'])])[::-1])))
            continue
    return ops


def int_to_hex(value):
    return '0x' + hex(value)[2:].zfill(2).upper()


while PC < len(CARTRIDGE):
    if PC >= 0x104 and PC < 0x150:
        # TODO CARTRIDGE HEADER
        incPC(1)
        continue

    data = int_to_hex(CARTRIDGE[PC])
    if (data == 0xCB):
        data = int_to_hex(CARTRIDGE[PC + 1])
        opcode = opcodes['cbprefixed'][data]
        incPC(opcode['bytes'] + 1)
        continue
    opcode = opcodes['unprefixed'][data]
    incPC(opcode['bytes'])

    
    


# clear_display()
# TILE_TEST = "FF 00 7E FF 85 81 89 83 93 85 A5 8B C9 97 7E FF 3C 7E 42 42 42 42 42 42 7E 5E 7E 0A 7C 56 38 7C"
# byte_data = hexstring_to_bytearray(TILE_TEST)
# for c in range(len(byte_data)):
#     if c % 16 != 0:
#         continue
#     tile = get_tile(byte_data[c:c+16])
#     draw_tile((c // 16, 0), tile)
# update_display()

# while True:
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             pygame.quit()
#             sys.exit()
#         # if event.type == pygame.KEYDOWN:
#         #     if event.scancode in keycodes.keys():
#         #         KEYS[keycodes[event.scancode]] = 1
#         # if event.type == pygame.KEYUP:
#         #     if event.scancode in keycodes.keys():
#         #         KEYS[keycodes[event.scancode]] = 0

# endregion