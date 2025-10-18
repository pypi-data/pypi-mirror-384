# utilities - convert RegEx

"""
Module provides a converter from Microsoft VB / COM regular expression to Python regular expressions
to overcome differences in the standard syntax. Basic Eval() functionality is supported as well
(i.e. basic formatting of found groups/elements).

The use case was a flexible file renaming tool including some boolean logic. It was used f. e. to
assign a report created at the beginning of the following month as report of the previous month.
Basically, all renaming logic is hidden in regular expressions.


Example / doctest (note escaping in output to avoid error):
```
>>> from utils_mystuff import convertRegExVB2Python

>>> # test - conversion
>>> print(convertRegExVB2Python('"$1_Report_" & $5+($2>$4)*1 & "_" & Format($2, "00") & "_$5$4$3$6"'))
"\\1_Report_" + str(\\5+(\\2>\\4)*-1) + "_" + "{:02d}".format(\\2) + "_\\5\\4\\3\\6"
>>> print(convertRegExVB2Python('"$1_Report_" & $2+($3+($4<28)=0) & Format($3+($4<28)-12*($3+($4<28)=0), "00") & "_Korr.pdf"'))
"\\1_Report_" + str(\\2+(\\3+(\\4<28)*-1==0)*-1) + "{:02d}".format(\\3+(\\4<28)*-1-12*(\\3+(\\4<28)*-1==0)*-1) + "_Korr.pdf"
>>> print(convertRegExVB2Python("$1_$2"))
\\1_\\2
>>> print(convertRegExVB2Python('"$1_Report_" & $5+($2>$4)*1 & "_" & Format($2, "00") & "_$5$4$3$6"'))
"\\1_Report_" + str(\\5+(\\2>\\4)*-1) + "_" + "{:02d}".format(\\2) + "_\\5\\4\\3\\6"
>>> print(convertRegExVB2Python('"$1_Report_" & $5+($2>$4)*1 + "_" + Format($2, "00") & "_$5$4$3$6"'))
"\\1_Report_" + str(\\5+(\\2>\\4)*-1) + "_" + "{:02d}".format(\\2) + "_\\5\\4\\3\\6"
>>> print(convertRegExVB2Python('"$1$2_Report_" & $3+($4+($5<28)=0) & Format($4+($5<28)-12*($4+($5<28)=0), "00") & "$6"'))
"\\1\\2_Report_" + str(\\3+(\\4+(\\5<28)*-1==0)*-1) + "{:02d}".format(\\4+(\\5<28)*-1-12*(\\4+(\\5<28)*-1==0)*-1) + "\\6"

>>> # test - clean leading zero")
>>> print(clean_for_eval('"(-1*1*0) + "_" + "{:02d}".format(08) + "_20210901.pdf"'))
"(-1*1*0) + "_" + "{:02d}".format(8) + "_20210901.pdf"
>>> print(clean_for_eval('"123456_Report_" + str(2021+(08>09)*-01*1*0) + "_" + "{:02d}".format(08) + "_20210901.pdf"'))
"123456_Report_" + str(2021+(8>9)*-1*1*0) + "_" + "{:02d}".format(8) + "_20210901.pdf"
>>> print(clean_for_eval('"123456_Report_" + str(2022+(4+(02<28)*-1==0)*-1) + "{:02d}".format(04+(02<28)*-1-12*(04+(02<28)*-1==0)*-1) + ".pdf"'))
"123456_Report_" + str(2022+(4+(2<28)*-1==0)*-1) + "{:02d}".format(4+(2<28)*-1-12*(4+(2<28)*-1==0)*-1) + ".pdf"

```
"""


# ruff and mypy per file settings
#
# empty lines
# ruff: noqa: E302, E303
# naming conventions
# ruff: noqa: N801, N802, N803, N806, N812, N813, N815, N816, N818, N999
# boolean-type arguments
# ruff: noqa: FBT001, FBT002, Q003
# others
# ruff: noqa: E501

# fmt: off



# convert Microsoft VB / COM regular expression to Python regular expression
def convertRegExVB2Python(reVB: str) -> str:
    """
    convertRegExVB2Python - convert Microsoft VB / COM regular expression to Python regular expression

    Problem: syntax for regular expressions in the Microsoft VB / COM standard is different from Python.

    Differences in the area of the standard syntax:

    - for group replacements notation is \\n instead $n

    Differences if regular expressions are used together with Eval():

    - different numerical value for True: VB environment = -1, Python = 1
      -> boolean expressions need to be adjusted
    - string concatenation is '&' in VB and '+' in Python
      assumption: '+' is not used for source expressions even allowed
    - '+' may not be applied on int/str in Python
      -> numerical expressions must be bracketed in str()
    - language functions are to be replaced. Implemented:
      "Format" for numerical values

    Arguments:
        reVB (str): regular expression according to VB / COM standard for Microsoft RegEx engine

    Returns:
        str: converted regular expression for Python RegEx engine
    """

    def split_terms(regex: str, quotemark, delim: str = "&+") -> list[str]:

        terms: list[str] = []
        regex_idx: int = 0
        term_start: int = 0
        quotemark_cnt: int = 0
        bracket_cnt: int = 0

        regex += " "
        while regex_idx < len(regex):
            if regex[regex_idx] == quotemark:
                quotemark_cnt += 1
            elif regex[regex_idx] in "(){}[]":
                bracket_cnt += 1
            elif (
                (regex[regex_idx] in delim or regex_idx >= len(regex) - 1) and
                quotemark_cnt % 2 == 0 and
                bracket_cnt % 2 == 0
            ):
                term = regex[term_start:regex_idx].strip()
                if (term[-1] in quotemark) or (terms[-1][-1] in quotemark) or (term.lower().find("format(") >= 0):
                    terms.append(term)
                else:
                    terms[-1] = terms[-1] + "+" + term
                term_start = regex_idx + 1
            regex_idx += 1

        return terms

    def convert_other(term: str, embedstr: bool = True) -> str:

        compare_operator = [">", "<", "="]
        foundbool = False

        term_idx = 0
        while term_idx < len(term):
            if term[term_idx] in compare_operator:
                if term[term_idx:term_idx + 1] == "<>":
                    term = term[:term_idx] + "!=" + term[term_idx + 2:]
                if term[term_idx:term_idx + 1] == "=":
                    term = term[:term_idx] + "==" + term[term_idx + 1:]
                    term_idx += 1
                while term[term_idx] != ")" and term_idx < len(term):
                    term_idx += 1
                if term[term_idx] == ")":
                    term = term[0:term_idx] + ")*-1" + term[term_idx + 1:]
                    term_idx += 3
                    foundbool = True
                elif term_idx == len(term):
                    term = "(" + term + ")*-1"
                    foundbool = True
            term_idx += 1

        if foundbool:
            term = term.replace("*-1*1", "*-1").replace("*-1*-1", "*1")

        if embedstr:
            return "str(" + term + ")"
        else:
            return term

    def convert_term(term: str, quotemark) -> str:

        if term[0] == quotemark:
            return term
        elif term.lower()[0:len("format(")] == "format(":
            # only simple integer formatting accepted
            params = term[len("format") + 1:len(term) - 1].split(",")
            params[0] = convert_other(params[0], False)
            return f"\"{{:0{params[1].count('0')}d}}\".format({params[0]})"
        else:
            return convert_other(term)

    # check quotation mark -> RegEx for use with Eval()
    if reVB[0] == "'":
        quotemark = "'"
    elif reVB[0] == "\"":
        quotemark = "\""
    else:
        quotemark = ""

    if quotemark != "":
        # top-level split of  regular expression into string terms
        terms = split_terms(reVB, quotemark)
        rePy = ""
        for term in terms:
            rePy = convert_term(term, quotemark) if rePy == "" else rePy + " + " + convert_term(term, quotemark)
    else:
        rePy = reVB

    # replace groups
    for grp_idx in range(9, 0, -1):
        rePy = rePy.replace(f"${grp_idx}", rf"\{grp_idx}")

    return rePy

def convert_regexVB2python(reVB: str) -> str:
    """
    convert_regexVB2python - convert Microsoft VB / COM regular expression to Python regular expression

    Alternative caller for convertRegExVB2Python. See details there.

    Arguments:
        reVB (str): regular expression according to VB / COM standard for Microsoft RegEx engine

    Returns:
        str: converted regular expression for Python RegEx engine
    """

    return convertRegExVB2Python(reVB)

def convert_regexVB_2_python(reVB: str) -> str:
    """
    convert_regexVB_2_python - convert Microsoft VB / COM regular expression to Python regular expression

    Alternative caller for convertRegExVB2Python. See details there.

    Arguments:
        reVB (str): regular expression according to VB / COM standard for Microsoft RegEx engine

    Returns:
        str: converted regular expression for Python RegEx engine
    """

    return convertRegExVB2Python(reVB)


# clean expression after substitution
def clean_for_eval(expression: str) -> str:
    """
    clean_for_eval - clean regular expression after substitution

    delete leading zeros from integer constants to overcome eval() error

    Arguments:
        expression (str): regular expression to be cleaned

    Returns:
        str: cleaned regular expression
    """

    operator_char = [" ", "<", "=", ">", "+", "-", "*", "/", "%", "("]

    find_start = 0
    for char in operator_char:
        pos = expression.find(f"{char}0")
        while pos >= 0:
            if expression[pos + 2:pos + 3] in "0123456789":
                expression = expression[0:pos + 1] + expression[pos + 2:]
                find_start = pos
            else:
                find_start = pos + 1
            pos = expression.find(f"{char}0", find_start)

    return expression
