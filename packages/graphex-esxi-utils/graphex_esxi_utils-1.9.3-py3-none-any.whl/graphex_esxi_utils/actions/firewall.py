from graphex import String, Boolean, Number, Node, InputSocket, OutputSocket, ListOutputSocket
from graphex_esxi_utils import esxi_constants, datatypes
import typing


class FirewallDefaultPolicy(Node):
    name: str = "ESXi Firewall Default Policy"
    description: str = "Get the default policy for the ESXi Firewall (default settings for the firewall, used for ports that are not explicitly opened)."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client.")

    incoming_blocked = OutputSocket(
        datatype=Boolean, name="Incoming Blocked", description="Flag indicating whether incoming traffic should be blocked by default."
    )
    outgoing_blocked = OutputSocket(
        datatype=Boolean, name="Outgoing Blocked", description="Flag indicating whether outgoing traffic should be blocked by default."
    )

    def run(self):
        data = self.esxi_client.firewall.default_policy
        self.incoming_blocked = data["IncomingBlocked"]
        self.outgoing_blocked = data["OutgoingBlocked"]


class FirewallGetRulesets(Node):
    name: str = "ESXi Firewall Get Rulesets"
    description: str = "Get all the rulesets for the ESXi Firewall."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client.")

    rulesets = ListOutputSocket(datatype=datatypes.ESXiFirewallRuleset, name="Rulesets", description="All Rulesets on the ESXi Firewall.")

    def run(self):
        self.rulesets = self.esxi_client.firewall.rulesets.items


class FirewallGetRulesetByKey(Node):
    name: str = "ESXi Firewall Get Ruleset By Key"
    description: str = "Get a particular ruleset by key on the ESXi Firewall."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client.")
    ruleset_key = InputSocket(datatype=String, name="Ruleset Key", description="The ruleset key to find by.")
    error_if_not_found = InputSocket(datatype=Boolean, name="Error If Not Found", description="Whether to raise an error if the ruleset is not found.")

    ruleset = OutputSocket(
        datatype=datatypes.ESXiFirewallRuleset,
        name="Ruleset",
        description="The found ruleset. If not found and 'Error If Not Found' is True, this socket will be disabled.",
    )
    found = OutputSocket(datatype=Boolean, name="Found", description="Whether or not the ruleset was found. Only applicable if 'Error If Not Found' is True.")

    def run(self):
        self.disable_output_socket("Ruleset")
        ruleset = next(iter([ruleset for ruleset in self.esxi_client.firewall.rulesets.items if ruleset.key == self.ruleset_key]), None)
        if not ruleset:
            self.found = False
            if self.error_if_not_found:
                raise RuntimeError(f"Ruleset Key {self.ruleset_key} does not exist.")
        else:
            self.found = True
            self.ruleset = ruleset


class FirewallGetRulesetByLabel(Node):
    name: str = "ESXi Firewall Get Ruleset By Label"
    description: str = "Get a particular ruleset by label on the ESXi Firewall."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client.")
    ruleset_label = InputSocket(datatype=String, name="Ruleset Label", description="The ruleset label to find by.")
    error_if_not_found = InputSocket(datatype=Boolean, name="Error If Not Found", description="Whether to raise an error if the ruleset is not found.")

    ruleset = OutputSocket(
        datatype=datatypes.ESXiFirewallRuleset,
        name="Ruleset",
        description="The found ruleset. If not found and 'Error If Not Found' is True, this socket will be disabled.",
    )
    found = OutputSocket(datatype=Boolean, name="Found", description="Whether or not the ruleset was found. Only applicable if 'Error If Not Found' is True.")

    def run(self):
        self.disable_output_socket("Ruleset")
        ruleset = next(iter([ruleset for ruleset in self.esxi_client.firewall.rulesets.items if ruleset.label == self.ruleset_label]), None)
        if not ruleset:
            self.found = False
            if self.error_if_not_found:
                raise RuntimeError(f"Ruleset Label {self.ruleset_label} does not exist.")
        else:
            self.found = True
            self.ruleset = ruleset


class FirewallGetRulesetByService(Node):
    name: str = "ESXi Firewall Get Ruleset By Service"
    description: str = "Get a particular ruleset by service on the ESXi Firewall. If multiple exist for this service, the first one found will be returned."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client.")
    ruleset_service = InputSocket(datatype=String, name="Ruleset Service", description="The ruleset service to find by.")
    error_if_not_found = InputSocket(datatype=Boolean, name="Error If Not Found", description="Whether to raise an error if the ruleset is not found.")

    ruleset = OutputSocket(
        datatype=datatypes.ESXiFirewallRuleset,
        name="Ruleset",
        description="The found ruleset. If not found and 'Error If Not Found' is True, this socket will be disabled.",
    )
    found = OutputSocket(datatype=Boolean, name="Found", description="Whether or not the ruleset was found. Only applicable if 'Error If Not Found' is True.")

    def run(self):
        self.disable_output_socket("Ruleset")
        ruleset = next(iter([ruleset for ruleset in self.esxi_client.firewall.rulesets.items if ruleset.service == self.ruleset_service]), None)
        if not ruleset:
            self.found = False
            if self.error_if_not_found:
                raise RuntimeError(f"Ruleset Service {self.ruleset_service} does not exist.")
        else:
            self.found = True
            self.ruleset = ruleset


class FirewallGetRulesetsByService(Node):
    name: str = "ESXi Firewall Get Rulesets By Service"
    description: str = "Get all rulesets for a service on the ESXi Firewall."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client.")
    ruleset_service = InputSocket(datatype=String, name="Ruleset Service", description="The ruleset service to find by.")

    rulesets = OutputSocket(
        datatype=datatypes.ESXiFirewallRuleset,
        name="Rulesets",
        description="The found rulesets.",
    )

    def run(self):
        self.rulesets = [ruleset for ruleset in self.esxi_client.firewall.rulesets.items if ruleset.service == self.ruleset_service]


class FirewallRulesetGetKey(Node):
    name: str = "ESXi Firewall Ruleset: Get Key"
    description: str = "Get the key of an ESXi Firewall Ruleset."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL_RULESET

    ruleset = InputSocket(datatype=datatypes.ESXiFirewallRuleset, name="Ruleset", description="The firewall ruleset.")

    value = OutputSocket(datatype=String, name="Key", description="The ruleset key.")

    def run(self):
        self.value = self.ruleset.key


class FirewallRulesetGetLabel(Node):
    name: str = "ESXi Firewall Ruleset: Get Label"
    description: str = "Get the label of an ESXi Firewall Ruleset."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL_RULESET

    ruleset = InputSocket(datatype=datatypes.ESXiFirewallRuleset, name="Ruleset", description="The firewall ruleset.")

    value = OutputSocket(datatype=String, name="Label", description="The ruleset label.")

    def run(self):
        self.value = self.ruleset.label


class FirewallRulesetGetService(Node):
    name: str = "ESXi Firewall Ruleset: Get Service"
    description: str = "Get the service of an ESXi Firewall Ruleset."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL_RULESET

    ruleset = InputSocket(datatype=datatypes.ESXiFirewallRuleset, name="Ruleset", description="The firewall ruleset.")

    value = OutputSocket(
        datatype=String, name="Service", description="The ruleset service. If no service is configured for this ruleset, this will be an empty string."
    )

    def run(self):
        self.value = self.ruleset.service or ""


class FirewallRulesetIsEnabled(Node):
    name: str = "ESXi Firewall Ruleset: Is Enabled"
    description: str = "Check whether the given ESXi Firewall Ruleset is enabled."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL_RULESET

    ruleset = InputSocket(datatype=datatypes.ESXiFirewallRuleset, name="Ruleset", description="The firewall ruleset.")

    is_enabled = OutputSocket(datatype=Boolean, name="Is Enabled", description="Whether the ruleset is enabled.")

    def run(self):
        self.is_enabled = self.ruleset.enabled


class FirewallRulesetGetRules(Node):
    name: str = "ESXi Firewall Ruleset: Get Rules"
    description: str = "Get the rules for an ESXi Firewall Ruleset."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL_RULESET

    ruleset = InputSocket(datatype=datatypes.ESXiFirewallRuleset, name="Ruleset", description="The firewall ruleset.")

    rules = ListOutputSocket(datatype=datatypes.ESXiFirewallRule, name="Rules", description="The ruleset rules.")

    def run(self):
        self.rules = self.ruleset.rules.items


class FirewallRuleGetPorts(Node):
    name: str = "ESXi Firewall Rule: Get Ports"
    description: str = "Get the start and end ports for an ESXi Firewall Rule."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL_RULE

    rule = InputSocket(datatype=datatypes.ESXiFirewallRule, name="Rule", description="The firewall rule.")

    start_port = OutputSocket(
        datatype=Number,
        name="Start Port",
        description="The starting port for the firewall rule. If the rule only defines a single port, this will be the same as 'End Port'.",
    )
    end_port = OutputSocket(
        datatype=Number,
        name="End Port",
        description="The ending port for the firewall rule. If the rule only defines a single port, this will be the same as 'Start Port'.",
    )

    def run(self):
        self.start_port = self.rule.port
        end_port = self.end_port
        self.end_port = end_port if end_port else self.start_port


class FirewallRuleGetDirection(Node):
    name: str = "ESXi Firewall Rule: Get Direction"
    description: str = "Get the direction (inbound or outbound) for an ESXi Firewall Rule."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL_RULE

    rule = InputSocket(datatype=datatypes.ESXiFirewallRule, name="Rule", description="The firewall rule.")

    direction = OutputSocket(
        datatype=String,
        name="Direction",
        description="The direction for the firewall rule. This will be either 'inbound' or 'outbound'.",
    )

    def run(self):
        self.direction = self.rule.direction


class FirewallRuleIsInbound(Node):
    name: str = "ESXi Firewall Rule: Is Inbound"
    description: str = "Get whether the direction for this ESXi Firewall Rule is Inbound."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL_RULE

    rule = InputSocket(datatype=datatypes.ESXiFirewallRule, name="Rule", description="The firewall rule.")

    is_inbound = OutputSocket(
        datatype=Boolean,
        name="Is Inbound",
        description="Whether the direction for this firewall rule is Inbound. If False, the direction is Outbound.",
    )

    def run(self):
        self.is_inbound = self.rule.direction == "inbound"


class FirewallRuleGetPortType(Node):
    name: str = "ESXi Firewall Rule: Get Port Type"
    description: str = "Get the port type (src or dst) for an ESXi Firewall Rule."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL_RULE

    rule = InputSocket(datatype=datatypes.ESXiFirewallRule, name="Rule", description="The firewall rule.")

    porttype = OutputSocket(
        datatype=String,
        name="Port Type",
        description="The port type for the firewall rule. This will be either 'src' or 'dst'.",
    )

    def run(self):
        self.porttype = self.rule.porttype


class FirewallRuleIsSource(Node):
    name: str = "ESXi Firewall Rule: Is Source"
    description: str = "Get whether the port type for this ESXi Firewall Rule is 'src' (i.e. this rule is for traffic with this port as the source)."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL_RULE

    rule = InputSocket(datatype=datatypes.ESXiFirewallRule, name="Rule", description="The firewall rule.")

    is_src = OutputSocket(
        datatype=Boolean,
        name="Is Source",
        description="Whether the port type for this ESXi Firewall Rule is 'src'. If False, the port type is 'dst'.",
    )

    def run(self):
        self.is_src = self.rule.porttype == "src"


class FirewallRuleGetProtocol(Node):
    name: str = "ESXi Firewall Rule: Get Protocol"
    description: str = "Get the protocol (TCP or UDP) for an ESXi Firewall Rule."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL_RULE

    rule = InputSocket(datatype=datatypes.ESXiFirewallRule, name="Rule", description="The firewall rule.")

    protocol = OutputSocket(
        datatype=String,
        name="Protocol",
        description="The protocol for the firewall rule. This will be either 'udp' or 'tcp'.",
    )

    def run(self):
        self.protocol = self.rule.protocol


class FirewallRuleIsTCP(Node):
    name: str = "ESXi Firewall Rule: Is TCP"
    description: str = "Get whether the protocol for this ESXi Firewall Rule is 'tcp' (i.e. this rule is for TCP traffic)."
    categories: typing.List[str] = ["ESXi", "Firewall"]
    color: str = esxi_constants.COLOR_FIREWALL_RULE

    rule = InputSocket(datatype=datatypes.ESXiFirewallRule, name="Rule", description="The firewall rule.")

    is_tcp = OutputSocket(
        datatype=Boolean,
        name="Is TCP",
        description="Whether the protocol for this ESXi Firewall Rule is 'tcp'. If False, the protocol is 'udp'.",
    )

    def run(self):
        self.is_src = self.rule.protocol == "tcp"
