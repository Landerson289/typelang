from functools import partial

def handle_brackets(expression, operations):
    depth = 0

    operation_symbols = []
    for operation in operations:
        operation_symbols.append(operation.symbol)

    new_expression = []
    enclosed = []
    tokens_before_open = []

    previous_token = None

    for token in expression:
        if token == "(":
            depth += 1 
            tokens_before_open.append(previous_token)
        elif token == ")":
            #if tokens_before_open.pop() in operation_symbols:
                depth -= 1
                if depth == 0:
                    new_expression.append(parse_expression(enclosed, operations))
                if depth < 0:
                    throw("Too many )")
            #else:
                
        else:
            if depth == 0:
                new_expression.append(token)
            elif depth > 0:
                enclosed.append(token)
            else:
                throw("Too many )")
        previous_token = token
    if depth > 0:
        throw("Too many (")
    return new_expression

def parse_expression(expression:list, operations:list):
    if len(expression) == 1:
        return expression[0]
    
    expression = handle_brackets(expression, operations)

    #print(expression)

    for operation in operations:
        if operation.symbol not in expression:
            continue

        operation_index = len(expression)-1
        while operation_index > 0:
            if expression[operation_index] == operation.symbol:
                break
            operation_index -= 1
        if operation.left and operation.right:
            lhs = parse_expression(expression[:operation_index], operations)
            rhs = parse_expression(expression[operation_index+1:], operations)
            rpn_tree = [lhs, rhs, operation]
        elif operation.right:
            rhs = parse_expression(expression[operation_index+1:], operations)
            rpn_tree = [rhs, operation]
        elif operation.left:
            lhs = parse_expression(expression[:operation_index], operations)
            rpn_tree = [lhs, operation]
        else:
            throw("Operator takes no input?")
    return rpn_tree

def evaluate_tree(tree):
    if type(tree) == str:
        return objects[tree]
    operator = tree[-1]
    if type(tree[0]) == list:
        tree[0] = evaluate_tree(tree[0])
    elif type(tree[0]) == str:
        tree[0] = objects[tree[0]]
    elif type(tree[0]) != Bin:
        throw("Weird type on line 62")

    if operator.right and operator.left:
        if type(tree[1]) == list:
            tree[1] = evaluate_tree(tree[1])
        elif type(tree[1]) == str:
            tree[1] = objects[tree[1]]
        elif type(tree[1]) != Bin:
            throw("Weird type on line 69")
        
        if operator.symbol != "<-": # Temporary
            value = tree[0].operations_from_left[operator.symbol](tree[1].value)
        else:
            value = tree[0].operations_from_left[operator.symbol](tree[1])
        if type(value) == str:
            return Bin(value)
        else:
            return value # Temporary
    elif operator.right or operator.left:
        value = tree[0].unitary_operations[operator.symbol]()
        if type(value):
            return Bin(value)
        else:
            return value # Temporary
    else:
        throw("Weird operator")
    
def evaluate(expression):
    operations = [Operator("!", 5, left = False), Operator(".", 4), Operator("+", 3), Operator(",", 2), Operator("<-", 1), Operator("=", 0)] # Highest to lowest precedence

    rpn_tree = parse_expression(expression, operations)

    #print(rpn_tree)

    value = evaluate_tree(rpn_tree)

    return value

class Operator:
    def __init__(self, symbol, precedence, left=True, right=True):
        """
        Docstring for __init__
        
        :param self: represents the instance of the class
        :param symbol: the symbol used to represent the operator, eg +-*/
        :param left: Does this operator take inputs from the left (False for ! x)
        :param right: Does this operator take inputs from the right
        """ 
        self.symbol = symbol
        self.precedence = precedence
        self.left = left
        self.right = right

class Type:
    def __init__(self, values):
        if type(values) == list:
            self.value = "" # Concatinate any bitstrings seperated by spaces
            for value in values:
                self.value += value
        elif type(values) == str:
            self.value = values
        else:
            throw("weird type of values passed into type")

        #self.operations_from_left = {
        #    "," : lambda r : self.serialise(self.value, r)
        #}
        
        self.operations_from_left = {
            "," : lambda r : (self.value, r)
        }

class Bin(Type):
    type = "Bin"
    def __init__(self, values):
        super().__init__(values)
    
        #self.operations_from_left = {
        self.operations_from_left["+"] = partial(self.bitwise_or, self.value) # Bitwise or
        self.operations_from_left["."] = partial(self.bitwise_and, self.value) # Bitwise and
        self.operations_from_left["="] = lambda r : "1" if self.value == r else "0"
        #}

        self.unitary_operations = {
            "!" : partial(self.bitwise_not, self.value)
        }
    
    def bitwise_or(self, l, r):
        result = ""

        for i in range(max(len(l), len(r))):
            #if i < len(l)-len(r)
            if l[i] != r[i]:
                result += "1"
            elif l[i] == "1":
                result += "1"
            else:
                result += "0"
        
        return result
    
    def bitwise_and(self, l, r):
        result = ""

        for i in range(max(len(l), len(r))):
            #if i < len(l)-len(r)
            if l[i] == "1" and r[i] == "1":
                result += "1"
            else:
                result += "0"

        return result
    
    def bitwise_not(self, l):
        result = ""

        for i in range(len(l)):
            if l[i] == "0":
                result += "1"
            else:
                result += "0"
        return result

class Tuple(Type):
    type = "Tuple"
    def __init__(self, values):
        pass

class Function(Type):
    type = "Func"
    def __init__(self, values):
        self.reference = int(values[-1][2:-2])
        self.parameters = []
        i = 0
        while i < len(values)-1:
            self.parameters.append(values[i])
            i += 2
        self.value = values

        self.operations_from_left = {
            "<-" : self.call,
        }
    
    def call(self, arguments):
        #print(self.parameters)
        for i in range(len(self.parameters)):
            #TODO Add check for collision with existing name
            objects[self.parameters[i]] = Bin(arguments[i])
        interpret(sub_routines[self.reference], sub_routines)

        self.value = objects["return"].value

        for i in range(len(self.parameters)):
            del objects[self.parameters[i]]
        
        return self.value
        

def throw(string):
    print(string)
    quit()

types = {
    "Bin" : Bin,
    "Func" : Function,
    "Tuple" : Tuple
}

objects = { # Variables + Constants
    
}

sub_routines = [

]

f = open("typelang/main.lang")
data = f.read()
f.close()

def tokenise(data):
    if type(data) == str:
        lines = data.splitlines()
    else:
        lines = data
    
    new_lines = []
    for line in lines:
        new_lines.append(line.split(" "))
    
    lines = new_lines

    index = 0
    while index < len(lines):

        if lines[index] == [""]:
            lines.pop(index)
            continue

        while lines[index][0] == "":
            lines[index] = lines[index][1:]
        
        if lines[index][0][0] == "#":
            lines.pop(index)
            continue
        index += 1
    
    subroutines = []

    start_indeces = []
    depth = 0

    index = 0
    while index < len(lines):
        if lines[index][0] == "}":
            start_index = start_indeces.pop()
            sub_routine = lines[start_index+1:index]
            sub_routines.append(sub_routine)

            critical_line = lines[start_index][:-1] + ["{{" + str(len(sub_routines)-1) + "}}"] + lines[index][1:]

            lines = lines[:start_index] + [critical_line] + lines[index+1:]
            index -= len(sub_routine) + 1

        if lines[index][-1] == "{":
            start_indeces.append(index)
            depth += 1
        index += 1
    return lines, sub_routines
    

def interpret(lines, sub_routines):
    for line in lines:
        #words = line.split(" ") # Improve tokenisation
        words = line

        if words[0] == "if":
            conditions = [[]]
            sub_routine_references = []
            i = 1
            while i < len(words):
                while words[i][0:2] != "{{":
                    conditions[-1].append(words[i])
                    i += 1
                conditions.append([])
                sub_routine_references.append(int(words[i][2:-2]))
                i += 1
                if i >= len(words):
                    break
                if words[i] not in ["elif", "else"]:
                    throw("elif or else must come after if")
                i += 1
            conditions.pop()
            for i in range(len(conditions)):
                condition = conditions[i]
                if condition == []: # Else
                    subroutine = sub_routines[sub_routine_references[-1]]
                    break

                truth = evaluate(condition).value

                if "1" in truth:
                    subroutine = sub_routines[sub_routine_references[i]]
                    break
            interpret(subroutine, sub_routines)
        elif words[0] == "while":
            expression = words[1:-1]
            subroutine = sub_routines[int(words[-1][2:-2])]
            while "1" in evaluate(expression).value:
                interpret(subroutine, sub_routines)

        elif words[1] == "=":
            if words[2][0] == "$":
                # Declaration of new object
                object_name = words[0]
                object_type_name = words[2][1:]
                object_value = words[3:]
                
                if object_type_name in types.keys():
                    object_type = types[object_type_name]
                    #print(object_value)
                    objects[object_name] = object_type(object_value)
                else:
                    throw("type is not defined")
                    quit()
            else:
                # Assigning result of a calculation to a variable
                object_name = words[0]
                expression = words[2:]
                object = evaluate(expression)
                objects[object_name] = object
            print(object_name, objects[object_name].value)

lines, sub_routines = tokenise(data)
interpret(lines, sub_routines)
