"""
def register_agent(address):
    params = [('address', config()['ui']['url']), ('state', status)]
        name = urlquote(config()['agent']['name'].encode('utf-8'), safe='')
        url = '%s/agents/%s' % (config()['service-capture.admin'][0], name)
        try:
            response = http_request(url, params).decode('utf-8')
            if response:
                logger.info(response)
        except pycurl.error as e:
            logger.warning('Could not set agent state to %s: %s' % (status, e))
"""

import re
from typing import Tuple, List, Optional

import xmltodict


def create_acl_rule_dict(role_name: str, action: str):
    d = {}
    _just_an_example = """
    <Rule RuleId="{ROLE_USER_ADMIN}_write_Permit" Effect="Permit">
		<Target>
			<Actions>
				<Action>
					<ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
						<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">write</AttributeValue>
						<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action-id" DataType="http://www.w3.org/2001/XMLSchema#string"/>
					</ActionMatch>
				</Action>
			</Actions>
		</Target>
		<Condition>
			<Apply FunctionId="urn:oasis:names:tc:xacml:1.0:function:string-is-in">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">{ROLE_USER_ADMIN}</AttributeValue>
				<SubjectAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:2.0:subject:role" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			</Apply>
		</Condition>
	</Rule>
    """
    d["@RuleId"] = f"{role_name}_{action}_Permit"
    d["@Effect"] = "Permit"
    d["Target"] = {
        "Actions": {
            "Action": {
                "ActionMatch": {
                    "@MatchId": "urn:oasis:names:tc:xacml:1.0:function:string-equal",
                    "AttributeValue": {
                        "@DataType": "http://www.w3.org/2001/XMLSchema#string",
                        "#text": action,
                    },
                    "ActionAttributeDesignator": {
                        "@AttributeId": "urn:oasis:names:tc:xacml:1.0:action:action-id",
                        "@DataType": "http://www.w3.org/2001/XMLSchema#string",
                    },
                }
            }
        }
    }
    return d


def create_acl_xml(
    event_id: str,
    role_right_tuples: List[Tuple[str, str]],
    output: Optional[str] = None,
):
    # pylint: disable=line-too-long
    d = {
        "Policy": {
            "@PolicyId": event_id,
            "@Version": "2.0",
            "@RuleCombiningAlgId": "urn:oasis:names:tc:xacml:1.0:rule-combining-algorithm:permit-overrides",
            "@xmlns": "urn:oasis:names:tc:xacml:2.0:policy:schema:os",
            "Target": {
                "Resources": {
                    "Resource": {
                        "ResourceMatch": {
                            "@MatchId": "urn:oasis:names:tc:xacml:1.0:function:string-equal",
                            "AttributeValue": {
                                "@DataType": "http://www.w3.org/2001/XMLSchema#string",
                                "#text": event_id,
                            },
                            "ResourceAttributeDesignator": {
                                "@AttributeId": "urn:oasis:names:tc:xacml:1.0:resource:resource-id",
                                "@DataType": "http://www.w3.org/2001/XMLSchema#string",
                            },
                        }
                    }
                }
            },
        },
    }
    rules = []
    for role_right_tuple in role_right_tuples:
        rules.append(create_acl_rule_dict(role_right_tuple[0], role_right_tuple[1]))

    rules.append({"@RuleId": "DenyRule", "@Effect": "Deny"})
    d["Policy"]["Rule"] = rules
    if output is not None:
        with open(output, "a+", encoding="utf-8") as f:
            xmltodict.unparse(d, pretty=True, output=f)
    else:
        return xmltodict.unparse(d, pretty=True)


def pretty_print_resquest(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in
    this function because it is programmed to be pretty
    printed and may differ from the actual request.
    """
    print(
        "{}\n{}\n{}\n\n{}".format(
            "-----------START-----------",
            req.method + " " + req.url,
            "\n".join(f"{k}: {v}" for k, v in req.headers.items()),
            req.body,
        )
    )


first_cap_re = re.compile("(.)([A-Z][a-z]+)")
all_cap_re = re.compile("([a-z0-9])([A-Z])")


def camel_case_to_snake_case(string):
    """
    Converts a CamelCase string to the corresponding snake_case string
    :param string:
    :return:
    """
    s1 = first_cap_re.sub(r"\1_\2", string)
    return all_cap_re.sub(r"\1_\2", s1).lower()


def main():
    test_str = "HTTPCall and webLogin, readOnly"
    print(camel_case_to_snake_case(test_str))

    create_acl_xml(
        "event_id",
        [("ROLE_USER_ADMIN", "read"), ("ROLE_USER_ADMIN", "write")],
        output="/tmp/test",
    )


if __name__ == "__main__":
    main()
