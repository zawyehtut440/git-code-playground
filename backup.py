OPTAB = dict()
ASSEMBLER_DIRECTIVE = ["START", "END", "WORD", "BYTE", "RESW", "RESB"]
SYMTAB, UNDEFINED_SYMTAB = dict(), dict()
H_RECORD, T_RECORD, E_RECORD = ["H"], [], ["E"]
ERROR_MESSAGES = []


def main():
    load_optab()
    if one_pass("SIC.asm"):
        # write record
        write_record("result.obj")
    else:
        # print error messages
        print_error_messages()

def write_record(file_name):
    fout = open(file_name, "w")
    # Head Record
    fout.write('^'.join(H_RECORD)+'\n')
    # Text Record
    for t_record in T_RECORD:
        fout.write('^'.join(t_record)+'\n')
    # End Record
    fout.write('^'.join(E_RECORD)+'\n')
    fout.close()

def print_error_messages():
    ERROR_MESSAGES.sort()
    for err_message in ERROR_MESSAGES:
        print(err_message[1])

def one_pass(file_name):
    try:
        fin = open(file_name, "r")
        read_lines = fin.readlines()
        fin.close()
    except FileNotFoundError:
        ERROR_MESSAGES.append([0, f"找不到檔案: {file_name}"])
        return False
    total_lines, line_no = len(read_lines), 0
    # find first instruction
    line_no = find_first_instruction(read_lines, line_no)
    if total_lines == 0 or line_no == total_lines:
        ERROR_MESSAGES([line_no, "程式必須\"START\"開始"])
        return False
    first_isntruction = read_lines[line_no].rstrip() # 找到第一行指令
    # check first instruction correct or not
    success = entry_point_checker(first_isntruction, line_no+1)
    if success: # 第一行指令沒有錯誤
        # 初始化t_record, locctr
        t_record, locctr = ["T"], H_RECORD[2]
    else:
        return False
    line_no += 1 # 讀下一行指令
    label, mnemonic, operand = '', '', ''
    while mnemonic != "END":
        if line_no == total_lines: # 讀到最後一行, 還沒有END指令
            break
        line = read_lines[line_no].rstrip()
        if not is_empty_line(line) and not is_comment(line):
            # 如果可以分成label, mnemonic, operand
            tokens = tokenize(line)
            if tokens_checker(tokens): # 合法token數
                label, mnemonic, operand = tokens_alloc(tokens)
                if mnemonic == "END":
                    if success and t_record != ["T"]:
                        t_record = cal_objcode_len_initial_t_record(t_record)
                    break
                if not instruction_checker(label, mnemonic, operand, locctr, line_no+1): # 指令不合法
                    success = False
                    line_no += 1
                    # 如果label在SYMTAB中, 把label重UNDEFINED_SYMTAB中移除
                    if label in UNDEFINED_SYMTAB:
                        UNDEFINED_SYMTAB.pop(label)
                    continue
                # 到這裡目前都成功
                if label:
                    # 前面組譯成功, 且label在undefined_symtab中
                    if success and label in UNDEFINED_SYMTAB:
                        if t_record != ["T"]:
                            t_record = cal_objcode_len_initial_t_record(t_record)
                        # write t_record
                        write_undefined_symbol_to_t_record(label)
                    elif label in UNDEFINED_SYMTAB:
                        UNDEFINED_SYMTAB.pop(label)
                # RESW or RESB
                if mnemonic == "RESW" or mnemonic == "RESB":
                    if success and t_record != ["T"]: # 有t_record
                        t_record = cal_objcode_len_initial_t_record(t_record)
                else: # mnemonic為OPCODE, WORD, BYTE
                    if success: # 如果成功
                        if t_record == ["T"]: # t_record目前沒內容
                            # 加入locctr
                            t_record.append(format_hex(locctr, 6))
                        # 產生object code
                        object_code = gen_object_code(mnemonic, operand)
                        # 寫入t_record中
                        t_record = write_objcode_to_t_record(t_record, mnemonic, locctr, object_code)
                locctr = update_locctr(locctr, mnemonic, operand)
            else:
                ERROR_MESSAGES.append([line_no+1, f"第{line_no+1}行: 無法將指令分成label, mnemonic, operand"])
                success = False
        line_no += 1 # 讀下一行
    # 檢查最後一個指令END
    if not exit_point_checker(label, mnemonic, operand, line_no+1):
        success = False
    # END指令之後不能有指令
    line_no += 1
    if mnemonic == "END" and not check_after_END_instruction(read_lines, line_no):
        success = False
    if UNDEFINED_SYMTAB: # 有未定義的symbol
        success = False
        undefined_symbol_error()
    if success:
        # 算出程式記憶體容量
        # 加入到H_RECORD中
        H_RECORD.append(format_hex(hex_subtract(locctr, SYMTAB[H_RECORD[1].strip()]), 6))
        E_RECORD.append(format_hex(SYMTAB[operand], 6))
    return success

def exit_point_checker(label, mnemonic, operand, line_no):
    check = True
    if mnemonic != "END":
        ERROR_MESSAGES.append([line_no, "程式結束必須要有指令\"END\"結尾"])
        check = False
    else:
        if label:
            ERROR_MESSAGES.append([line_no, f"第{line_no}行: \"END\"指令不用有label"])
            check = False
        if not self_define_variable_checker(operand):
            ERROR_MESSAGES.append([line_no, f"第{line_no}行: \"END\"指令的operand: {operand}不符合規定"])
            check = False
        elif operand not in SYMTAB:
            ERROR_MESSAGES.append([line_no, f"第{line_no}行: \"END\"指令的operand: {operand}沒有定義"])
            check = False
    return check

def check_after_END_instruction(read_lines, line_no):
    no_instruction = True
    for i in range(line_no, len(read_lines)):
        if not is_empty_line(read_lines[i]) and not is_comment(read_lines[i]):
            no_instruction = False
            ERROR_MESSAGES.append([i+1, f"第{i+1}行: 錯誤, END指令之後不能有instruction"])
    return no_instruction

def hex_subtract(hex_num1, hex_num2):
    num1 = hex_to_decimal(hex_num1)
    num2 = hex_to_decimal(hex_num2)
    return decimal_to_hex(num1 - num2)

def undefined_symbol_error():
    for symbol in UNDEFINED_SYMTAB:
        # example of symbol: [[4, 1004, False], [5, 1007, True]], [line_no, address, indexed_addressing]
        symbol_infos = UNDEFINED_SYMTAB[symbol]
        for symbol_info in symbol_infos:
            ERROR_MESSAGES.append([symbol_info[0], f"第{symbol_info[0]}行: operand的symbol: {symbol}未被定義"])

def write_undefined_symbol_to_t_record(symbol):
    symbol_infos = UNDEFINED_SYMTAB.pop(symbol)
    for symbol_info in symbol_infos:
        # symbol_info[0]: symbol出現的行號
        # symbol_info[1]: symbol出現在operand的記憶體位址
        # symbol_info[2]: 是否為索引定址
        t_record = ["T", format_hex(symbol_info[1], 6), "02"]
        if symbol_info[2]: # 索引定址
            t_record.append(format_hex(hex_add(SYMTAB[symbol], hex_to_decimal("8000")), 4))
        else: # 直接定址
            t_record.append(format_hex(SYMTAB[symbol], 4))
        T_RECORD.append(t_record)

def cal_objcode_len_initial_t_record(t_record):
    t_record_obj_len = cal_t_record_objcode_len(t_record)
    t_record.insert(2, format_hex(decimal_to_hex(t_record_obj_len//2), 2))
    T_RECORD.append(t_record)
    return ["T"]

def cal_t_record_objcode_len(t_record):
    t_record_objcode = t_record[2:]
    total = 0
    for objcode in t_record_objcode:
        total += len(objcode)
    return total

def write_objcode_to_t_record(t_record, mnemonic, locctr, object_code):
    t_record_objcode_len = cal_t_record_objcode_len(t_record) # 未換算成以byte
    if mnemonic in OPTAB:
        # 如果t_record的object code長度加上要新增的object code長度 > 60
        if t_record_objcode_len + len(object_code) > 60:
            # 算出目前t_record的object code的總長度(單位: byte), 加到t_record的第2個位置
            t_record.insert(2, format_hex(decimal_to_hex(t_record_objcode_len//2), 2))
            # 把t_record加到T_RECORD
            T_RECORD.append(t_record)
            # 初始化新的t_record為["T", locctr, 要新增的object_code]
            t_record = ["T", format_hex(locctr, 6), object_code]
        # 否則
        else:
            # 直接把要新增的object code加入t_record
            t_record.append(object_code)
    else: # WORD or BYTE
        current_locctr = locctr
        while object_code:
            if t_record_objcode_len + len(object_code) > 60:
                d = 60 - t_record_objcode_len
                t_record.append(object_code[:d])
                t_record.insert(2, "1E")
                T_RECORD.append(t_record)
                current_locctr = hex_add(current_locctr, d//2)
                t_record = ["T", format_hex(current_locctr, 6)]
                t_record_objcode_len, object_code = 0, object_code[d:]
            elif t_record_objcode_len + len(object_code) < 60:
                # 直接加object_code
                t_record.append(object_code)
                object_code = ""
            else: # t_record_objcode_len + len(object_code) == 60
                t_record.append(object_code)
                t_record.insert(2, "1E")
                T_RECORD.append(t_record)
                t_record = ["T"]
                object_code = ""
    return t_record

def gen_object_code(mnemonic, operand):
    object_code = ""
    if mnemonic in OPTAB:
        object_code += OPTAB[mnemonic]
        # symbol = operand[:-2] if operand.endswith(',X') else operand
        if operand.endswith(',X'):
            symbol, indexed_addressing = operand[:-2], True
        else:
            symbol, indexed_addressing = operand, False
        if indexed_addressing and symbol in SYMTAB: # indexed addressing
            object_code += hex_add(SYMTAB[symbol], hex_to_decimal("8000"))
        elif symbol in SYMTAB: # direct addressing
            object_code += SYMTAB[symbol]
        else: # symbol in undefined_symtab
            object_code += "0000"
    elif mnemonic == "WORD":
        object_code = format_hex(decimal_to_hex(operand), 6)
    else: # mnemoinc是BYTE
        content = operand[2:-1]
        if operand[0] == 'C':
            object_code = to_ascii(content)
        else: # operand[0] == 'X'
            object_code = content
    return object_code

def update_locctr(locctr, mnemonic, operand):
    new_locctr = locctr
    if mnemonic in OPTAB:
        new_locctr = hex_add(locctr, 3)
    elif mnemonic == "WORD":
        new_locctr = hex_add(locctr, 3)
    elif mnemonic == "RESW":
        new_locctr = hex_add(locctr, 3 * int(operand))
    elif mnemonic == "RESB":
        new_locctr = hex_add(locctr, int(operand))
    else: # mnemonic == BYTE
        content = operand[2:-1]
        if operand[0] == 'C':
            new_locctr = hex_add(locctr, len(content))
        else: # operand[0] == 'X'
            new_locctr = hex_add(locctr, len(content)//2)
    return new_locctr

def instruction_label_checker(label, locctr, line_no):
    check = True
    if label: # 有label
        if not self_define_variable_checker(label):
            ERROR_MESSAGES.append([line_no, f"第{line_no}行: label: {label}, label只能為英文或數字且為英文字母開頭"])
            check = False
        elif label in OPTAB or label in ASSEMBLER_DIRECTIVE:
            ERROR_MESSAGES.append([line_no, f"第{line_no}行: label: {label}, label不能跟指令同名"])
            check = False
        elif label in SYMTAB:
            ERROR_MESSAGES.append([line_no, f"第{line_no}行: label: {label}, label重複定義, {label}已經定義過了"])
            check = False
        else: # label沒問題
            insert_SYMTAB(label, locctr)
    return check

def instruction_mnemonic_operand_checker(label, mnemonic, operand, locctr, line_no):
    check = True
    if mnemonic == "RSUB":
        if operand:
            ERROR_MESSAGES.append([line_no, f"第{line_no}行: operand: {operand}, RSUB指令不能有operand"])
            check = False
    elif mnemonic in OPTAB or mnemonic in ASSEMBLER_DIRECTIVE: # 其他的OPCODE指令, assembler directive
        # 剩下的指令要有operand
        if not operand:
            ERROR_MESSAGES.append([line_no, f"第{line_no}行: 指令{mnemonic}要有operand"])
            check = False
        elif mnemonic in OPTAB: # OPCODE指令, 除了RSUB
            symbol = operand[:-2] if operand.endswith(',X') else operand
            # operand不可以跟指令的名字一樣
            if symbol in OPTAB or symbol in ASSEMBLER_DIRECTIVE:
                ERROR_MESSAGES.append([line_no, f"第{line_no}行: operand的symbol: {symbol}, operand的symbol命名不可以跟指令一樣"])
                check = False
            elif not self_define_variable_checker(symbol): # operand自定義命名不合法
                ERROR_MESSAGES.append([line_no, f"第{line_no}行: operand的symbol: {symbol}, operand的symbol不符合規定"])
                check = False
            elif symbol == label:
                ERROR_MESSAGES.append([line_no, f"第{line_no}行: label: {label}, operand的symbol: {symbol}, operand不能跟label一樣"])
                check = False
            else: # operand合法
                if symbol not in SYMTAB: # 如果operand的symbol不在SYMTAB
                    insert_UNDEFINED_SYMTAB(operand, hex_add(locctr, 1), line_no)
        elif mnemonic == "START":
            ERROR_MESSAGES.append([line_no, f"第{line_no}行: mnemonic: {mnemonic}, \"START\"指令只能為程式一開始的指令"])
            check = False
        elif mnemonic != "END":
            # WORD, BYTE, RESW, RESB要有label
            if not label:
                ERROR_MESSAGES.append([line_no, f"第{line_no}行: 指令{mnemonic}的label不能為空"])
                check = False
            if mnemonic == "BYTE":
                start, content, end = operand[:2], operand[2:-1], operand[-1]
                if start != "C'" and start != "X'" or end != "'": # BYTE指令怎樣算格是錯誤
                    ERROR_MESSAGES.append([line_no, f"第{line_no}行: 指令BYTE的operand: {operand}格式錯誤"])
                    check = False
                elif content == "":
                    ERROR_MESSAGES.append([line_no, f"第{line_no}行: 指令BYTE的operand: {operand}單引號內不能為空"])
                    check = False
                else:
                    if start[0] == 'X' and not is_hex(content):
                        ERROR_MESSAGES.append([line_no, f"第{line_no}行: 指令BYTE的operand: {operand}錯誤, X字串內容只能是16進位"])
                        check = False
                    if start[0] == 'X' and len(content) % 2 != 0:
                        ERROR_MESSAGES.append([line_no, f"第{line_no}行: 指令BYTE的operand: {operand}錯誤, X字串內容只能是偶數個數"])
                        check = False
            else: # WORD, RESW, RESB
                if not is_decimal(operand):
                    ERROR_MESSAGES.append([line_no, f"第{line_no}行: 指令{mnemonic}的operand: {operand}錯誤, {mnemonic}的operand只能是10進位數字"])
                    check = False
                elif mnemonic == "WORD" and int(operand) > 16777216:
                    ERROR_MESSAGES.append([line_no, f"第{line_no}行: 指令WORD的宣告不能超過3個bytes"])
                    check = False
                elif mnemonic == "RESW" and 3 * int(operand) > 32768:
                    ERROR_MESSAGES.append([line_no, f"第{line_no}行: 指令RESW的宣告不能超過最大記憶體範圍(2^15)"])
                    check = False
                elif mnemonic == "RESB" and int(operand) > 32768:
                    ERROR_MESSAGES.append([line_no, f"第{line_no}行: 指令RESB的宣告不能超過最大記憶體範圍(2^15)"])
                    check = False
    else:
        ERROR_MESSAGES.append([line_no, f"第{line_no}行: mnemonic: {mnemonic}錯誤, 找不到指令{mnemonic}"])
        check = False
    return check

def instruction_checker(label, mnemonic, operand, locctr, line_no):
    check = True
    # 如果有label, 看合不合法, 合法的話, 把label加入SYMTAB
    if not instruction_label_checker(label, locctr, line_no): # label不合法
        check = False
    # 看mnemonic跟operand的部分, mnemonic跟operand一起看
    if not instruction_mnemonic_operand_checker(label, mnemonic, operand, locctr, line_no):
        check = False
    return check

def find_first_instruction(read_lines, line_no):
    current_line_no = line_no
    if read_lines:
        while is_empty_line(read_lines[current_line_no]) or is_comment(read_lines[current_line_no]):
            current_line_no += 1
            if current_line_no == len(read_lines):
                break
    return current_line_no

def start_checker(label, mnemonic, operand, line_no):
    check = True
    if mnemonic != "START":
        ERROR_MESSAGES.append([line_no, f"第{line_no}行: 程式第一行mnemonic必須\"START\"指令開始"])
        check = False
    else: # mnemoinc == START
        if not label: # 沒有label
            ERROR_MESSAGES.append([line_no, f"第{line_no}行: \"START\"指令的label不能為空"])
            check = False
        elif not self_define_variable_checker(label):
            ERROR_MESSAGES.append([line_no, f"第{line_no}行: label: {label}, label只能是英文或數字且英文開頭"])
            check = False
        elif len(label) > 6:
            ERROR_MESSAGES.append([line_no, f"第{line_no}行: label: {label}, label不可以超過6個字元"])
            check = False
        # operand
        if not is_hex(operand):
            ERROR_MESSAGES.append([line_no, f"第{line_no}行: operand: {operand}, \"START\"指令的operand只能是16進位"])
            check = False
        elif hex_to_decimal(operand) > 32767:
            ERROR_MESSAGES.append([line_no, f"第{line_no}行: operand: {operand}, \"START\"指令的operand超過記憶體可以存取的位址"])
            check = False
    return check

def entry_point_checker(first_instruction, line_no):
    check = True
    tokens = tokenize(first_instruction)
    if tokens_checker(tokens):
        label, mnemonic, operand = tokens_alloc(tokens)
        if start_checker(label, mnemonic, operand, line_no):
            insert_SYMTAB(label, operand)
            H_RECORD.append(format_label(label))
            H_RECORD.append(format_hex(operand, 6))
        else:
            check = False
    else:
        ERROR_MESSAGES.append([line_no, f"第{line_no}行: {first_instruction}, 程式第一行指令欄位數不對"])
        check = False
    return check

def self_define_variable_checker(variable_name):
    if variable_name[0].isdigit():
        return False
    for i in range(1, len(variable_name)):
        if not variable_name[i].isdigit() and not variable_name[i].isalpha():
            return False
    return True

def tokens_checker(tokens):
    return len(tokens) < 4 and len(tokens) > 0

def tokens_alloc(tokens):
    if len(tokens) == 1:
        return '', tokens[0], ''
    elif len(tokens) == 3:
        return tokens[0], tokens[1], tokens[2]
    else: # len(tokens) == 2
        if tokens[1] in OPTAB or tokens[1] in ASSEMBLER_DIRECTIVE:
            return tokens[0], tokens[1], ''
        else:
            return '', tokens[0], tokens[1]

def tokenize(instruction):
    tokens, token = [], ''
    inside_single_quote = False
    for c in instruction:
        if c == '.':
            break
        if c == "'":
            inside_single_quote = not inside_single_quote
        if not inside_single_quote and (c == ' ' or c == '\t'):
            if token:
                tokens.append(token)
                token = ''
            continue
        elif not inside_single_quote and c == ',':
            if token:
                tokens.append(token)
                token = ''
            tokens.append(',')
        else:
            token += c
    if token:
        tokens.append(token)
    return final_tokens(tokens)

def final_tokens(tokens):
    final_result = []
    for token in tokens:
        if len(final_result) > 0 and (token == ',' or final_result[-1][-1] == ','):
            final_result.append(final_result.pop()+token)
        elif token[0] == "'":
            if len(final_result) > 0 and (final_result[-1] not in OPTAB or final_result[-1] not in ASSEMBLER_DIRECTIVE):
                final_result.append(final_result.pop()+token)
            else:
                final_result.append(token)
        else:
            final_result.append(token)
    return final_result

def is_empty_line(line):
    return line.strip() == ''

def is_comment(line):
    return line.split()[0][0] == '.'

def is_hex(hex_num):
    hex_digit = ["A", "B", "C", "D", "E", "F"]
    for d in hex_num:
        c = d.upper()
        if not c.isdigit() and not c in hex_digit:
            return False
    return True

def is_decimal(decimal_num):
    for d in decimal_num:
        if not d.isdigit():
            return False
    return True

def hex_to_decimal(hex_num):
    hex_digit = {"A": 10, "B": 11, "C": 12, "D": 13, "E": 14, "F": 15}
    total = 0
    n = len(hex_num) - 1
    for d in hex_num:
        c = d.upper()
        if c.isdigit():
            total += int(c) * 16**n
        else:
            total += hex_digit[c] * 16**n
        n -= 1
    return total

def decimal_to_hex(decimal_num):
    return hex(int(decimal_num))[2:].upper()

def hex_add(hex_num, decimal_num):
    return decimal_to_hex(hex_to_decimal(hex_num) + decimal_num)

def to_ascii(string):
    result = ''
    for c in string:
        ascii_code = decimal_to_hex(ord(c))
        if len(ascii_code) == 1:
            result += f'0{ascii_code}'
        else:
            result += ascii_code
    return result

def format_label(label):
    n = 6 - len(label)
    return label + ' ' * n

def format_hex(hex_num, digit):
    n = digit - len(hex_num)
    return '0' * n + hex_num

def load_optab():
    with open("opCode.txt", "r") as file:
        for line in file:
            mnemonic, opcode = line.rstrip().split()
            OPTAB[mnemonic] = opcode
    return True

def insert_SYMTAB(symbol, locctr):
    SYMTAB[symbol] = locctr

def insert_UNDEFINED_SYMTAB(operand, locctr, line_no):
    if operand.endswith(',X'):
        symbol, indexed_addressing = operand[:-2], True
    else:
        symbol, indexed_addressing = operand, False
    if symbol not in UNDEFINED_SYMTAB:
        UNDEFINED_SYMTAB[symbol] = [[line_no, locctr, indexed_addressing]]
    else:
        UNDEFINED_SYMTAB[symbol].append([line_no, locctr, indexed_addressing])

if __name__ == "__main__":
    main()