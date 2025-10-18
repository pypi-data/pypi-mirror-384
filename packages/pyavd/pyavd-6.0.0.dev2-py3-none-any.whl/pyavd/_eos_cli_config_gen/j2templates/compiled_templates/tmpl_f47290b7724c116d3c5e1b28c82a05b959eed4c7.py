from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/enable-password.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_enable_password = resolve('enable_password')
    l_0_hide_passwords = resolve('hide_passwords')
    try:
        t_1 = environment.filters['arista.avd.hide_passwords']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.hide_passwords' found.")
    try:
        t_2 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_2((undefined(name='enable_password') if l_0_enable_password is missing else l_0_enable_password)):
        pass
        if t_2(environment.getattr((undefined(name='enable_password') if l_0_enable_password is missing else l_0_enable_password), 'disabled'), True):
            pass
            yield '!\nno enable password\n'
        elif t_2(environment.getattr((undefined(name='enable_password') if l_0_enable_password is missing else l_0_enable_password), 'key')):
            pass
            yield '!\n'
            if t_2(environment.getattr((undefined(name='enable_password') if l_0_enable_password is missing else l_0_enable_password), 'hash_algorithm'), 'md5'):
                pass
                yield 'enable password 5 '
                yield str(t_1(environment.getattr((undefined(name='enable_password') if l_0_enable_password is missing else l_0_enable_password), 'key'), (undefined(name='hide_passwords') if l_0_hide_passwords is missing else l_0_hide_passwords)))
                yield '\n'
            elif t_2(environment.getattr((undefined(name='enable_password') if l_0_enable_password is missing else l_0_enable_password), 'hash_algorithm'), 'sha512'):
                pass
                yield 'enable password sha512 '
                yield str(t_1(environment.getattr((undefined(name='enable_password') if l_0_enable_password is missing else l_0_enable_password), 'key'), (undefined(name='hide_passwords') if l_0_hide_passwords is missing else l_0_hide_passwords)))
                yield '\n'

blocks = {}
debug_info = '7=25&8=27&11=30&13=33&14=36&15=38&16=41'