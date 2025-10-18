from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos-intended-config.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_eos_cli_config_gen_configuration = resolve('eos_cli_config_gen_configuration')
    l_0_hide_passwords = missing
    try:
        t_1 = environment.filters['arista.avd.default']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.default' found.")
    pass
    l_0_hide_passwords = t_1(environment.getattr((undefined(name='eos_cli_config_gen_configuration') if l_0_eos_cli_config_gen_configuration is missing else l_0_eos_cli_config_gen_configuration), 'hide_passwords'), False)
    context.vars['hide_passwords'] = l_0_hide_passwords
    context.exported_vars.add('hide_passwords')
    template = environment.get_template('eos/config-comment.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/boot.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/enable-password.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/aaa-root.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/local-users.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/address-locking.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/agents.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/hardware.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/service-routing-configuration-bgp.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/cfm.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/prompt.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/terminal.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/aliases.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/logging-event-storm-control.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/daemon-terminattr.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/daemons.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/dhcp-relay.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-dhcp-relay.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ipv6-dhcp-relay.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/dhcp-servers.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-dhcp-snooping.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/switchport-default.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/vlan-internal-order.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/errdisable.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/event-monitor.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/flow-tracking.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/hardware-access-list-update-default-result-permit.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-igmp-snooping.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/logging-event-congestion-drops.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/load-interval.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/transceiver-qsfp-default-mode.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/platform-sfe-interface.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/interface-defaults.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/service-routing-protocols-model.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/kernel.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/l2-protocol-forwarding.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/lacp.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/queue-monitor-length.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/monitor-layer1.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/load-balance.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/link-tracking-groups.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/lldp.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/logging.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/match-list-input.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/mcs-client.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-virtual-router-mac-address-mlag-peer.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/monitor-server-radius.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/monitor-twamp.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-name-server-groups.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/platform-trident.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-nat-part1.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/hostname.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-domain-lookup.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-name-servers.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/dns-domain.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/domain-list.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/aaa-server-groups-ldap.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/trackers.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/poe.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/switchport-port-security.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ptp.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/qos-profiles.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/radius-proxy.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/redundancy.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-adaptive-virtual-topology.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-internet-exit.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-l2-vpn.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-path-selection.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-service-insertion.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/platform.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/sflow.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/snmp-server.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/hardware-speed-groups.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/spanning-tree.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/sync-e.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/service-unsupported-transceiver.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/transceiver.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/port-channel.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/system-l1.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/tap-aggregation.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/clock.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/vlans.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/vrfs.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/bgp-groups.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/queue-monitor-streaming.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/banners.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/management-accounts.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/management-api-http.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/management-console.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/management-cvx.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/management-defaults.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/management-api-gnmi.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/management-api-models.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/management-security.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/radius-server.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/aaa-server-groups-radius.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/tacacs-servers.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/aaa-server-groups-tacacs-plus.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/aaa.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/cvx.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/dot1x.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/monitor-telemetry-influx.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-security.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/mac-security.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/port-channel-interfaces.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/dps-interfaces.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ethernet-interfaces.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/loopback-interfaces.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/management-interfaces.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/tunnel-interfaces.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/vlan-interfaces.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/vxlan-interface.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/tcam-profile.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/application-traffic-recognition.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/load-balance-cluster.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/monitor-connectivity.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/mac-address-table-aging-time.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/mac-address-table-static-entries.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/event-handlers.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-segment-security.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/interface-groups.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/interface-profiles.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-virtual-router-mac-address.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/virtual-source-nat-vrfs.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ipv6-access-lists.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ipv6-standard-access-lists.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/access-lists.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-access-lists.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/class-maps-pbr.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/standard-access-lists.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-routing.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-icmp-redirect.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-hardware.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-routing-vrfs.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ipv6-icmp-redirect.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/as-path.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-community-lists.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-extcommunity-lists.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-extcommunity-lists-regexp.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/dynamic-prefix-lists.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/prefix-lists.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ipv6-prefix-lists.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ipv6-unicast-routing.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ipv6-hardware.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ipv6-unicast-routing-vrfs.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ipv6-neighbors.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/mac-access-lists.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/system.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/mac-address-table-notification.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/maintenance.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/monitor-sessions.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/monitor-session-default-encapsulation-gre.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/mlag-configuration.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/static-routes.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/arp.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ipv6-static-routes.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/mpls.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-nat-part2.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-client-source-interfaces.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ntp.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/patch-panel.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/policy-maps-pbr.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/monitor-telemetry-postcard-policy.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/qos.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/class-maps.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/policy-maps-copp.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/policy-maps-qos.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/priority-flow-control.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-radius-source-interfaces.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/roles.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/route-maps.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/peer-filters.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-bfd.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-bgp.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-general.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-traffic-engineering.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-igmp.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-isis.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-multicast.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-ospf.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ipv6-router-ospf.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-pim-sparse-mode.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-msdp.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/router-rip.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/stun.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/ip-tacacs-source-interfaces.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/traffic-policies.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/platform-apply.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/platform-headroom-pool.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/vmtracer-sessions.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/dot1x_part2.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/management-ssh.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/management-tech-support.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/eos-cli.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()
    template = environment.get_template('eos/end.j2', 'eos-intended-config.j2')
    gen = template.root_render_func(template.new_context(context.get_all(), True, {'hide_passwords': l_0_hide_passwords}))
    try:
        for event in gen:
            yield event
    finally: gen.close()

blocks = {}
debug_info = '8=19&9=22&11=28&13=34&15=40&17=46&19=52&21=58&23=64&25=70&27=76&29=82&31=88&33=94&35=100&37=106&39=112&41=118&43=124&45=130&47=136&49=142&51=148&53=154&55=160&57=166&59=172&61=178&63=184&65=190&67=196&69=202&71=208&73=214&75=220&77=226&79=232&81=238&83=244&85=250&87=256&89=262&91=268&93=274&95=280&97=286&99=292&101=298&103=304&105=310&107=316&109=322&111=328&113=334&115=340&117=346&119=352&121=358&123=364&125=370&127=376&129=382&131=388&133=394&135=400&137=406&139=412&141=418&143=424&145=430&147=436&149=442&151=448&153=454&155=460&157=466&159=472&161=478&163=484&165=490&167=496&169=502&171=508&173=514&175=520&177=526&179=532&181=538&183=544&185=550&187=556&189=562&191=568&193=574&195=580&197=586&199=592&201=598&203=604&205=610&207=616&209=622&211=628&213=634&215=640&217=646&219=652&221=658&223=664&225=670&227=676&229=682&231=688&233=694&235=700&237=706&239=712&241=718&243=724&245=730&247=736&249=742&251=748&253=754&255=760&257=766&259=772&261=778&263=784&265=790&267=796&269=802&271=808&273=814&275=820&277=826&279=832&281=838&283=844&285=850&287=856&289=862&291=868&293=874&295=880&297=886&299=892&301=898&303=904&305=910&307=916&309=922&310=928&312=934&314=940&316=946&318=952&320=958&322=964&324=970&326=976&328=982&330=988&332=994&334=1000&336=1006&338=1012&340=1018&342=1024&344=1030&346=1036&348=1042&350=1048&352=1054&354=1060&356=1066&358=1072&360=1078&362=1084&364=1090&366=1096&368=1102&370=1108&372=1114&374=1120&376=1126&378=1132&380=1138&382=1144&384=1150&386=1156&388=1162&390=1168&392=1174&394=1180&396=1186'