import re


def re2format(pattern, string):
    r = re.fullmatch(pattern, string)
    fm = []
    args = []
    cursor = 0
    for begin, end in r.regs[1:]:
        fm.append(string[cursor:begin])
        args.append(string[begin:end])
        cursor = end
    fm.append(string[cursor:])
    return '%s'.join(fm), tuple(args), fm


def re2args(pattern, string):
    r = re.fullmatch(pattern, string)
    args = []
    for begin, end in r.regs[1:]:
        args.append(string[begin:end])
    return args


if __name__ == '__main__':
    print(re2format(r'aa-([\d]+)-bb-([\d]+)', 'aa-1-bb-1'))
    print(re2args(r'aa-([\d]+)-bb-([\d]+)', 'aa-1-bb-1'))
