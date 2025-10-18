from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos-device-documentation.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_eos_cli_config_gen_documentation = resolve('eos_cli_config_gen_documentation')
    l_0_hostname = resolve('hostname')
    l_0_inventory_hostname = resolve('inventory_hostname')
    l_0_metadata = resolve('metadata')
    l_0_hide_passwords = missing
    try:
        t_1 = environment.filters['arista.avd.default']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.default' found.")
    try:
        t_2 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    l_0_hide_passwords = t_1(environment.getattr((undefined(name='eos_cli_config_gen_documentation') if l_0_eos_cli_config_gen_documentation is missing else l_0_eos_cli_config_gen_documentation), 'hide_passwords'), True)
    context.vars['hide_passwords'] = l_0_hide_passwords
    context.exported_vars.add('hide_passwords')
    yield '# '
    yield str(t_1((undefined(name='hostname') if l_0_hostname is missing else l_0_hostname), (undefined(name='inventory_hostname') if l_0_inventory_hostname is missing else l_0_inventory_hostname)))
    yield '\n'
    if t_2(environment.getattr((undefined(name='metadata') if l_0_metadata is missing else l_0_metadata), 'serial_number')):
        pass
        yield '\nSerial Number: '
        yield str(environment.getattr((undefined(name='metadata') if l_0_metadata is missing else l_0_metadata), 'serial_number'))
        yield '\n'
    if (not t_2(environment.getattr((undefined(name='eos_cli_config_gen_documentation') if l_0_eos_cli_config_gen_documentation is missing else l_0_eos_cli_config_gen_documentation), 'toc'), False)):
        pass
        yield '\n## Table of Contents\n\n<!-- toc -->\n<!-- toc -->\n'
    template = environment.get_template('documentation/management.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/cvx.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/authentication.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/address-locking.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/management-security.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/prompt.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/aliases.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/dhcp-relay.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/dhcp-servers.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/boot.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/kernel.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/monitoring.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/monitor-connectivity.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/monitor-layer1.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/tcam-profile.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/load-balance.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/link-tracking-groups.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/mlag-configuration.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/lldp.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/l2-protocol-forwarding.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/lacp.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/spanning-tree.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/sync-e.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/port-channel.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/vlan-internal-order.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/vlans.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/mac-address-table.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/ip-security.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/interfaces.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/switchport-port-security.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/routing.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/bfd.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/mpls.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/patch-panel.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/queue-monitor.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/multicast.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/filters.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/dot1x.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/poe.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/acl.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/vrfs.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/virtual-source-nat-vrfs.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/platform.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/system-l1.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/application-traffic-recognition.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/router-segment-security.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/router-path-selection.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/router-internet-exit.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/router-l2-vpn.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/ip-dhcp-relay.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/ipv6-dhcp-relay.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/ip-dhcp-snooping.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/ip-nat.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/ip-hardware.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/errdisable.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/mac-security.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/traffic-policies.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/quality-of-service.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/monitor-telemetry-influx.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/priority-flow-control.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/stun.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/maintenance-mode.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('documentation/eos-cli.j2', 'eos-device-documentation.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()

blocks = {}
debug_info = '7=28&8=32&9=34&11=37&13=39&21=42&23=48&25=54&27=60&29=66&31=72&33=78&35=84&37=90&39=96&41=102&43=108&45=114&47=120&49=126&51=132&53=138&55=144&57=150&59=156&61=162&63=168&65=174&67=180&69=186&71=192&73=198&75=204&77=210&79=216&81=222&83=228&85=234&87=240&89=246&91=252&93=258&95=264&97=270&99=276&101=282&103=288&105=294&107=300&109=306&111=312&113=318&115=324&117=330&119=336&121=342&123=348&125=354&127=360&129=366&131=372&133=378&135=384&137=390&139=396&141=402&143=408&145=414'