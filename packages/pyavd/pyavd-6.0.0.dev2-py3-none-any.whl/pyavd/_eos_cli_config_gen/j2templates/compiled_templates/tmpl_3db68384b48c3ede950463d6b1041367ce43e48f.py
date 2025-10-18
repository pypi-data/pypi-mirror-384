from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'documentation/cfm.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_cfm = resolve('cfm')
    l_0_domains = resolve('domains')
    l_0_cfm_domain_associations = resolve('cfm_domain_associations')
    l_0_associations = resolve('associations')
    l_0_cfm_domain_end_points = resolve('cfm_domain_end_points')
    l_0_cfm_domain_remote_end_points = resolve('cfm_domain_remote_end_points')
    l_0_profiles = resolve('profiles')
    l_0_cfm_profile_continuity_check = resolve('cfm_profile_continuity_check')
    l_0_cfm_profile_alarm_indication = resolve('cfm_profile_alarm_indication')
    l_0_cfm_profile_delay_measurement = resolve('cfm_profile_delay_measurement')
    l_0_cfm_profile_loss_measurement = resolve('cfm_profile_loss_measurement')
    l_0_cfm_profile_synthetic_loss_measurement = resolve('cfm_profile_synthetic_loss_measurement')
    try:
        t_1 = environment.filters['arista.avd.default']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.default' found.")
    try:
        t_2 = environment.filters['arista.avd.natural_sort']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.natural_sort' found.")
    try:
        t_3 = environment.filters['join']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No filter named 'join' found.")
    try:
        t_4 = environment.filters['list']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No filter named 'list' found.")
    try:
        t_5 = environment.filters['map']
    except KeyError:
        @internalcode
        def t_5(*unused):
            raise TemplateRuntimeError("No filter named 'map' found.")
    try:
        t_6 = environment.filters['selectattr']
    except KeyError:
        @internalcode
        def t_6(*unused):
            raise TemplateRuntimeError("No filter named 'selectattr' found.")
    try:
        t_7 = environment.filters['sum']
    except KeyError:
        @internalcode
        def t_7(*unused):
            raise TemplateRuntimeError("No filter named 'sum' found.")
    try:
        t_8 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_8(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_8((undefined(name='cfm') if l_0_cfm is missing else l_0_cfm)):
        pass
        yield '\n### Connectivity Fault Management (CFM)\n'
        if t_8(environment.getattr((undefined(name='cfm') if l_0_cfm is missing else l_0_cfm), 'domains')):
            pass
            l_0_domains = t_2(environment.getattr((undefined(name='cfm') if l_0_cfm is missing else l_0_cfm), 'domains'), 'name')
            context.vars['domains'] = l_0_domains
            context.exported_vars.add('domains')
            l_0_cfm_domain_associations = t_4(context.eval_ctx, t_6(context, (undefined(name='domains') if l_0_domains is missing else l_0_domains), 'associations', 'arista.avd.defined'))
            context.vars['cfm_domain_associations'] = l_0_cfm_domain_associations
            context.exported_vars.add('cfm_domain_associations')
            l_0_associations = t_7(environment, t_5(context, (undefined(name='cfm_domain_associations') if l_0_cfm_domain_associations is missing else l_0_cfm_domain_associations), attribute='associations'), start=[])
            context.vars['associations'] = l_0_associations
            context.exported_vars.add('associations')
            l_0_cfm_domain_end_points = t_4(context.eval_ctx, t_6(context, (undefined(name='associations') if l_0_associations is missing else l_0_associations), 'end_points', 'arista.avd.defined'))
            context.vars['cfm_domain_end_points'] = l_0_cfm_domain_end_points
            context.exported_vars.add('cfm_domain_end_points')
            l_0_cfm_domain_remote_end_points = t_4(context.eval_ctx, t_6(context, (undefined(name='associations') if l_0_associations is missing else l_0_associations), 'remote_end_points', 'arista.avd.defined'))
            context.vars['cfm_domain_remote_end_points'] = l_0_cfm_domain_remote_end_points
            context.exported_vars.add('cfm_domain_remote_end_points')
            yield '\n#### CFM Domains Summary\n\n| Name | Level | Intermediate Point |\n| ---- | ----- | ------------------ |\n'
            for l_1_domain in (undefined(name='domains') if l_0_domains is missing else l_0_domains):
                _loop_vars = {}
                pass
                yield '| '
                yield str(environment.getattr(l_1_domain, 'name'))
                yield ' | '
                yield str(environment.getattr(l_1_domain, 'level'))
                yield ' | '
                yield str(t_1(environment.getattr(l_1_domain, 'intermediate_point'), '-'))
                yield ' |\n'
            l_1_domain = missing
            if (undefined(name='cfm_domain_associations') if l_0_cfm_domain_associations is missing else l_0_cfm_domain_associations):
                pass
                yield '\n##### CFM Domain Associations\n\n| Domain | Association ID | Direction | Profile | VLAN |\n| ------ | -------------- | --------- | ------- | ---- |\n'
                for l_1_domain in (undefined(name='cfm_domain_associations') if l_0_cfm_domain_associations is missing else l_0_cfm_domain_associations):
                    _loop_vars = {}
                    pass
                    for l_2_association in t_2(environment.getattr(l_1_domain, 'associations'), 'id'):
                        _loop_vars = {}
                        pass
                        yield '| '
                        yield str(environment.getattr(l_1_domain, 'name'))
                        yield ' | '
                        yield str(environment.getattr(l_2_association, 'id'))
                        yield ' | '
                        yield str(t_1(environment.getattr(l_2_association, 'direction'), '-'))
                        yield ' | '
                        yield str(t_1(environment.getattr(l_2_association, 'profile'), '-'))
                        yield ' | '
                        yield str(t_1(environment.getattr(l_2_association, 'vlan'), '-'))
                        yield ' |\n'
                    l_2_association = missing
                l_1_domain = missing
            if (undefined(name='cfm_domain_end_points') if l_0_cfm_domain_end_points is missing else l_0_cfm_domain_end_points):
                pass
                yield '\n##### CFM Domain Endpoints\n\n| Domain | Association ID | Endpoint ID | Remote Endpoint ID | Interface |\n| ------ | -------------- | ----------- | ------------------ | --------- |\n'
                for l_1_domain in (undefined(name='cfm_domain_associations') if l_0_cfm_domain_associations is missing else l_0_cfm_domain_associations):
                    _loop_vars = {}
                    pass
                    for l_2_association in t_2(environment.getattr(l_1_domain, 'associations'), 'id'):
                        _loop_vars = {}
                        pass
                        for l_3_endpoint in t_2(environment.getattr(l_2_association, 'end_points'), 'id'):
                            _loop_vars = {}
                            pass
                            yield '| '
                            yield str(environment.getattr(l_1_domain, 'name'))
                            yield ' | '
                            yield str(environment.getattr(l_2_association, 'id'))
                            yield ' | '
                            yield str(environment.getattr(l_3_endpoint, 'id'))
                            yield ' | '
                            yield str(t_1(environment.getattr(l_3_endpoint, 'remote_end_point'), '-'))
                            yield ' | '
                            yield str(t_1(environment.getattr(l_3_endpoint, 'interface'), '-'))
                            yield ' |\n'
                        l_3_endpoint = missing
                    l_2_association = missing
                l_1_domain = missing
            if (undefined(name='cfm_domain_remote_end_points') if l_0_cfm_domain_remote_end_points is missing else l_0_cfm_domain_remote_end_points):
                pass
                yield '\n##### CFM Domain Remote Endpoints\n\n| Domain | Association ID | Remote Endpoint ID | MAC Address |\n| ------ | -------------- | ------------------ | ----------- |\n'
                for l_1_domain in (undefined(name='cfm_domain_associations') if l_0_cfm_domain_associations is missing else l_0_cfm_domain_associations):
                    _loop_vars = {}
                    pass
                    for l_2_association in t_2(environment.getattr(l_1_domain, 'associations'), 'id'):
                        _loop_vars = {}
                        pass
                        for l_3_remote_endpoint in t_2(environment.getattr(l_2_association, 'remote_end_points'), 'id'):
                            _loop_vars = {}
                            pass
                            yield '| '
                            yield str(environment.getattr(l_1_domain, 'name'))
                            yield ' | '
                            yield str(environment.getattr(l_2_association, 'id'))
                            yield ' | '
                            yield str(environment.getattr(l_3_remote_endpoint, 'id'))
                            yield ' | '
                            yield str(t_1(environment.getattr(l_3_remote_endpoint, 'mac_address'), '-'))
                            yield ' |\n'
                        l_3_remote_endpoint = missing
                    l_2_association = missing
                l_1_domain = missing
        if t_8(environment.getattr((undefined(name='cfm') if l_0_cfm is missing else l_0_cfm), 'profiles')):
            pass
            l_0_profiles = t_2(environment.getattr((undefined(name='cfm') if l_0_cfm is missing else l_0_cfm), 'profiles'), 'name')
            context.vars['profiles'] = l_0_profiles
            context.exported_vars.add('profiles')
            l_0_cfm_profile_continuity_check = t_4(context.eval_ctx, t_6(context, (undefined(name='profiles') if l_0_profiles is missing else l_0_profiles), 'continuity_check', 'arista.avd.defined'))
            context.vars['cfm_profile_continuity_check'] = l_0_cfm_profile_continuity_check
            context.exported_vars.add('cfm_profile_continuity_check')
            l_0_cfm_profile_alarm_indication = t_4(context.eval_ctx, t_6(context, (undefined(name='profiles') if l_0_profiles is missing else l_0_profiles), 'alarm_indication', 'arista.avd.defined'))
            context.vars['cfm_profile_alarm_indication'] = l_0_cfm_profile_alarm_indication
            context.exported_vars.add('cfm_profile_alarm_indication')
            l_0_cfm_profile_delay_measurement = t_4(context.eval_ctx, t_6(context, (undefined(name='profiles') if l_0_profiles is missing else l_0_profiles), 'measurement.delay', 'arista.avd.defined'))
            context.vars['cfm_profile_delay_measurement'] = l_0_cfm_profile_delay_measurement
            context.exported_vars.add('cfm_profile_delay_measurement')
            l_0_cfm_profile_loss_measurement = t_4(context.eval_ctx, t_6(context, (undefined(name='profiles') if l_0_profiles is missing else l_0_profiles), 'measurement.loss', 'arista.avd.defined'))
            context.vars['cfm_profile_loss_measurement'] = l_0_cfm_profile_loss_measurement
            context.exported_vars.add('cfm_profile_loss_measurement')
            l_0_cfm_profile_synthetic_loss_measurement = t_4(context.eval_ctx, t_6(context, (undefined(name='profiles') if l_0_profiles is missing else l_0_profiles), 'measurement.loss.synthetic', 'arista.avd.defined'))
            context.vars['cfm_profile_synthetic_loss_measurement'] = l_0_cfm_profile_synthetic_loss_measurement
            context.exported_vars.add('cfm_profile_synthetic_loss_measurement')
            yield '\n#### CFM Profiles Summary\n'
            if (undefined(name='cfm_profile_continuity_check') if l_0_cfm_profile_continuity_check is missing else l_0_cfm_profile_continuity_check):
                pass
                yield '\n##### CFM Profile Continuity Check\n\n| Profile | Enabled | QoS COS | TX Interval | Alarm Defects |\n| ------- | ------- | ------- | ----------- | ------------- |\n'
                for l_1_profile in (undefined(name='cfm_profile_continuity_check') if l_0_cfm_profile_continuity_check is missing else l_0_cfm_profile_continuity_check):
                    l_1_enabled_defects = missing
                    _loop_vars = {}
                    pass
                    l_1_enabled_defects = '-'
                    _loop_vars['enabled_defects'] = l_1_enabled_defects
                    if t_8(environment.getattr(environment.getattr(l_1_profile, 'continuity_check'), 'alarm_defects')):
                        pass
                        l_1_enabled_defects = t_3(context.eval_ctx, environment.getattr(environment.getattr(l_1_profile, 'continuity_check'), 'alarm_defects'), ', ')
                        _loop_vars['enabled_defects'] = l_1_enabled_defects
                    yield '| '
                    yield str(environment.getattr(l_1_profile, 'name'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(l_1_profile, 'continuity_check'), 'enabled'), '-'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(l_1_profile, 'continuity_check'), 'qos_cos'), '-'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(l_1_profile, 'continuity_check'), 'tx_interval'), '-'))
                    yield ' | '
                    yield str((undefined(name='enabled_defects') if l_1_enabled_defects is missing else l_1_enabled_defects))
                    yield ' |\n'
                l_1_profile = l_1_enabled_defects = missing
            if (undefined(name='cfm_profile_alarm_indication') if l_0_cfm_profile_alarm_indication is missing else l_0_cfm_profile_alarm_indication):
                pass
                yield '\n##### CFM Profile Alarm Indication\n\n| Profile | Enabled | Client Domain Level | TX Interval |\n| ------- | ------- | ------------------- | ----------- |\n'
                for l_1_profile in (undefined(name='cfm_profile_alarm_indication') if l_0_cfm_profile_alarm_indication is missing else l_0_cfm_profile_alarm_indication):
                    _loop_vars = {}
                    pass
                    yield '| '
                    yield str(environment.getattr(l_1_profile, 'name'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(l_1_profile, 'alarm_indication'), 'enabled'), '-'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(l_1_profile, 'alarm_indication'), 'client_domain_level'), '-'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(l_1_profile, 'alarm_indication'), 'tx_interval'), '-'))
                    yield ' |\n'
                l_1_profile = missing
            if (undefined(name='cfm_profile_delay_measurement') if l_0_cfm_profile_delay_measurement is missing else l_0_cfm_profile_delay_measurement):
                pass
                yield '\n##### CFM Profile Delay Measurement\n\n| Profile | Single Ended | QoS COS | TX Interval |\n| ------- | ------------ | ------- | ----------- |\n'
                for l_1_profile in (undefined(name='cfm_profile_delay_measurement') if l_0_cfm_profile_delay_measurement is missing else l_0_cfm_profile_delay_measurement):
                    _loop_vars = {}
                    pass
                    yield '| '
                    yield str(environment.getattr(l_1_profile, 'name'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'delay'), 'single_ended'), '-'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'delay'), 'qos_cos'), '-'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'delay'), 'tx_interval'), '-'))
                    yield ' |\n'
                l_1_profile = missing
            if (undefined(name='cfm_profile_loss_measurement') if l_0_cfm_profile_loss_measurement is missing else l_0_cfm_profile_loss_measurement):
                pass
                yield '\n##### CFM Profile Loss Measurement\n\n| Profile | Enabled | Single Ended | QoS COS | TX Interval |\n| ------- | ------- | ------------ | ------- | ----------- |\n'
                for l_1_profile in (undefined(name='cfm_profile_loss_measurement') if l_0_cfm_profile_loss_measurement is missing else l_0_cfm_profile_loss_measurement):
                    _loop_vars = {}
                    pass
                    yield '| '
                    yield str(environment.getattr(l_1_profile, 'name'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'enabled'), '-'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'single_ended'), '-'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'qos_cos'), '-'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'tx_interval'), '-'))
                    yield ' |\n'
                l_1_profile = missing
            if (undefined(name='cfm_profile_synthetic_loss_measurement') if l_0_cfm_profile_synthetic_loss_measurement is missing else l_0_cfm_profile_synthetic_loss_measurement):
                pass
                yield '\n##### CFM Profile Synthetic Loss Measurement\n\n| Profile | Enabled | Single Ended | QoS COS | TX Interval | Period Frames |\n| ------- | ------- | ------------ | ------- | ----------- | ------------- |\n'
                for l_1_profile in (undefined(name='cfm_profile_synthetic_loss_measurement') if l_0_cfm_profile_synthetic_loss_measurement is missing else l_0_cfm_profile_synthetic_loss_measurement):
                    _loop_vars = {}
                    pass
                    yield '| '
                    yield str(environment.getattr(l_1_profile, 'name'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'synthetic'), 'enabled'), '-'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'synthetic'), 'single_ended'), '-'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'synthetic'), 'qos_cos'), '-'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'synthetic'), 'tx_interval'), 'interval'), '-'))
                    yield ' | '
                    yield str(t_1(environment.getattr(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'measurement'), 'loss'), 'synthetic'), 'tx_interval'), 'period_frames'), '-'))
                    yield ' |\n'
                l_1_profile = missing
        yield '\n#### CFM Device Configuration\n\n```eos\n'
        template = environment.get_template('eos/cfm.j2', 'documentation/cfm.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {'associations': l_0_associations, 'cfm_domain_associations': l_0_cfm_domain_associations, 'cfm_domain_end_points': l_0_cfm_domain_end_points, 'cfm_domain_remote_end_points': l_0_cfm_domain_remote_end_points, 'cfm_profile_alarm_indication': l_0_cfm_profile_alarm_indication, 'cfm_profile_continuity_check': l_0_cfm_profile_continuity_check, 'cfm_profile_delay_measurement': l_0_cfm_profile_delay_measurement, 'cfm_profile_loss_measurement': l_0_cfm_profile_loss_measurement, 'cfm_profile_synthetic_loss_measurement': l_0_cfm_profile_synthetic_loss_measurement, 'domains': l_0_domains, 'profiles': l_0_profiles}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        yield '```\n'

blocks = {}
debug_info = '7=71&10=74&11=76&12=79&13=82&14=85&15=88&21=92&22=96&24=103&30=106&31=109&32=113&36=125&42=128&43=131&44=134&45=138&50=151&56=154&57=157&58=160&59=164&65=175&66=177&67=180&68=183&69=186&70=189&71=192&74=196&80=199&81=203&82=205&83=207&85=210&88=221&94=224&95=228&98=237&104=240&105=244&108=253&114=256&115=260&118=271&124=274&125=278&133=292'