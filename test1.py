# def tokenize(operation):
#     # initialize token to '' and initialize tokens list to []
#     token, tokens = '', []
#     inside_single_quote = False
#     # for each character c in operation
#     for c in operation:
#         if c == '.' and not inside_single_quote: # comment
#             break
#         if c == "'":
#             inside_single_quote = not inside_single_quote
#             if token and inside_single_quote:
#                 tokens.append(token)
#                 token = ''
#         # if there is a token and c is ' ' or '\t'
#         if token and not inside_single_quote and (c == ' ' or c == '\t'):
#             # add this token to tokens list
#             tokens.append(token)
#             # clear token to ''
#             token = ''
#         elif not inside_single_quote and (c == ' ' or c == '\t'):
#             continue
#         elif token and c == ',' and not inside_single_quote:
#             tokens.append(token)
#             tokens.append(',')
#             token = ''
#         elif c == ',' and not inside_single_quote:
#             tokens.append(',')
#         # else if c is not ' ' and '\t'
#         # elif c != ' ' and c != '\t' and not inside_single_quote:
#         #     # add c to token
#         #     token += c
#         else:
#             token += c
#     if token:
#         tokens.append(token)
#     return tokenizer(tokens)

# def tokenizer(tokens):
#     # stack
#     stack = []
#     if len(tokens) > 0:
#         stack.append(tokens.pop(0))
#     # stack = [tokens.pop(0)]
#     while len(tokens) != 0:
#         token = tokens.pop(0)
#         if token == ',':
#             op = stack.pop()
#             next_token = ''
#             while len(tokens) > 0 and tokens[0] == ',':
#                 next_token += tokens.pop(0)
#             if len(tokens) > 0:
#                 next_token += tokens.pop(0)
#             stack.append(op+','+next_token)
#         elif token[0] == "'":
#             op = stack.pop()
#             if op == 'C' or op == 'X':
#                 stack.append(op+token)
#             else:
#                 stack.append(op)
#                 stack.append(token)
#         else:
#             stack.append(token)
#     return stack
OPTAB = {}
ASSEMBLER_DIRECTIVE = ["START", "END", "WORD", "BYTE", "RESW", "RESB"]
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

def new_tokenize(operation):
    token, tokens = '', []
    inside_single_quote = False
    # concat_next is for determining whether should concat next char or not
    concat_next = False
    for c in operation:
        if c == '.' and not inside_single_quote: # comment
            break
        if concat_next and c != ' ':
            if token:
                token += c
            else:
                token = tokens.pop()+c
            if c == "'":
                inside_single_quote = not inside_single_quote
            concat_next = c == ',' and not inside_single_quote
            continue
        elif c == "'" and token: # "'" and there is token
            inside_single_quote = not inside_single_quote
            token += "'"
        elif c == "'" and len(tokens) > 0: # token is '' and c is "'" and tokens is not empty list
            inside_single_quote = not inside_single_quote
            # check last element in tokens
            op = tokens.pop()
            # if last element in tokens is key word 'C' or 'X'
            if op == 'C' or op == 'X':
                # set token to op+"'"
                token = op + "'"
            # otherwise last element in tokens is not key word for character
            else:
                # push last element back to tokens stack
                tokens.append(op)
                # set token to "'"(token is originally '')
                token = "'"
        elif c == ',' and not inside_single_quote and token: # ',' and there is token
            token += ','
            concat_next = True
        elif c == ',' and not inside_single_quote and len(tokens) > 0: # ',' and there is no token
            op = tokens.pop()
            tokens.append(op+',')
            concat_next = True
        elif token and (c == ' ' or c == '\t') and not inside_single_quote: # space and there is token
            tokens.append(token)
            token = ''
        elif (c == ' ' or c == '\t') and not inside_single_quote: # only space and there is no token
            continue
        else:
            token += c
    if token:
        tokens.append(token)
    return tokens

def load_optab():
    with open("opCode.txt", "r") as file:
        for line in file:
            key, value = line.rstrip().split()
            OPTAB[key] = value

def self_define_variable_checker(variable_name):
    if variable_name[0].isdigit():
        return False
    for i in range(1, len(variable_name)):
        if not variable_name[i].isdigit() and not variable_name[i].isalpha():
            return False
    return True

def decimal_to_hex(decimal_num):
    return hex(int(decimal_num))[2:].upper()

def to_ascii(string):
    result = ''
    for c in string:
        ascii_code = decimal_to_hex(ord(c))
        if len(ascii_code) == 1:
            result += f'0{ascii_code}'
        else:
            result += str(ascii_code)
    return result

def tokenizer(instruction):
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
            if token in OPTAB or token in ASSEMBLER_DIRECTIVE or final_result[-1] in OPTAB or final_result[-1] in ASSEMBLER_DIRECTIVE:
                final_result.append(token)
            else:
                final_result.append(final_result.pop()+token)
        elif token[0] == "'":
            if len(final_result) > 0 and (final_result[-1] not in OPTAB or final_result[-1] not in ASSEMBLER_DIRECTIVE):
                final_result.append(final_result.pop()+token)
            else:
                final_result.append(token)
        else:
            final_result.append(token)
    return final_result

def main():
    load_optab()
    # print(tokenize("EOF BYTE C 'EOF''"))
    # print(tokenize("EOF BYTE C 'EOF''eof   '"))
    # print(tokenizer('LDCH BUFFER ,X'))
    # print(tokenizer('LDCH BUFFER, X'))
    # print(tokenizer('LDCH BUFFER , X'))
    # print(tokenizer("EOF BYTE C'EO  F'"))
    # print(tokenizer("EOF BYTE C    'EO  F'"))
    # print(tokenizer("EOF BYTE XD     'EO  F'"))
    # print(tokenizer("EOF BYTE D'EO  F'"))
    # print(tokenizer("EOF BYTE D     'EO  F'"))
    # print(tokenizer("LDA LDA LDA"))
    # print(new_tokenize("LDCH WORD BUFFER,'EOF'"))
    # print(new_tokenize("LDCH WORD BUFFER ,'EOF'"))
    # print(new_tokenize("LDCH WORD BUFFER , 'EO  ,, ,  F'"))
    # print(new_tokenize("EOF BYTE C 'EOF''eof   '"))
    with open("SIC.asm", "r") as file:
        for line in file:
            print(tokenizer(line.rstrip()))


if __name__ == "__main__":
    main()