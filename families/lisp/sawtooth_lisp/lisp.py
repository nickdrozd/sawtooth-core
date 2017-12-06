import hashlib
import json
import operator
import logging


LOGGER = logging.getLogger(__name__)


LISP_NAMESPACE = hashlib.sha512('lisp'.encode('utf-8')).hexdigest()[:6]


def txn_decode(data):
    loaded = json.loads(data.decode())

    return (
        loaded['name'],
        loaded['cmd'],
        loaded['expr'],
    )


def state_decode(data):
    return json.loads(data.decode())


def state_encode(data):
    return json.dumps(data).encode()


def lisp_commands(*txn_and_state_data):
    cmd, expr, data = txn_and_state_data

    if cmd == 'step':
        return lisp_eval(data)

    elif cmd == 'declare':
        return initialize(expr)


PRIMITIVES = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.floordiv,
    '=': operator.eq,
    '<': operator.lt,
    '>': operator.gt,
}


def lisp_eval(data):
    expr = data['expr']
    env = data['env']
    instr = data['instr']
    cont = data['cont']
    val = data['val']
    evlist = data['evlist']
    unev = data['unev']
    stack = data['stack']

    if instr == 'EVAL':
        if is_num(expr):
            val = expr
            instr = cont

        elif isinstance(expr, str):
            val = lookup(expr, env)
            instr = cont

        else:
            keyword, *_ = expr

            if keyword == 'quote':
                _, val = expr
                instr = cont

            elif keyword == 'lambda' or keyword == 'λ':
                _, params, body = expr
                val = ['lambda', params, body, env]
                instr = cont

            elif keyword == 'if':
                stack = [expr, env, cont] + stack
                _, expr, _, _ = expr
                cont = 'IF-DECIDE'
                instr = 'EVAL'

            else:
                expr, *unev = expr
                stack = [unev, env, cont] + stack
                cont = 'DID-FUNC'
                instr = 'EVAL'

    elif instr == 'IF-DECIDE':
        expr, env, cont, *stack = stack
        _, _, consequent, alternative = expr
        expr = consequent if val else alternative
        instr = 'EVAL'

    elif instr == 'DID-FUNC':
        evlist = [val]
        unev, env, *stack = stack
        instr = 'ARG-LOOP' if unev else 'APPLY'

    elif instr == 'ARG-LOOP':
        stack = [evlist] + stack
        expr, *unev, = unev
        if unev:
            stack = [unev, env] + stack
            cont = 'ACC-ARG'
        else:
            cont = 'LAST-ARG'
        instr = 'EVAL'

    elif instr == 'ACC-ARG':
        unev, env, evlist, *stack = stack
        evlist += [val]
        instr = 'ARG-LOOP'

    elif instr == 'LAST-ARG':
        evlist, *stack = stack
        evlist += [val]
        instr = 'APPLY'

    elif instr == 'APPLY':
        cont, *stack = stack
        func, *args = evlist

        try:
            func = PRIMITIVES[func]
            arg1, arg2 = args
            val = func(arg1, arg2)
            instr = cont
        except (KeyError, TypeError):
            _, params, body, env = func
            env = [dict(zip(params, args))] + env
            expr = body
            instr = 'EVAL'

    result = {
        'expr': expr,
        'env': env,
        'instr': instr,
        'cont': cont,
        'val': val,
        'evlist': evlist,
        'unev': unev,
        'stack': stack,
    }

    LOGGER.info('Lisp step result: %s', result)

    return result


def is_num(expr):
    try:
        int(expr)
        return True
    except (TypeError, ValueError):
        return False


def lookup(var, env):
    if var in PRIMITIVES:
        return var
    else:
        for frame in env:
            try:
                return frame[var]
            except KeyError:
                pass

    raise Exception('Unbound variable: {}'.format(var))


def initialize(expr):
    return {
        'expr': expr,
        'env': [],
        'instr': 'EVAL',
        'cont': 'DONE',
        'val': '',
        'evlist': '',
        'unev': '',
        'stack': []
    }
