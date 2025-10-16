import shlex

import parsegument as pg


parser = pg.Parsegumenter()
group = pg.CommandGroup("test")
parser.add_child(group)

@group.command
def check_type(foo: str, bar: str, test: int=1, test2: float=2.0, flag:bool=False):
    print(f"foo: {foo}\nbar: {bar}\ntest: {test}\ntest2: {test2}\nflag: {flag}\n")

testcases = [
    'test check_type yes something',
    'test check_type idkbruh yes --test=4',
    'test check_type something yes --test2=3.9',
    'test check_type fr idk bruh -flag',
    'test check_type "this is crazy" "double quotes!!!" --test=3 -flag'
]


for cases in testcases:
    parser.execute(cases)