from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/transceiver-qsfp-default-mode.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_transceiver_qsfp_default_mode_4x10 = resolve('transceiver_qsfp_default_mode_4x10')
    try:
        t_1 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_1((undefined(name='transceiver_qsfp_default_mode_4x10') if l_0_transceiver_qsfp_default_mode_4x10 is missing else l_0_transceiver_qsfp_default_mode_4x10), True):
        pass
        yield '!\ntransceiver qsfp default-mode 4x10G\n'

blocks = {}
debug_info = '7=18'