from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/cfm.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_cfm = resolve('cfm')
    try:
        t_1 = environment.filters['arista.avd.natural_sort']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.natural_sort' found.")
    try:
        t_2 = environment.filters['join']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'join' found.")
    try:
        t_3 = environment.filters['sort']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No filter named 'sort' found.")
    try:
        t_4 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_4((undefined(name='cfm') if l_0_cfm is missing else l_0_cfm)):
        pass
        yield '!\ncfm\n'
        if t_4(environment.getattr(environment.getattr((undefined(name='cfm') if l_0_cfm is missing else l_0_cfm), 'measurement_loss'), 'inband'), True):
            pass
            yield '   measurement loss inband\n'
        if t_4(environment.getattr(environment.getattr((undefined(name='cfm') if l_0_cfm is missing else l_0_cfm), 'measurement_loss'), 'synthetic'), True):
            pass
            yield '   measurement loss synthetic\n'
        if t_4(environment.getattr((undefined(name='cfm') if l_0_cfm is missing else l_0_cfm), 'continuity_check_loc_state_action_disable_interface_routing'), True):
            pass
            yield '   continuity-check loc-state action disable interface routing\n'
        for l_1_profile in t_1(environment.getattr((undefined(name='cfm') if l_0_cfm is missing else l_0_cfm), 'profiles'), 'name'):
            l_1_alarm_indication_cli = resolve('alarm_indication_cli')
            l_1_tx_interval_cli = resolve('tx_interval_cli')
            _loop_vars = {}
            pass
            yield '   !\n   profile '
            yield str(environment.getattr(l_1_profile, 'name'))
            yield '\n'
            if t_4(environment.getattr(environment.getattr(l_1_profile, 'continuity_check'), 'enabled'), True):
                pass
                yield '      continuity-check\n'
            if t_4(environment.getattr(environment.getattr(l_1_profile, 'continuity_check'), 'tx_interval')):
                pass
                yield '      continuity-check tx-interval '
                yield str(environment.getattr(environment.getattr(l_1_profile, 'continuity_check'), 'tx_interval'))
                yield '\n'
            if t_4(environment.getattr(environment.getattr(l_1_profile, 'continuity_check'), 'qos_cos')):
                pass
                yield '      continuity-check qos cos '
                yield str(environment.getattr(environment.getattr(l_1_profile, 'continuity_check'), 'qos_cos'))
                yield '\n'
            if t_4(environment.getattr(environment.getattr(l_1_profile, 'continuity_check'), 'alarm_defects')):
                pass
                yield '      continuity-check alarm defect '
                yield str(t_2(context.eval_ctx, t_3(environment, environment.getattr(environment.getattr(l_1_profile, 'continuity_check'), 'alarm_defects'), reverse=True), ' '))
                yield '\n'
            if t_4(environment.getattr(environment.getattr(l_1_profile, 'alarm_indication'), 'enabled'), True):
                pass
                yield '      alarm indication\n'
            if t_4(environment.getattr(environment.getattr(l_1_profile, 'alarm_indication'), 'client_domain_level')):
                pass
                l_1_alarm_indication_cli = str_join(('alarm indication client domain level ', environment.getattr(environment.getattr(l_1_profile, 'alarm_indication'), 'client_domain_level'), ))
                _loop_vars['alarm_indication_cli'] = l_1_alarm_indication_cli
                if t_4(environment.getattr(environment.getattr(l_1_profile, 'alarm_indication'), 'tx_interval')):
                    pass
                    l_1_alarm_indication_cli = str_join(((undefined(name='alarm_indication_cli') if l_1_alarm_indication_cli is missing else l_1_alarm_indication_cli), ' tx-interval ', environment.getattr(environment.getattr(l_1_profile, 'alarm_indication'), 'tx_interval'), ))
                    _loop_vars['alarm_indication_cli'] = l_1_alarm_indication_cli
                yield '      '
                yield str((undefined(name='alarm_indication_cli') if l_1_alarm_indication_cli is missing else l_1_alarm_indication_cli))
                yield '\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'delay'), 'single_ended'), True):
                pass
                yield '      measurement delay single-ended\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'delay'), 'tx_interval')):
                pass
                yield '      measurement delay tx-interval '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'delay'), 'tx_interval'))
                yield ' milliseconds\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'delay'), 'qos_cos')):
                pass
                yield '      measurement delay qos cos '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'delay'), 'qos_cos'))
                yield '\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'single_ended'), True):
                pass
                yield '      measurement loss single-ended\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'tx_interval')):
                pass
                yield '      measurement loss tx-interval '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'tx_interval'))
                yield ' milliseconds\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'qos_cos')):
                pass
                yield '      measurement loss qos cos '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'qos_cos'))
                yield '\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'synthetic'), 'single_ended'), True):
                pass
                yield '      measurement loss synthetic single-ended\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'synthetic'), 'tx_interval'), 'interval')):
                pass
                l_1_tx_interval_cli = str_join(('measurement loss synthetic tx-interval ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'synthetic'), 'tx_interval'), 'interval'), ' milliseconds', ))
                _loop_vars['tx_interval_cli'] = l_1_tx_interval_cli
                if t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'synthetic'), 'tx_interval'), 'period_frames')):
                    pass
                    l_1_tx_interval_cli = str_join(((undefined(name='tx_interval_cli') if l_1_tx_interval_cli is missing else l_1_tx_interval_cli), ' period ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'synthetic'), 'tx_interval'), 'period_frames'), ' frames', ))
                    _loop_vars['tx_interval_cli'] = l_1_tx_interval_cli
                yield '      '
                yield str((undefined(name='tx_interval_cli') if l_1_tx_interval_cli is missing else l_1_tx_interval_cli))
                yield '\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'synthetic'), 'qos_cos')):
                pass
                yield '      measurement loss synthetic qos cos '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'synthetic'), 'qos_cos'))
                yield '\n'
        l_1_profile = l_1_alarm_indication_cli = l_1_tx_interval_cli = missing
        for l_1_domain in t_1(environment.getattr((undefined(name='cfm') if l_0_cfm is missing else l_0_cfm), 'domains'), 'name'):
            _loop_vars = {}
            pass
            yield '   !\n   domain '
            yield str(environment.getattr(l_1_domain, 'name'))
            yield ' level '
            yield str(environment.getattr(l_1_domain, 'level'))
            yield '\n'
            if t_4(environment.getattr(l_1_domain, 'intermediate_point'), True):
                pass
                yield '      intermediate-point\n'
            for l_2_association in t_1(environment.getattr(l_1_domain, 'associations'), 'id'):
                _loop_vars = {}
                pass
                yield '      !\n      association '
                yield str(environment.getattr(l_2_association, 'id'))
                yield '\n'
                if t_4(environment.getattr(l_2_association, 'direction')):
                    pass
                    yield '         direction '
                    yield str(environment.getattr(l_2_association, 'direction'))
                    yield '\n'
                if t_4(environment.getattr(l_2_association, 'profile')):
                    pass
                    yield '         profile '
                    yield str(environment.getattr(l_2_association, 'profile'))
                    yield '\n'
                if t_4(environment.getattr(l_2_association, 'vlan')):
                    pass
                    yield '         vlan '
                    yield str(environment.getattr(l_2_association, 'vlan'))
                    yield '\n'
                for l_3_remote_end_point in t_1(environment.getattr(l_2_association, 'remote_end_points'), 'id'):
                    _loop_vars = {}
                    pass
                    yield '         !\n         remote end-point '
                    yield str(environment.getattr(l_3_remote_end_point, 'id'))
                    yield '\n'
                    if t_4(environment.getattr(l_3_remote_end_point, 'mac_address')):
                        pass
                        yield '            mac address '
                        yield str(environment.getattr(l_3_remote_end_point, 'mac_address'))
                        yield '\n'
                l_3_remote_end_point = missing
                for l_3_end_point in t_1(environment.getattr(l_2_association, 'end_points'), 'id'):
                    _loop_vars = {}
                    pass
                    yield '         !\n         end-point '
                    yield str(environment.getattr(l_3_end_point, 'id'))
                    yield '\n'
                    if t_4(environment.getattr(l_3_end_point, 'interface')):
                        pass
                        yield '            interface '
                        yield str(environment.getattr(l_3_end_point, 'interface'))
                        yield '\n'
                    if t_4(environment.getattr(l_3_end_point, 'remote_end_point')):
                        pass
                        yield '            remote end-point '
                        yield str(environment.getattr(l_3_end_point, 'remote_end_point'))
                        yield '\n'
                l_3_end_point = missing
            l_2_association = missing
        l_1_domain = missing

blocks = {}
debug_info = '7=36&10=39&13=42&16=45&19=48&21=54&22=56&25=59&26=62&28=64&29=67&31=69&32=72&34=74&37=77&38=79&39=81&40=83&42=86&44=88&47=91&48=94&50=96&51=99&53=101&56=104&57=107&59=109&60=112&62=114&65=117&66=119&67=121&68=123&70=126&72=128&73=131&76=134&78=138&79=142&82=145&84=149&85=151&86=154&88=156&89=159&91=161&92=164&94=166&96=170&97=172&98=175&101=178&103=182&104=184&105=187&107=189&108=192'